from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.carbon.report_extraction import ReportCarbonActivityExtractor
from app.knowledge import get_knowledge_service
from app.knowledge.schemas import KnowledgeChunk
from app.rag import RagEngineService, build_rag_query_params, get_rag_engine_service

UPLOAD_RETRIEVAL_MIN_TOP_K = 12
UPLOAD_OVERVIEW_MAX_FILES = 4
UPLOAD_OVERVIEW_MAX_CHUNKS_PER_FILE = 12
UPLOAD_OVERVIEW_SNIPPET_MAX_CHARS = 700
UPLOAD_CARBON_ACTIVITY_MEMORY_MAX_ITEMS = 24


class SessionFileSearchTool(BaseTool):
    def __init__(
        self,
        rag_engine: RagEngineService | None = None,
        carbon_extractor: ReportCarbonActivityExtractor | None = None,
    ) -> None:
        self.rag_engine = rag_engine or get_rag_engine_service()
        self.carbon_extractor = carbon_extractor or ReportCarbonActivityExtractor()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="session_file_search",
            description="Retrieve parsed private upload chunks selected for the current session turn.",
            category="session_file_retrieval",
        )

    def invoke(
        self,
        *,
        arguments: Mapping[str, Any],
        context: Mapping[str, Any],
        trace_id: str,
    ) -> ToolResult:
        payload = arguments.get("payload", {})
        question = str(arguments.get("question") or arguments.get("user_input") or "").strip()
        top_k = int(arguments.get("top_k") or payload.get("top_k", 5))
        effective_top_k = max(top_k, UPLOAD_RETRIEVAL_MIN_TOP_K)
        allowed_ids = {
            str(item)
            for item in payload.get("attached_file_knowledge_item_ids", [])
            if str(item).strip()
        }
        if not allowed_ids:
            return ToolResult(
                name=self.definition.name,
                status="success",
                output={
                    "query": question,
                    "knowledge_scope": "private_upload",
                    "top_k": top_k,
                    "effective_top_k": effective_top_k,
                    "hits": [],
                    "file_overviews": [],
                },
                metadata={"trace_id": trace_id, "hit_count": 0, "context_keys": sorted(context)},
            )

        rag_result = self.rag_engine.retrieve(build_rag_query_params(
            question=question,
            knowledge_scope="private_sample",
            top_k=effective_top_k,
            mode=payload.get("rag_mode") or arguments.get("rag_mode"),
            allowed_knowledge_item_ids=allowed_ids,
        ))
        hits = [
            chunk.to_retrieved_hit()
            for chunk in rag_result.chunks
            if chunk.source_type == "private_upload"
        ]
        fallback_used = False
        if not hits:
            hits = _fallback_selected_upload_chunks(
                allowed_knowledge_item_ids=allowed_ids,
                top_k=effective_top_k,
            )
            fallback_used = bool(hits)
        file_overviews = _build_selected_upload_file_overviews(
            allowed_knowledge_item_ids=allowed_ids,
            carbon_extractor=self.carbon_extractor,
        )
        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "query": question,
                "knowledge_scope": "private_upload",
                "top_k": top_k,
                "effective_top_k": effective_top_k,
                "allowed_knowledge_item_ids": sorted(allowed_ids),
                "hits": hits,
                "file_overviews": file_overviews,
                "fallback_used": fallback_used,
                "retrieval_data": rag_result.model_dump(),
            },
            metadata={
                "trace_id": trace_id,
                "hit_count": len(hits),
                "context_keys": sorted(context),
                "rag_metadata": rag_result.metadata.model_dump(),
                "fallback_used": fallback_used,
            },
        )


def _build_selected_upload_file_overviews(
    *,
    allowed_knowledge_item_ids: set[str],
    carbon_extractor: ReportCarbonActivityExtractor,
) -> list[dict]:
    """Add table-aware coverage for explicitly selected upload files.

    Retrieval alone can miss tables or early report sections when the question is
    broad. This overview gives the prompt a bounded, structured sample of each
    selected file: front-matter chunks plus numeric/table-like chunks.
    """
    if not allowed_knowledge_item_ids:
        return []

    knowledge_service = get_knowledge_service()
    chunks = knowledge_service.list_chunks(knowledge_item_ids=sorted(allowed_knowledge_item_ids))
    grouped: dict[str, list[KnowledgeChunk]] = {}
    for chunk in chunks:
        if chunk.source_type != "private_upload" or chunk.knowledge_item_id not in allowed_knowledge_item_ids:
            continue
        grouped.setdefault(chunk.knowledge_item_id, []).append(chunk)

    overviews: list[dict] = []
    for knowledge_item_id in sorted(grouped)[:UPLOAD_OVERVIEW_MAX_FILES]:
        item_chunks = sorted(grouped[knowledge_item_id], key=lambda chunk: chunk.order_index)
        selected_chunks = _select_overview_chunks(item_chunks)
        first_chunk = item_chunks[0]
        carbon_activity_memory = _extract_carbon_activity_memory(
            chunks=item_chunks,
            carbon_extractor=carbon_extractor,
        )
        overviews.append(
            {
                "knowledge_item_id": knowledge_item_id,
                "title": first_chunk.title,
                "source": first_chunk.source,
                "source_type": first_chunk.source_type,
                "library_scope": first_chunk.library_scope,
                "chunk_count": len(item_chunks),
                "sampled_chunk_count": len(selected_chunks),
                "table_like_chunk_count": sum(1 for chunk in item_chunks if _is_table_like_chunk(chunk.snippet)),
                "numeric_chunk_count": sum(1 for chunk in item_chunks if _has_numeric_content(chunk.snippet)),
                "carbon_activity_memory": carbon_activity_memory,
                "chunks": [
                    _chunk_to_overview_entry(chunk, index=index)
                    for index, chunk in enumerate(selected_chunks, start=1)
                ],
            }
        )
    return overviews


def _extract_carbon_activity_memory(
    *,
    chunks: list[KnowledgeChunk],
    carbon_extractor: ReportCarbonActivityExtractor,
) -> dict:
    try:
        result = carbon_extractor.extract(chunks)
    except Exception as exc:  # noqa: BLE001 - extraction must not block general file QA.
        return {
            "status": "failed",
            "activity_count": 0,
            "items": [],
            "warnings": [f"上传文件碳活动抽取失败：{exc}"],
        }

    items = [
        _carbon_activity_to_memory_entry(extracted, index=index)
        for index, extracted in enumerate(
            result.extracted_activities[:UPLOAD_CARBON_ACTIVITY_MEMORY_MAX_ITEMS],
            start=1,
        )
    ]
    return {
        "status": "found" if items else "empty",
        "activity_count": len(result.extracted_activities),
        "items": items,
        "warnings": result.warnings[:5],
    }


def _carbon_activity_to_memory_entry(extracted, *, index: int) -> dict:
    activity = extracted.activity
    return {
        "memory_id": f"upload-carbon-{index}",
        "scope": activity.scope,
        "activity_category": activity.activity_category,
        "activity_name": activity.activity_name,
        "activity_value": activity.activity_value,
        "activity_unit": activity.activity_unit,
        "region": activity.region,
        "year": activity.year,
        "requested_factor_id": activity.requested_factor_id,
        "confidence": extracted.confidence,
        "matched_alias": extracted.matched_alias,
        "chunk_id": extracted.chunk_id,
        "page_number": extracted.page_number,
        "sheet_name": extracted.sheet_name,
        "slide_number": extracted.slide_number,
        "section_title": extracted.section_title,
        "snippet": _trim_snippet(extracted.snippet, UPLOAD_OVERVIEW_SNIPPET_MAX_CHARS),
    }


def _select_overview_chunks(chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
    selected: list[KnowledgeChunk] = []
    seen: set[str] = set()

    def add(chunk: KnowledgeChunk) -> None:
        if chunk.chunk_id in seen or len(selected) >= UPLOAD_OVERVIEW_MAX_CHUNKS_PER_FILE:
            return
        selected.append(chunk)
        seen.add(chunk.chunk_id)

    for chunk in chunks[:3]:
        add(chunk)
    for chunk in chunks:
        if _is_table_like_chunk(chunk.snippet):
            add(chunk)
    for chunk in chunks:
        if _has_numeric_content(chunk.snippet):
            add(chunk)
    for chunk in chunks:
        add(chunk)
        if len(selected) >= UPLOAD_OVERVIEW_MAX_CHUNKS_PER_FILE:
            break
    return sorted(selected, key=lambda chunk: chunk.order_index)


def _chunk_to_overview_entry(chunk: KnowledgeChunk, *, index: int) -> dict:
    metadata = chunk.metadata or {}
    return {
        "overview_id": f"upload-overview-{index}",
        "chunk_id": chunk.chunk_id,
        "order_index": chunk.order_index,
        "page_number": _optional_int(metadata.get("page_number")),
        "sheet_name": _optional_str(metadata.get("sheet_name")),
        "slide_number": _optional_int(metadata.get("slide_number")),
        "section_title": _optional_str(metadata.get("section_title")),
        "content_kind": _infer_content_kind(chunk.snippet),
        "snippet": _trim_snippet(chunk.snippet, UPLOAD_OVERVIEW_SNIPPET_MAX_CHARS),
    }


def _fallback_selected_upload_chunks(
    *,
    allowed_knowledge_item_ids: set[str],
    top_k: int,
) -> list[dict]:
    """Return parsed chunks when explicit file search has no lexical hit.

    Uploaded-file questions are often broad, e.g. "根据这份报告回答以下问题".
    In that case BM25 can return zero even though the file is parsed and selected.
    Returning the first parsed chunks is safer than pretending the file is unreadable.
    """
    if not allowed_knowledge_item_ids:
        return []

    knowledge_service = get_knowledge_service()
    chunks = knowledge_service.list_chunks(knowledge_item_ids=sorted(allowed_knowledge_item_ids))
    upload_chunks = [
        chunk for chunk in chunks
        if chunk.source_type == "private_upload" and chunk.knowledge_item_id in allowed_knowledge_item_ids
    ]
    upload_chunks.sort(key=lambda chunk: (chunk.knowledge_item_id, chunk.order_index))
    return [_chunk_to_fallback_hit(chunk, index=index) for index, chunk in enumerate(upload_chunks[:top_k], start=1)]


def _chunk_to_fallback_hit(chunk: KnowledgeChunk, *, index: int) -> dict:
    metadata = chunk.metadata or {}
    return {
        "reference_id": f"upload-fallback-{index}",
        "doc_id": chunk.knowledge_item_id,
        "knowledge_item_id": chunk.knowledge_item_id,
        "title": chunk.title,
        "source_type": "private_upload",
        "source": chunk.source,
        "source_url": chunk.source_url,
        "issued_at": chunk.issued_at,
        "region": chunk.region,
        "doc_type": chunk.doc_type,
        "sample_type": chunk.sample_type,
        "business_topic": chunk.business_topic,
        "library_scope": chunk.library_scope,
        "file_id": str(metadata.get("file_id") or "") or None,
        "page_number": _optional_int(metadata.get("page_number")),
        "sheet_name": _optional_str(metadata.get("sheet_name")),
        "slide_number": _optional_int(metadata.get("slide_number")),
        "section_title": _optional_str(metadata.get("section_title")),
        "chunk_id": chunk.chunk_id,
        "snippet": chunk.snippet,
        "score": 0.01,
        "retrieval_layer": "selected_upload_chunk_fallback",
    }


def _infer_content_kind(snippet: str) -> str:
    if _is_table_like_chunk(snippet):
        return "table_or_structured"
    if _has_numeric_content(snippet):
        return "numeric_text"
    return "text"


def _is_table_like_chunk(snippet: str) -> bool:
    normalized = snippet.strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    return (
        lowered.startswith("[table")
        or lowered.startswith("[sheet")
        or " | " in normalized and "=" in normalized
        or normalized.count("|") >= 3
        or "\t" in normalized
    )


def _has_numeric_content(snippet: str) -> bool:
    return any(char.isdigit() for char in snippet)


def _trim_snippet(snippet: str, max_chars: int) -> str:
    normalized = " ".join(str(snippet).split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 1].rstrip() + "…"


def _optional_str(value) -> str | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip()
    return normalized or None


def _optional_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
