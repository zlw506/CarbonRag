from fastapi.testclient import TestClient

from app.files.service import FileService
from app.files.storage import FileStorage
from app.main import app
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService

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


def test_mixed_scope_returns_public_and_private_citations(monkeypatch, tmp_path) -> None:
    session_service, file_service = build_test_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)
    monkeypatch.setattr("app.api.v1.endpoints.private_samples.get_session_service", lambda: session_service)

    def fake_stream(method: str, url: str, *, headers: dict, json: dict, timeout: float):
        return FakeStreamingResponse(
            status_code=200,
            lines=[
                'data: {"id":"chatcmpl-mixed-ok","choices":[{"delta":{"role":"assistant","content":"从政策要求看，需要建立规范统计核算体系；从当前样例看，压缩空气和蒸汽系统仍是重点治理环节。"}}]}',
                "data: [DONE]",
            ],
        )

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.stream", fake_stream)

    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    attach_response = client.put(
        f"/api/v1/sessions/{session_id}/attached-files/private-samples",
        json={"doc_ids": ["enterprise_doc_001", "enterprise_doc_002", "energy_bill_sample_001"]},
    )
    assert attach_response.status_code == 200

    response = client.post(
        f"/api/v1/sessions/{session_id}/ask",
        json={
            "question": "政策要求和当前样例企业现状之间有什么关系？",
            "knowledge_scope": "mixed",
            "top_k": 5,
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["source_summary"]["knowledge_scope"] == "mixed"
    assert payload["source_summary"]["public_policy_count"] >= 1
    assert payload["source_summary"]["private_sample_count"] >= 1
    source_types = {item["source_type"] for item in payload["citations"]}
    assert source_types == {"public_policy", "private_sample"}
