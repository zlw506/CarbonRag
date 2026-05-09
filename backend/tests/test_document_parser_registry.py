from pathlib import Path

import pytest

from app.files.parser.registry import FileParserRegistry
from app.knowledge.parsers import KnowledgeParseError


class _UnavailableDocling:
    def supports(self, *args, **kwargs) -> bool:  # noqa: ANN002, ANN003
        return False

    def parse(self, *args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("fallback parser should be used")


def test_parser_registry_uses_lightweight_fallback_for_text(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.txt"
    file_path.write_text("企业电费账单显示 2026 年 1 月用电 1200 kWh。", encoding="utf-8")

    parsed = FileParserRegistry(docling_provider=_UnavailableDocling()).parse(
        path=file_path,
        mime_type="text/plain",
    )

    assert parsed.parser_name == "carbonrag-fallback"
    assert "1200 kWh" in parsed.text
    assert parsed.summary


def test_parser_registry_strips_html_with_fallback(tmp_path: Path) -> None:
    file_path = tmp_path / "sample.html"
    file_path.write_text("<html><body><h1>排放报告</h1><p>用电量 800 kWh</p></body></html>", encoding="utf-8")

    parsed = FileParserRegistry(docling_provider=_UnavailableDocling()).parse(
        path=file_path,
        mime_type="text/html",
    )

    assert parsed.parser_name == "carbonrag-html-fallback"
    assert "排放报告" in parsed.text
    assert "<h1>" not in parsed.text


def test_parser_registry_marks_image_as_ocr_unavailable_without_docling(tmp_path: Path) -> None:
    file_path = tmp_path / "scan.png"
    file_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    with pytest.raises(KnowledgeParseError, match="Docling OCR"):
        FileParserRegistry(docling_provider=_UnavailableDocling()).parse(
            path=file_path,
            mime_type="image/png",
        )
