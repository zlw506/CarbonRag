from app.memory.store import MemoryStore, build_memory_store


class FakePostgresMemoryDatabase:
    def __init__(self) -> None:
        self.memory_notes: dict[str, dict] = {}


class FakeCursor:
    def __init__(self, db: FakePostgresMemoryDatabase) -> None:
        self.db = db
        self._rows: list[dict] = []
        self.rowcount = 0

    def execute(self, statement: str, params=None) -> None:
        normalized = " ".join(statement.split()).lower()
        params = params or ()
        self.rowcount = 0

        if (
            normalized.startswith("create table")
            or normalized.startswith("create index")
            or normalized.startswith("create unique index")
            or normalized.startswith("alter table")
        ):
            self._rows = []
            return

        if normalized.startswith("insert into memory_notes"):
            memory_note_id, owner_user_id, title, content, is_enabled, created_at, updated_at = params
            row = {
                "memory_note_id": memory_note_id,
                "owner_user_id": owner_user_id,
                "title": title,
                "content": content,
                "is_enabled": is_enabled,
                "created_at": created_at,
                "updated_at": updated_at,
            }
            self.db.memory_notes[memory_note_id] = row
            self._rows = [row]
            self.rowcount = 1
            return

        if normalized.startswith("select * from memory_notes where owner_user_id = %s"):
            owner_user_id = params[0]
            rows = [row for row in self.db.memory_notes.values() if row["owner_user_id"] == owner_user_id]
            if "and is_enabled = true" in normalized:
                rows = [row for row in rows if row["is_enabled"] is True]
            rows.sort(key=lambda item: (item["updated_at"], item["created_at"]), reverse=True)
            self._rows = rows
            return

        if normalized.startswith("select * from memory_notes where memory_note_id = %s and owner_user_id = %s"):
            memory_note_id, owner_user_id = params
            row = self.db.memory_notes.get(memory_note_id)
            self._rows = [row] if row is not None and row["owner_user_id"] == owner_user_id else []
            return

        if normalized.startswith("update memory_notes"):
            title, content, is_enabled, updated_at, memory_note_id, owner_user_id = params
            row = self.db.memory_notes.get(memory_note_id)
            if row is not None and row["owner_user_id"] == owner_user_id:
                row.update(
                    {
                        "title": title,
                        "content": content,
                        "is_enabled": is_enabled,
                        "updated_at": updated_at,
                    }
                )
                self._rows = [row]
                self.rowcount = 1
            else:
                self._rows = []
            return

        if normalized.startswith("delete from memory_notes where memory_note_id = %s and owner_user_id = %s"):
            memory_note_id, owner_user_id = params
            row = self.db.memory_notes.get(memory_note_id)
            if row is not None and row["owner_user_id"] == owner_user_id:
                del self.db.memory_notes[memory_note_id]
                self.rowcount = 1
            self._rows = []
            return

        raise AssertionError(f"Unsupported SQL in fake memory postgres layer: {statement}")

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class FakeConnection:
    def __init__(self, db: FakePostgresMemoryDatabase) -> None:
        self.db = db

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.db)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def patch_fake_postgres(monkeypatch, db: FakePostgresMemoryDatabase) -> None:
    fake_connect = lambda *args, **kwargs: FakeConnection(db)
    monkeypatch.setattr("app.memory.store.connect_postgres", fake_connect)
    monkeypatch.setattr("app.runtime_db.bootstrap.connect_postgres", fake_connect)


def test_memory_store_postgres_initializes_without_sqlite_path(monkeypatch) -> None:
    db = FakePostgresMemoryDatabase()
    patch_fake_postgres(monkeypatch, db)

    store = MemoryStore(
        database_url="postgresql://carbonrag_user:secret@127.0.0.1:5432/carbonrag_db",
        sqlite_db_path=None,
        memory_backend="postgres",
    )

    assert store.memory_backend == "postgres"
    assert store.sqlite_db_path is None
    assert store.db_path is None


def test_build_memory_store_defaults_to_postgres_with_database_url(monkeypatch) -> None:
    db = FakePostgresMemoryDatabase()
    patch_fake_postgres(monkeypatch, db)

    store = build_memory_store(
        database_url="postgresql://carbonrag_user:secret@127.0.0.1:5432/carbonrag_db",
        sqlite_db_path=None,
        memory_backend=None,
    )

    assert store.memory_backend == "postgres"
    assert store.sqlite_db_path is None


def test_memory_store_postgres_can_read_write_notes(monkeypatch) -> None:
    db = FakePostgresMemoryDatabase()
    patch_fake_postgres(monkeypatch, db)

    store = MemoryStore(
        database_url="postgresql://carbonrag_user:secret@127.0.0.1:5432/carbonrag_db",
        sqlite_db_path=None,
        memory_backend="postgres",
    )
    created = store.create_note(
        owner_user_id="user-memory-postgres",
        title="偏好",
        content="请先给政策结论。",
        is_enabled=True,
        created_at="2026-04-11T10:00:00+00:00",
    )

    notes = store.list_notes(owner_user_id="user-memory-postgres")

    assert created.memory_note_id
    assert len(notes) == 1
    assert notes[0].content == "请先给政策结论。"
