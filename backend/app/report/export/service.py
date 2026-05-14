from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import resolve_repo_path
from app.report.export.docx_exporter import DocxReportExporter
from app.report.export.filenames import build_report_filename
from app.report.export.markdown_ir import report_to_ir
from app.report.export.pdf_exporter import PdfReportExporter
from app.report.export.schemas import (
    CreateReportExportRequest,
    ReportExportFormat,
    ReportExportResponse,
    ReportFileRecord,
    ReportFileSummary,
)
from app.report.export.security import ensure_child_path
from app.report.export.storage import ReportExportStorage
from app.report.service import ReportService, get_report_service


class ReportExportError(RuntimeError):
    pass


class ReportExportService:
    def __init__(
        self,
        *,
        report_service: ReportService | None = None,
        storage: ReportExportStorage | None = None,
        output_root: Path | None = None,
    ) -> None:
        self.report_service = report_service or get_report_service()
        self.storage = storage or ReportExportStorage()
        self.output_root = output_root or resolve_repo_path("data/outputs/report_files")
        self.exporters = {
            "docx": DocxReportExporter(),
            "pdf": PdfReportExporter(),
        }

    def create_exports(
        self,
        *,
        owner_user_id: str,
        report_id: str,
        payload: CreateReportExportRequest | dict,
    ) -> ReportExportResponse:
        request = payload if isinstance(payload, CreateReportExportRequest) else CreateReportExportRequest.model_validate(payload)
        report = self.report_service.get_report(owner_user_id=owner_user_id, report_id=report_id)
        if report is None:
            raise KeyError(report_id)

        ir = report_to_ir(report)
        files: list[ReportFileSummary] = []
        for fmt in request.formats:
            existing = None if request.force_regenerate else self.storage.find_existing(
                owner_user_id=owner_user_id,
                report_id=report_id,
                fmt=fmt,
                template_id=request.template_id,
            )
            if existing is not None and Path(existing.storage_path).exists():
                files.append(ReportFileSummary.from_record(existing))
                continue

            record = self._export_one(
                owner_user_id=owner_user_id,
                report_id=report_id,
                session_id=report.session_id,
                title=report.title,
                fmt=fmt,
                template_id=request.template_id,
                ir=ir,
            )
            files.append(ReportFileSummary.from_record(record))

        return ReportExportResponse(report_id=report_id, files=files)

    def list_exports(self, *, owner_user_id: str, report_id: str) -> ReportExportResponse:
        report = self.report_service.get_report(owner_user_id=owner_user_id, report_id=report_id)
        if report is None:
            raise KeyError(report_id)
        records = self.storage.list_report_files(owner_user_id=owner_user_id, report_id=report_id)
        return ReportExportResponse(report_id=report_id, files=[ReportFileSummary.from_record(item) for item in records])

    def get_download_file(self, *, owner_user_id: str, file_id: str) -> ReportFileRecord | None:
        record = self.storage.get_file(owner_user_id=owner_user_id, file_id=file_id)
        if record is None:
            return None
        path = Path(record.storage_path)
        if not path.exists() or not path.is_file():
            return None
        ensure_child_path(self.output_root, path)
        return record

    def _export_one(
        self,
        *,
        owner_user_id: str,
        report_id: str,
        session_id: str,
        title: str,
        fmt: ReportExportFormat,
        template_id: str,
        ir,
    ) -> ReportFileRecord:
        exporter = self.exporters.get(fmt)
        if exporter is None:
            raise ReportExportError(f"Unsupported export format: {fmt}")

        file_id = f"rfile-{fmt}-{uuid4().hex[:12]}"
        filename = build_report_filename(title=title, report_id=report_id, fmt=fmt)
        output_dir = ensure_child_path(self.output_root, self.output_root / owner_user_id / report_id)
        output_path = ensure_child_path(output_dir, output_dir / f"{file_id}.{fmt}")
        result = exporter.export(ir, output_path, template_id=template_id)
        record = ReportFileRecord(
            file_id=file_id,
            owner_user_id=owner_user_id,
            report_id=report_id,
            session_id=session_id,
            format=fmt,
            template_id=template_id,
            filename=filename,
            storage_path=str(result.output_path),
            content_type=result.content_type,
            file_size_bytes=result.file_size_bytes,
            checksum_sha256=result.checksum_sha256,
            created_at=datetime.now(timezone.utc),
        )
        return self.storage.create_file(record)


def get_report_export_service() -> ReportExportService:
    return ReportExportService()
