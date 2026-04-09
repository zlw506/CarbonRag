from fastapi.testclient import TestClient

from app.main import app
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import TEST_PASSWORD, patch_test_auth_service

client = TestClient(app)


def build_session_service(tmp_path) -> SessionService:
    store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    return SessionService(store=store)


def test_auth_register_login_logout_and_me(monkeypatch, tmp_path) -> None:
    session_service = build_session_service(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    client.cookies.clear()
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/system/info").status_code == 401

    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": "trial_user", "password": TEST_PASSWORD},
    )
    assert register_response.status_code == 200
    assert register_response.json()["user"]["role"] == "user"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "trial_user", "password": TEST_PASSWORD},
    )
    assert login_response.status_code == 200
    assert login_response.json()["must_change_password"] is False

    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["user"]["username"] == "trial_user"

    create_session_response = client.post("/api/v1/sessions", json={})
    assert create_session_response.status_code == 200

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401


def test_seed_admin_must_change_password_before_access(monkeypatch, tmp_path) -> None:
    session_service = build_session_service(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    auth_service = patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")
    auth_service.ensure_seed_admin_and_backfill()

    client.cookies.clear()
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "123456"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["must_change_password"] is True

    blocked_response = client.get("/api/v1/sessions")
    assert blocked_response.status_code == 403

    change_response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "123456", "new_password": "newpass123"},
    )
    assert change_response.status_code == 200
    assert change_response.json()["must_change_password"] is False

    sessions_response = client.get("/api/v1/sessions")
    assert sessions_response.status_code == 200
    system_response = client.get("/api/v1/system/info")
    assert system_response.status_code == 200
