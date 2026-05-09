from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
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
        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "query": question,
                "knowledge_scope": "private_upload",
                "top_k": top_k,
                "allowed_knowledge_item_ids": sorted(allowed_ids),
                "hits": hits,
                "retrieval_data": rag_result.model_dump(),
            },
            metadata={
                "trace_id": trace_id,
                "hit_count": len(hits),
                "context_keys": sorted(context),
                "rag_metadata": rag_result.metadata.model_dump(),
            },
        )
