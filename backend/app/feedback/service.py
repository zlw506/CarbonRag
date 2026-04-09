import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from app.core.config import get_settings
from app.feedback.schemas import FeedbackRequest, FeedbackResponse, StoredFeedbackEntry
from app.runtime_db.bootstrap import bootstrap_runtime_database, get_runtime_backend_kind
from app.session.service import SessionService, get_session_service
from app.session.store import DEFAULT_SESSION_DB_PATH, SessionStore, get_session_store


class FeedbackService:
    def __init__(
        self,
        *,
        session_service: SessionService | None = None,
        store: SessionStore | None = None,
        database_url: str | None = None,
        sqlite_db_path: Path | str | None = None,
    ) -> None:
        self.session_service = session_service or get_session_service()
        self.store = store or get_session_store()
        settings = get_settings()
        self.database_url = database_url or getattr(self.store, "database_url", None) or settings.database_url
        self.sqlite_db_path = Path(sqlite_db_path or getattr(self.store, "db_path", DEFAULT_SESSION_DB_PATH))
        self.backend_kind = get_runtime_backend_kind(self.database_url)
        self.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
        bootstrap_runtime_database(
            database_url=self.database_url,
            sqlite_db_path=self.sqlite_db_path,
        )

    def _connect(self):
        if self.backend_kind == "postgresql":
            return psycopg.connect(self.database_url, row_factory=dict_row)

        connection = sqlite3.connect(self.sqlite_db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    def submit(self, *, owner_user_id: str, payload: FeedbackRequest) -> FeedbackResponse:
        if payload.session_id is not None:
            self.session_service.require_session(owner_user_id=owner_user_id, session_id=payload.session_id)

        feedback_id = f"feedback-{uuid4().hex[:12]}"
        created_at = self._utcnow()
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO feedback_entries (
                            feedback_id,
                            owner_user_id,
                            target_type,
                            trace_id,
                            session_id,
                            rating,
                            comment,
                            created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            feedback_id,
                            owner_user_id,
                            payload.target_type,
                            payload.trace_id,
                            payload.session_id,
                            payload.rating,
                            payload.comment,
                            created_at.isoformat(),
                        ),
                    )
            else:
                connection.execute(
                    """
                    INSERT INTO feedback_entries (
                        feedback_id,
                        owner_user_id,
                        target_type,
                        trace_id,
                        session_id,
                        rating,
                        comment,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feedback_id,
                        owner_user_id,
                        payload.target_type,
                        payload.trace_id,
                        payload.session_id,
                        payload.rating,
                        payload.comment,
                        created_at.isoformat(),
                    ),
                )

        return FeedbackResponse(status="ok", feedback_id=feedback_id, created_at=created_at)

    def get_entry(self, *, owner_user_id: str, feedback_id: str) -> StoredFeedbackEntry | None:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT feedback_id, target_type, trace_id, session_id, rating, comment, created_at
                        FROM feedback_entries
                        WHERE feedback_id = %s
                          AND owner_user_id = %s
                        """,
                        (feedback_id, owner_user_id),
                    )
                    row = cursor.fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT feedback_id, target_type, trace_id, session_id, rating, comment, created_at
                    FROM feedback_entries
                    WHERE feedback_id = ?
                      AND owner_user_id = ?
                    """,
                    (feedback_id, owner_user_id),
                ).fetchone()

        if row is None:
            return None

        payload = dict(row)
        return StoredFeedbackEntry(
            feedback_id=payload["feedback_id"],
            target_type=payload["target_type"],
            trace_id=payload["trace_id"],
            session_id=payload["session_id"],
            rating=payload["rating"],
            comment=payload["comment"],
            created_at=datetime.fromisoformat(payload["created_at"]),
        )


def get_feedback_service() -> FeedbackService:
    return FeedbackService()
