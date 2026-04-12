import json
import sqlite3
from functools import lru_cache
from pathlib import Path

from app.retrieval.private_corpus_loader import load_private_sample_manifest
from app.runtime_db.schema import ensure_sqlite_schema
from app.schemas.ask import AskCitation, AskSourceSummary, KnowledgeScope, MessageStatus
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

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            ensure_sqlite_schema(connection)

    def create_session(self, *, session_id: str, owner_user_id: str, title: str, created_at: str) -> SessionSummary:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions (
                    session_id,
                    owner_user_id,
                    title,
                    created_at,
                    updated_at,
                    knowledge_scope_last_used,
                    source_summary_json
                )
                VALUES (?, ?, ?, ?, ?, NULL, NULL)
                """,
                (session_id, owner_user_id, title, created_at, created_at),
            )
        return self._get_session_summary(owner_user_id=owner_user_id, session_id=session_id)

    def list_sessions(self, *, owner_user_id: str) -> list[SessionSummary]:
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
                    COALESCE(k.attached_knowledge_item_count, 0) + COALESCE(p.private_sample_count, 0) AS attached_private_sample_count,
                    COALESCE(k.attached_knowledge_item_count, 0) AS attached_knowledge_item_count
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
                    SELECT session_id, COUNT(*) AS attached_knowledge_item_count
                    FROM session_knowledge_items
                    GROUP BY session_id
                ) k ON k.session_id = s.session_id
                LEFT JOIN (
                    SELECT session_id, COUNT(*) AS private_sample_count
                    FROM session_private_samples
                    GROUP BY session_id
                ) p ON p.session_id = s.session_id
                WHERE s.owner_user_id = ?
                ORDER BY s.updated_at DESC, s.created_at DESC
                """,
                (owner_user_id,),
            ).fetchall()
        return [self._row_to_session_summary(row) for row in rows]

    def get_session(self, *, owner_user_id: str, session_id: str) -> SessionDetail | None:
        summary = self._get_session_summary(owner_user_id=owner_user_id, session_id=session_id)
        if summary is None:
            return None

        with self._connect() as connection:
            session_row = connection.execute(
                """
                SELECT knowledge_scope_last_used, source_summary_json
                FROM sessions
                WHERE session_id = ? AND owner_user_id = ?
                """,
                (session_id, owner_user_id),
            ).fetchone()
            knowledge_attachment_rows = connection.execute(
                """
                SELECT
                    ski.knowledge_item_id,
                    ki.title,
                    ki.source_type,
                    ki.source_ref,
                    ki.file_id,
                    ki.library_scope,
                    ski.attached_at
                FROM session_knowledge_items ski
                LEFT JOIN knowledge_items ki ON ki.knowledge_item_id = ski.knowledge_item_id
                WHERE ski.session_id = ?
                ORDER BY ski.attachment_seq DESC
                """,
                (session_id,),
            ).fetchall()
            message_rows = connection.execute(
                """
                SELECT message_id, role, content, thinking_content, status, trace_id, citations_json, created_at
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
                WHERE session_id = ? AND owner_user_id = ?
                ORDER BY file_seq DESC
                """,
                (session_id, owner_user_id),
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
        attached_files.extend(self._row_to_knowledge_attachment(row) for row in knowledge_attachment_rows)
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
            owner_row = connection.execute(
                "SELECT owner_user_id FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            cursor = connection.execute(
                """
                UPDATE sessions
                SET title = ?, updated_at = ?
                WHERE session_id = ?
                """,
                (title, updated_at, session_id),
            )
            if cursor.rowcount == 0 or owner_row is None:
                return None
        return self._get_session_summary(owner_user_id=owner_row["owner_user_id"], session_id=session_id)

    def update_session_runtime_state(
        self,
        *,
        session_id: str,
        updated_at: str,
        knowledge_scope_last_used: KnowledgeScope,
        source_summary: AskSourceSummary,
    ) -> SessionSummary | None:
        with self._connect() as connection:
            owner_row = connection.execute(
                "SELECT owner_user_id FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
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
            if cursor.rowcount == 0 or owner_row is None:
                return None
        return self._get_session_summary(owner_user_id=owner_row["owner_user_id"], session_id=session_id)

    def append_message(
        self,
        *,
        session_id: str,
        message_id: str,
        role: str,
        content: str,
        created_at: str,
        status: MessageStatus | None = None,
        trace_id: str | None = None,
        citations: list[AskCitation] | None = None,
        thinking_content: str | None = None,
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
                    thinking_content,
                    status,
                    trace_id,
                    citations_json,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (message_id, session_id, role, content, thinking_content, status, trace_id, citations_json, created_at),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (created_at, session_id),
            )
            row = connection.execute(
                """
                SELECT message_id, role, content, thinking_content, status, trace_id, citations_json, created_at
                FROM messages
                WHERE message_id = ?
                """,
                (message_id,),
            ).fetchone()
        return self._row_to_session_message(row)

    def update_message(
        self,
        *,
        session_id: str,
        message_id: str,
        content: str,
        updated_at: str,
        status: MessageStatus | None = None,
        trace_id: str | None = None,
        citations: list[AskCitation] | None = None,
        thinking_content: str | None = None,
    ) -> SessionMessage | None:
        citations_json = json.dumps(
            [citation.model_dump() for citation in (citations or [])],
            ensure_ascii=False,
        )
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE messages
                SET content = ?, thinking_content = ?, status = ?, trace_id = ?, citations_json = ?
                WHERE session_id = ? AND message_id = ?
                """,
                (content, thinking_content, status, trace_id, citations_json, session_id, message_id),
            )
            if cursor.rowcount == 0:
                return None
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (updated_at, session_id),
            )
            row = connection.execute(
                """
                SELECT message_id, role, content, thinking_content, status, trace_id, citations_json, created_at
                FROM messages
                WHERE session_id = ? AND message_id = ?
                """,
                (session_id, message_id),
            ).fetchone()
        return self._row_to_session_message(row)

    def list_recent_messages(self, *, session_id: str, limit: int) -> list[SessionMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT message_id, role, content, thinking_content, status, trace_id, citations_json, created_at
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

    def session_exists(self, *, owner_user_id: str, session_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM sessions WHERE session_id = ? AND owner_user_id = ?",
                (session_id, owner_user_id),
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
            owner_row = connection.execute(
                "SELECT owner_user_id FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            owner_user_id = owner_row["owner_user_id"] if owner_row else None
            connection.execute(
                """
                INSERT INTO files (file_id, owner_user_id, session_id, filename, size, mime_type, stored_at, storage_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (file_id, owner_user_id, session_id, filename, size, mime_type, stored_at, storage_path),
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

    def replace_attached_knowledge_items(self, *, session_id: str, knowledge_item_ids: list[str], attached_at: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM session_knowledge_items WHERE session_id = ?",
                (session_id,),
            )
            connection.execute(
                "DELETE FROM session_private_samples WHERE session_id = ?",
                (session_id,),
            )
            for knowledge_item_id in knowledge_item_ids:
                connection.execute(
                    """
                    INSERT INTO session_knowledge_items (session_id, knowledge_item_id, attached_at)
                    VALUES (?, ?, ?)
                    """,
                    (session_id, knowledge_item_id, attached_at),
                )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE session_id = ?",
                (attached_at, session_id),
            )

    def list_attached_private_sample_ids(self, *, session_id: str) -> list[str]:
        return self.list_attached_knowledge_item_ids(session_id=session_id)

    def list_attached_knowledge_item_ids(self, *, session_id: str) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT knowledge_item_id
                FROM session_knowledge_items
                WHERE session_id = ?
                ORDER BY attachment_seq ASC
                """,
                (session_id,),
            ).fetchall()
            legacy_rows = connection.execute(
                """
                SELECT doc_id
                FROM session_private_samples
                WHERE session_id = ?
                ORDER BY attachment_seq ASC
                """,
                (session_id,),
            ).fetchall()
        knowledge_item_ids = [row["knowledge_item_id"] for row in rows]
        for legacy_row in legacy_rows:
            mapped = self._resolve_knowledge_item_id_from_legacy_doc_id(legacy_row["doc_id"])
            knowledge_item_ids.append(mapped or legacy_row["doc_id"])
        return list(dict.fromkeys(knowledge_item_ids))

    def _get_session_summary(self, *, owner_user_id: str, session_id: str) -> SessionSummary | None:
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
                    COALESCE(k.attached_knowledge_item_count, 0) + COALESCE(p.private_sample_count, 0) AS attached_private_sample_count,
                    COALESCE(k.attached_knowledge_item_count, 0) AS attached_knowledge_item_count
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
                    SELECT session_id, COUNT(*) AS attached_knowledge_item_count
                    FROM session_knowledge_items
                    GROUP BY session_id
                ) k ON k.session_id = s.session_id
                LEFT JOIN (
                    SELECT session_id, COUNT(*) AS private_sample_count
                    FROM session_private_samples
                    GROUP BY session_id
                ) p ON p.session_id = s.session_id
                WHERE s.session_id = ? AND s.owner_user_id = ?
                """,
                (session_id, owner_user_id),
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
            knowledge_item_id=None,
            filename=file.filename,
            source_type="uploaded_file",
            attached_at=file.stored_at,
        )

    @staticmethod
    def _row_to_knowledge_attachment(row: sqlite3.Row) -> SessionAttachment:
        title = row["title"] or row["knowledge_item_id"]
        source_type = "uploaded_file" if row["source_type"] == "uploaded_file" else "private_sample"
        return SessionAttachment(
            file_id=row["file_id"] or row["knowledge_item_id"],
            knowledge_item_id=row["knowledge_item_id"],
            filename=title,
            source_type=source_type,
            attached_at=row["attached_at"],
        )

    @staticmethod
    def _row_to_private_sample_attachment(row: sqlite3.Row) -> SessionAttachment:
        catalog_map = {item.doc_id: item for item in load_private_sample_manifest()}
        doc_id = row["doc_id"]
        item = catalog_map.get(doc_id)
        filename = item.title if item else doc_id
        return SessionAttachment(
            file_id=doc_id,
            knowledge_item_id=None,
            filename=filename,
            source_type="private_sample",
            attached_at=row["attached_at"],
        )

    def _resolve_knowledge_item_id_from_legacy_doc_id(self, doc_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT knowledge_item_id
                FROM knowledge_items
                WHERE source_ref = ? AND source_type = 'private_sample_repo'
                ORDER BY updated_at DESC, created_at DESC
                LIMIT 1
                """,
                (doc_id,),
            ).fetchone()
        return row["knowledge_item_id"] if row else None


@lru_cache(maxsize=1)
def get_session_store() -> SQLiteSessionStore:
    return SQLiteSessionStore()
