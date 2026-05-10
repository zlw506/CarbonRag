from __future__ import annotations

from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.rag.kb.models import RagSearchRequest
from app.rag.spine import RagSpineService, get_rag_spine_service


class LangChainRagSearchTool(BaseTool):
    def __init__(self, rag_service: RagSpineService | None = None) -> None:
        self.rag_service = rag_service or get_rag_spine_service()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="langchain_rag_search",
            description="Search CarbonRag knowledge through LangChain hybrid RAG.",
            category="rag_retrieval",
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
        owner_user_id = str(payload.get("owner_user_id") or "")
        knowledge_scope = str(arguments.get("knowledge_scope") or payload.get("knowledge_scope_effective") or "public")
        allowed_ids = _resolve_allowed_ids(arguments=arguments, payload=payload)
        kb_id = _optional_str(payload.get("kb_id") or arguments.get("kb_id"))
        rag_mode = str(payload.get("rag_mode") or arguments.get("rag_mode") or "hybrid_rerank")
        if not owner_user_id:
            return _missing_owner_result(tool_name=self.definition.name, query=question, knowledge_scope=knowledge_scope, top_k=top_k, trace_id=trace_id)
        result = self.rag_service.search(
            owner_user_id=owner_user_id,
            request=RagSearchRequest(
                query=question,
                kb_id=kb_id,
                knowledge_scope=knowledge_scope,  # type: ignore[arg-type]
                top_k=top_k,
                allowed_knowledge_item_ids=allowed_ids,
                mode=rag_mode,  # type: ignore[arg-type]
            ),
        )
        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "query": result.query,
                "knowledge_scope": knowledge_scope,
                "kb_id": result.kb_id,
                "top_k": top_k,
                "hits": [hit.to_tool_hit() for hit in result.hits],
                "retrieval_trace": result.trace.model_dump(),
            },
            metadata={
                "trace_id": trace_id,
                "hit_count": len(result.hits),
                "context_keys": sorted(context),
                "rag_metadata": result.trace.model_dump(),
            },
        )


class LangChainRagAnswerTool(BaseTool):
    def __init__(self, rag_service: RagSpineService | None = None) -> None:
        self.rag_service = rag_service or get_rag_spine_service()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="langchain_rag_answer",
            description="Generate a grounded answer from CarbonRag LangChain RAG.",
            category="rag_answer",
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
        owner_user_id = str(payload.get("owner_user_id") or "")
        knowledge_scope = str(arguments.get("knowledge_scope") or payload.get("knowledge_scope_effective") or "public")
        kb_id = _optional_str(payload.get("kb_id") or arguments.get("kb_id"))
        rag_mode = str(payload.get("rag_mode") or arguments.get("rag_mode") or "hybrid_rerank")
        if not owner_user_id:
            result = _missing_owner_result(tool_name=self.definition.name, query=question, knowledge_scope=knowledge_scope, top_k=top_k, trace_id=trace_id)
            result.output["answer"] = ""
            result.output["citations"] = []
            return result
        result = self.rag_service.answer(
            owner_user_id=owner_user_id,
            request=RagSearchRequest(
                query=question,
                kb_id=kb_id,
                knowledge_scope=knowledge_scope,  # type: ignore[arg-type]
                top_k=top_k,
                allowed_knowledge_item_ids=_resolve_allowed_ids(arguments=arguments, payload=payload),
                mode=rag_mode,  # type: ignore[arg-type]
            ),
        )
        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "answer": result.answer,
                "hits": [hit.to_tool_hit() for hit in result.hits],
                "citations": result.citations,
                "retrieval_trace": result.retrieval_trace.model_dump(),
            },
            metadata={"trace_id": trace_id, "rag_metadata": result.retrieval_trace.model_dump()},
        )


def _resolve_allowed_ids(*, arguments: Mapping[str, Any], payload: Mapping[str, Any]) -> list[str]:
    raw = (
        arguments.get("allowed_knowledge_item_ids")
        or payload.get("attached_file_knowledge_item_ids")
        or payload.get("attached_knowledge_item_ids")
        or []
    )
    return [str(item) for item in raw if str(item).strip()]


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _missing_owner_result(*, tool_name: str, query: str, knowledge_scope: str, top_k: int, trace_id: str) -> ToolResult:
    retrieval_trace = {
        "dense_count": 0,
        "sparse_count": 0,
        "merged_count": 0,
        "rerank_applied": False,
        "vector_backend": "unavailable",
        "degraded": True,
        "warnings": ["RAG skipped because owner_user_id is missing from runtime payload."],
        "retrieval_mode": "hybrid_rerank",
        "kb_id": None,
        "knowledge_scope": knowledge_scope,
    }
    return ToolResult(
        name=tool_name,
        status="success",
        output={
            "query": query,
            "knowledge_scope": knowledge_scope,
            "kb_id": None,
            "top_k": top_k,
            "hits": [],
            "retrieval_trace": retrieval_trace,
        },
        metadata={
            "trace_id": trace_id,
            "hit_count": 0,
            "rag_metadata": retrieval_trace,
        },
    )
