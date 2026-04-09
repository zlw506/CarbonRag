import sqlite3
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from app.admin.schemas import (
    AdminFeedbackOverview,
    AdminFeedbackRecentEntry,
    AdminPrivateSampleItem,
    AdminSystemStatus,
    AdminUserSummary,
    KnowledgeRefreshTask,
    KnowledgeRefreshStatus,
    KnowledgeRefreshScope,
)
from app.ai_runtime.providers.factory import get_chat_provider
from app.auth.schemas import UserRole
from app.auth.service import AuthService, get_auth_service
from app.core.config import get_settings
from app.private_samples.catalog import (
    list_admin_private_sample_catalog,
    refresh_private_sample_catalog,
)
from app.private_samples.overrides import update_private_sample_override
from app.retrieval.mixed_retriever import get_mixed_scope_retriever
from app.retrieval.private_corpus_loader import load_private_sample_documents
from app.retrieval.private_retriever import get_private_sample_retriever
from app.retrieval.public_corpus_loader import load_public_policy_documents
from app.retrieval.public_retriever import get_public_policy_retriever
from app.runtime_db.bootstrap import bootstrap_runtime_database, get_runtime_backend_kind
from app.session.store import DEFAULT_SESSION_DB_PATH


class AdminService:
    def __init__(
        self,
        *,
        auth_service: AuthService | None = None,
        database_url: str | None = None,
        sqlite_db_path: Path | str | None = None,
    ) -> None:
        self.auth_service = auth_service or get_auth_service()
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.sqlite_db_path = Path(sqlite_db_path or DEFAULT_SESSION_DB_PATH)
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

    def list_users(self) -> list[AdminUserSummary]:
        users = {user.user_id: user for user in self.auth_service.list_users()}
        session_counts = self._count_grouped_rows("sessions", "owner_user_id")
        report_counts = self._count_grouped_rows("reports", "owner_user_id")
        feedback_counts = self._count_grouped_rows("feedback_entries", "owner_user_id")

        items: list[AdminUserSummary] = []
        for user in users.values():
            items.append(
                AdminUserSummary(
                    user_id=user.user_id,
                    username=user.username,
                    role=user.role,
                    is_active=user.is_active,
                    password_must_change=user.password_must_change,
                    created_at=user.created_at,
                    last_login_at=user.last_login_at,
                    session_count=session_counts.get(user.user_id, 0),
                    report_count=report_counts.get(user.user_id, 0),
                    feedback_count=feedback_counts.get(user.user_id, 0),
                )
            )
        return items

    def update_user(self, *, user_id: str, role: UserRole, is_active: bool):
        return self.auth_service.update_user(user_id=user_id, role=role, is_active=is_active)

    def reset_password(self, *, user_id: str) -> str:
        return self.auth_service.reset_password(user_id=user_id)

    def get_feedback_overview(self) -> AdminFeedbackOverview:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            COUNT(*) AS total_count,
                            COUNT(*) FILTER (WHERE target_type = 'ask' AND rating = 'up') AS ask_up_count,
                            COUNT(*) FILTER (WHERE target_type = 'ask' AND rating = 'down') AS ask_down_count,
                            COUNT(*) FILTER (WHERE target_type = 'calc_carbon' AND rating = 'up') AS calc_up_count,
                            COUNT(*) FILTER (WHERE target_type = 'calc_carbon' AND rating = 'down') AS calc_down_count
                        FROM feedback_entries
                        """
                    )
                    aggregate = cursor.fetchone()
                    cursor.execute(
                        """
                        SELECT feedback_id, target_type, rating, session_id, owner_user_id, created_at
                        FROM feedback_entries
                        ORDER BY created_at DESC
                        LIMIT 20
                        """
                    )
                    recent_rows = cursor.fetchall()
            else:
                aggregate = connection.execute(
                    """
                    SELECT
                        COUNT(*) AS total_count,
                        SUM(CASE WHEN target_type = 'ask' AND rating = 'up' THEN 1 ELSE 0 END) AS ask_up_count,
                        SUM(CASE WHEN target_type = 'ask' AND rating = 'down' THEN 1 ELSE 0 END) AS ask_down_count,
                        SUM(CASE WHEN target_type = 'calc_carbon' AND rating = 'up' THEN 1 ELSE 0 END) AS calc_up_count,
                        SUM(CASE WHEN target_type = 'calc_carbon' AND rating = 'down' THEN 1 ELSE 0 END) AS calc_down_count
                    FROM feedback_entries
                    """
                ).fetchone()
                recent_rows = connection.execute(
                    """
                    SELECT feedback_id, target_type, rating, session_id, owner_user_id, created_at
                    FROM feedback_entries
                    ORDER BY created_at DESC
                    LIMIT 20
                    """
                ).fetchall()

        aggregate = dict(aggregate or {})
        return AdminFeedbackOverview(
            total_count=int(aggregate.get("total_count") or 0),
            ask_up_count=int(aggregate.get("ask_up_count") or 0),
            ask_down_count=int(aggregate.get("ask_down_count") or 0),
            calc_up_count=int(aggregate.get("calc_up_count") or 0),
            calc_down_count=int(aggregate.get("calc_down_count") or 0),
            recent_entries=[AdminFeedbackRecentEntry.model_validate(dict(row)) for row in recent_rows],
        )

    def list_private_samples(self) -> list[AdminPrivateSampleItem]:
        return [
            AdminPrivateSampleItem.model_validate(item)
            for item in list_admin_private_sample_catalog(
                database_url=self.database_url,
                sqlite_db_path=self.sqlite_db_path,
            )
        ]

    def update_private_sample(self, *, doc_id: str, is_enabled: bool, session_attachable: bool, updated_by_user_id: str):
        known_doc_ids = {item.doc_id for item in self.list_private_samples()}
        if doc_id not in known_doc_ids:
            raise KeyError(doc_id)
        update_private_sample_override(
            doc_id=doc_id,
            is_enabled=is_enabled,
            session_attachable=session_attachable,
            updated_by_user_id=updated_by_user_id,
            database_url=self.database_url,
            sqlite_db_path=self.sqlite_db_path,
        )
        self._clear_retrieval_caches("private_sample")
        return next(item for item in self.list_private_samples() if item.doc_id == doc_id)

    def list_knowledge_refresh_tasks(self) -> list[KnowledgeRefreshTask]:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT task_id, scope, status, requested_by_user_id, summary, created_at, started_at, finished_at
                        FROM knowledge_refresh_tasks
                        ORDER BY created_at DESC
                        """
                    )
                    rows = cursor.fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT task_id, scope, status, requested_by_user_id, summary, created_at, started_at, finished_at
                    FROM knowledge_refresh_tasks
                    ORDER BY created_at DESC
                    """
                ).fetchall()
        return [KnowledgeRefreshTask.model_validate(dict(row)) for row in rows]

    def trigger_knowledge_refresh(self, *, scope: KnowledgeRefreshScope, requested_by_user_id: str) -> KnowledgeRefreshTask:
        task_id = f"refresh-{uuid4().hex[:12]}"
        created_at = self._utcnow()
        self._persist_refresh_task(
            task_id=task_id,
            scope=scope,
            status="running",
            requested_by_user_id=requested_by_user_id,
            summary="Knowledge refresh started.",
            created_at=created_at,
            started_at=created_at,
            finished_at=None,
        )
        try:
            self._clear_retrieval_caches(scope)
            summary = self._validate_reloaded_sources(scope)
            finished_at = self._utcnow()
            self._persist_refresh_task(
                task_id=task_id,
                scope=scope,
                status="succeeded",
                requested_by_user_id=requested_by_user_id,
                summary=summary,
                created_at=created_at,
                started_at=created_at,
                finished_at=finished_at,
                replace=True,
            )
        except Exception as exc:
            finished_at = self._utcnow()
            self._persist_refresh_task(
                task_id=task_id,
                scope=scope,
                status="failed",
                requested_by_user_id=requested_by_user_id,
                summary=str(exc),
                created_at=created_at,
                started_at=created_at,
                finished_at=finished_at,
                replace=True,
            )
            raise

        return next(item for item in self.list_knowledge_refresh_tasks() if item.task_id == task_id)

    def get_system_status(self) -> AdminSystemStatus:
        settings = get_settings()
        provider = get_chat_provider().describe()
        private_samples = self.list_private_samples()
        refresh_tasks = self.list_knowledge_refresh_tasks()
        latest_refresh_status = refresh_tasks[0].status if refresh_tasks else None
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) AS count FROM users")
                    total_users = cursor.fetchone()["count"]
                    cursor.execute("SELECT COUNT(*) AS count FROM sessions")
                    total_sessions = cursor.fetchone()["count"]
                    cursor.execute("SELECT COUNT(*) AS count FROM reports")
                    total_reports = cursor.fetchone()["count"]
                    cursor.execute("SELECT COUNT(*) AS count FROM feedback_entries")
                    total_feedback = cursor.fetchone()["count"]
            else:
                total_users = connection.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
                total_sessions = connection.execute("SELECT COUNT(*) AS count FROM sessions").fetchone()["count"]
                total_reports = connection.execute("SELECT COUNT(*) AS count FROM reports").fetchone()["count"]
                total_feedback = connection.execute("SELECT COUNT(*) AS count FROM feedback_entries").fetchone()["count"]
        return AdminSystemStatus(
            app_name=settings.app_name,
            version=settings.app_version,
            env=settings.app_env,
            database_backend=self.backend_kind,
            model_provider_mode=provider.mode,
            model_name=provider.default_model,
            total_users=int(total_users),
            total_sessions=int(total_sessions),
            total_reports=int(total_reports),
            total_feedback_entries=int(total_feedback),
            total_private_samples=len(private_samples),
            enabled_private_samples=sum(1 for item in private_samples if item.is_enabled),
            latest_refresh_status=latest_refresh_status,
        )

    def _count_grouped_rows(self, table_name: str, column_name: str) -> dict[str, int]:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        SELECT {column_name} AS owner_user_id, COUNT(*) AS count
                        FROM {table_name}
                        WHERE {column_name} IS NOT NULL
                        GROUP BY {column_name}
                        """
                    )
                    rows = cursor.fetchall()
            else:
                rows = connection.execute(
                    f"""
                    SELECT {column_name} AS owner_user_id, COUNT(*) AS count
                    FROM {table_name}
                    WHERE {column_name} IS NOT NULL
                    GROUP BY {column_name}
                    """
                ).fetchall()
        return {row["owner_user_id"]: int(row["count"]) for row in rows}

    def _persist_refresh_task(
        self,
        *,
        task_id: str,
        scope: KnowledgeRefreshScope,
        status: KnowledgeRefreshStatus,
        requested_by_user_id: str,
        summary: str,
        created_at: datetime,
        started_at: datetime | None,
        finished_at: datetime | None,
        replace: bool = False,
    ) -> None:
        created_at_value = created_at.isoformat()
        started_at_value = started_at.isoformat() if started_at else None
        finished_at_value = finished_at.isoformat() if finished_at else None
        if replace:
            delete_statement = "DELETE FROM knowledge_refresh_tasks WHERE task_id = %s" if self.backend_kind == "postgresql" else "DELETE FROM knowledge_refresh_tasks WHERE task_id = ?"
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    if replace:
                        cursor.execute(delete_statement, (task_id,))
                    cursor.execute(
                        """
                        INSERT INTO knowledge_refresh_tasks (
                            task_id, scope, status, requested_by_user_id, summary, created_at, started_at, finished_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            task_id,
                            scope,
                            status,
                            requested_by_user_id,
                            summary,
                            created_at_value,
                            started_at_value,
                            finished_at_value,
                        ),
                    )
            else:
                if replace:
                    connection.execute(delete_statement, (task_id,))
                connection.execute(
                    """
                    INSERT INTO knowledge_refresh_tasks (
                        task_id, scope, status, requested_by_user_id, summary, created_at, started_at, finished_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task_id,
                        scope,
                        status,
                        requested_by_user_id,
                        summary,
                        created_at_value,
                        started_at_value,
                        finished_at_value,
                    ),
                )

    @staticmethod
    def _clear_retrieval_caches(scope: KnowledgeRefreshScope) -> None:
        if scope in {"public_policy", "all"}:
            load_public_policy_documents.cache_clear()
            get_public_policy_retriever.cache_clear()
        if scope in {"private_sample", "all"}:
            refresh_private_sample_catalog()
            load_private_sample_documents.cache_clear()
            get_private_sample_retriever.cache_clear()
        get_mixed_scope_retriever.cache_clear()

    @staticmethod
    def _validate_reloaded_sources(scope: KnowledgeRefreshScope) -> str:
        summaries: list[str] = []
        if scope in {"public_policy", "all"}:
            public_documents = load_public_policy_documents()
            get_public_policy_retriever()
            summaries.append(f"public_policy={len(public_documents)} docs")
        if scope in {"private_sample", "all"}:
            private_documents = load_private_sample_documents()
            get_private_sample_retriever()
            summaries.append(f"private_sample={len(private_documents)} docs")
        get_mixed_scope_retriever()
        return "; ".join(summaries) or "no-op"


@lru_cache(maxsize=1)
def get_admin_service() -> AdminService:
    return AdminService()
