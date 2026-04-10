from app.ai_runtime.providers.base import ChatCompletionResult, ChatProviderError, ProviderDescriptor
from app.memory.schemas import CreateMemoryNoteRequest, UpdateMemoryNoteRequest
from app.memory.service import MemoryService
from app.memory.store import MemoryStore
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService
from tests.test_helpers import create_test_user_id


class StubSummaryProvider:
    def __init__(self, *, content: str = "这是自动生成的会话摘要。", should_fail: bool = False) -> None:
        self.content = content
        self.should_fail = should_fail

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(name="stub-summary", provider_type="test", mode="chat", default_model="stub")

    def generate_response(self, *, system_prompt: str, user_input: str) -> ChatCompletionResult:
        del system_prompt, user_input
        if self.should_fail:
            raise ChatProviderError("summary provider failed", reason="summary_failed")
        return ChatCompletionResult(content=self.content)


def build_services(tmp_path, *, provider: StubSummaryProvider | None = None):
    db_path = tmp_path / "carbonrag.sqlite3"
    session_store = SQLiteSessionStore(db_path)
    memory_store = MemoryStore(sqlite_db_path=db_path)
    memory_service = MemoryService(store=memory_store, chat_provider=provider or StubSummaryProvider())
    session_service = SessionService(store=session_store, memory_service=memory_service)
    return session_service, memory_service, db_path


def _seed_session_history(*, session_service: SessionService, owner_user_id: str, session_id: str, pairs: int = 8) -> None:
    for index in range(pairs):
        session_service.record_exchange(
            owner_user_id=owner_user_id,
            session_id=session_id,
            user_content=f"第 {index + 1} 轮用户问题：关于双碳转型的长问题说明 {index}。",
            assistant_content=f"第 {index + 1} 轮助手回答：给出政策依据和处理建议 {index}。",
            assistant_status="ok",
            trace_id=f"trace-{index + 1:03d}",
            citations=[],
        )


def test_memory_notes_crud_and_user_isolation(tmp_path) -> None:
    _, memory_service, db_path = build_services(tmp_path)
    owner_user_id = create_test_user_id(db_path, prefix="memory-owner")
    other_user_id = create_test_user_id(db_path, prefix="memory-other")

    note = memory_service.create_note(
        owner_user_id=owner_user_id,
        payload=CreateMemoryNoteRequest(
            title="偏好",
            content="用户偏好看到简洁的结构化回答。",
            is_enabled=True,
        ),
    )

    assert len(memory_service.list_notes(owner_user_id=owner_user_id)) == 1
    assert memory_service.list_notes(owner_user_id=other_user_id) == []
    assert memory_service.update_note(
        owner_user_id=other_user_id,
        memory_note_id=note.memory_note_id,
        payload=UpdateMemoryNoteRequest(title="不应成功"),
    ) is None
    assert memory_service.delete_note(owner_user_id=other_user_id, memory_note_id=note.memory_note_id) is False

    updated = memory_service.update_note(
        owner_user_id=owner_user_id,
        memory_note_id=note.memory_note_id,
        payload=UpdateMemoryNoteRequest(
            content="用户偏好先给结论，再列政策依据。",
            is_enabled=False,
        ),
    )
    assert updated is not None
    assert updated.content.startswith("用户偏好先给结论")
    assert updated.is_enabled is False
    assert memory_service.delete_note(owner_user_id=owner_user_id, memory_note_id=note.memory_note_id) is True
    assert memory_service.list_notes(owner_user_id=owner_user_id) == []


def test_memory_service_compacts_old_messages_and_exposes_session_state(tmp_path) -> None:
    session_service, memory_service, db_path = build_services(tmp_path, provider=StubSummaryProvider(content="压缩后的旧对话摘要。"))
    owner_user_id = create_test_user_id(db_path, prefix="memory-session")
    session = session_service.create_session(owner_user_id=owner_user_id)
    _seed_session_history(session_service=session_service, owner_user_id=owner_user_id, session_id=session.session_id, pairs=8)

    memory_service.create_note(
        owner_user_id=owner_user_id,
        payload=CreateMemoryNoteRequest(
            title="回答偏好",
            content="回答时先给结论，再给依据。",
            is_enabled=True,
        ),
    )

    bundle = memory_service.build_session_context(
        owner_user_id=owner_user_id,
        session_id=session.session_id,
        upcoming_user_input="请基于之前的讨论继续总结。",
        max_turns=6,
    )

    assert bundle.session_summary == "压缩后的旧对话摘要。"
    assert bundle.compaction_status == "compacted"
    assert bundle.compacted_message_count == 4
    assert len(bundle.recent_messages) == 12
    assert bundle.memory_notes

    session_detail = session_service.get_session(owner_user_id=owner_user_id, session_id=session.session_id)
    assert session_detail is not None
    assert session_detail.memory_state is not None
    assert session_detail.memory_state.summary_present is True
    assert session_detail.memory_state.compaction_status == "compacted"
    assert session_detail.memory_state.compacted_message_count == 4


def test_memory_service_compaction_failure_does_not_block_context_build(tmp_path) -> None:
    session_service, memory_service, db_path = build_services(tmp_path, provider=StubSummaryProvider(should_fail=True))
    owner_user_id = create_test_user_id(db_path, prefix="memory-failure")
    session = session_service.create_session(owner_user_id=owner_user_id)
    _seed_session_history(session_service=session_service, owner_user_id=owner_user_id, session_id=session.session_id, pairs=8)

    bundle = memory_service.build_session_context(
        owner_user_id=owner_user_id,
        session_id=session.session_id,
        upcoming_user_input="继续提问。",
        max_turns=6,
    )

    assert bundle.session_summary is None
    assert bundle.compaction_status == "failed"
    assert len(bundle.recent_messages) == 12

    session_detail = session_service.get_session(owner_user_id=owner_user_id, session_id=session.session_id)
    assert session_detail is not None
    assert session_detail.memory_state is not None
    assert session_detail.memory_state.compaction_status == "failed"
    assert session_detail.memory_state.summary_present is False
