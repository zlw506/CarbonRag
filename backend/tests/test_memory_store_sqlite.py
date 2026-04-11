from app.memory.store import DEFAULT_SESSION_DB_PATH, MemoryStore, build_memory_store
from tests.test_helpers import create_test_user_id


def test_memory_store_sqlite_uses_default_path_when_none(monkeypatch, tmp_path) -> None:
    expected_db_path = tmp_path / "memory-runtime.sqlite3"
    monkeypatch.setattr("app.memory.store.DEFAULT_SESSION_DB_PATH", expected_db_path)

    store = MemoryStore(sqlite_db_path=None, memory_backend="sqlite")

    assert store.memory_backend == "sqlite"
    assert store.sqlite_db_path == expected_db_path
    assert store.db_path == expected_db_path


def test_build_memory_store_defaults_to_sqlite_without_database_url(monkeypatch, tmp_path) -> None:
    expected_db_path = tmp_path / "memory-runtime.sqlite3"
    monkeypatch.setattr("app.memory.store.DEFAULT_SESSION_DB_PATH", expected_db_path)

    store = build_memory_store(database_url=None, sqlite_db_path=None, memory_backend=None)

    assert store.memory_backend == "sqlite"
    assert store.sqlite_db_path == expected_db_path
    assert store.db_path == expected_db_path


def test_memory_store_sqlite_can_read_write_notes_with_fallback_path(monkeypatch, tmp_path) -> None:
    expected_db_path = tmp_path / "memory-runtime.sqlite3"
    monkeypatch.setattr("app.memory.store.DEFAULT_SESSION_DB_PATH", expected_db_path)

    store = MemoryStore(sqlite_db_path=None, memory_backend="sqlite")
    owner_user_id = create_test_user_id(expected_db_path, prefix="memory-sqlite")
    created = store.create_note(
        owner_user_id=owner_user_id,
        title="偏好",
        content="回答时先给结论。",
        is_enabled=True,
        created_at="2026-04-11T10:00:00+00:00",
    )

    notes = store.list_notes(owner_user_id=owner_user_id)

    assert created.memory_note_id
    assert len(notes) == 1
    assert notes[0].title == "偏好"
    assert store.sqlite_db_path != DEFAULT_SESSION_DB_PATH or expected_db_path == DEFAULT_SESSION_DB_PATH
