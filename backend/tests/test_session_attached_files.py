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


def test_session_attached_files_support_uploaded_and_private_samples(monkeypatch, tmp_path) -> None:
    session_service, file_service = build_test_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)
    monkeypatch.setattr("app.api.v1.endpoints.private_samples.get_session_service", lambda: session_service)

    catalog_response = client.get("/api/v1/private-samples")
    assert catalog_response.status_code == 200
    assert any(item["doc_id"] == "enterprise_doc_001" for item in catalog_response.json())

    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]

    first_attach = client.put(
        f"/api/v1/sessions/{session_id}/attached-files/private-samples",
        json={"doc_ids": ["enterprise_doc_001", "energy_bill_sample_001"]},
    )
    assert first_attach.status_code == 200
    assert len([item for item in first_attach.json()["attached_files"] if item["source_type"] == "private_sample"]) == 2

    second_attach = client.put(
        f"/api/v1/sessions/{session_id}/attached-files/private-samples",
        json={"doc_ids": ["enterprise_doc_002"]},
    )
    assert second_attach.status_code == 200
    private_attachments = [item for item in second_attach.json()["attached_files"] if item["source_type"] == "private_sample"]
    assert len(private_attachments) == 1
    assert private_attachments[0]["file_id"] == "enterprise_doc_002"

    upload_response = client.post(
        "/api/v1/files",
        data={"session_id": session_id},
        files={"file": ("sample.txt", BytesIO(b"hello carbon"), "text/plain")},
    )
    assert upload_response.status_code == 200

    detail = client.get(f"/api/v1/sessions/{session_id}").json()
    source_types = {item["source_type"] for item in detail["attached_files"]}
    assert source_types == {"uploaded_file", "private_sample"}
