from __future__ import annotations

from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.langchain_rag.service import LangChainRagService, get_langchain_rag_service


class LangChainRagSearchTool(BaseTool):
    def __init__(self, rag_service: LangChainRagService | None = None) -> None:
        self.rag_service = rag_service or get_langchain_rag_service()

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
        result = self.rag_service.search(
            owner_user_id=owner_user_id,
            query=question,
            knowledge_scope=knowledge_scope,  # type: ignore[arg-type]
            top_k=top_k,
            allowed_knowledge_item_ids=allowed_ids,
        )
        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "query": result.query,
                "hyde_query": result.hyde_query,
                "knowledge_scope": knowledge_scope,
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
    def __init__(self, rag_service: LangChainRagService | None = None) -> None:
        self.rag_service = rag_service or get_langchain_rag_service()

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
        result = self.rag_service.answer(
            owner_user_id=owner_user_id,
            query=question,
            knowledge_scope=knowledge_scope,  # type: ignore[arg-type]
            top_k=top_k,
            allowed_knowledge_item_ids=_resolve_allowed_ids(arguments=arguments, payload=payload),
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
