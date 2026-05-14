from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.report.schemas import ReportCitation

ReportExportFormat = Literal["docx", "pdf"]
ReportBlockType = Literal[
    "paragraph",
    "heading",
    "bullet_list",
    "numbered_list",
    "table",
    "quote",
    "citation_list",
    "page_break",
]


class ReportTable(BaseModel):
    caption: str | None = None
    columns: list[str]
    rows: list[list[str]]
    footnote: str | None = None


class ReportBlock(BaseModel):
    type: ReportBlockType
    text: str | None = None
    items: list[str] | None = None
    table: ReportTable | None = None


class ReportSectionIR(BaseModel):
    heading: str
    blocks: list[ReportBlock] = Field(default_factory=list)


class ReportDocumentIR(BaseModel):
    title: str
    subtitle: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    sections: list[ReportSectionIR] = Field(default_factory=list)
    references: list[ReportCitation] = Field(default_factory=list)
    appendices: list[ReportSectionIR] = Field(default_factory=list)


class CreateReportExportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    formats: list[ReportExportFormat] = Field(default_factory=lambda: ["docx"])
    template_id: str = "default"
    include_citations: bool = True
    include_source_snippets: bool = True
    include_carbon_trace: bool = True
    force_regenerate: bool = False

    @field_validator("formats")
    @classmethod
    def normalize_formats(cls, value: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(item.strip().lower() for item in value if item.strip()))
        if not normalized:
            raise ValueError("formats cannot be empty.")
        unsupported = [item for item in normalized if item not in {"docx", "pdf"}]
        if unsupported:
            raise ValueError(f"Unsupported export format: {', '.join(unsupported)}")
        return normalized

    @field_validator("template_id")
    @classmethod
    def normalize_template_id(cls, value: str) -> str:
        normalized = value.strip() or "default"
        if normalized != "default":
            raise ValueError("Only the default report export template is supported in this version.")
        return normalized


class ReportFileRecord(BaseModel):
    file_id: str
    owner_user_id: str
    report_id: str
    session_id: str
    format: ReportExportFormat
    template_id: str
    filename: str
    storage_path: str
    content_type: str
    file_size_bytes: int
    checksum_sha256: str
    created_at: datetime


class ReportFileSummary(BaseModel):
    file_id: str
    format: ReportExportFormat
    filename: str
    download_url: str
    content_type: str
    file_size_bytes: int
    checksum_sha256: str
    created_at: datetime

    @classmethod
    def from_record(cls, record: ReportFileRecord) -> "ReportFileSummary":
        return cls(
            file_id=record.file_id,
            format=record.format,
            filename=record.filename,
            download_url=f"/api/v1/report-files/{record.file_id}/download",
            content_type=record.content_type,
            file_size_bytes=record.file_size_bytes,
            checksum_sha256=record.checksum_sha256,
            created_at=record.created_at,
        )


class ReportExportResponse(BaseModel):
    report_id: str
    files: list[ReportFileSummary]


class ExportResult(BaseModel):
    output_path: Path
    content_type: str
    file_size_bytes: int
    checksum_sha256: str

    @model_validator(mode="after")
    def validate_file(self) -> "ExportResult":
        if self.file_size_bytes <= 0:
            raise ValueError("Exported file is empty.")
        return self
