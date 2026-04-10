from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.ai_runtime.providers.base import ChatProviderError
from app.core.config import get_settings
from app.main import app
from app.memory.service import MemoryService
from app.memory.store import MemoryStore
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import patch_test_auth_service, register_and_login


class FakeMemoryChatProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        return SimpleNamespace(content="会话摘要已生成")


def _build_services(tmp_path):
    db_path = tmp_path / "carbonrag.sqlite3"
    memory_store = MemoryStore(sqlite_db_path=db_path)
    session_store = SQLiteSessionStore(db_path)
    memory_service = MemoryService(store=memory_store, chat_provider=FakeMemoryChatProvider())
    session_service = SessionService(store=session_store, memory_service=memory_service)
    return db_path, memory_store, session_service, memory_service


def test_session_detail_exposes_memory_state(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MEMORY_COMPACTION_TRIGGER_ESTIMATE", "1")
    monkeypatch.setenv("MEMORY_RECENT_TURN_WINDOW", "1")
    monkeypatch.setenv("MEMORY_MIN_RECENT_MESSAGE_COUNT", "2")
    get_settings.cache_clear()

    db_path, _, session_service, memory_service = _build_services(tmp_path)
    patch_test_auth_service(monkeypatch, db_path=db_path)
    monkeypatch.setattr("app.api.v1.endpoints.sessions.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.session.service.get_session_service", lambda: session_service)
    monkeypatch.setattr("app.memory.service.get_memory_service", lambda: memory_service)

    client = TestClient(app)
    user = register_and_login(client, prefix="memory-state")
    session_id = client.post("/api/v1/sessions", json={}).json()["session_id"]

    for index in range(4):
        session_service.record_exchange(
            owner_user_id=user["user_id"],
            session_id=session_id,
            user_content=f"问题 {index}",
            assistant_content=f"回答 {index}",
            assistant_status="ok",
            trace_id=f"trace-memory-state-{index}",
            citations=[],
        )

    memory_service.build_session_context(
        owner_user_id=user["user_id"],
        session_id=session_id,
        upcoming_user_input="触发状态读取",
    )

    response = client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["memory_state"] is not None
    assert detail["memory_state"]["compaction_status"] == "compacted"
    assert detail["memory_state"]["summary_present"] is True
    assert detail["memory_state"]["summary_estimated_tokens"] > 0

    get_settings.cache_clear()
