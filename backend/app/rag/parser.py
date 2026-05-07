from __future__ import annotations

import importlib
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.knowledge.parsers import KnowledgeParseError, parse_document
from app.rag.contracts import DocumentBlock, ParsedDocument, hash_content


class ParserProviderDescriptor(BaseModel):
    name: str
    mode: str = "lightweight"
    supported_suffixes: list[str] = Field(default_factory=list)


class ParserProvider(Protocol):
    def describe(self) -> ParserProviderDescriptor:
        ...

    def supports(
        self,
        file_path: str | Path | None = None,
        content_type: str | None = None,
        *,
        mime_type: str | None = None,
        name: str | None = None,
    ) -> bool:
        ...

    def parse(
        self,
        file_path: str | Path | None = None,
        *,
        path: Path | str | None = None,
        mime_type: str | None = None,
        content_type: str | None = None,
    ) -> ParsedDocument:
        ...

    def score(self, document: ParsedDocument) -> float:
        ...


class DefaultParserProvider:
    parser_name = "carbonrag-default"
    parser_version = "1.0"
    supported_suffixes = {".txt", ".md", ".csv", ".xlsx", ".xls", ".docx", ".pdf"}
    supported_content_types = {
        "application/pdf",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/csv",
        "text/markdown",
        "text/plain",
    }

    def describe(self) -> ParserProviderDescriptor:
        return ParserProviderDescriptor(
            name=self.parser_name,
            mode="local",
            supported_suffixes=sorted(self.supported_suffixes),
        )

    def supports(
        self,
        file_path: str | Path | None = None,
        content_type: str | None = None,
        *,
        mime_type: str | None = None,
        name: str | None = None,
    ) -> bool:
        candidate_name = name or str(file_path or "")
        suffix = Path(candidate_name).suffix.lower()
        if suffix:
            return suffix in self.supported_suffixes
        resolved_content_type = content_type or mime_type
        return bool(resolved_content_type and resolved_content_type in self.supported_content_types)

    def parse(
        self,
        file_path: str | Path | None = None,
        *,
        path: Path | str | None = None,
        mime_type: str | None = None,
        content_type: str | None = None,
    ) -> ParsedDocument:
        resolved_path = Path(path or file_path or "")
        resolved_mime_type = content_type or mime_type or _guess_mime_type(resolved_path)
        if not self.supports(resolved_path, resolved_mime_type):
            return self._failed_document(
                path=resolved_path,
                mime_type=resolved_mime_type,
                error=f"Default parser does not support {resolved_path.suffix or resolved_path.name or 'unknown'}.",
            )
        try:
            parsed = parse_document(path=resolved_path, mime_type=resolved_mime_type)
        except KnowledgeParseError as exc:
            return self._failed_document(path=resolved_path, mime_type=resolved_mime_type, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            return self._failed_document(path=resolved_path, mime_type=resolved_mime_type, error=str(exc))

        document_id = f"parsed-{hash_content(str(resolved_path))[:12]}"
        document = ParsedDocument(
            document_id=document_id,
            source_uri=str(resolved_path),
            source_type="local_file",
            title=resolved_path.name,
            text=parsed.text,
            mime_type=parsed.mime_type,
            source_path=str(resolved_path),
            parser_name=self.parser_name,
            blocks=_blocks_from_text(parsed.text, document_id=document_id),
            metadata=self._metadata(
                source_file=str(resolved_path),
                parse_success=True,
                parse_error=None,
            ),
        )
        return document.model_copy(update={"quality_score": self.score(document)})

    def score(self, document: ParsedDocument) -> float:
        if not document.text.strip() or document.metadata.get("parse_success") is False:
            return 0.0
        score = 0.55
        if any(block.block_type == "title" for block in document.blocks) or document.title:
            score += 0.2
        if document.blocks:
            score += 0.15
        if any(block.page is not None for block in document.blocks):
            score += 0.1
        return min(score, 1.0)

    def _failed_document(self, *, path: Path, mime_type: str, error: str) -> ParsedDocument:
        document_id = f"parsed-{hash_content(str(path))[:12]}" if str(path) else "parsed-error"
        document = ParsedDocument(
            document_id=document_id,
            source_uri=str(path) if str(path) else None,
            source_type="local_file",
            title=path.name if str(path) else None,
            text="",
            mime_type=mime_type,
            source_path=str(path) if str(path) else None,
            parser_name=self.parser_name,
            quality_score=0.0,
            blocks=[],
            metadata=self._metadata(source_file=str(path), parse_success=False, parse_error=error),
        )
        return document

    def _metadata(self, *, source_file: str, parse_success: bool, parse_error: str | None) -> dict:
        return {
            "parser_name": self.parser_name,
            "parser_version": self.parser_version,
            "source": "app.knowledge.parsers",
            "source_file": source_file,
            "parse_success": parse_success,
            "parse_error": parse_error,
        }


class LightweightParserProvider(DefaultParserProvider):
    parser_name = "carbonrag-lightweight"


class DoclingParserProvider:
    parser_name = "docling"
    supported_suffixes = {".pdf", ".docx", ".pptx", ".html", ".md", ".txt"}
    supported_content_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/html",
        "text/markdown",
        "text/plain",
    }

    def __init__(self, *, converter: Any | None = None) -> None:
        self._converter = converter
        self.parser_version = _optional_package_version("docling")

    def describe(self) -> ParserProviderDescriptor:
        return ParserProviderDescriptor(
            name=self.parser_name,
            mode="optional",
            supported_suffixes=sorted(self.supported_suffixes),
        )

    @property
    def parser_available(self) -> bool:
        return self._converter is not None or importlib.util.find_spec("docling") is not None

    def supports(
        self,
        file_path: str | Path | None = None,
        content_type: str | None = None,
        *,
        mime_type: str | None = None,
        name: str | None = None,
    ) -> bool:
        if not self.parser_available:
            return False
        candidate_name = name or str(file_path or "")
        suffix = Path(candidate_name).suffix.lower()
        if suffix:
            return suffix in self.supported_suffixes
        resolved_content_type = content_type or mime_type
        return bool(resolved_content_type and resolved_content_type in self.supported_content_types)

    def parse(
        self,
        file_path: str | Path | None = None,
        *,
        path: Path | str | None = None,
        mime_type: str | None = None,
        content_type: str | None = None,
    ) -> ParsedDocument:
        resolved_path = Path(path or file_path or "")
        resolved_mime_type = content_type or mime_type or _guess_mime_type(resolved_path)
        if not self.supports(resolved_path, resolved_mime_type):
            return self._failed_document(
                path=resolved_path,
                mime_type=resolved_mime_type,
                error="Docling parser is unavailable or does not support this file.",
            )
        try:
            converter = self._converter or _build_docling_converter()
            converted = converter.convert(str(resolved_path))
            text = _extract_docling_text(converted)
            if not text.strip():
                return self._failed_document(
                    path=resolved_path,
                    mime_type=resolved_mime_type,
                    error="Docling parser returned empty text.",
                )
        except Exception as exc:  # noqa: BLE001
            return self._failed_document(path=resolved_path, mime_type=resolved_mime_type, error=str(exc))

        document_id = f"docling-{hash_content(str(resolved_path))[:12]}"
        document = ParsedDocument(
            document_id=document_id,
            source_uri=str(resolved_path),
            source_type="local_file",
            title=resolved_path.name,
            text=text,
            mime_type=resolved_mime_type,
            source_path=str(resolved_path),
            parser_name=self.parser_name,
            blocks=_blocks_from_text(text, document_id=document_id),
            metadata=self._metadata(
                source_file=str(resolved_path),
                parse_success=True,
                parse_error=None,
            ),
        )
        return document.model_copy(update={"quality_score": self.score(document)})

    def score(self, document: ParsedDocument) -> float:
        if not document.text.strip() or document.metadata.get("parse_success") is False:
            return 0.0
        score = 0.6
        if any(block.block_type == "title" for block in document.blocks) or document.title:
            score += 0.15
        if document.blocks:
            score += 0.15
        if any(block.page is not None for block in document.blocks):
            score += 0.1
        return min(score, 1.0)

    def _failed_document(self, *, path: Path, mime_type: str, error: str) -> ParsedDocument:
        document_id = f"docling-{hash_content(str(path))[:12]}" if str(path) else "docling-error"
        return ParsedDocument(
            document_id=document_id,
            source_uri=str(path) if str(path) else None,
            source_type="local_file",
            title=path.name if str(path) else None,
            text="",
            mime_type=mime_type,
            source_path=str(path) if str(path) else None,
            parser_name=self.parser_name,
            quality_score=0.0,
            blocks=[],
            metadata=self._metadata(source_file=str(path), parse_success=False, parse_error=error),
        )

    def _metadata(self, *, source_file: str, parse_success: bool, parse_error: str | None) -> dict:
        return {
            "parser_name": self.parser_name,
            "parser_available": self.parser_available,
            "parser_version": self.parser_version,
            "source_file": source_file,
            "parse_success": parse_success,
            "parse_error": parse_error,
        }


class ParserRegistry:
    def __init__(
        self,
        *,
        preferred_provider: str = "default",
        default_provider: DefaultParserProvider | None = None,
        docling_provider: DoclingParserProvider | None = None,
    ) -> None:
        self.preferred_provider = preferred_provider
        self.default_provider = default_provider or DefaultParserProvider()
        self.docling_provider = docling_provider or DoclingParserProvider()

    def select_provider(
        self,
        file_path: str | Path | None = None,
        content_type: str | None = None,
        *,
        mime_type: str | None = None,
        name: str | None = None,
    ) -> ParserProvider:
        if self.preferred_provider == "docling" and self.docling_provider.supports(
            file_path,
            content_type,
            mime_type=mime_type,
            name=name,
        ):
            return self.docling_provider
        return self.default_provider

    def parse(
        self,
        file_path: str | Path | None = None,
        *,
        path: Path | str | None = None,
        mime_type: str | None = None,
        content_type: str | None = None,
    ) -> ParsedDocument:
        resolved_path = path or file_path
        resolved_content_type = content_type or mime_type
        if self.preferred_provider != "docling":
            return self.default_provider.parse(resolved_path, content_type=resolved_content_type)

        fallback_reason: str | None = None
        if not self.docling_provider.supports(resolved_path, resolved_content_type):
            fallback_reason = "docling_unavailable_or_unsupported"
        else:
            docling_result = self.docling_provider.parse(resolved_path, content_type=resolved_content_type)
            if docling_result.metadata.get("parse_success") is True:
                return docling_result
            fallback_reason = str(docling_result.metadata.get("parse_error") or "docling_parse_failed")

        fallback = self.default_provider.parse(resolved_path, content_type=resolved_content_type)
        return fallback.model_copy(
            update={
                "metadata": {
                    **fallback.metadata,
                    "fallback_from": "docling",
                    "fallback_reason": fallback_reason,
                }
            }
        )


def _blocks_from_text(text: str, *, document_id: str) -> list[DocumentBlock]:
    blocks: list[DocumentBlock] = []
    for index, segment in enumerate((part.strip() for part in text.split("\n\n")), start=1):
        if not segment:
            continue
        first_line = segment.splitlines()[0].strip()
        if first_line.startswith("#"):
            block_type = "title"
        elif "；" in segment and ("=" in segment or segment.startswith("表格")):
            block_type = "table"
        elif first_line.startswith(("-", "*", "1.")):
            block_type = "list"
        else:
            block_type = "paragraph"
        blocks.append(
            DocumentBlock(
                block_id=f"block-{index:04d}",
                document_id=document_id,
                block_type=block_type,  # type: ignore[arg-type]
                text=segment,
                order_index=index,
            )
        )
    return blocks


def _guess_mime_type(path: Path) -> str:
    mapping = {
        ".csv": "text/csv",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".md": "text/markdown",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
    return mapping.get(path.suffix.lower(), "application/octet-stream")


def _optional_package_version(package_name: str) -> str | None:
    try:
        return importlib_metadata.version(package_name)
    except importlib_metadata.PackageNotFoundError:
        return None


def _build_docling_converter() -> Any:
    try:
        module = importlib.import_module("docling.document_converter")
        converter_cls = getattr(module, "DocumentConverter")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Docling is not installed. Install optional dependency `docling` first.") from exc
    return converter_cls()


def _extract_docling_text(converted: Any) -> str:
    document = getattr(converted, "document", converted)
    for method_name in ("export_to_markdown", "export_to_text"):
        method = getattr(document, method_name, None)
        if callable(method):
            text = method()
            if text:
                return str(text).strip()
    text = getattr(document, "text", None)
    if text:
        return str(text).strip()
    return str(document).strip()


def get_default_parser_provider() -> DefaultParserProvider:
    return DefaultParserProvider()


def get_lightweight_parser_provider() -> LightweightParserProvider:
    return LightweightParserProvider()


def get_parser_registry(settings: Settings | None = None) -> ParserRegistry:
    resolved_settings = settings or get_settings()
    return ParserRegistry(preferred_provider=resolved_settings.rag_parser_provider)
