import httpx
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


def test_session_ask_route_persists_history_and_citations(monkeypatch, tmp_path) -> None:
    session_service, file_service = build_test_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)

    captured: dict[str, dict] = {}

    def fake_stream(method: str, url: str, *, headers: dict, json: dict, timeout: float):
        captured["payload"] = json
        return FakeStreamingResponse(
            status_code=200,
            lines=[
                'data: {"id":"chatcmpl-session-ok","choices":[{"delta":{"role":"assistant","content":"双碳目标包括"}}]}',
                'data: {"id":"chatcmpl-session-ok","choices":[{"delta":{"role":"assistant","content":"碳达峰和碳中和。"}}]}',
                "data: [DONE]",
            ],
        )

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.stream", fake_stream)

    session = client.post("/api/v1/sessions", json={}).json()
    session_id = session["session_id"]

    first_response = client.post(
        f"/api/v1/sessions/{session_id}/ask",
        json={
            "question": "什么是双碳目标？",
            "knowledge_scope": "public",
            "top_k": 3,
        },
    )
    second_response = client.post(
        f"/api/v1/sessions/{session_id}/ask",
        json={
            "question": "它和企业有什么关系？",
            "knowledge_scope": "public",
            "top_k": 3,
        },
    )
    detail = client.get(f"/api/v1/sessions/{session_id}").json()

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert detail["messages"][0]["role"] == "user"
    assert detail["messages"][1]["role"] == "assistant"
    assert detail["messages"][-1]["role"] == "assistant"
    assert detail["messages"][-1]["citations"]
    assert "最近单会话历史如下" in captured["payload"]["messages"][0]["content"]


def test_session_ask_route_returns_422_for_non_public_scope(monkeypatch, tmp_path) -> None:
    session_service, file_service = build_test_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)

    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/ask",
        json={
            "question": "企业样例可以用吗？",
            "knowledge_scope": "mixed",
            "top_k": 3,
        },
    )

    assert response.status_code == 422
    assert response.json()["status"] == "invalid_input"


def test_session_ask_route_records_provider_error_message(monkeypatch, tmp_path) -> None:
    session_service, file_service = build_test_services(tmp_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)

    def failing_stream(method: str, url: str, *, headers: dict, json: dict, timeout: float):
        raise httpx.ConnectError("provider down")

    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.stream", failing_stream)

    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]
    response = client.post(
        f"/api/v1/sessions/{session_id}/ask",
        json={
            "question": "什么是双碳目标？",
            "knowledge_scope": "public",
            "top_k": 3,
        },
    )
    detail = client.get(f"/api/v1/sessions/{session_id}").json()

    assert response.status_code == 502
    assert response.json()["status"] == "provider_error"
    assert detail["messages"][-1]["role"] == "assistant"
    assert detail["messages"][-1]["status"] == "provider_error"
