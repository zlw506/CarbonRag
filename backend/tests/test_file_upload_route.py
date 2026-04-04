from io import BytesIO

from fastapi.testclient import TestClient

from app.files.service import FileService
from app.files.storage import FileStorage
from app.main import app
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService

client = TestClient(app)


def build_test_services(tmp_path):
    session_service = SessionService(store=SQLiteSessionStore(tmp_path / "carbonrag.sqlite3"))
    file_service = FileService(
        session_service=session_service,
        storage=FileStorage(tmp_path / "uploads"),
    )
    return session_service, file_service


def test_file_upload_route_saves_file_and_returns_metadata(monkeypatch, tmp_path) -> None:
    session_service, file_service = build_test_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)

    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    response = client.post(
        "/api/v1/files",
        data={"session_id": session_id},
        files={"file": ("sample.txt", BytesIO(b"hello carbon"), "text/plain")},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["session_id"] == session_id
    assert payload["filename"] == "sample.txt"
    assert payload["mime_type"] == "text/plain"
    assert (tmp_path / "uploads" / session_id).exists()


def test_file_upload_route_returns_404_for_unknown_session(monkeypatch, tmp_path) -> None:
    session_service, file_service = build_test_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)

    response = client.post(
        "/api/v1/files",
        data={"session_id": "session-missing"},
        files={"file": ("sample.txt", BytesIO(b"hello carbon"), "text/plain")},
    )

    assert response.status_code == 404
