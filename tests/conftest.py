import os
import uuid
from dotenv import dotenv_values
from pathlib import Path

postgres_url = None
if os.environ.get("INSIGHTFORGE_TEST_POSTGRES") == "1":
    values = {}
    root = Path(__file__).resolve().parents[1]
    for name in [root / "backend/.env", root / ".env"]:
        values.update(dotenv_values(name))
    postgres_url = os.environ.get("TEST_DATABASE_URL") or values.get("DATABASE_URL")

# Never connect automated tests to the developer database or AI account.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-only-secret-not-for-deployment"
os.environ["GEMINI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database.base import Base
from app.database.session import get_db
from app.routers import dataset


@pytest.fixture
def client(tmp_path, monkeypatch):
    admin_engine = None
    schema = None
    if postgres_url:
        from sqlalchemy import text
        schema = "insightforge_test_" + uuid.uuid4().hex
        admin_engine = create_engine(postgres_url)
        with admin_engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(postgres_url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)

    def test_db():
        with sessions() as session:
            yield session

    monkeypatch.setattr(dataset, "UPLOAD_DIR", tmp_path)
    app.dependency_overrides[get_db] = test_db
    # Startup is tested separately; this client uses only its isolated database.
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()
    if admin_engine is not None:
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()


def register(client, email="student@example.com"):
    response = client.post("/register", json={"full_name": "Test Student", "email": email, "password": "StrongPass123"})
    assert response.status_code == 200, response.text
    login = client.post("/login", data={"username": email, "password": "StrongPass123"})
    assert login.status_code == 200, login.text
    return {"Authorization": "Bearer " + login.json()["access_token"]}


@pytest.fixture
def auth(client):
    return register(client)
