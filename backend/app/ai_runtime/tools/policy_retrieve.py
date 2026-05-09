from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.rag import RagEngineService, build_rag_query_params, get_rag_engine_service


class PolicyRetrieveTool(BaseTool):
    def __init__(self, rag_engine: RagEngineService | None = None) -> None:
        self.rag_engine = rag_engine or get_rag_engine_service()

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="policy_retrieve",
            description="Retrieve public policy snippets from the local public policy corpus.",
            category="policy_retrieval",
        )

    def invoke(
        self,
        *,
        arguments: Mapping[str, Any],
        context: Mapping[str, Any],
        trace_id: str
    ) -> ToolResult:
        payload = arguments.get("payload", {})
        question = str(arguments.get("question") or arguments.get("user_input") or "").strip()
        top_k = int(arguments.get("top_k") or payload.get("top_k", 5))
        knowledge_scope = str(arguments.get("knowledge_scope") or payload.get("knowledge_scope_effective", "public"))
        region = arguments.get("region") or payload.get("region")
        doc_type = arguments.get("doc_type") or payload.get("doc_type")

        rag_result = self.rag_engine.retrieve(build_rag_query_params(
            question=question,
            knowledge_scope="public",
            top_k=top_k,
            mode=payload.get("rag_mode") or arguments.get("rag_mode"),
            region=region,
            doc_type=doc_type,
        ))
        hits = [chunk.to_retrieved_hit() for chunk in rag_result.chunks]

        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "query": question,
                "knowledge_scope": knowledge_scope,
                "top_k": top_k,
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
