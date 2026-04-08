import json
import sqlite3
from functools import lru_cache
from pathlib import Path

from app.retrieval.private_corpus_loader import load_private_sample_catalog
from app.schemas.ask import AskCitation, AskSourceSummary, AskStatus, KnowledgeScope
from app.session.schemas import (
    SessionAttachment,
    SessionDetail,
    SessionMessage,
    SessionSummary,
    UploadedFile,
)
from app.session.store import DEFAULT_SESSION_DB_PATH, SessionStore


class SQLiteSessionStore(SessionStore):
    def __init__(self, db_path: Path | str = DEFAULT_SESSION_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing_columns = {
            row["name"]
            for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
        }
        if column not in existing_columns:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    message_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT NOT NULL UNIQUE,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT,
                    trace_id TEXT,
                    citations_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS files (
                    file_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL UNIQUE,
                    session_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    mime_type TEXT NOT NULL,
                    stored_at TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS session_private_samples (
                    attachment_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    doc_id TEXT NOT NULL,
                    attached_at TEXT NOT NULL,
                    UNIQUE (session_id, doc_id),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session_seq
                    ON messages(session_id, message_seq);
                CREATE INDEX IF NOT EXISTS idx_files_session_seq
                    ON files(session_id, file_seq);
                CREATE INDEX IF NOT EXISTS idx_sessions_updated_at
                    ON sessions(updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_private_samples_session_seq
                    ON session_private_samples(session_id, attachment_seq DESC);
                """
            )
            self._ensure_column(connection, "sessions", "knowledge_scope_last_used", "TEXT")
            self._ensure_column(connection, "sessions", "source_summary_json", "TEXT")

    def create_session(self, *, session_id: str, title: str, created_at: str) -> SessionSummary:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions (
                    session_id,
                    title,
                    created_at,
                    updated_at,
                    knowledge_scope_last_used,
                    source_summary_json
                )
                VALUES (?, ?, ?, ?, NULL, NULL)
                """,
                (session_id, title, created_at, created_at),
            )
        return self._get_session_summary(session_id)

    def list_sessions(self) -> list[SessionSummary]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    s.session_id,
                    s.title,
                    s.created_at,
                    s.updated_at,
                    COALESCE(m.message_count, 0) AS message_count,
                    COALESCE(f.file_count, 0) AS file_count,
                    COALESCE(p.private_sample_count, 0) AS attached_private_sample_count
                FROM sessions s
                LEFT JOIN (
                    SELECT session_id, COUNT(*) AS message_count
                    FROM messages
                    GROUP BY session_id
                ) m ON m.session_id = s.session_id
                LEFT JOIN (
                    SELECT session_id, COUNT(*) AS file_count
                    FROM files
                    GROUP BY session_id
                ) f ON f.session_id = s.session_id
                LEFT JOIN (
                    SELECT session_id, COUNT(*) AS private_sample_count
                    FROM session_private_samples
                    GROUP BY session_id
                ) p ON p.session_id = s.session_id
                ORDER BY s.updated_at DESC, s.created_at DESC
                """
            ).fetchall()
        return [self._row_to_session_summary(row) for row in rows]

    def get_session(self, session_id: str) -> SessionDetail | None:
        summary = self._get_session_summary(session_id)
        if summary is None:
            return None

        with self._connect() as connection:
            session_row = connection.execute(
                """
                SELECT knowledge_scope_last_used, source_summary_json
                FROM sessions
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
            message_rows = connection.execute(
                """
                SELECT message_id, role, content, status, trace_id, citations_json, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY message_seq ASC
                """,
                (session_id,),
            ).fetchall()
            file_rows = connection.execute(
                """
                SELECT file_id, session_id, filename, size, mime_type, stored_at
                FROM files
                WHERE session_id = ?
                ORDER BY file_seq DESC
                """,
                (session_id,),
            ).fetchall()
            private_sample_rows = connection.execute(
                """
                SELECT doc_id, attached_at
                FROM session_private_samples
                WHERE session_id = ?
                ORDER BY attachment_seq DESC
                """,
                (session_id,),
            ).fetchall()

        uploaded_files = [self._row_to_uploaded_file(row) for row in file_rows]
        attached_files = [self._uploaded_file_to_attachment(file) for file in uploaded_files]
        attached_files.extend(self._row_to_private_sample_attachment(row) for row in private_sample_rows)
        attached_files.sort(key=lambda item: item.attached_at, reverse=True)

        source_summary = None
        if session_row is not None and session_row["source_summary_json"]:
            source_summary = AskSourceSummary.model_validate(json.loads(session_row["source_summary_json"]))

        return SessionDetail(
            **summary.model_dump(),
            messages=[self._row_to_session_message(row) for row in message_rows],
            files=uploaded_files,
            attached_files=attached_files,
            knowledge_scope_last_used=session_row["knowledge_scope_last_used"] if session_row else None,
            source_summary=source_summary,
        )

    def update_session_title(self, *, session_id: str, title: str, updated_at: str) -> SessionSummary | None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE sessions
                SET title = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (title, updated_at, session_id),
            )
            if cursor.rowcount == 0:
                return None
        return self._get_session_summary(session_id)

    def update_session_runtime_state(
        self,
        *,
        session_id: str,
        updated_at: str,
        knowledge_scope_last_used: KnowledgeScope,
        source_summary: AskSourceSummary,
    ) -> SessionSummary | None:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE sessions
                SET updated_at = ?, knowledge_scope_last_used = ?, source_summary_json = ?
                WHERE session_id = ?
                """,
                (
                    updated_at,
                    knowledge_scope_last_used,
                    json.dumps(source_summary.model_dump(), ensure_ascii=False),
                    session_id,
                ),
            )
            if cursor.rowcount == 0:
                return None
        return self._get_session_summary(session_id)

    def append_message(
        self,
        *,
        session_id: str,
        message_id: str,
        role: str,
        content: str,
        created_at: str,
        status: AskStatus | None = None,
        trace_id: str | None = None,
        citations: list[AskCitation] | None = None,
    ) -> SessionMessage:
        citations_json = json.dumps(
            [citation.model_dump() for citation in (citations or [])],
            ensure_ascii=False,
        )
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO messages (
                    message_id,
                    session_id,
                    role,
                    content,
                    status,
                    trace_id,
                    citations_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (message_id, session_id, role, content, status, trace_id, citations_json, created_at),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (created_at, session_id),
            )
            row = connection.execute(
                """
                SELECT message_id, role, content, status, trace_id, citations_json, created_at
                FROM messages
                WHERE message_id = ?
                """,
                (message_id,),
            ).fetchone()
        return self._row_to_session_message(row)

    def list_recent_messages(self, *, session_id: str, limit: int) -> list[SessionMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT message_id, role, content, status, trace_id, citations_json, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY message_seq DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        messages = [self._row_to_session_message(row) for row in rows]
        messages.reverse()
        return messages

    def session_exists(self, session_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return row is not None

    def create_uploaded_file(
        self,
        *,
        file_id: str,
        session_id: str,
        filename: str,
        size: int,
        mime_type: str,
        stored_at: str,
        storage_path: str,
    ) -> UploadedFile:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO files (file_id, session_id, filename, size, mime_type, stored_at, storage_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (file_id, session_id, filename, size, mime_type, stored_at, storage_path),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (stored_at, session_id),
            )
            row = connection.execute(
                """
                SELECT file_id, session_id, filename, size, mime_type, stored_at
                FROM files
                WHERE file_id = ?
                """,
                (file_id,),
            ).fetchone()
        return self._row_to_uploaded_file(row)

    def replace_attached_private_samples(self, *, session_id: str, doc_ids: list[str], attached_at: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM session_private_samples WHERE session_id = ?",
                (session_id,),
            )
            for doc_id in doc_ids:
                connection.execute(
                    """
                    INSERT INTO session_private_samples (session_id, doc_id, attached_at)
                    VALUES (?, ?, ?)
                    """,
                    (session_id, doc_id, attached_at),
                )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (attached_at, session_id),
            )

    def list_attached_private_sample_ids(self, *, session_id: str) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT doc_id
                FROM session_private_samples
                WHERE session_id = ?
                ORDER BY attachment_seq DESC
                """,
                (session_id,),
            ).fetchall()
        return [row["doc_id"] for row in rows]

    def _get_session_summary(self, session_id: str) -> SessionSummary | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    s.session_id,
                    s.title,
                    s.created_at,
                    s.updated_at,
                    COALESCE(m.message_count, 0) AS message_count,
                    COALESCE(f.file_count, 0) AS file_count,
                    COALESCE(p.private_sample_count, 0) AS attached_private_sample_count
                FROM sessions s
                LEFT JOIN (
                    SELECT session_id, COUNT(*) AS message_count
                    FROM messages
                    GROUP BY session_id
                ) m ON m.session_id = s.session_id
                LEFT JOIN (
                    SELECT session_id, COUNT(*) AS file_count
                    FROM files
                    GROUP BY session_id
                ) f ON f.session_id = s.session_id
                LEFT JOIN (
                    SELECT session_id, COUNT(*) AS private_sample_count
                    FROM session_private_samples
                    GROUP BY session_id
                ) p ON p.session_id = s.session_id
                WHERE s.session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_session_summary(row)

    @staticmethod
    def _row_to_session_summary(row: sqlite3.Row) -> SessionSummary:
        return SessionSummary.model_validate(dict(row))

    @staticmethod
    def _row_to_session_message(row: sqlite3.Row) -> SessionMessage:
        payload = dict(row)
        payload["citations"] = json.loads(payload.pop("citations_json") or "[]")
        return SessionMessage.model_validate(payload)

    @staticmethod
    def _row_to_uploaded_file(row: sqlite3.Row) -> UploadedFile:
        return UploadedFile.model_validate(dict(row))

    @staticmethod
    def _uploaded_file_to_attachment(file: UploadedFile) -> SessionAttachment:
        return SessionAttachment(
            file_id=file.file_id,
            filename=file.filename,
            source_type="uploaded_file",
            attached_at=file.stored_at,
        )

    @staticmethod
    def _row_to_private_sample_attachment(row: sqlite3.Row) -> SessionAttachment:
        catalog_map = {item.doc_id: item for item in load_private_sample_catalog()}
        doc_id = row["doc_id"]
        item = catalog_map.get(doc_id)
        filename = item.title if item else doc_id
        return SessionAttachment(
            file_id=doc_id,
            filename=filename,
            source_type="private_sample",
            attached_at=row["attached_at"],
        )


@lru_cache(maxsize=1)
def get_session_store() -> SQLiteSessionStore:
    return SQLiteSessionStore()
