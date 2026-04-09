from __future__ import annotations

import csv
import io
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader
import xlrd

from app.knowledge.schemas import ParsedDocument


class KnowledgeParseError(RuntimeError):
    pass


def parse_document(*, path: Path, mime_type: str) -> ParsedDocument:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return ParsedDocument(text=_read_text_file(path), mime_type=mime_type)
    if suffix == ".csv":
        return ParsedDocument(text=_read_csv_file(path), mime_type=mime_type)
    if suffix == ".xlsx":
        return ParsedDocument(text=_read_xlsx_file(path), mime_type=mime_type)
    if suffix == ".xls":
        return ParsedDocument(text=_read_xls_file(path), mime_type=mime_type)
    if suffix == ".docx":
        return ParsedDocument(text=_read_docx_file(path), mime_type=mime_type)
    if suffix == ".pdf":
        return ParsedDocument(text=_read_pdf_file(path), mime_type=mime_type)
    if suffix == ".doc":
        raise KnowledgeParseError("当前暂不支持解析旧版 .doc 二进制文档，请改为 .docx 或可提取文本的 PDF。")
    raise KnowledgeParseError(f"当前暂不支持解析该文件格式：{suffix or 'unknown'}")


def _read_text_file(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            content = path.read_text(encoding=encoding)
            return _require_text(content)
        except UnicodeDecodeError:
            continue
    raise KnowledgeParseError("文本文件编码无法识别，当前仅支持可解码的 UTF-8/GBK 文本。")


def _read_csv_file(path: Path) -> str:
    raw_text = _read_text_file(path)
    reader = csv.reader(io.StringIO(raw_text))
    rows = list(reader)
    if not rows:
        raise KnowledgeParseError("CSV 文件内容为空。")
    headers = rows[0]
    rendered: list[str] = []
    for index, row in enumerate(rows[1:], start=1):
        cells: list[str] = []
        for column, value in zip(headers, row, strict=False):
            if value is None or str(value).strip() == "":
                continue
            cells.append(f"{column}={str(value).strip()}")
        if cells:
            rendered.append(f"第 {index} 行：{'；'.join(cells)}")
    return _require_text("\n\n".join(rendered) or raw_text)


def _read_xlsx_file(path: Path) -> str:
    workbook = load_workbook(filename=path, read_only=True, data_only=True)
    rendered: list[str] = []
    for sheet in workbook.worksheets:
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            continue
        headers = [str(cell).strip() if cell is not None else "" for cell in rows[0]]
        for row_index, row in enumerate(rows[1:], start=1):
            pairs: list[str] = []
            for column_name, value in zip(headers, row, strict=False):
                if value is None or str(value).strip() == "":
                    continue
                label = column_name or f"列{len(pairs) + 1}"
                pairs.append(f"{label}={str(value).strip()}")
            if pairs:
                rendered.append(f"工作表 {sheet.title} 第 {row_index} 行：{'；'.join(pairs)}")
    return _require_text("\n\n".join(rendered))


def _read_xls_file(path: Path) -> str:
    try:
        workbook = xlrd.open_workbook(path)
    except Exception as exc:  # noqa: BLE001
        raise KnowledgeParseError("旧版 Excel 文件无法读取。") from exc

    rendered: list[str] = []
    for sheet in workbook.sheets():
        if sheet.nrows == 0:
            continue
        headers = [str(sheet.cell_value(0, col)).strip() for col in range(sheet.ncols)]
        for row_index in range(1, sheet.nrows):
            pairs: list[str] = []
            for col_index in range(sheet.ncols):
                value = sheet.cell_value(row_index, col_index)
                if value is None or str(value).strip() == "":
                    continue
                label = headers[col_index] or f"列{col_index + 1}"
                pairs.append(f"{label}={str(value).strip()}")
            if pairs:
                rendered.append(f"工作表 {sheet.name} 第 {row_index} 行：{'；'.join(pairs)}")
    return _require_text("\n\n".join(rendered))


def _read_docx_file(path: Path) -> str:
    document = Document(path)
    parts: list[str] = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)
    for table in document.tables:
        for row_index, row in enumerate(table.rows, start=1):
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(f"表格第 {row_index} 行：{'；'.join(cells)}")
    return _require_text("\n\n".join(parts))


def _read_pdf_file(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # noqa: BLE001
        raise KnowledgeParseError("PDF 文件无法读取。") from exc

    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # noqa: BLE001
            raise KnowledgeParseError("PDF 文本提取失败。") from exc
        normalized = text.strip()
        if normalized:
            pages.append(normalized)
    return _require_text("\n\n".join(pages), empty_message="PDF 未提取到可用文本，可能是扫描件。")


def _require_text(text: str, *, empty_message: str = "文件未提取到可用文本内容。") -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        raise KnowledgeParseError(empty_message)
    return normalized
