import sqlite3
from datetime import datetime

import psycopg
from psycopg.rows import dict_row
from fastapi import APIRouter, Depends

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.feedback.schemas import StoredFeedbackEntry
from app.knowledge import get_knowledge_service
from app.report.schemas import ReportSummary
from app.report.service import get_report_service
from app.knowledge.schemas import KnowledgeItemSummary
from app.session.service import get_session_service

router = APIRouter(prefix="/me")


@router.get("/uploads", response_model=list[KnowledgeItemSummary])
def list_my_uploads(current_user: AuthenticatedUser = Depends(require_authenticated_user)) -> list[KnowledgeItemSummary]:
    service = get_knowledge_service()
    service.sync_uploaded_files(owner_user_id=current_user.user_id)
    try:
        service.run_queued_tasks()
    except Exception:
        pass
    items = service.list_personal_items(owner_user_id=current_user.user_id, source_type="uploaded_file")
    return [KnowledgeItemSummary.model_validate(item.model_dump()) for item in items]


@router.get("/reports", response_model=list[ReportSummary])
def list_my_reports(current_user: AuthenticatedUser = Depends(require_authenticated_user)) -> list[ReportSummary]:
    session_service = get_session_service()
    report_service = get_report_service()
    reports: list[ReportSummary] = []
    for session in session_service.list_sessions(owner_user_id=current_user.user_id):
        reports.extend(report_service.list_session_reports(owner_user_id=current_user.user_id, session_id=session.session_id))
    reports.sort(key=lambda item: (item.updated_at, item.created_at), reverse=True)
    return reports


@router.get("/feedback", response_model=list[StoredFeedbackEntry])
def list_my_feedback(current_user: AuthenticatedUser = Depends(require_authenticated_user)) -> list[StoredFeedbackEntry]:
    session_service = get_session_service()
    store = session_service.store
    rows = _fetch_rows(
        database_url=getattr(store, "database_url", None),
        sqlite_db_path=getattr(store, "db_path", None),
        owner_user_id=current_user.user_id,
    )
    return [StoredFeedbackEntry.model_validate(dict(row)) for row in rows]


def _fetch_rows(*, database_url: str | None, sqlite_db_path, owner_user_id: str):
    if database_url:
        with psycopg.connect(database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT feedback_id, target_type, trace_id, session_id, rating, comment, created_at
                    FROM feedback_entries
                    WHERE owner_user_id = %s
                    ORDER BY created_at DESC
                    """,
                    (owner_user_id,),
                )
                return cursor.fetchall()

    connection = sqlite3.connect(sqlite_db_path)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            """
            SELECT feedback_id, target_type, trace_id, session_id, rating, comment, created_at
            FROM feedback_entries
            WHERE owner_user_id = ?
            ORDER BY created_at DESC
            """,
            (owner_user_id,),
        ).fetchall()
        return rows
    finally:
        connection.close()
