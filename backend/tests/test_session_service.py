from app.schemas.ask import AskCitation
from app.session.adapters.sqlite_store import SQLiteSessionStore
from app.session.service import SessionService


def build_session_service(tmp_path) -> SessionService:
    store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    return SessionService(store=store)


def test_session_service_creates_default_title_and_builds_context(tmp_path) -> None:
    service = build_session_service(tmp_path)
    session = service.create_session()

    assert session.title.startswith("新对话")

    service.record_exchange(
        session_id=session.session_id,
        user_content="什么是双碳目标？",
        assistant_content="双碳目标是碳达峰和碳中和。",
        assistant_status="ok",
        trace_id="trace-001",
        citations=[],
    )
    service.record_exchange(
        session_id=session.session_id,
        user_content="它和企业有什么关系？",
        assistant_content="企业需要在政策框架下理解低碳转型。",
        assistant_status="ok",
        trace_id="trace-002",
        citations=[],
    )

    session_context = service.build_session_context(session.session_id, max_turns=1)

    assert len(session_context) == 2
    assert session_context[0]["role"] == "user"
    assert session_context[1]["role"] == "assistant"


def test_session_service_promotes_first_question_to_title(tmp_path) -> None:
    service = build_session_service(tmp_path)
    session = service.create_session()

    service.record_exchange(
        session_id=session.session_id,
        user_content="什么是双碳目标以及它对企业意味着什么？",
        assistant_content="回答内容",
        assistant_status="ok",
        trace_id="trace-001",
        citations=[
            AskCitation(
                doc_id="policy_001",
                title="政策标题",
                source="国务院",
                source_url="https://example.com",
                snippet="片段",
                chunk_id="policy_001_chunk_01",
            )
        ],
    )
    updated = service.maybe_promote_title_from_first_question(
        session.session_id,
        "什么是双碳目标以及它对企业意味着什么？",
    )

    assert updated is not None
    assert updated.title.startswith("什么是双碳目标")
    assert updated.title != session.title
