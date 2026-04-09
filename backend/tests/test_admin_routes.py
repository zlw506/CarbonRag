from fastapi.testclient import TestClient

from app.admin.service import AdminService
from app.main import app
from tests.test_helpers import TEST_PASSWORD, patch_test_auth_service

client = TestClient(app)


def build_admin_service(*, auth_service, db_path):
    return AdminService(auth_service=auth_service, sqlite_db_path=db_path)


def login_seed_admin_and_change_password() -> None:
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "123456"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["must_change_password"] is True
    change_response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "123456", "new_password": "newpass123"},
    )
    assert change_response.status_code == 200


def test_admin_routes_require_admin_role_and_password_change(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    auth_service = patch_test_auth_service(monkeypatch, db_path=db_path)
    auth_service.ensure_seed_admin_and_backfill()
    admin_service = build_admin_service(auth_service=auth_service, db_path=db_path)
    monkeypatch.setattr("app.api.v1.endpoints.admin.get_admin_service", lambda: admin_service)

    client.cookies.clear()
    client.post("/api/v1/auth/register", json={"username": "member_one", "password": TEST_PASSWORD})
    client.post("/api/v1/auth/login", json={"username": "member_one", "password": TEST_PASSWORD})
    user_response = client.get("/api/v1/admin/users")
    assert user_response.status_code == 403

    client.cookies.clear()
    login_response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "123456"})
    assert login_response.status_code == 200
    assert login_response.json()["must_change_password"] is True
    blocked_response = client.get("/api/v1/admin/users")
    assert blocked_response.status_code == 403


def test_admin_routes_manage_users_private_samples_and_refresh(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    auth_service = patch_test_auth_service(monkeypatch, db_path=db_path)
    auth_service.ensure_seed_admin_and_backfill()
    admin_service = build_admin_service(auth_service=auth_service, db_path=db_path)
    monkeypatch.setattr("app.api.v1.endpoints.admin.get_admin_service", lambda: admin_service)

    client.cookies.clear()
    login_seed_admin_and_change_password()

    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": "member_two", "password": TEST_PASSWORD},
    )
    user_id = register_response.json()["user"]["user_id"]

    users_response = client.get("/api/v1/admin/users")
    assert users_response.status_code == 200
    assert any(item["user_id"] == user_id for item in users_response.json())

    update_response = client.patch(
        f"/api/v1/admin/users/{user_id}",
        json={"role": "admin", "is_active": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["role"] == "admin"

    reset_response = client.post(f"/api/v1/admin/users/{user_id}/reset-password")
    assert reset_response.status_code == 200
    assert reset_response.json()["temporary_password"]

    private_samples_response = client.get("/api/v1/admin/private-samples")
    assert private_samples_response.status_code == 200
    doc_id = private_samples_response.json()[0]["doc_id"]

    update_private_sample_response = client.patch(
        f"/api/v1/admin/private-samples/{doc_id}",
        json={"is_enabled": True, "session_attachable": True},
    )
    assert update_private_sample_response.status_code == 200
    assert update_private_sample_response.json()["doc_id"] == doc_id

    refresh_response = client.post(
        "/api/v1/admin/knowledge-refresh-tasks",
        json={"scope": "public_policy"},
    )
    assert refresh_response.status_code == 200
    assert refresh_response.json()["status"] == "succeeded"

    feedback_response = client.get("/api/v1/admin/feedback/overview")
    assert feedback_response.status_code == 200

    system_response = client.get("/api/v1/admin/system/status")
    assert system_response.status_code == 200
    assert system_response.json()["total_users"] >= 2
