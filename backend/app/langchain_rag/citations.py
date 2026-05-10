from __future__ import annotations

from app.langchain_rag.schemas import LangChainRagHit


def citations_from_hits(hits: list[LangChainRagHit]) -> list[dict]:
    return [
        {
            "doc_id": hit.doc_id,
            "knowledge_item_id": hit.knowledge_item_id,
            "title": hit.title,
            "source_type": hit.source_type,
            "source": hit.source,
            "source_url": hit.source_url,
            "snippet": hit.snippet,
            "chunk_id": hit.chunk_id,
            "library_scope": hit.library_scope,
            "file_id": hit.file_id,
            "page_number": hit.page_number,
            "sheet_name": hit.sheet_name,
            "slide_number": hit.slide_number,
            "section_title": hit.section_title,
        }
        for hit in hits
    ]
