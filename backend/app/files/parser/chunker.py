from app.files.parser.models import ParsedFileResult
from app.knowledge.chunker import chunk_knowledge_text
from app.knowledge.schemas import KnowledgeChunk, KnowledgeItem


def build_file_chunks(*, item: KnowledgeItem, parsed: ParsedFileResult, created_at) -> list[KnowledgeChunk]:
    chunks = chunk_knowledge_text(item=item, text=parsed.text, created_at=created_at)
    for index, chunk in enumerate(chunks):
        block_meta = parsed.chunk_metadata[min(index, len(parsed.chunk_metadata) - 1)] if parsed.chunk_metadata else None
        chunk.metadata = {
            **chunk.metadata,
            "file_id": item.file_id or item.source_ref,
            "parser_name": parsed.parser_name,
            "parser_version": parsed.parser_version,
            "ocr_used": parsed.ocr_used,
            "page_number": block_meta.page_number if block_meta else None,
            "sheet_name": block_meta.sheet_name if block_meta else None,
            "slide_number": block_meta.slide_number if block_meta else None,
            "section_title": block_meta.section_title if block_meta else None,
        }
    return chunks
