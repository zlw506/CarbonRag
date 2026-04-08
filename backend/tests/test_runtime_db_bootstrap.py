import sqlite3

from app.runtime_db.bootstrap import bootstrap_runtime_database
from app.runtime_db.schema import CORE_TABLES


class FakeCursor:
    def __init__(self, executed: list[str]) -> None:
        self.executed = executed

    def execute(self, statement: str, params=None) -> None:
        self.executed.append(" ".join(statement.split()))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class FakeConnection:
    def __init__(self, executed: list[str]) -> None:
        self.executed = executed

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.executed)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def test_bootstrap_runtime_database_creates_sqlite_schema(tmp_path) -> None:
    db_path = tmp_path / "runtime.sqlite3"

    backend_kind = bootstrap_runtime_database(sqlite_db_path=db_path)

    assert backend_kind == "sqlite"
    connection = sqlite3.connect(db_path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        connection.close()
    assert set(CORE_TABLES).issubset(tables)


def test_bootstrap_runtime_database_executes_postgres_schema(monkeypatch) -> None:
    executed: list[str] = []

    monkeypatch.setattr(
        "app.runtime_db.bootstrap.psycopg.connect",
        lambda *args, **kwargs: FakeConnection(executed),
    )

    backend_kind = bootstrap_runtime_database(database_url="postgresql://example")

    assert backend_kind == "postgresql"
    assert any("CREATE TABLE IF NOT EXISTS sessions" in statement for statement in executed)
    assert any("CREATE TABLE IF NOT EXISTS feedback_entries" in statement for statement in executed)
    assert any("CREATE TABLE IF NOT EXISTS carbon_calculations" in statement for statement in executed)
