import sqlite3
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.core.config import get_settings
from app.runtime_db.schema import ensure_postgres_schema, ensure_sqlite_schema
from app.session.store import DEFAULT_SESSION_DB_PATH


def get_runtime_backend_kind(database_url: str | None) -> str:
    return "postgresql" if database_url else "sqlite"


def bootstrap_runtime_database(
    *,
    database_url: str | None = None,
    sqlite_db_path: Path | str | None = None,
) -> str:
    if database_url:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            ensure_postgres_schema(connection)
        return "postgresql"

    db_path = Path(sqlite_db_path or DEFAULT_SESSION_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        ensure_sqlite_schema(connection)
        connection.commit()
    finally:
        connection.close()
    return "sqlite"


def main() -> None:
    settings = get_settings()
    bootstrap_runtime_database(
        database_url=settings.database_url,
        sqlite_db_path=DEFAULT_SESSION_DB_PATH,
    )


if __name__ == "__main__":
    main()
