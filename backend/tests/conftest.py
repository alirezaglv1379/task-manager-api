from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "test-only-secret-key-with-at-least-32-bytes-long")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("COOKIE_SECURE", "false")
os.environ.setdefault("CSRF_TRUSTED_ORIGINS", "http://testserver,http://localhost:5173")
os.environ.setdefault("CORS_ORIGINS", "http://testserver,http://localhost:5173")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def db_session_factory(tmp_path):
    database_file = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{database_file}",
        connect_args={"check_same_thread": False, "timeout": 15},
    )

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=15000")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    yield factory
    engine.dispose()


@pytest.fixture
def client(db_session_factory):
    application = create_app()

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()


def signup(client: TestClient, username: str = "testuser", password: str = "StrongPass123"):
    return client.post("/signup", json={"username": username, "password": password})


def login(client: TestClient, username: str = "testuser", password: str = "StrongPass123"):
    return client.post("/login", data={"username": username, "password": password})


def auth_headers(client: TestClient, username: str = "testuser", password: str = "StrongPass123"):
    response = login(client, username, password)
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
