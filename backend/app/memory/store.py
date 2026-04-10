import sqlite3
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings
from app.memory.schemas import MemoryNote, SessionMemoryMessage, SessionMemorySnapshot
from app.runtime_db.compat import connect_postgres
from app.runtime_db.bootstrap import bootstrap_runtime_database
from app.session.store import DEFAULT_SESSION_DB_PATH


class MemoryStore:
    def __init__(self, *, database_url: str | None = None, sqlite_db_path: Path | str = DEFAULT_SESSION_DB_PATH) -> None:
        self.database_url = database_url
        self.sqlite_db_path = Path(sqlite_db_path)
        bootstrap_runtime_database(database_url=self.database_url, sqlite_db_path=self.sqlite_db_path)

    def list_notes(self, *, owner_user_id: str, enabled_only: bool = False) -> list[MemoryNote]:
        if self.database_url:
            return self._list_notes_postgres(owner_user_id=owner_user_id, enabled_only=enabled_only)
        return self._list_notes_sqlite(owner_user_id=owner_user_id, enabled_only=enabled_only)

    def create_note(self, *, owner_user_id: str, title: str, content: str, is_enabled: bool, created_at: str) -> MemoryNote:
        payload = (
            f"memory-{uuid4().hex[:12]}",
            owner_user_id,
            title,
            content,
            is_enabled,
            created_at,
            created_at,
        )
        if self.database_url:
            with self._connect_postgres() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO memory_notes (
                        memory_note_id, owner_user_id, title, content, is_enabled, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    payload,
                )
                return MemoryNote.model_validate(cursor.fetchone())

        with self._connect_sqlite() as connection:
            connection.execute(
                """
                INSERT INTO memory_notes (
                    memory_note_id, owner_user_id, title, content, is_enabled, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            row = connection.execute(
                "SELECT * FROM memory_notes WHERE memory_note_id = ?",
                (payload[0],),
            ).fetchone()
        return MemoryNote.model_validate(dict(row))

    def update_note(
        self,
        *,
        owner_user_id: str,
        memory_note_id: str,
        title: str | None,
        content: str | None,
        is_enabled: bool | None,
        updated_at: str,
    ) -> MemoryNote | None:
        current = self.get_note(owner_user_id=owner_user_id, memory_note_id=memory_note_id)
        if current is None:
            return None

        next_title = title if title is not None else current.title
        next_content = content if content is not None else current.content
        next_enabled = is_enabled if is_enabled is not None else current.is_enabled

        if self.database_url:
            with self._connect_postgres() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE memory_notes
                    SET title = %s, content = %s, is_enabled = %s, updated_at = %s
                    WHERE memory_note_id = %s AND owner_user_id = %s
                    RETURNING *
                    """,
                    (next_title, next_content, next_enabled, updated_at, memory_note_id, owner_user_id),
                )
                row = cursor.fetchone()
                return MemoryNote.model_validate(row) if row else None

        with self._connect_sqlite() as connection:
            cursor = connection.execute(
                """
                UPDATE memory_notes
                SET title = ?, content = ?, is_enabled = ?, updated_at = ?
                WHERE memory_note_id = ? AND owner_user_id = ?
                """,
                (next_title, next_content, int(next_enabled), updated_at, memory_note_id, owner_user_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT * FROM memory_notes WHERE memory_note_id = ?",
                (memory_note_id,),
            ).fetchone()
        return MemoryNote.model_validate(dict(row))

    def delete_note(self, *, owner_user_id: str, memory_note_id: str) -> bool:
        if self.database_url:
            with self._connect_postgres() as connection, connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM memory_notes WHERE memory_note_id = %s AND owner_user_id = %s",
                    (memory_note_id, owner_user_id),
                )
                return cursor.rowcount > 0

        with self._connect_sqlite() as connection:
            cursor = connection.execute(
                "DELETE FROM memory_notes WHERE memory_note_id = ? AND owner_user_id = ?",
                (memory_note_id, owner_user_id),
            )
            return cursor.rowcount > 0

    def get_note(self, *, owner_user_id: str, memory_note_id: str) -> MemoryNote | None:
        if self.database_url:
            with self._connect_postgres() as connection, connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM memory_notes WHERE memory_note_id = %s AND owner_user_id = %s",
                    (memory_note_id, owner_user_id),
                )
                row = cursor.fetchone()
                return MemoryNote.model_validate(row) if row else None

        with self._connect_sqlite() as connection:
            row = connection.execute(
                "SELECT * FROM memory_notes WHERE memory_note_id = ? AND owner_user_id = ?",
                (memory_note_id, owner_user_id),
            ).fetchone()
        return MemoryNote.model_validate(dict(row)) if row else None

    def get_session_memory_snapshot(self, *, owner_user_id: str, session_id: str) -> SessionMemorySnapshot | None:
        if self.database_url:
            with self._connect_postgres() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        session_id,
                        owner_user_id,
                        session_summary,
                        summary_message_seq_upto,
                        summary_updated_at,
                        summary_estimated_tokens,
                        compaction_status,
                        last_compaction_error
                    FROM sessions
                    WHERE session_id = %s AND owner_user_id = %s
                    """,
                    (session_id, owner_user_id),
                )
                row = cursor.fetchone()
                if row is None:
                    return None
                cursor.execute(
                    """
                    SELECT message_seq, role, content, created_at
                    FROM messages
                    WHERE session_id = %s
                    ORDER BY message_seq ASC
                    """,
                    (session_id,),
                )
                message_rows = cursor.fetchall()
                snapshot = dict(row)
        else:
            with self._connect_sqlite() as connection:
                row = connection.execute(
                    """
                    SELECT
                        session_id,
                        owner_user_id,
                        session_summary,
                        summary_message_seq_upto,
                        summary_updated_at,
                        summary_estimated_tokens,
                        compaction_status,
                        last_compaction_error
                    FROM sessions
                    WHERE session_id = ? AND owner_user_id = ?
                    """,
                    (session_id, owner_user_id),
                ).fetchone()
                if row is None:
                    return None
                message_rows = connection.execute(
                    """
                    SELECT message_seq, role, content, created_at
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY message_seq ASC
                    """,
                    (session_id,),
                ).fetchall()
                snapshot = dict(row)

        snapshot["messages"] = [SessionMemoryMessage.model_validate(dict(message_row)) for message_row in message_rows]
        return SessionMemorySnapshot.model_validate(snapshot)

    def count_compacted_messages(self, *, session_id: str, summary_message_seq_upto: int | None) -> int:
        if not summary_message_seq_upto:
            return 0
        if self.database_url:
            with self._connect_postgres() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM messages
                    WHERE session_id = %s
                      AND message_seq <= %s
                      AND role IN ('user', 'assistant')
                    """,
                    (session_id, summary_message_seq_upto),
                )
                row = cursor.fetchone()
                return int(row["count"]) if row else 0

        with self._connect_sqlite() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS message_count
                FROM messages
                WHERE session_id = ?
                  AND message_seq <= ?
                  AND role IN ('user', 'assistant')
                """,
                (session_id, summary_message_seq_upto),
            ).fetchone()
        return int(row["message_count"]) if row else 0

    def update_session_memory(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        session_summary: str | None,
        summary_message_seq_upto: int | None,
        summary_updated_at: str | None,
        summary_estimated_tokens: int,
        compaction_status: str,
        last_compaction_error: str | None,
    ) -> bool:
        if self.database_url:
            with self._connect_postgres() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE sessions
                    SET session_summary = %s,
                        summary_message_seq_upto = %s,
                        summary_updated_at = %s,
                        summary_estimated_tokens = %s,
                        compaction_status = %s,
                        last_compaction_error = %s
                    WHERE session_id = %s AND owner_user_id = %s
                    """,
                    (
                        session_summary,
                        summary_message_seq_upto,
                        summary_updated_at,
                        summary_estimated_tokens,
                        compaction_status,
                        last_compaction_error,
                        session_id,
                        owner_user_id,
                    ),
                )
                return cursor.rowcount > 0

        with self._connect_sqlite() as connection:
            cursor = connection.execute(
                """
                UPDATE sessions
                SET session_summary = ?,
                    summary_message_seq_upto = ?,
                    summary_updated_at = ?,
                    summary_estimated_tokens = ?,
                    compaction_status = ?,
                    last_compaction_error = ?
                WHERE session_id = ? AND owner_user_id = ?
                """,
                (
                    session_summary,
                    summary_message_seq_upto,
                    summary_updated_at,
                    summary_estimated_tokens,
                    compaction_status,
                    last_compaction_error,
                    session_id,
                    owner_user_id,
                ),
            )
            return cursor.rowcount > 0

    def _list_notes_postgres(self, *, owner_user_id: str, enabled_only: bool) -> list[MemoryNote]:
        query = "SELECT * FROM memory_notes WHERE owner_user_id = %s"
        params: list[object] = [owner_user_id]
        if enabled_only:
            query += " AND is_enabled = TRUE"
        query += " ORDER BY updated_at DESC, created_at DESC"
        with self._connect_postgres() as connection, connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
        return [MemoryNote.model_validate(row) for row in rows]

    def _list_notes_sqlite(self, *, owner_user_id: str, enabled_only: bool) -> list[MemoryNote]:
        query = "SELECT * FROM memory_notes WHERE owner_user_id = ?"
        params: list[object] = [owner_user_id]
        if enabled_only:
            query += " AND is_enabled = 1"
        query += " ORDER BY updated_at DESC, created_at DESC"
        with self._connect_sqlite() as connection:
            rows = connection.execute(query, tuple(params)).fetchall()
        return [MemoryNote.model_validate(dict(row)) for row in rows]

    def _connect_sqlite(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.sqlite_db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _connect_postgres(self):
        return connect_postgres(self.database_url)


@lru_cache(maxsize=1)
def get_memory_store() -> MemoryStore:
    settings = get_settings()
    return MemoryStore(database_url=settings.database_url, sqlite_db_path=DEFAULT_SESSION_DB_PATH)
