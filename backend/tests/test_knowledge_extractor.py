from pathlib import Path

import pytest
from docx import Document
from openpyxl import Workbook
from reportlab.pdfgen import canvas
import xlwt

from app.knowledge.extractor import extract_text_from_source


def _build_pdf(path: Path, text: str) -> None:
    pdf = canvas.Canvas(str(path))
    pdf.drawString(72, 720, text)
    pdf.drawString(72, 700, "carbon retrofit")
    pdf.save()


def _build_docx(path: Path, text: str) -> None:
    document = Document()
    document.add_paragraph(text)
    document.add_paragraph("节能改造建议")
    document.save(str(path))


def _build_xlsx(path: Path, text: str) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "能耗月报"
    sheet.append(["指标", "数值"])
    sheet.append([text, 1200])
    workbook.save(str(path))


def _build_xls(path: Path, text: str) -> None:
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("能耗月报")
    sheet.write(0, 0, "指标")
    sheet.write(0, 1, "数值")
    sheet.write(1, 0, text)
    sheet.write(1, 1, 880)
    workbook.save(str(path))


def test_extract_text_from_supported_knowledge_files(tmp_path) -> None:
    txt_path = tmp_path / "sample.txt"
    md_path = tmp_path / "sample.md"
    csv_path = tmp_path / "sample.csv"
    docx_path = tmp_path / "sample.docx"
    xlsx_path = tmp_path / "sample.xlsx"
    xls_path = tmp_path / "sample.xls"
    pdf_path = tmp_path / "sample.pdf"

    txt_path.write_text("双碳目标\n企业节能改造", encoding="utf-8")
    md_path.write_text("# 双碳目标\n\n企业节能改造", encoding="utf-8")
    csv_path.write_text("月份,电量\n2026-01,1200\n2026-02,980\n", encoding="utf-8")
    _build_docx(docx_path, "企业能源审计摘要")
    _build_xlsx(xlsx_path, "电量")
    _build_xls(xls_path, "天然气")
    _build_pdf(pdf_path, "dual carbon target")

    assert "双碳目标" in extract_text_from_source(txt_path)
    assert "企业节能改造" in extract_text_from_source(md_path)
    csv_text = extract_text_from_source(csv_path)
    assert "第 1 行" in csv_text
    assert "电量=1200" in csv_text
    assert "企业能源审计摘要" in extract_text_from_source(docx_path)
    xlsx_text = extract_text_from_source(xlsx_path)
    assert "工作表" in xlsx_text
    assert "数值=1200" in xlsx_text
    xls_text = extract_text_from_source(xls_path)
    assert "天然气" in xls_text
    assert "880" in xls_text
    assert "dual carbon target" in extract_text_from_source(pdf_path)


def test_extract_text_from_old_doc_raises_clear_error(tmp_path) -> None:
    doc_path = tmp_path / "legacy.doc"
    doc_path.write_text("旧版 DOC 文件", encoding="utf-8")

    with pytest.raises(ValueError, match="DOC 旧版二进制文档暂不支持"):
        extract_text_from_source(doc_path)
