import json
from functools import lru_cache

from app.retrieval.private_corpus_loader import load_private_sample_manifest
from app.runtime_db.compat import connect_postgres
from app.runtime_db.bootstrap import bootstrap_runtime_database
from app.schemas.ask import AskCitation, AskSourceSummary, KnowledgeScope, MessageStatus
from app.session.schemas import (
    SessionAttachment,
    SessionDetail,
    SessionMessage,
    SessionSummary,
    UploadedFile,
)
from app.session.store import SessionStore


class PostgreSQLSessionStore(SessionStore):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        bootstrap_runtime_database(database_url=self.database_url)

    def _connect(self):
        return connect_postgres(self.database_url)

    def create_session(self, *, session_id: str, owner_user_id: str, title: str, created_at: str) -> SessionSummary:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
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
                    VALUES (%s, %s, %s, %s, %s, NULL, NULL)
                    """,
                    (session_id, owner_user_id, title, created_at, created_at),
                )
        return self._get_session_summary(owner_user_id=owner_user_id, session_id=session_id)

    def list_sessions(self, *, owner_user_id: str) -> list[SessionSummary]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        s.session_id,
                        s.title,
                        s.created_at,
                        s.updated_at,
                        COALESCE(s.is_pinned, FALSE) AS is_pinned,
                        s.pinned_at,
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
                    WHERE s.owner_user_id = %s
                    ORDER BY COALESCE(s.is_pinned, FALSE) DESC, s.pinned_at DESC NULLS LAST, s.updated_at DESC, s.created_at DESC
                    """
                , (owner_user_id,))
                rows = cursor.fetchall()
        return [self._row_to_session_summary(row) for row in rows]

    def get_session(self, *, owner_user_id: str, session_id: str) -> SessionDetail | None:
        summary = self._get_session_summary(owner_user_id=owner_user_id, session_id=session_id)
        if summary is None:
            return None

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT knowledge_scope_last_used, source_summary_json
                    FROM sessions
                    WHERE session_id = %s AND owner_user_id = %s
                    """,
                    (session_id, owner_user_id),
                )
                session_row = cursor.fetchone()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            ski.knowledge_item_id,
                            ki.title,
                            ki.source_type,
                            ki.source_ref,
                            ki.file_id,
                            ki.library_scope,
                            ki.index_status,
                            f.parse_status,
                            f.page_count,
                            f.sheet_count,
                            f.slide_count,
                            f.error_message,
                            r.summary,
                            COALESCE(r.chunk_count, 0) AS chunk_count,
                            ski.attached_at
                        FROM session_knowledge_items ski
                        LEFT JOIN knowledge_items ki ON ki.knowledge_item_id = ski.knowledge_item_id
                        LEFT JOIN files f ON f.file_id = ki.file_id
                        LEFT JOIN file_parse_results r ON r.file_id = f.file_id
                        WHERE ski.session_id = %s
                        ORDER BY ski.attachment_seq DESC
                        """,
                        (session_id,),
                    )
                    knowledge_attachment_rows = cursor.fetchall()
            except Exception:
                knowledge_attachment_rows = []
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT message_id, role, content, thinking_content, status, trace_id, citations_json, created_at
                    FROM messages
                    WHERE session_id = %s
                    ORDER BY message_seq ASC
                    """,
                    (session_id,),
                )
                message_rows = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT
                        f.*,
                        i.knowledge_item_id,
                        i.index_status,
                        r.summary,
                        COALESCE(r.chunk_count, 0) AS chunk_count
                    FROM files f
                    LEFT JOIN knowledge_items i ON i.file_id = f.file_id
                    LEFT JOIN file_parse_results r ON r.file_id = f.file_id
                    WHERE f.session_id = %s AND f.owner_user_id = %s
                    ORDER BY f.file_seq DESC
                    """,
                    (session_id, owner_user_id),
                )
                file_rows = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT doc_id, attached_at
                    FROM session_private_samples
                    WHERE session_id = %s
                    ORDER BY attachment_seq DESC
                    """,
                    (session_id,),
                )
                private_sample_rows = cursor.fetchall()

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
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT owner_user_id FROM sessions WHERE session_id = %s",
                    (session_id,),
                )
                owner_row = cursor.fetchone()
                cursor.execute(
                    """
                    UPDATE sessions
                    SET title = %s, updated_at = %s
                    WHERE session_id = %s
                    """,
                    (title, updated_at, session_id),
                )
                if cursor.rowcount == 0 or owner_row is None:
                    return None
        return self._get_session_summary(owner_user_id=owner_row["owner_user_id"], session_id=session_id)

    def update_session_pin(
        self,
        *,
        session_id: str,
        is_pinned: bool,
        pinned_at: str | None,
        updated_at: str,
    ) -> SessionSummary | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT owner_user_id FROM sessions WHERE session_id = %s",
                    (session_id,),
                )
                owner_row = cursor.fetchone()
                cursor.execute(
                    """
                    UPDATE sessions
                    SET is_pinned = %s, pinned_at = %s, updated_at = %s
                    WHERE session_id = %s
                    """,
                    (is_pinned, pinned_at, updated_at, session_id),
                )
                if cursor.rowcount == 0 or owner_row is None:
                    return None
        return self._get_session_summary(owner_user_id=owner_row["owner_user_id"], session_id=session_id)

    def delete_session(self, *, owner_user_id: str, session_id: str) -> bool:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM sessions WHERE session_id = %s AND owner_user_id = %s",
                    (session_id, owner_user_id),
                )
                if cursor.fetchone() is None:
                    return False

                # Existing runtime databases may have been created before every
                # child table had ON DELETE CASCADE. Delete dependent rows
                # explicitly so the UI delete action behaves consistently.
                cursor.execute(
                    """
                    DELETE FROM report_sources
                    WHERE report_id IN (
                        SELECT report_id FROM reports WHERE session_id = %s
                    )
                    """,
                    (session_id,),
                )
                cursor.execute("DELETE FROM reports WHERE session_id = %s", (session_id,))
                cursor.execute(
                    """
                    DELETE FROM file_parse_results
                    WHERE file_id IN (
                        SELECT file_id FROM files WHERE session_id = %s
                    )
                    """,
                    (session_id,),
                )
                cursor.execute("DELETE FROM session_knowledge_items WHERE session_id = %s", (session_id,))
                cursor.execute("DELETE FROM session_private_samples WHERE session_id = %s", (session_id,))
                cursor.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
                cursor.execute("DELETE FROM files WHERE session_id = %s", (session_id,))
                cursor.execute(
                    "DELETE FROM sessions WHERE session_id = %s AND owner_user_id = %s",
                    (session_id, owner_user_id),
                )
                return cursor.rowcount > 0

    def update_session_runtime_state(
        self,
        *,
        session_id: str,
        updated_at: str,
        knowledge_scope_last_used: KnowledgeScope,
        source_summary: AskSourceSummary,
    ) -> SessionSummary | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT owner_user_id FROM sessions WHERE session_id = %s",
                    (session_id,),
                )
                owner_row = cursor.fetchone()
                cursor.execute(
                    """
                    UPDATE sessions
                    SET updated_at = %s, knowledge_scope_last_used = %s, source_summary_json = %s
                    WHERE session_id = %s
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
        citations_json = json.dumps([citation.model_dump() for citation in (citations or [])], ensure_ascii=False)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
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
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (message_id, session_id, role, content, thinking_content, status, trace_id, citations_json, created_at),
                )
                cursor.execute(
                    "UPDATE sessions SET updated_at = %s WHERE session_id = %s",
                    (created_at, session_id),
                )
                cursor.execute(
                    """
                    SELECT message_id, role, content, thinking_content, status, trace_id, citations_json, created_at
                    FROM messages
                    WHERE message_id = %s
                    """,
                    (message_id,),
                )
                row = cursor.fetchone()
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
        citations_json = json.dumps([citation.model_dump() for citation in (citations or [])], ensure_ascii=False)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE messages
                    SET content = %s, thinking_content = %s, status = %s, trace_id = %s, citations_json = %s
                    WHERE session_id = %s AND message_id = %s
                    """,
                    (content, thinking_content, status, trace_id, citations_json, session_id, message_id),
                )
                if cursor.rowcount == 0:
                    return None
                cursor.execute(
                    "UPDATE sessions SET updated_at = %s WHERE session_id = %s",
                    (updated_at, session_id),
                )
                cursor.execute(
                    """
                    SELECT message_id, role, content, thinking_content, status, trace_id, citations_json, created_at
                    FROM messages
                    WHERE session_id = %s AND message_id = %s
                    """,
                    (session_id, message_id),
                )
                row = cursor.fetchone()
        return self._row_to_session_message(row)

    def list_recent_messages(self, *, session_id: str, limit: int) -> list[SessionMessage]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT message_id, role, content, thinking_content, status, trace_id, citations_json, created_at
                    FROM messages
                    WHERE session_id = %s
                    ORDER BY message_seq DESC
                    LIMIT %s
                    """,
                    (session_id, limit),
                )
                rows = cursor.fetchall()
        messages = [self._row_to_session_message(row) for row in rows]
        messages.reverse()
        return messages

    def session_exists(self, *, owner_user_id: str, session_id: str) -> bool:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM sessions WHERE session_id = %s AND owner_user_id = %s",
                    (session_id, owner_user_id),
                )
                row = cursor.fetchone()
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
        stored_filename: str | None = None,
        file_ext: str | None = None,
        sha256: str | None = None,
    ) -> UploadedFile:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT owner_user_id FROM sessions WHERE session_id = %s", (session_id,))
                owner_row = cursor.fetchone()
                owner_user_id = owner_row["owner_user_id"] if owner_row else None
                cursor.execute(
                    """
                    INSERT INTO files (
                        file_id, owner_user_id, session_id, filename, stored_filename, file_ext,
                        size, mime_type, stored_at, storage_path, sha256, parse_status, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        file_id,
                        owner_user_id,
                        session_id,
                        filename,
                        stored_filename,
                        file_ext,
                        size,
                        mime_type,
                        stored_at,
                        storage_path,
                        sha256,
                        "uploaded",
                        stored_at,
                    ),
                )
                cursor.execute(
                    "UPDATE sessions SET updated_at = %s WHERE session_id = %s",
                    (stored_at, session_id),
                )
                cursor.execute(
                    """
                    SELECT f.*, NULL AS knowledge_item_id, NULL AS index_status, NULL AS summary, 0 AS chunk_count
                    FROM files f
                    WHERE f.file_id = %s
                    """,
                    (file_id,),
                )
                row = cursor.fetchone()
        return self._row_to_uploaded_file(row)

    def replace_attached_private_samples(self, *, session_id: str, doc_ids: list[str], attached_at: str) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM session_private_samples WHERE session_id = %s",
                    (session_id,),
                )
                for doc_id in doc_ids:
                    cursor.execute(
                        """
                        INSERT INTO session_private_samples (session_id, doc_id, attached_at)
                        VALUES (%s, %s, %s)
                        """,
                        (session_id, doc_id, attached_at),
                    )
                cursor.execute(
                    "UPDATE sessions SET updated_at = %s WHERE session_id = %s",
                    (attached_at, session_id),
                )

    def replace_attached_knowledge_items(self, *, session_id: str, knowledge_item_ids: list[str], attached_at: str) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM session_knowledge_items WHERE session_id = %s",
                    (session_id,),
                )
                cursor.execute(
                    "DELETE FROM session_private_samples WHERE session_id = %s",
                    (session_id,),
                )
                for knowledge_item_id in knowledge_item_ids:
                    cursor.execute(
                        """
                        INSERT INTO session_knowledge_items (session_id, knowledge_item_id, attached_at)
                        VALUES (%s, %s, %s)
                        """,
                        (session_id, knowledge_item_id, attached_at),
                    )
                cursor.execute(
                    "UPDATE sessions SET updated_at = %s WHERE session_id = %s",
                    (attached_at, session_id),
                )

    def list_attached_private_sample_ids(self, *, session_id: str) -> list[str]:
        return self.list_attached_knowledge_item_ids(session_id=session_id)

    def list_attached_knowledge_item_ids(self, *, session_id: str) -> list[str]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT knowledge_item_id
                    FROM session_knowledge_items
                    WHERE session_id = %s
                    ORDER BY attachment_seq ASC
                    """,
                    (session_id,),
                )
                rows = cursor.fetchall()
                cursor.execute(
                    """
                    SELECT doc_id
                    FROM session_private_samples
                    WHERE session_id = %s
                    ORDER BY attachment_seq ASC
                    """,
                    (session_id,),
                )
                legacy_rows = cursor.fetchall()
        knowledge_item_ids = [row["knowledge_item_id"] for row in rows]
        for legacy_row in legacy_rows:
            mapped = self._resolve_knowledge_item_id_from_legacy_doc_id(legacy_row["doc_id"])
            knowledge_item_ids.append(mapped or legacy_row["doc_id"])
        return list(dict.fromkeys(knowledge_item_ids))

    def _get_session_summary(self, *, owner_user_id: str, session_id: str) -> SessionSummary | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        s.session_id,
                        s.title,
                        s.created_at,
                        s.updated_at,
                        COALESCE(s.is_pinned, FALSE) AS is_pinned,
                        s.pinned_at,
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
                    WHERE s.session_id = %s AND s.owner_user_id = %s
                    """,
                    (session_id, owner_user_id),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        return self._row_to_session_summary(row)

    @staticmethod
    def _row_to_session_summary(row) -> SessionSummary:
        return SessionSummary.model_validate(dict(row))

    @staticmethod
    def _row_to_session_message(row) -> SessionMessage:
        payload = dict(row)
        payload["citations"] = json.loads(payload.pop("citations_json") or "[]")
        return SessionMessage.model_validate(payload)

    @staticmethod
    def _row_to_uploaded_file(row) -> UploadedFile:
        payload = dict(row)
        payload["ocr_used"] = bool(payload.get("ocr_used", False))
        return UploadedFile.model_validate(payload)

    @staticmethod
    def _uploaded_file_to_attachment(file: UploadedFile) -> SessionAttachment:
        return SessionAttachment(
            file_id=file.file_id,
            knowledge_item_id=file.knowledge_item_id,
            filename=file.filename,
            source_type="uploaded_file",
            attached_at=file.stored_at,
            parse_status=file.parse_status,
            index_status=None,
            summary=file.summary,
            page_count=file.page_count,
            sheet_count=file.sheet_count,
            slide_count=file.slide_count,
            chunk_count=file.chunk_count,
            error_message=file.error_message,
        )

    @staticmethod
    def _row_to_knowledge_attachment(row) -> SessionAttachment:
        title = row["title"] or row["knowledge_item_id"]
        source_type = "uploaded_file" if row["source_type"] == "uploaded_file" else "private_sample"
        return SessionAttachment(
            file_id=row["file_id"] or row["knowledge_item_id"],
            knowledge_item_id=row["knowledge_item_id"],
            filename=title,
            source_type=source_type,
            attached_at=row["attached_at"],
            index_status=row.get("index_status"),
            parse_status=row.get("parse_status"),
            summary=row.get("summary"),
            page_count=row.get("page_count"),
            sheet_count=row.get("sheet_count"),
            slide_count=row.get("slide_count"),
            chunk_count=row.get("chunk_count"),
            error_message=row.get("error_message"),
        )

    @staticmethod
    def _row_to_private_sample_attachment(row) -> SessionAttachment:
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
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT knowledge_item_id
                    FROM knowledge_items
                    WHERE source_ref = %s AND source_type = 'private_sample_repo'
                    ORDER BY updated_at DESC, created_at DESC
                    LIMIT 1
                    """,
                    (doc_id,),
                )
                row = cursor.fetchone()
        return row["knowledge_item_id"] if row else None


@lru_cache(maxsize=1)
def build_postgres_session_store(database_url: str) -> PostgreSQLSessionStore:
    return PostgreSQLSessionStore(database_url)
