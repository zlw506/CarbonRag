from fastapi.testclient import TestClient

from app.main import app
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import patch_test_auth_service, register_and_login

client = TestClient(app)


def test_session_bulk_delete_route_deletes_selected_sessions(monkeypatch, tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    session_service = SessionService(store=SQLiteSessionStore(db_path))
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    patch_test_auth_service(monkeypatch, db_path=db_path)

    register_and_login(client, prefix="bulk-delete")
    first = client.post("/api/v1/sessions", json={"title": "要删除 1"}).json()
    second = client.post("/api/v1/sessions", json={"title": "要删除 2"}).json()
    kept = client.post("/api/v1/sessions", json={"title": "保留"}).json()

    response = client.post(
        "/api/v1/sessions/bulk-delete",
        json={"session_ids": [first["session_id"], second["session_id"], "missing-session", first["session_id"]]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["deleted_count"] == 2
    assert payload["deleted_session_ids"] == [first["session_id"], second["session_id"]]
    assert payload["missing_session_ids"] == ["missing-session"]

    sessions = client.get("/api/v1/sessions").json()
    assert [item["session_id"] for item in sessions] == [kept["session_id"]]
