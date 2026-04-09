import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.core.config import get_settings
from app.session.store import DEFAULT_SESSION_DB_PATH


def _connect(database_url: str | None = None, sqlite_db_path: Path | str | None = None):
    settings = get_settings()
    effective_database_url = database_url or settings.database_url
    if effective_database_url:
        return psycopg.connect(effective_database_url, row_factory=dict_row)

    db_path = Path(sqlite_db_path or DEFAULT_SESSION_DB_PATH)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def load_private_sample_override_map(
    *,
    database_url: str | None = None,
    sqlite_db_path: Path | str | None = None,
) -> dict[str, dict[str, bool]]:
    with _connect(database_url=database_url, sqlite_db_path=sqlite_db_path) as connection:
        if database_url or get_settings().database_url:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT doc_id, is_enabled, session_attachable
                    FROM private_sample_catalog_overrides
                    """
                )
                rows = cursor.fetchall()
        else:
            rows = connection.execute(
                """
                SELECT doc_id, is_enabled, session_attachable
                FROM private_sample_catalog_overrides
                """
            ).fetchall()

    return {
        row["doc_id"]: {
            "is_enabled": bool(row["is_enabled"]),
            "session_attachable": bool(row["session_attachable"]),
        }
        for row in rows
    }


def update_private_sample_override(
    *,
    doc_id: str,
    is_enabled: bool,
    session_attachable: bool,
    updated_by_user_id: str,
    database_url: str | None = None,
    sqlite_db_path: Path | str | None = None,
) -> None:
    updated_at = datetime.now(timezone.utc).isoformat()
    with _connect(database_url=database_url, sqlite_db_path=sqlite_db_path) as connection:
        if database_url or get_settings().database_url:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO private_sample_catalog_overrides (
                        doc_id,
                        is_enabled,
                        session_attachable,
                        updated_at,
                        updated_by_user_id
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (doc_id)
                    DO UPDATE SET
                        is_enabled = EXCLUDED.is_enabled,
                        session_attachable = EXCLUDED.session_attachable,
                        updated_at = EXCLUDED.updated_at,
                        updated_by_user_id = EXCLUDED.updated_by_user_id
                    """,
                    (doc_id, is_enabled, session_attachable, updated_at, updated_by_user_id),
                )
        else:
            connection.execute(
                """
                INSERT INTO private_sample_catalog_overrides (
                    doc_id,
                    is_enabled,
                    session_attachable,
                    updated_at,
                    updated_by_user_id
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(doc_id)
                DO UPDATE SET
                    is_enabled = excluded.is_enabled,
                    session_attachable = excluded.session_attachable,
                    updated_at = excluded.updated_at,
                    updated_by_user_id = excluded.updated_by_user_id
                """,
                (doc_id, int(is_enabled), int(session_attachable), updated_at, updated_by_user_id),
            )
