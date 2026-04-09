import json

from app.report.schemas import ReportGenerationPayload, ReportSection
from app.report.templates import ReportTemplate


class ReportRenderError(ValueError):
    pass


def parse_report_generation_payload(raw_content: str, template: ReportTemplate) -> ReportGenerationPayload:
    try:
        payload = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ReportRenderError("Report provider returned non-JSON content.") from exc

    if not isinstance(payload, dict):
        raise ReportRenderError("Report provider returned an invalid payload shape.")

    title = payload.get("title")
    sections = payload.get("sections")
    if not isinstance(title, str) or not title.strip():
        raise ReportRenderError("Report provider did not return a valid title.")
    if not isinstance(sections, list) or not sections:
        raise ReportRenderError("Report provider did not return valid sections.")

    parsed_sections: list[ReportSection] = []
    for item in sections:
        if not isinstance(item, dict):
            raise ReportRenderError("Report provider returned malformed section items.")
        heading = item.get("heading")
        body = item.get("body")
        if not isinstance(heading, str) or not heading.strip() or not isinstance(body, str) or not body.strip():
            raise ReportRenderError("Report provider returned empty section fields.")
        parsed_sections.append(ReportSection(heading=heading.strip(), body=body.strip()))

    returned_headings = [item.heading for item in parsed_sections]
    if returned_headings != list(template.sections):
        raise ReportRenderError("Report provider returned unexpected section headings.")

    return ReportGenerationPayload(title=title.strip(), sections=parsed_sections)


def render_markdown_report(
    *,
    title: str,
    sections: list[ReportSection],
    references_markdown: str,
) -> str:
    lines = [f"# {title}", ""]

    for section in sections:
        lines.append(f"## {section.heading}")
        lines.append("")
        lines.append(section.body.strip())
        lines.append("")

    lines.append("## 依据列表")
    lines.append("")
    lines.append(references_markdown.strip() or "暂无依据。")
    lines.append("")

    return "\n".join(lines).strip() + "\n"
