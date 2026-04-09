from app.session.adapters.sqlite_store import SQLiteSessionStore
from tests.test_helpers import create_test_user_id


def test_sqlite_session_store_persists_after_reopen(tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    store = SQLiteSessionStore(db_path)
    owner_user_id = create_test_user_id(db_path, prefix="store")

    created = store.create_session(
        session_id="session-demo",
        owner_user_id=owner_user_id,
        title="New conversation 2026-04-04 10:00",
        created_at="2026-04-04T10:00:00+00:00",
    )
    store.append_message(
        session_id=created.session_id,
        message_id="msg-001",
        role="user",
        content="What is the dual-carbon target?",
        created_at="2026-04-04T10:00:01+00:00",
    )

    reopened = SQLiteSessionStore(db_path)
    session = reopened.get_session(owner_user_id=owner_user_id, session_id=created.session_id)

    assert session is not None
    assert session.session_id == created.session_id
    assert session.messages[0].content == "What is the dual-carbon target?"


def test_sqlite_session_store_lists_sessions_by_updated_at_desc(tmp_path) -> None:
    db_path = tmp_path / "carbonrag.sqlite3"
    store = SQLiteSessionStore(db_path)
    owner_user_id = create_test_user_id(db_path, prefix="store-list")
    first = store.create_session(
        session_id="session-first",
        owner_user_id=owner_user_id,
        title="First",
        created_at="2026-04-04T10:00:00+00:00",
    )
    second = store.create_session(
        session_id="session-second",
        owner_user_id=owner_user_id,
        title="Second",
        created_at="2026-04-04T10:01:00+00:00",
    )
    store.append_message(
        session_id=first.session_id,
        message_id="msg-001",
        role="user",
        content="Refresh the first session.",
        created_at="2026-04-04T10:02:00+00:00",
    )

    sessions = store.list_sessions(owner_user_id=owner_user_id)

    assert sessions[0].session_id == first.session_id
    assert sessions[1].session_id == second.session_id
