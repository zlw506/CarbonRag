from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.ai_runtime.providers.base import ChatProviderError
from app.core.config import get_settings
from app.memory.service import MemoryService
from app.memory.store import MemoryStore
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import create_test_user_id


class FakeMemoryChatProvider:
    def __init__(self, content: str) -> None:
        self.content = content

    def generate_response(self, *, system_prompt: str, user_input: str):
        return SimpleNamespace(content=self.content)


class FailingMemoryChatProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        raise ChatProviderError("memory compaction failed", reason="provider_error", status_code=502)


def _build_services(tmp_path, chat_provider):
    db_path = tmp_path / "carbonrag.sqlite3"
    memory_store = MemoryStore(sqlite_db_path=db_path)
    session_store = SQLiteSessionStore(db_path)
    memory_service = MemoryService(store=memory_store, chat_provider=chat_provider)
    session_service = SessionService(store=session_store, memory_service=memory_service)
    owner_user_id = create_test_user_id(db_path, prefix="memorycmp")
    session = session_service.create_session(owner_user_id=owner_user_id)
    return db_path, owner_user_id, session, memory_store, session_service, memory_service


def _seed_conversation(session_service: SessionService, *, owner_user_id: str, session_id: str) -> None:
    for index in range(4):
        session_service.record_exchange(
            owner_user_id=owner_user_id,
            session_id=session_id,
            user_content=f"用户问题 {index}",
            assistant_content=f"助手回答 {index}",
            assistant_status="ok",
            trace_id=f"trace-{index}",
            citations=[],
        )


def test_memory_compaction_triggers_and_updates_session_state(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MEMORY_COMPACTION_TRIGGER_ESTIMATE", "1")
    monkeypatch.setenv("MEMORY_RECENT_TURN_WINDOW", "1")
    monkeypatch.setenv("MEMORY_MIN_RECENT_MESSAGE_COUNT", "2")
    get_settings.cache_clear()

    db_path, owner_user_id, session, memory_store, session_service, memory_service = _build_services(
        tmp_path,
        FakeMemoryChatProvider("压缩后的会话摘要")
    )
    _seed_conversation(session_service, owner_user_id=owner_user_id, session_id=session.session_id)

    bundle = memory_service.build_session_context(
        owner_user_id=owner_user_id,
        session_id=session.session_id,
        upcoming_user_input="继续压缩",
    )
    assert bundle.session_summary == "压缩后的会话摘要"
    assert bundle.compaction_status == "compacted"
    assert bundle.summary_present is True

    state = session_service.get_session(owner_user_id=owner_user_id, session_id=session.session_id).memory_state
    assert state is not None
    assert state.compaction_status == "compacted"
    assert state.summary_present is True
    assert state.compacted_message_count >= 2
    assert state.summary_estimated_tokens > 0

    snapshot = memory_store.get_session_memory_snapshot(owner_user_id=owner_user_id, session_id=session.session_id)
    assert snapshot is not None
    assert snapshot.session_summary == "压缩后的会话摘要"
    assert snapshot.summary_message_seq_upto is not None

    get_settings.cache_clear()


def test_memory_compaction_fallback_marks_failure(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MEMORY_COMPACTION_TRIGGER_ESTIMATE", "1")
    monkeypatch.setenv("MEMORY_RECENT_TURN_WINDOW", "1")
    monkeypatch.setenv("MEMORY_MIN_RECENT_MESSAGE_COUNT", "2")
    get_settings.cache_clear()

    _, owner_user_id, session, memory_store, session_service, memory_service = _build_services(
        tmp_path,
        FailingMemoryChatProvider(),
    )
    _seed_conversation(session_service, owner_user_id=owner_user_id, session_id=session.session_id)

    bundle = memory_service.build_session_context(
        owner_user_id=owner_user_id,
        session_id=session.session_id,
        upcoming_user_input="继续压缩",
    )
    assert bundle.compaction_status == "failed"
    assert bundle.summary_present is False

    state = session_service.get_session(owner_user_id=owner_user_id, session_id=session.session_id).memory_state
    assert state is not None
    assert state.compaction_status == "failed"
    assert state.summary_present is False

    snapshot = memory_store.get_session_memory_snapshot(owner_user_id=owner_user_id, session_id=session.session_id)
    assert snapshot is not None
    assert snapshot.last_compaction_error is not None

    get_settings.cache_clear()
