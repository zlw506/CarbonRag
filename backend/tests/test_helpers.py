from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.auth.service import AuthService

TEST_OWNER_USER_ID = "user-test-owner"
TEST_PASSWORD = "pass123456"


def build_test_auth_service(db_path: Path | str) -> AuthService:
    return AuthService(sqlite_db_path=db_path)


def create_test_user_id(db_path: Path | str, *, prefix: str = "owner") -> str:
    auth_service = build_test_auth_service(db_path)
    user = auth_service.register(
        {
            "username": f"{prefix}-{uuid4().hex[:10]}",
            "password": TEST_PASSWORD,
        }
    )
    return user.user_id


def patch_test_auth_service(monkeypatch, *, db_path: Path | str) -> AuthService:
    auth_service = build_test_auth_service(db_path)
    monkeypatch.setattr("app.auth.service.get_auth_service", lambda: auth_service)
    monkeypatch.setattr("app.auth.dependencies.get_auth_service", lambda: auth_service)
    monkeypatch.setattr("app.api.v1.endpoints.auth.get_auth_service", lambda: auth_service)
    return auth_service


def register_and_login(client: TestClient, *, prefix: str = "tester") -> dict:
    client.cookies.clear()
    username = f"{prefix}-{uuid4().hex[:10]}"
    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": TEST_PASSWORD},
    )
    assert register_response.status_code == 200, register_response.text

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": TEST_PASSWORD},
    )
    assert login_response.status_code == 200, login_response.text
    return login_response.json()["user"]
