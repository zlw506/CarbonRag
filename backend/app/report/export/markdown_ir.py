import re

from app.report.export.schemas import ReportBlock, ReportDocumentIR, ReportSectionIR, ReportTable
from app.report.schemas import ReportDetail

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$")
_NUMBERED_RE = re.compile(r"^\s*\d+[.)]\s+(.+?)\s*$")


def report_to_ir(report: ReportDetail) -> ReportDocumentIR:
    """Convert stored Markdown report content into a conservative document IR."""

    try:
        return _parse_markdown_report(report)
    except Exception:
        return ReportDocumentIR(
            title=report.title,
            metadata=_build_metadata(report),
            sections=[
                ReportSectionIR(
                    heading="正文",
                    blocks=[ReportBlock(type="paragraph", text=report.content)],
                )
            ],
            references=report.citations,
        )


def _parse_markdown_report(report: ReportDetail) -> ReportDocumentIR:
    lines = report.content.splitlines()
    title = report.title
    sections: list[ReportSectionIR] = []
    current = ReportSectionIR(heading="正文", blocks=[])
    paragraph_lines: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph_lines:
            text = " ".join(item.strip() for item in paragraph_lines if item.strip()).strip()
            if text:
                current.blocks.append(ReportBlock(type="paragraph", text=text))
            paragraph_lines.clear()

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            index += 1
            continue

        heading_match = _HEADING_RE.match(stripped)
        if heading_match:
            flush_paragraph()
            level = len(heading_match.group(1))
            heading = heading_match.group(2).strip()
            if level == 1 and title == report.title:
                title = heading
            elif level <= 2:
                if current.blocks or current.heading != "正文":
                    sections.append(current)
                current = ReportSectionIR(heading=heading, blocks=[])
            else:
                current.blocks.append(ReportBlock(type="heading", text=heading))
            index += 1
            continue

        if _is_table_start(lines, index):
            flush_paragraph()
            table, next_index = _parse_table(lines, index)
            current.blocks.append(ReportBlock(type="table", table=table))
            index = next_index
            continue

        bullet_match = _BULLET_RE.match(stripped)
        if bullet_match:
            flush_paragraph()
            items: list[str] = []
            while index < len(lines):
                match = _BULLET_RE.match(lines[index].strip())
                if match is None:
                    break
                items.append(match.group(1).strip())
                index += 1
            current.blocks.append(ReportBlock(type="bullet_list", items=items))
            continue

        numbered_match = _NUMBERED_RE.match(stripped)
        if numbered_match:
            flush_paragraph()
            items = []
            while index < len(lines):
                match = _NUMBERED_RE.match(lines[index].strip())
                if match is None:
                    break
                items.append(match.group(1).strip())
                index += 1
            current.blocks.append(ReportBlock(type="numbered_list", items=items))
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote_lines.append(lines[index].strip().lstrip(">").strip())
                index += 1
            current.blocks.append(ReportBlock(type="quote", text=" ".join(quote_lines).strip()))
            continue

        paragraph_lines.append(stripped)
        index += 1

    flush_paragraph()
    if current.blocks or not sections:
        sections.append(current)

    return ReportDocumentIR(
        title=title,
        metadata=_build_metadata(report),
        sections=sections,
        references=report.citations,
    )


def _build_metadata(report: ReportDetail) -> dict[str, str]:
    return {
        "报告 ID": report.report_id,
        "会话 ID": report.session_id,
        "报告类型": report.report_type,
        "追踪 ID": report.trace_id,
        "创建时间": report.created_at.isoformat(),
        "更新时间": report.updated_at.isoformat(),
    }


def _is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    header = lines[index].strip()
    separator = lines[index + 1].strip()
    return "|" in header and "|" in separator and bool(re.fullmatch(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?", separator))


def _parse_table(lines: list[str], index: int) -> tuple[ReportTable, int]:
    columns = _split_table_row(lines[index])
    rows: list[list[str]] = []
    index += 2
    while index < len(lines) and "|" in lines[index]:
        row = _split_table_row(lines[index])
        if len(row) < len(columns):
            row.extend([""] * (len(columns) - len(row)))
        rows.append(row[: len(columns)])
        index += 1
    return ReportTable(columns=columns, rows=rows), index


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]
