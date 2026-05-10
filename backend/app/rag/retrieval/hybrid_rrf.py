from __future__ import annotations

from app.rag.kb.models import RagChunk, RagHit
from app.rag.vector_backend.base import VectorSearchHit


def merge_with_rrf(
    *,
    sparse_hits: list[tuple[RagChunk, float]],
    dense_hits: list[VectorSearchHit],
    k: int = 60,
) -> list[RagHit]:
    records: dict[str, dict] = {}
    for rank, (chunk, score) in enumerate(sparse_hits, start=1):
        record = records.setdefault(chunk.rag_chunk_id, {"chunk": chunk, "sparse_score": score, "dense_score": None, "rrf": 0.0})
        record["sparse_score"] = score
        record["rrf"] += 1.0 / (k + rank)
    for rank, hit in enumerate(dense_hits, start=1):
        record = records.setdefault(hit.chunk.rag_chunk_id, {"chunk": hit.chunk, "sparse_score": None, "dense_score": hit.score, "rrf": 0.0})
        record["dense_score"] = hit.score
        record["rrf"] += 1.0 / (k + rank)

    merged = [_record_to_hit(record) for record in records.values()]
    merged.sort(key=lambda item: item.rrf_score or 0.0, reverse=True)
    return merged


def _record_to_hit(record: dict) -> RagHit:
    chunk: RagChunk = record["chunk"]
    metadata = chunk.metadata
    source_type = _normalize_source_type(metadata.get("source_type"))
    return RagHit(
        chunk_id=chunk.knowledge_chunk_id or chunk.rag_chunk_id,
        rag_chunk_id=chunk.rag_chunk_id,
        kb_id=chunk.kb_id,
        doc_id=chunk.doc_id,
        title=str(metadata.get("title") or metadata.get("source") or "RAG 文档"),
        snippet=chunk.text,
        source_type=source_type,
        source=_optional_str(metadata.get("source") or metadata.get("title") or "RAG 文档"),
        source_url=_optional_str(metadata.get("source_url")),
        library_scope=_normalize_library_scope(metadata.get("library_scope")),
        file_id=_optional_str(metadata.get("file_id")),
        knowledge_item_id=_optional_str(metadata.get("knowledge_item_id")),
        page_number=chunk.page_number,
        sheet_name=chunk.sheet_name,
        slide_number=chunk.slide_number,
        section_title=chunk.section_title,
        dense_score=record.get("dense_score"),
        sparse_score=record.get("sparse_score"),
        rrf_score=float(record.get("rrf") or 0.0),
    )


def _optional_str(value) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _normalize_source_type(value) -> str:
    normalized = str(value or "").strip()
    if normalized == "public_policy_web":
        return "public_policy"
    if normalized in {"uploaded_file", "personal_upload", "file_upload"}:
        return "private_upload"
    if normalized in {"public_policy", "public_policy_demo", "private_sample", "private_upload"}:
        return normalized
    return "private_upload"


def _normalize_library_scope(value) -> str | None:
    normalized = str(value or "").strip()
    if normalized in {"personal", "shared"}:
        return normalized
    return None
