from fastapi.testclient import TestClient

from app.api.v1.endpoints.sessions import emit_partial_stream_success
from app.files.service import FileService
from app.files.storage import FileStorage
from app.main import app
from app.memory.schemas import MemoryState, SessionMemoryBundle
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_ask_route_with_session import FakeStreamingResponse
from tests.test_helpers import create_test_user_id, patch_test_auth_service, register_and_login


client = TestClient(app)


class DelegatingPostgresModeStore:
    database_url = "postgresql://carbonrag_user:secret@127.0.0.1:5432/carbonrag_db"

    def __init__(self, delegate) -> None:
        self.delegate = delegate

    def __getattr__(self, name):
        if name == "db_path":
            raise AttributeError(name)
        return getattr(self.delegate, name)


class FakeDerivedMemoryService:
    def __init__(self, *, store) -> None:
        self.store = store

    def get_session_memory_state(self, *, owner_user_id: str, session_id: str):
        del owner_user_id, session_id
        return MemoryState(
            context_usage_estimate=1600,
            context_budget_estimate=258_000,
            summary_present=False,
            compacted_message_count=0,
            compaction_status="idle",
            summary_estimated_tokens=0,
        )

    def build_session_context(self, *, owner_user_id: str, session_id: str, max_turns: int, upcoming_user_input: str):
        del owner_user_id, session_id, max_turns, upcoming_user_input
        return SessionMemoryBundle(
            recent_messages=[],
            session_summary=None,
            memory_notes=[],
            context_usage_estimate=1600,
            context_budget_estimate=258_000,
            compacted_message_count=0,
            compaction_status="idle",
            summary_present=False,
            summary_estimated_tokens=0,
        )


def build_test_services(tmp_path):
    delegate = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    session_service = SessionService(store=DelegatingPostgresModeStore(delegate))
    file_service = FileService(
        session_service=session_service,
        storage=FileStorage(tmp_path / "uploads"),
    )
    return session_service, file_service


def test_session_routes_do_not_crash_in_postgres_memory_mode(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}
    session_service, file_service = build_test_services(tmp_path)
    patch_test_auth_service(monkeypatch, db_path=tmp_path / "carbonrag.sqlite3")
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.api.v1.endpoints.files.get_file_service", lambda: file_service)
    monkeypatch.setattr("app.session.service.get_settings", lambda: type("Settings", (), {"memory_backend": "postgres"})())

    def fake_build_memory_store(**kwargs):
        captured.update(kwargs)
        return object()

    def fake_stream(method: str, url: str, *, headers: dict, json: dict, timeout: float):
        del method, url, headers, json, timeout
        return FakeStreamingResponse(
            status_code=200,
            lines=[
                'data: {"id":"chatcmpl-session-ok","choices":[{"delta":{"role":"assistant","content":"双碳目标包括"}}]}',
                'data: {"id":"chatcmpl-session-ok","choices":[{"delta":{"role":"assistant","content":"碳达峰和碳中和。"}}]}',
                "data: [DONE]",
            ],
        )

    monkeypatch.setattr("app.memory.store.build_memory_store", fake_build_memory_store)
    monkeypatch.setattr("app.memory.service.MemoryService", FakeDerivedMemoryService)
    monkeypatch.setattr("app.ai_runtime.providers.chat_openai_compatible.httpx.stream", fake_stream)

    register_and_login(client, prefix="memory-hotfix")
    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]

    detail_response = client.get(f"/api/v1/sessions/{session_id}")
    ask_response = client.post(
        f"/api/v1/sessions/{session_id}/ask",
        json={
            "question": "什么是双碳目标？",
            "knowledge_scope": "public",
            "top_k": 3,
        },
    )

    with client.stream(
        "POST",
        f"/api/v1/sessions/{session_id}/ask/stream",
        json={
            "question": "继续解释一下。",
            "knowledge_scope": "public",
            "top_k": 3,
        },
    ) as stream_response:
        body = "".join(stream_response.iter_text())
        assert stream_response.status_code == 200
        assert "event: message_start" in body
        assert "event: done" in body

    assert detail_response.status_code == 200
    assert ask_response.status_code == 200
    assert captured["database_url"] == "postgresql://carbonrag_user:secret@127.0.0.1:5432/carbonrag_db"
    assert captured["sqlite_db_path"] is None
    assert captured["memory_backend"] == "postgres"


def test_emit_partial_stream_success_persists_answer_after_late_failure(tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    owner_user_id = create_test_user_id(db_path, prefix="late-stream")
    session_service = SessionService(store=SQLiteSessionStore(db_path))
    session = session_service.create_session(owner_user_id=owner_user_id, title="late stream")
    _, assistant_message = session_service.begin_exchange(
        owner_user_id=owner_user_id,
        session_id=session.session_id,
        user_content="请回答一个问题",
    )

    class FakeStreamSession:
        session_id = session.session_id
        user_message_id = "user-msg"
        assistant_message_id = assistant_message.message_id
        trace_id = "trace-late-stream"
        request_group_id = "reqgrp-late-stream"
        provider_ref = "builtin:test"
        title_updated = False

        def __init__(self) -> None:
            self.events: list[tuple[str, dict]] = []
            self.completed = False

        def append(self, *, event: str, data: dict) -> None:
            self.events.append((event, data))

        def complete(self) -> None:
            self.completed = True

    stream_session = FakeStreamSession()

    emit_partial_stream_success(
        stream_session=stream_session,
        session_service=session_service,
        owner_user_id=owner_user_id,
        requested_scope="public",
        answer="已经完成的回答。",
        thinking_content="已完成思考。",
        attempt=1,
        max_attempts=5,
    )

    detail = session_service.get_session(owner_user_id=owner_user_id, session_id=session.session_id)
    assert detail is not None
    persisted = detail.messages[-1]
    assert persisted.message_id == assistant_message.message_id
    assert persisted.status == "done"
    assert persisted.content == "已经完成的回答。"
    assert persisted.thinking_content == "已完成思考。"
    assert stream_session.completed is True
    assert [event for event, _ in stream_session.events] == ["metadata", "status", "done"]
    assert stream_session.events[-1][1]["stream_recovered_from_late_failure"] is True
