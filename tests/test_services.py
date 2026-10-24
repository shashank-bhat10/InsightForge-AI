import json
import numpy as np
import pandas as pd
import pytest
from app.services.dataset_service import load_dataset, get_dataset_preview
from app.services.forecast_service import get_forecast_columns, generate_forecast, _parse_date_column
from app.services.ml_service import train_and_compare_models, _build_preprocessor, _build_pipeline
from app.services.ai_service import generate_ai_response
from sklearn.linear_model import LinearRegression


def test_missing_and_infinite_values(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("category,value\na,1\n,inf\nb,\n")
    df = load_dataset(str(path))
    assert df["value"].isna().sum() == 2
    json.dumps(get_dataset_preview(str(path)), allow_nan=False)


def test_excel_and_invalid_file(tmp_path):
    path = tmp_path / "data.xlsx"
    pd.DataFrame({"a": [1, 2]}).to_excel(path, index=False)
    assert len(load_dataset(str(path))) == 2
    with pytest.raises(ValueError):
        load_dataset(str(tmp_path / "missing.csv"))


@pytest.mark.parametrize("problem", ["classification", "regression"])
def test_ml_mixed_missing_and_dates(tmp_path, problem):
    n = 60
    df = pd.DataFrame({"date": pd.date_range("2025-01-01", periods=n), "x": [np.nan if i%9==0 else i for i in range(n)], "category": ["a", "b", "c"] * 20, "target": [i%2 if problem=="classification" else i*2+1 for i in range(n)]})
    df.loc[0, "target"] = np.nan
    path = tmp_path / "ml.csv"
    df.to_csv(path, index=False)
    result = train_and_compare_models(str(path), "target", problem)
    assert result["rows_used"] == 59
    assert result["train_rows"] + result["test_rows"] == 59
    assert all("error" not in model for model in result["models"]), result
    assert result["explainability"]["features"]
    json.dumps(result, allow_nan=False)


def test_preprocessors_are_independent():
    pre = _build_preprocessor(pd.DataFrame({"x": [1, 2]}))
    first = _build_pipeline(pre, LinearRegression())
    second = _build_pipeline(pre, LinearRegression())
    assert first.named_steps["preprocessor"] is not second.named_steps["preprocessor"]


def test_forecast_detection_and_month_end(tmp_path):
    path = tmp_path / "forecast.csv"
    pd.DataFrame({"date": pd.date_range("2024-01-01", periods=12, freq="MS"), "sales": range(12)}).to_csv(path, index=False)
    assert get_forecast_columns(str(path))["date_columns"] == ["date"]
    result = generate_forecast(str(path), "date", "sales", 3, "M")
    assert result["frequency"] == "ME"
    assert len(result["forecast"]) == 3
    assert _parse_date_column(pd.Series([1700000000000, 1700086400000]), "timestamp").iloc[0].year == 2023


def test_ai_failure_is_sanitized(monkeypatch):
    from app.services import ai_service
    monkeypatch.setattr(ai_service.settings, "GEMINI_API_KEY", "fake-test-key")
    def broken():
        raise RuntimeError("sensitive-provider-details")
    monkeypatch.setattr(ai_service, "_client", broken)
    result = generate_ai_response("Hello")
    assert not result["success"]
    assert "sensitive" not in result["response"]


@pytest.mark.parametrize("target,problem", [("missing", "auto"), ("target", "invalid")])
def test_invalid_ml_requests(tmp_path, target, problem):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"x": range(20), "target": [0, 1]*10}).to_csv(path, index=False)
    with pytest.raises(ValueError):
        train_and_compare_models(str(path), target, problem)


def test_ai_success_and_empty_response(monkeypatch):
    from types import SimpleNamespace
    from app.services import ai_service
    monkeypatch.setattr(ai_service, "_client", lambda: SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs: SimpleNamespace(text="Mocked answer"))))
    assert generate_ai_response("Hello")["response"] == "Mocked answer"
    monkeypatch.setattr(ai_service, "_client", lambda: SimpleNamespace(models=SimpleNamespace(generate_content=lambda **kwargs: SimpleNamespace(text=None))))
    assert not generate_ai_response("Hello")["success"]



def test_jwt_expiry_and_signature():
    import jwt
    from datetime import datetime, timedelta, timezone
    from app.auth.jwt_handler import create_access_token, verify_token
    from app.config.settings import settings
    token = create_access_token({"sub": "student@example.com"})
    assert verify_token(token)["sub"] == "student@example.com"
    expired = jwt.encode({"sub": "student@example.com", "exp": datetime.now(timezone.utc)-timedelta(seconds=10)}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    assert verify_token(expired) is None
    forged = jwt.encode({"sub": "student@example.com"}, "different-test-key-which-is-at-least-32-bytes", algorithm=settings.ALGORITHM)
    assert verify_token(forged) is None



def test_password_hashing_validation():
    from app.auth.hashing import hash_password, verify_password
    hashed = hash_password("StrongPass123")
    assert verify_password("StrongPass123", hashed)
    assert not verify_password("wrong", hashed)
    assert not verify_password("x"*73, hashed)
    assert not verify_password("StrongPass123", "malformed")
    with pytest.raises(ValueError):
        hash_password("short")
