from app.session.adapters.sqlite_store import SQLiteSessionStore


def test_sqlite_session_store_persists_after_reopen(tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    store = SQLiteSessionStore(db_path)

    created = store.create_session(
        session_id="session-demo",
        title="新对话 2026-04-04 10:00",
        created_at="2026-04-04T10:00:00+00:00",
    )
    store.append_message(
        session_id=created.session_id,
        message_id="msg-001",
        role="user",
        content="什么是双碳目标？",
        created_at="2026-04-04T10:00:01+00:00",
    )

    reopened = SQLiteSessionStore(db_path)
    session = reopened.get_session(created.session_id)

    assert session is not None
    assert session.session_id == created.session_id
    assert session.messages[0].content == "什么是双碳目标？"


def test_sqlite_session_store_lists_sessions_by_updated_at_desc(tmp_path) -> None:
    store = SQLiteSessionStore(tmp_path / "carbonrag.sqlite3")
    first = store.create_session(
        session_id="session-first",
        title="第一个",
        created_at="2026-04-04T10:00:00+00:00",
    )
    second = store.create_session(
        session_id="session-second",
        title="第二个",
        created_at="2026-04-04T10:01:00+00:00",
    )
    store.append_message(
        session_id=first.session_id,
        message_id="msg-001",
        role="user",
        content="让第一个会话更新到最新",
        created_at="2026-04-04T10:02:00+00:00",
    )

    sessions = store.list_sessions()

    assert sessions[0].session_id == first.session_id
    assert sessions[1].session_id == second.session_id
