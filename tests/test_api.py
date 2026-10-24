from conftest import register
from app.config.settings import settings
import pytest


def upload(client, auth, content=b"category,value\na,1\nb,2\na,3\n", filename="sample.csv"):
    return client.post("/api/v1/datasets/", headers=auth, files={"file": (filename, content)})


def test_auth_and_validation(client, auth):
    assert client.get("/health").status_code == 200
    assert client.get("/me", headers=auth).json()["email"] == "student@example.com"
    assert client.get("/api/v1/datasets/").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
    assert client.post("/login", data={"username": "student@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/register", json={"full_name": "a", "email": "bad", "password": "x"}).status_code == 422
    assert client.post("/register", json={"full_name": "a", "email": "student@example.com", "password": "StrongPass123"}).status_code == 400


def test_dataset_analytics_and_ownership(client, auth):
    response = upload(client, auth)
    assert response.status_code == 200, response.text
    dataset_id = response.json()["id"]
    base = f"/api/v1/analytics/{dataset_id}"
    for endpoint in ["preview", "summary", "statistics", "insights", "grouped-analysis", "quality", "advanced"]:
        result = client.get(f"{base}/{endpoint}", headers=auth)
        assert result.status_code == 200, result.text
    assert client.get(f"{base}/summary", headers=auth).json()["rows"] == 3
    assert client.get(f"{base}/grouped-analysis", headers=auth).json()["category_by_value"][0]["total"] == 4
    other = register(client, "other@example.com")
    assert client.get(f"/api/v1/datasets/{dataset_id}", headers=other).status_code == 404
    assert client.delete(f"/api/v1/datasets/{dataset_id}", headers=other).status_code == 404
    assert client.delete(f"/api/v1/datasets/{dataset_id}", headers=auth).status_code == 200
    assert client.get(f"/api/v1/datasets/{dataset_id}", headers=auth).status_code == 404


def test_bad_uploads_and_cleanup(client, auth, tmp_path, monkeypatch):
    for filename, content in [("bad.csv", b""), ("bad.csv", b"a,b\n"), ("bad.xlsx", b"invalid"), ("bad.txt", b"a\n1")]:
        assert upload(client, auth, content, filename).status_code == 400
    monkeypatch.setattr(settings, "MAX_UPLOAD_BYTES", 5)
    assert upload(client, auth).status_code == 413
    assert not list(tmp_path.iterdir())
    assert client.get("/api/v1/datasets/", headers=auth).json() == []


def test_conversation_crud_and_ai_missing_key(client, auth):
    response = client.post("/api/v1/conversations/", headers=auth, json={"title": "Demo"})
    cid = response.json()["id"]
    assert client.put(f"/api/v1/conversations/{cid}", headers=auth, json={"title": "Renamed"}).status_code == 200
    other = register(client, "other@example.com")
    assert client.put(f"/api/v1/conversations/{cid}", headers=other, json={"title": "No"}).status_code == 404
    assert client.post("/api/v1/ai/chat", headers=auth, json={"prompt": "Hello", "conversation_id": cid}).status_code == 503
    assert client.post("/api/v1/ai/chat", headers=auth, json={"prompt": ""}).status_code == 422
    assert client.delete(f"/api/v1/conversations/{cid}", headers=auth).status_code == 200


def test_ml_and_forecast_api(client, auth):
    content = "date,category,x,target\n" + "".join(f"2025-{i//28+1:02d}-{i%28+1:02d},{'a' if i%2 else 'b'},{i},{i*2+3}\n" for i in range(56))
    did = upload(client, auth, content.encode()).json()["id"]
    trained = client.post(f"/api/v1/ml/{did}/train", headers=auth, json={"target_column": "target", "problem_type": "regression"})
    assert trained.status_code == 200, trained.text
    assert len(trained.json()["models"]) == 4
    assert all("error" not in m for m in trained.json()["models"])
    forecast = client.post(f"/api/v1/forecast/{did}/predict", headers=auth, json={"date_column": "date", "target_column": "target", "periods": 3, "frequency": "D"})
    assert forecast.status_code == 200, forecast.text
    assert len(forecast.json()["forecast"]) == 3
    assert client.post(f"/api/v1/ml/{did}/train", headers=auth, json={"target_column": "missing"}).status_code == 400
    assert client.post(f"/api/v1/forecast/{did}/predict", headers=auth, json={"date_column": "date", "target_column": "target", "periods": 0}).status_code == 422


def test_failed_database_upload_removes_file(client, auth, tmp_path, monkeypatch):
    from app.routers import dataset

    def failed_save(**kwargs):
        raise RuntimeError("simulated database failure")

    monkeypatch.setattr(dataset, "create_dataset", failed_save)
    with pytest.raises(RuntimeError, match="simulated database failure"):
        upload(client, auth)
    assert not list(tmp_path.iterdir())


def test_missing_upload_and_ai_failure_cleanup(client, auth):
    from pathlib import Path
    result = upload(client, auth)
    did = result.json()["id"]
    Path(result.json()["file_path"]).unlink()
    assert client.get(f"/api/v1/analytics/{did}/summary", headers=auth).status_code == 400
    assert client.post("/api/v1/ai/chat", headers=auth, json={"prompt": "Hello"}).status_code == 503
    assert client.get("/api/v1/conversations/", headers=auth).json() == []
