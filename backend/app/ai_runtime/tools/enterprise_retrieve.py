from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.rag import RagEngineService, build_rag_query_params, get_rag_engine_service


class EnterpriseRetrieveTool(BaseTool):
    def __init__(self, rag_engine: RagEngineService | None = None) -> None:
        self.rag_engine = rag_engine or get_rag_engine_service()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="enterprise_retrieve",
            description="Retrieve private sample snippets from the local enterprise sample corpus.",
            category="enterprise_retrieval",
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
        allowed_knowledge_item_ids_raw = (
            arguments.get("allowed_knowledge_item_ids")
            or arguments.get("allowed_doc_ids")
            or payload.get("attached_knowledge_item_ids")
            or payload.get("attached_private_sample_ids", [])
        )
        allowed_knowledge_item_ids = {
            str(item)
            for item in allowed_knowledge_item_ids_raw
            if str(item).strip()
        }

        rag_result = self.rag_engine.retrieve(build_rag_query_params(
            question=question,
            knowledge_scope="private_sample",
            top_k=top_k,
            mode=payload.get("rag_mode") or arguments.get("rag_mode"),
            allowed_knowledge_item_ids=allowed_knowledge_item_ids,
        ))
        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "query": question,
                "knowledge_scope": "private_sample",
                "top_k": top_k,
                "allowed_doc_ids": sorted(allowed_knowledge_item_ids),
                "allowed_knowledge_item_ids": sorted(allowed_knowledge_item_ids),
                "hits": rag_result.hits,
                "retrieval_data": rag_result.model_dump(),
            },
            metadata={
                "trace_id": trace_id,
                "hit_count": rag_result.total_hits,
                "context_keys": sorted(context),
                "rag_metadata": rag_result.metadata.model_dump(),
            },
        )
