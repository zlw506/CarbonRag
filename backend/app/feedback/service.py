import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.feedback.schemas import FeedbackRequest, FeedbackResponse, StoredFeedbackEntry
from app.session.adapters.sqlite_store import SQLiteSessionStore, get_session_store
from app.session.service import SessionService, get_session_service


class FeedbackService:
    def __init__(
        self,
        *,
        session_service: SessionService | None = None,
        store: SQLiteSessionStore | None = None,
    ) -> None:
        self.session_service = session_service or get_session_service()
        self.store = store or get_session_store()
        self.db_path = Path(self.store.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback_entries (
                    feedback_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback_id TEXT NOT NULL UNIQUE,
                    target_type TEXT NOT NULL,
                    trace_id TEXT NOT NULL,
                    session_id TEXT,
                    rating TEXT NOT NULL,
                    comment TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_feedback_entries_trace
                ON feedback_entries(trace_id, created_at DESC)
                """
            )

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(timezone.utc)

    def submit(self, payload: FeedbackRequest) -> FeedbackResponse:
        if payload.session_id is not None and self.session_service.get_session(payload.session_id) is None:
            raise KeyError(f"Unknown session: {payload.session_id}")

        feedback_id = f"feedback-{uuid4().hex[:12]}"
        created_at = self._utcnow()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO feedback_entries (
                    feedback_id,
                    target_type,
                    trace_id,
                    session_id,
                    rating,
                    comment,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback_id,
                    payload.target_type,
                    payload.trace_id,
                    payload.session_id,
                    payload.rating,
                    payload.comment,
                    created_at.isoformat(),
                ),
            )

        return FeedbackResponse(status="ok", feedback_id=feedback_id, created_at=created_at)

    def get_entry(self, feedback_id: str) -> StoredFeedbackEntry | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT feedback_id, target_type, trace_id, session_id, rating, comment, created_at
                FROM feedback_entries
                WHERE feedback_id = ?
                """,
                (feedback_id,),
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
