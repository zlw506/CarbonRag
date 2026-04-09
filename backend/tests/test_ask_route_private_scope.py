from fastapi.testclient import TestClient

from app.files.service import FileService
from app.files.storage import FileStorage
from app.main import app
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import patch_test_auth_service, register_and_login

client = TestClient(app)


class FakeStreamingResponse:
    def __init__(self, *, status_code: int, lines: list[str]) -> None:
        self.status_code = status_code
        self._lines = lines

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def iter_lines(self):
        for line in self._lines:
            yield line


def build_test_services(tmp_path):
    session_service = SessionService(store=SQLiteSessionStore(tmp_path / "carbonrag.sqlite3"))
    file_service = FileService(
        session_service=session_service,
        storage=FileStorage(tmp_path / "uploads"),
    )
    return session_service, file_service


def test_private_scope_returns_private_sample_citations(monkeypatch, tmp_path) -> None:
    session_service, file_service = build_test_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)
    monkeypatch.setattr("app.api.v1.endpoints.private_samples.get_session_service", lambda: session_service)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")

    def fake_stream(method: str, url: str, *, headers: dict, json: dict, timeout: float):
        return FakeStreamingResponse(
            status_code=200,
            lines=[
                'data: {"id":"chatcmpl-private-ok","choices":[{"delta":{"role":"assistant","content":"According to the current sanitized enterprise sample, the compressed-air system still has idle running and weak energy tracking."}}]}',
                "data: [DONE]",
            ],
        )

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.stream", fake_stream)

    register_and_login(client, prefix="ask-private")
    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    attach_response = client.put(
        f"/api/v1/sessions/{session_id}/attached-files/private-samples",
        json={"doc_ids": ["enterprise_doc_001"]},
    )
    assert attach_response.status_code == 200

    response = client.post(
        f"/api/v1/sessions/{session_id}/ask",
        json={
            "question": "What problems are shown in the enterprise sample?",
            "knowledge_scope": "private_sample",
            "top_k": 3,
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["citations"]
    assert all(item["source_type"] == "private_sample" for item in payload["citations"])
