import html
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.report.export.schemas import ExportResult, ReportBlock, ReportDocumentIR, ReportTable
from app.report.export.security import sha256_file

_FONT_NAME = "CarbonRagCJK"


class PdfReportExporter:
    content_type = "application/pdf"

    def export(self, ir: ReportDocumentIR, output_path: Path, template_id: str | None = None) -> ExportResult:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        font_name = _register_cjk_font()
        styles = _build_styles(font_name)
        document = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title=ir.title,
        )
        story = [Paragraph(_escape(ir.title), styles["Title"]), Spacer(1, 8)]

        if ir.subtitle:
            story.extend([Paragraph(_escape(ir.subtitle), styles["Subtitle"]), Spacer(1, 8)])
        if ir.metadata:
            story.extend(_metadata_flowables(ir.metadata, styles))

        for section in ir.sections:
            story.extend([Paragraph(_escape(section.heading), styles["Heading1"]), Spacer(1, 4)])
            for block in section.blocks:
                story.extend(_block_flowables(block, styles))

        if ir.references:
            story.extend([Spacer(1, 8), Paragraph("引用依据", styles["Heading1"])])
            for index, citation in enumerate(ir.references, start=1):
                text = f"{index}. <b>{_escape(citation.title)}</b>｜{_escape(citation.source)}"
                if citation.source_url:
                    text += f"｜{_escape(citation.source_url)}"
                story.append(Paragraph(text, styles["Body"]))
                if citation.snippet:
                    story.append(Paragraph(_escape(citation.snippet), styles["Quote"]))
                story.append(Spacer(1, 4))

        for appendix in ir.appendices:
            story.append(PageBreak())
            story.append(Paragraph(_escape(appendix.heading), styles["Heading1"]))
            for block in appendix.blocks:
                story.extend(_block_flowables(block, styles))

        document.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
        return ExportResult(
            output_path=output_path,
            content_type=self.content_type,
            file_size_bytes=output_path.stat().st_size,
            checksum_sha256=sha256_file(output_path),
        )


def _register_cjk_font() -> str:
    if _FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return _FONT_NAME

    candidates = [
        os.environ.get("CARBONRAG_PDF_FONT_PATH"),
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simsun.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if not path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(_FONT_NAME, str(path)))
            return _FONT_NAME
        except Exception:
            continue
    return "Helvetica"


def _build_styles(font_name: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "CarbonRagTitle",
            parent=base["Title"],
            fontName=font_name,
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "Subtitle": ParagraphStyle(
            "CarbonRagSubtitle",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#666666"),
            alignment=TA_CENTER,
        ),
        "Heading1": ParagraphStyle(
            "CarbonRagHeading1",
            parent=base["Heading1"],
            fontName=font_name,
            fontSize=15,
            leading=22,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "Heading2": ParagraphStyle(
            "CarbonRagHeading2",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=12,
            leading=18,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "CarbonRagBody",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=10,
            leading=16,
            spaceAfter=6,
        ),
        "Quote": ParagraphStyle(
            "CarbonRagQuote",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=9,
            leading=14,
            leftIndent=10,
            textColor=colors.HexColor("#555555"),
            borderColor=colors.HexColor("#DDDDDD"),
            borderWidth=0.5,
            borderPadding=6,
            spaceAfter=6,
        ),
    }


def _metadata_flowables(metadata: dict[str, str], styles: dict[str, ParagraphStyle]) -> list:
    rows = [["字段", "内容"], *[[key, value] for key, value in metadata.items()]]
    return [_table_flowable(ReportTable(columns=rows[0], rows=rows[1:]), styles), Spacer(1, 8)]


def _block_flowables(block: ReportBlock, styles: dict[str, ParagraphStyle]) -> list:
    if block.type == "paragraph":
        return [Paragraph(_escape(block.text or ""), styles["Body"])]
    if block.type == "heading":
        return [Paragraph(_escape(block.text or ""), styles["Heading2"])]
    if block.type == "quote":
        return [Paragraph(_escape(block.text or ""), styles["Quote"])]
    if block.type == "bullet_list":
        return [_list_flowable(block.items or [], styles, "bullet")]
    if block.type == "numbered_list":
        return [_list_flowable(block.items or [], styles, "1")]
    if block.type == "table" and block.table is not None:
        return [_table_flowable(block.table, styles), Spacer(1, 8)]
    if block.type == "page_break":
        return [PageBreak()]
    return []


def _list_flowable(items: list[str], styles: dict[str, ParagraphStyle], bullet_type: str) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(_escape(item), styles["Body"])) for item in items],
        bulletType=bullet_type,
        start="1",
        leftIndent=14,
    )


def _table_flowable(table_ir: ReportTable, styles: dict[str, ParagraphStyle]) -> Table:
    rows = [
        [Paragraph(f"<b>{_escape(column)}</b>", styles["Body"]) for column in table_ir.columns],
        *[[Paragraph(_escape(cell), styles["Body"]) for cell in row] for row in table_ir.rows],
    ]
    table = Table(rows, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0F4F8")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D7DE")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _draw_footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"第 {document.page} 页")
    canvas.restoreState()


def _escape(value: str) -> str:
    return html.escape(value or "").replace("\n", "<br/>")
