from app.core.config import get_settings
from app.session.store import get_session_store


def test_settings_read_database_url_and_upload_dir(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://carbonrag_user:secret@127.0.0.1:5432/carbonrag_db")
    monkeypatch.setenv("UPLOAD_DIR", "/srv/carbonrag/shared/uploads")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.database_url == "postgresql://carbonrag_user:secret@127.0.0.1:5432/carbonrag_db"
    assert settings.upload_dir == "/srv/carbonrag/shared/uploads"
    get_settings.cache_clear()


def test_session_store_factory_selects_sqlite_when_database_url_missing(monkeypatch) -> None:
    class FakeSQLiteStore:
        pass

    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    get_session_store.cache_clear()
    monkeypatch.setattr("app.session.adapters.sqlite_store.SQLiteSessionStore", lambda: FakeSQLiteStore())

    store = get_session_store()

    assert isinstance(store, FakeSQLiteStore)
    get_session_store.cache_clear()
    get_settings.cache_clear()


def test_session_store_factory_selects_postgres_when_database_url_present(monkeypatch) -> None:
    sentinel = object()

    monkeypatch.setenv("DATABASE_URL", "postgresql://carbonrag_user:secret@127.0.0.1:5432/carbonrag_db")
    get_settings.cache_clear()
    get_session_store.cache_clear()
    monkeypatch.setattr(
        "app.session.adapters.postgres_store.build_postgres_session_store",
        lambda database_url: sentinel,
    )

    store = get_session_store()

    assert store is sentinel
    get_session_store.cache_clear()
    get_settings.cache_clear()
