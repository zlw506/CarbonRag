import json
import sqlite3
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.core.config import get_settings
from app.report.schemas import ReportDetail, ReportSourceEntry, ReportSummary, StoredReport
from app.runtime_db.bootstrap import bootstrap_runtime_database, get_runtime_backend_kind
from app.session.store import DEFAULT_SESSION_DB_PATH, SessionStore, get_session_store


class ReportStorage:
    def __init__(
        self,
        *,
        store: SessionStore | None = None,
        database_url: str | None = None,
        sqlite_db_path: Path | str | None = None,
    ) -> None:
        self.store = store or get_session_store()
        settings = get_settings()
        self.database_url = database_url or getattr(self.store, "database_url", None) or settings.database_url
        self.sqlite_db_path = Path(sqlite_db_path or getattr(self.store, "db_path", DEFAULT_SESSION_DB_PATH))
        self.backend_kind = get_runtime_backend_kind(self.database_url)
        self.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
        bootstrap_runtime_database(database_url=self.database_url, sqlite_db_path=self.sqlite_db_path)

    def _connect(self):
        if self.backend_kind == "postgresql":
            return psycopg.connect(self.database_url, row_factory=dict_row)

        connection = sqlite3.connect(self.sqlite_db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def create_report(self, *, owner_user_id: str, report: StoredReport) -> ReportDetail:
        citations_json = json.dumps([item.model_dump() for item in report.citations], ensure_ascii=False)
        source_summary_json = json.dumps(report.source_summary.model_dump(), ensure_ascii=False)

        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO reports (
                            report_id, owner_user_id, session_id, report_type, title, content, output_format,
                            citations_json, source_summary_json, trace_id, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            report.report_id,
                            owner_user_id,
                            report.session_id,
                            report.report_type,
                            report.title,
                            report.content,
                            report.output_format,
                            citations_json,
                            source_summary_json,
                            report.trace_id,
                            report.created_at.isoformat(),
                            report.updated_at.isoformat(),
                        ),
                    )
                    for source in report.sources:
                        cursor.execute(
                            """
                            INSERT INTO report_sources (report_id, source_type, source_ref, label, order_index)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                report.report_id,
                                source.source_type,
                                source.source_ref,
                                source.label,
                                source.order_index,
                            ),
                        )
            else:
                connection.execute(
                    """
                    INSERT INTO reports (
                        report_id, owner_user_id, session_id, report_type, title, content, output_format,
                        citations_json, source_summary_json, trace_id, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        report.report_id,
                        owner_user_id,
                        report.session_id,
                        report.report_type,
                        report.title,
                        report.content,
                        report.output_format,
                        citations_json,
                        source_summary_json,
                        report.trace_id,
                        report.created_at.isoformat(),
                        report.updated_at.isoformat(),
                    ),
                )
                for source in report.sources:
                    connection.execute(
                        """
                        INSERT INTO report_sources (report_id, source_type, source_ref, label, order_index)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            report.report_id,
                            source.source_type,
                            source.source_ref,
                            source.label,
                            source.order_index,
                        ),
                    )

        created = self.get_report(owner_user_id=owner_user_id, report_id=report.report_id)
        if created is None:
            raise RuntimeError("Stored report could not be reloaded.")
        return created

    def get_report(self, *, owner_user_id: str, report_id: str) -> ReportDetail | None:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM reports WHERE report_id = %s AND owner_user_id = %s",
                        (report_id, owner_user_id),
                    )
                    row = cursor.fetchone()
                    if row is None:
                        return None
                    cursor.execute(
                        """
                        SELECT source_type, source_ref, label, order_index
                        FROM report_sources
                        WHERE report_id = %s
                        ORDER BY order_index ASC, source_seq ASC
                        """,
                        (report_id,),
                    )
                    source_rows = cursor.fetchall()
            else:
                row = connection.execute(
                    "SELECT * FROM reports WHERE report_id = ? AND owner_user_id = ?",
                    (report_id, owner_user_id),
                ).fetchone()
                if row is None:
                    return None
                source_rows = connection.execute(
                    """
                    SELECT source_type, source_ref, label, order_index
                    FROM report_sources
                    WHERE report_id = ?
                    ORDER BY order_index ASC, source_seq ASC
                    """,
                    (report_id,),
                ).fetchall()

        return self._row_to_report_detail(row, source_rows)

    def update_report(
        self,
        *,
        owner_user_id: str,
        report_id: str,
        title: str | None,
        content: str,
        updated_at: datetime,
    ) -> ReportDetail | None:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE reports
                        SET title = COALESCE(%s, title),
                            content = %s,
                            updated_at = %s
                        WHERE report_id = %s
                          AND owner_user_id = %s
                        """,
                        (title, content, updated_at.isoformat(), report_id, owner_user_id),
                    )
                    if cursor.rowcount == 0:
                        return None
            else:
                cursor = connection.execute(
                    """
                    UPDATE reports
                    SET title = COALESCE(?, title),
                        content = ?,
                        updated_at = ?
                    WHERE report_id = ?
                      AND owner_user_id = ?
                    """,
                    (title, content, updated_at.isoformat(), report_id, owner_user_id),
                )
                if cursor.rowcount == 0:
                    return None

        return self.get_report(owner_user_id=owner_user_id, report_id=report_id)

    def list_session_reports(self, *, owner_user_id: str, session_id: str) -> list[ReportSummary]:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT
                            r.report_id,
                            r.report_type,
                            r.title,
                            r.created_at,
                            r.updated_at,
                            COUNT(rs.source_seq) AS source_count
                        FROM reports r
                        LEFT JOIN report_sources rs ON rs.report_id = r.report_id
                        WHERE r.session_id = %s
                          AND r.owner_user_id = %s
                        GROUP BY r.report_id
                        ORDER BY r.updated_at DESC, r.created_at DESC
                        """,
                        (session_id, owner_user_id),
                    )
                    rows = cursor.fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT
                        r.report_id,
                        r.report_type,
                        r.title,
                        r.created_at,
                        r.updated_at,
                        COUNT(rs.source_seq) AS source_count
                    FROM reports r
                    LEFT JOIN report_sources rs ON rs.report_id = r.report_id
                    WHERE r.session_id = ?
                      AND r.owner_user_id = ?
                    GROUP BY r.report_id
                    ORDER BY r.updated_at DESC, r.created_at DESC
                    """,
                    (session_id, owner_user_id),
                ).fetchall()

        return [
            ReportSummary(
                report_id=row["report_id"],
                report_type=row["report_type"],
                title=row["title"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                source_count=row["source_count"],
            )
            for row in rows
        ]

    @staticmethod
    def _row_to_report_detail(row, source_rows) -> ReportDetail:
        payload = dict(row)
        return ReportDetail(
            report_id=payload["report_id"],
            session_id=payload["session_id"],
            report_type=payload["report_type"],
            title=payload["title"],
            content=payload["content"],
            output_format=payload["output_format"],
            citations=json.loads(payload["citations_json"] or "[]"),
            source_summary=json.loads(payload["source_summary_json"] or "{}"),
            sources=[ReportSourceEntry.model_validate(dict(item)) for item in source_rows],
            trace_id=payload["trace_id"],
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
        )
