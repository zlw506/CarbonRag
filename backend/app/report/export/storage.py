import sqlite3
from datetime import datetime
from pathlib import Path

from app.core.config import get_settings
from app.report.export.schemas import ReportExportFormat, ReportFileRecord
from app.runtime_db.bootstrap import bootstrap_runtime_database, get_runtime_backend_kind
from app.runtime_db.compat import connect_postgres
from app.session.store import DEFAULT_SESSION_DB_PATH, SessionStore, get_session_store


class ReportExportStorage:
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
            return connect_postgres(self.database_url)
        connection = sqlite3.connect(self.sqlite_db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def create_file(self, record: ReportFileRecord) -> ReportFileRecord:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO report_files (
                            file_id, owner_user_id, report_id, session_id, format, template_id,
                            filename, storage_path, content_type, file_size_bytes,
                            checksum_sha256, created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        _record_values(record),
                    )
            else:
                connection.execute(
                    """
                    INSERT INTO report_files (
                        file_id, owner_user_id, report_id, session_id, format, template_id,
                        filename, storage_path, content_type, file_size_bytes,
                        checksum_sha256, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    _record_values(record),
                )
        return record

    def find_existing(
        self,
        *,
        owner_user_id: str,
        report_id: str,
        fmt: ReportExportFormat,
        template_id: str,
    ) -> ReportFileRecord | None:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM report_files
                        WHERE owner_user_id = %s AND report_id = %s AND format = %s AND template_id = %s
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (owner_user_id, report_id, fmt, template_id),
                    )
                    row = cursor.fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM report_files
                    WHERE owner_user_id = ? AND report_id = ? AND format = ? AND template_id = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (owner_user_id, report_id, fmt, template_id),
                ).fetchone()
        return _row_to_record(row) if row else None

    def list_report_files(self, *, owner_user_id: str, report_id: str) -> list[ReportFileRecord]:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * FROM report_files
                        WHERE owner_user_id = %s AND report_id = %s
                        ORDER BY created_at DESC
                        """,
                        (owner_user_id, report_id),
                    )
                    rows = cursor.fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM report_files
                    WHERE owner_user_id = ? AND report_id = ?
                    ORDER BY created_at DESC
                    """,
                    (owner_user_id, report_id),
                ).fetchall()
        return [_row_to_record(row) for row in rows]

    def get_file(self, *, owner_user_id: str, file_id: str) -> ReportFileRecord | None:
        with self._connect() as connection:
            if self.backend_kind == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT * FROM report_files WHERE owner_user_id = %s AND file_id = %s",
                        (owner_user_id, file_id),
                    )
                    row = cursor.fetchone()
            else:
                row = connection.execute(
                    "SELECT * FROM report_files WHERE owner_user_id = ? AND file_id = ?",
                    (owner_user_id, file_id),
                ).fetchone()
        return _row_to_record(row) if row else None


def _record_values(record: ReportFileRecord) -> tuple:
    return (
        record.file_id,
        record.owner_user_id,
        record.report_id,
        record.session_id,
        record.format,
        record.template_id,
        record.filename,
        record.storage_path,
        record.content_type,
        record.file_size_bytes,
        record.checksum_sha256,
        record.created_at.isoformat(),
    )


def _row_to_record(row) -> ReportFileRecord:
    payload = dict(row)
    return ReportFileRecord(
        file_id=payload["file_id"],
        owner_user_id=payload["owner_user_id"],
        report_id=payload["report_id"],
        session_id=payload["session_id"],
        format=payload["format"],
        template_id=payload["template_id"],
        filename=payload["filename"],
        storage_path=payload["storage_path"],
        content_type=payload["content_type"],
        file_size_bytes=payload["file_size_bytes"],
        checksum_sha256=payload["checksum_sha256"],
        created_at=datetime.fromisoformat(payload["created_at"]),
    )
