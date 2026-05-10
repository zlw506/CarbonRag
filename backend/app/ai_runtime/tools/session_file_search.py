from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.knowledge import get_knowledge_service
from app.knowledge.schemas import KnowledgeChunk
from app.rag import RagEngineService, build_rag_query_params, get_rag_engine_service


class SessionFileSearchTool(BaseTool):
    def __init__(self, rag_engine: RagEngineService | None = None) -> None:
        self.rag_engine = rag_engine or get_rag_engine_service()

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
        allowed_ids = {
            str(item)
            for item in payload.get("attached_file_knowledge_item_ids", [])
            if str(item).strip()
        }
        if not allowed_ids:
            return ToolResult(
                name=self.definition.name,
                status="success",
                output={"query": question, "knowledge_scope": "private_upload", "top_k": top_k, "hits": []},
                metadata={"trace_id": trace_id, "hit_count": 0, "context_keys": sorted(context)},
            )

        rag_result = self.rag_engine.retrieve(build_rag_query_params(
            question=question,
            knowledge_scope="private_sample",
            top_k=top_k,
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
                top_k=top_k,
            )
            fallback_used = bool(hits)
        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "query": question,
                "knowledge_scope": "private_upload",
                "top_k": top_k,
                "allowed_knowledge_item_ids": sorted(allowed_ids),
                "hits": hits,
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
