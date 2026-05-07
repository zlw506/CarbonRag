from app.core.config import Settings
from app.rag.parser import DefaultParserProvider, DoclingParserProvider, ParserRegistry, get_default_parser_provider


def test_default_parser_provider_supports_current_file_types() -> None:
    provider = DefaultParserProvider()

    assert provider.supports("sample.md", "text/markdown")
    assert provider.supports("sample.txt", "text/plain")
    assert provider.supports("sample.csv", "text/csv")
    assert provider.supports("sample.xlsx")
    assert provider.supports("sample.xls")
    assert provider.supports("sample.docx")
    assert provider.supports("sample.pdf", "application/pdf")
    assert provider.supports(content_type="text/plain")
    assert not provider.supports("legacy.doc", "application/msword")


def test_default_parser_provider_parse_returns_parsed_document_with_blocks(tmp_path) -> None:
    source = tmp_path / "sample.md"
    source.write_text("# 企业节能方案\n\n照明优化和空调优化。", encoding="utf-8")
    provider = get_default_parser_provider()

    parsed = provider.parse(source, content_type="text/markdown")

    assert parsed.document_id.startswith("parsed-")
    assert parsed.source_uri == str(source)
    assert parsed.source_type == "local_file"
    assert parsed.title == "sample.md"
    assert parsed.text
    assert parsed.blocks
    assert {block.block_type for block in parsed.blocks} >= {"title", "paragraph"}
    assert parsed.metadata["parser_name"] == "carbonrag-default"
    assert parsed.metadata["parser_version"] == "1.0"
    assert parsed.metadata["source_file"] == str(source)
    assert parsed.metadata["parse_success"] is True
    assert parsed.metadata["parse_error"] is None


def test_default_parser_provider_score_stays_between_zero_and_one(tmp_path) -> None:
    source = tmp_path / "sample.txt"
    source.write_text("企业节能改造\n照明优化\n空调优化", encoding="utf-8")
    provider = DefaultParserProvider()

    parsed = provider.parse(file_path=source, content_type="text/plain")
    score = provider.score(parsed)

    assert 0.0 <= score <= 1.0
    assert parsed.quality_score == score


def test_default_parser_provider_records_parse_error(tmp_path) -> None:
    source = tmp_path / "empty.txt"
    source.write_text("", encoding="utf-8")
    provider = DefaultParserProvider()

    parsed = provider.parse(file_path=source, content_type="text/plain")

    assert parsed.text == ""
    assert parsed.blocks == []
    assert parsed.quality_score == 0.0
    assert parsed.metadata["parse_success"] is False
    assert parsed.metadata["parse_error"]
    assert provider.score(parsed) == 0.0


def test_docling_provider_is_safe_when_docling_is_missing(monkeypatch, tmp_path) -> None:
    source = tmp_path / "sample.pdf"
    source.write_text("not a real pdf", encoding="utf-8")
    monkeypatch.setattr("app.rag.parser.importlib.util.find_spec", lambda name: None)
    provider = DoclingParserProvider()

    assert provider.parser_available is False
    assert provider.supports(source, "application/pdf") is False
    parsed = provider.parse(source, content_type="application/pdf")
    assert parsed.metadata["parser_name"] == "docling"
    assert parsed.metadata["parser_available"] is False
    assert parsed.metadata["parse_success"] is False
    assert parsed.metadata["parse_error"]


def test_parser_registry_uses_default_when_configured(tmp_path) -> None:
    source = tmp_path / "sample.md"
    source.write_text("# 默认解析\n\n当前默认解析行为不变。", encoding="utf-8")
    registry = ParserRegistry(preferred_provider=Settings(rag_parser_provider="default").rag_parser_provider)

    parsed = registry.parse(source, content_type="text/markdown")

    assert parsed.metadata["parser_name"] == "carbonrag-default"
    assert parsed.metadata["parse_success"] is True


def test_parser_registry_falls_back_when_docling_unavailable(monkeypatch, tmp_path) -> None:
    source = tmp_path / "sample.md"
    source.write_text("# Fallback\n\nDocling 不可用时回退默认解析。", encoding="utf-8")
    monkeypatch.setattr("app.rag.parser.importlib.util.find_spec", lambda name: None)
    registry = ParserRegistry(preferred_provider="docling")

    parsed = registry.parse(source, content_type="text/markdown")

    assert parsed.metadata["parser_name"] == "carbonrag-default"
    assert parsed.metadata["parse_success"] is True
    assert parsed.metadata["fallback_from"] == "docling"
    assert parsed.metadata["fallback_reason"] == "docling_unavailable_or_unsupported"


class _FakeDoclingDocument:
    def export_to_markdown(self) -> str:
        return "# Docling 标题\n\nDocling 解析内容。"


class _FakeDoclingResult:
    document = _FakeDoclingDocument()


class _FakeDoclingConverter:
    def convert(self, file_path: str) -> _FakeDoclingResult:
        assert file_path
        return _FakeDoclingResult()


def test_docling_provider_parse_metadata_with_mock_converter(tmp_path) -> None:
    source = tmp_path / "sample.pdf"
    source.write_text("mock pdf", encoding="utf-8")
    provider = DoclingParserProvider(converter=_FakeDoclingConverter())

    parsed = provider.parse(source, content_type="application/pdf")

    assert parsed.metadata["parser_name"] == "docling"
    assert parsed.metadata["parser_available"] is True
    assert "parser_version" in parsed.metadata
    assert parsed.metadata["parse_success"] is True
    assert parsed.metadata["parse_error"] is None
    assert parsed.blocks
    assert parsed.quality_score > 0
