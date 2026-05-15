from datetime import datetime, timezone

from app.ai_runtime.tools.report_file_generate import ReportFileGenerateTool
from app.report.export.schemas import ReportExportResponse, ReportFileSummary
from app.report.schemas import ReportDetail, ReportSourceSummary
from app.report.service import ReportValidationError


class FakeReportService:
    def __init__(self) -> None:
        self.payload = None

    def create_report(self, *, owner_user_id: str, payload):
        self.payload = payload
        return ReportDetail(
            report_id="report-demo",
            session_id=payload.session_id,
            report_type=payload.report_type,
            title=payload.title or "对话报告",
            content="报告正文",
            citations=[],
            source_summary=ReportSourceSummary(),
            sources=[],
            trace_id="report-trace-demo",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )


class StrictFakeReportService(FakeReportService):
    def __init__(self) -> None:
        super().__init__()
        self.draft_warning = None

    def create_report(self, *, owner_user_id: str, payload):
        self.payload = payload
        raise ReportValidationError("policy_summary requires public policy citations.")

    def create_conversation_draft_report(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        report_type: str,
        title: str | None = None,
        request_text: str | None = None,
        validation_warning: str | None = None,
    ):
        self.draft_warning = validation_warning
        now = datetime.now(timezone.utc)
        return ReportDetail(
            report_id="report-draft-demo",
            session_id=session_id,
            report_type=report_type,
            title=title or "即时报告草稿",
            content=f"草稿正文\n\n校验说明：{validation_warning}",
            citations=[],
            source_summary=ReportSourceSummary(),
            sources=[],
            trace_id="report-trace-draft-demo",
            created_at=now,
            updated_at=now,
        )


class FakeExportService:
    def __init__(self) -> None:
        self.payload = None

    def create_exports(self, *, owner_user_id: str, report_id: str, payload):
        self.payload = payload
        now = datetime.now(timezone.utc)
        return ReportExportResponse(
            report_id=report_id,
            files=[
                ReportFileSummary(
                    file_id="rfile-docx-demo",
                    format="docx",
                    filename="对话报告.docx",
                    download_url="/api/v1/report-files/rfile-docx-demo/download",
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    file_size_bytes=123,
                    checksum_sha256="abc",
                    created_at=now,
                ),
                ReportFileSummary(
                    file_id="rfile-pdf-demo",
                    format="pdf",
                    filename="对话报告.pdf",
                    download_url="/api/v1/report-files/rfile-pdf-demo/download",
                    content_type="application/pdf",
                    file_size_bytes=456,
                    checksum_sha256="def",
                    created_at=now,
                ),
            ],
        )


def test_report_file_generate_tool_exports_docx_and_pdf() -> None:
    report_service = FakeReportService()
    export_service = FakeExportService()
    tool = ReportFileGenerateTool(report_service=report_service, export_service=export_service)

    result = tool.invoke(
        arguments={
            "question": "请把刚才内容生成 PDF 报告文件",
            "payload": {"owner_user_id": "user-demo", "session_id": "session-demo"},
        },
        context={},
        trace_id="trace-demo",
    )

    assert result.status == "success"
    assert result.output["report_id"] == "report-demo"
    assert result.output["formats"] == ["docx", "pdf"]
    assert [item["format"] for item in result.output["files"]] == ["docx", "pdf"]
    assert report_service.payload.report_type in {"policy_summary", "mixed_analysis", "carbon_summary"}
    assert export_service.payload.formats == ["docx", "pdf"]


def test_report_file_generate_tool_requires_runtime_payload() -> None:
    tool = ReportFileGenerateTool(report_service=FakeReportService(), export_service=FakeExportService())

    result = tool.invoke(
        arguments={"question": "请生成 DOCX 报告文件", "payload": {}},
        context={},
        trace_id="trace-demo",
    )

    assert result.status == "error"
    assert result.output["error_stage"] == "runtime_payload"
    assert result.output["files"] == []


def test_report_file_generate_tool_falls_back_to_downloadable_draft() -> None:
    report_service = StrictFakeReportService()
    export_service = FakeExportService()
    tool = ReportFileGenerateTool(report_service=report_service, export_service=export_service)

    result = tool.invoke(
        arguments={
            "question": "请立刻生成 PDF 报告文件",
            "payload": {"owner_user_id": "user-demo", "session_id": "session-demo"},
        },
        context={},
        trace_id="trace-demo",
    )

    assert result.status == "success"
    assert result.output["report_id"] == "report-draft-demo"
    assert result.output["files"]
    assert result.output["download_urls"] == [
        "/api/v1/report-files/rfile-docx-demo/download",
        "/api/v1/report-files/rfile-pdf-demo/download",
    ]
    assert report_service.draft_warning == "policy_summary requires public policy citations."
    assert "即时草稿" in result.output["title"]
    assert result.output["warnings"]
