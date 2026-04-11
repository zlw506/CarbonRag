from types import SimpleNamespace

from app.memory.schemas import MemoryState, SessionMemoryBundle
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import create_test_user_id


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
            context_usage_estimate=2048,
            context_budget_estimate=258_000,
            summary_present=True,
            compacted_message_count=4,
            compaction_status="compacted",
            summary_estimated_tokens=128,
        )

    def build_session_context(self, *, owner_user_id: str, session_id: str, max_turns: int, upcoming_user_input: str):
        del owner_user_id, session_id, max_turns, upcoming_user_input
        return SessionMemoryBundle(
            recent_messages=[{"role": "user", "content": "最近一轮问题"}],
            session_summary="已有会话摘要。",
            memory_notes=[],
            context_usage_estimate=2048,
            context_budget_estimate=258_000,
            compacted_message_count=4,
            compaction_status="compacted",
            summary_present=True,
            summary_estimated_tokens=128,
        )


def test_session_service_uses_memory_factory_in_postgres_mode_without_db_path(monkeypatch, tmp_path) -> None:
    captured: dict[str, object] = {}
    delegate = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    store = DelegatingPostgresModeStore(delegate)
    owner_user_id = create_test_user_id(tmp_path / "carbonrag.sqlite3", prefix="memory-compat")

    def fake_build_memory_store(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("app.session.service.get_settings", lambda: SimpleNamespace(memory_backend="postgres"))
    monkeypatch.setattr("app.memory.store.build_memory_store", fake_build_memory_store)
    monkeypatch.setattr("app.memory.service.MemoryService", FakeDerivedMemoryService)

    service = SessionService(store=store)
    session = service.create_session(owner_user_id=owner_user_id)
    detail = service.get_session(owner_user_id=owner_user_id, session_id=session.session_id)
    bundle = service.build_session_context(
        owner_user_id=owner_user_id,
        session_id=session.session_id,
        max_turns=6,
        upcoming_user_input="继续提问。",
    )

    assert detail is not None
    assert detail.memory_state is not None
    assert detail.memory_state.compaction_status == "compacted"
    assert bundle["summary_present"] is True
    assert captured["database_url"] == store.database_url
    assert captured["sqlite_db_path"] is None
    assert captured["memory_backend"] == "postgres"
