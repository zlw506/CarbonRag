import re

from app.report.export.schemas import ReportExportFormat

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')
_WHITESPACE = re.compile(r"\s+")


def sanitize_filename_part(value: str, *, fallback: str = "report") -> str:
    cleaned = _INVALID_FILENAME_CHARS.sub("_", value)
    cleaned = _WHITESPACE.sub(" ", cleaned).strip(" ._")
    if not cleaned:
        return fallback
    return cleaned[:80]


def build_report_filename(*, title: str, report_id: str, fmt: ReportExportFormat) -> str:
    safe_title = sanitize_filename_part(title, fallback="CarbonRag 报告")
    safe_report_id = sanitize_filename_part(report_id, fallback="report")
    return f"{safe_title}-{safe_report_id}.{fmt}"
