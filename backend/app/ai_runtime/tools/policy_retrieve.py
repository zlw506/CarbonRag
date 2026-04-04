from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.retrieval.public_retriever import PublicPolicyRetriever, get_public_policy_retriever


class PolicyRetrieveTool(BaseTool):
    def __init__(self, retriever: PublicPolicyRetriever | None = None) -> None:
        self.retriever = retriever or get_public_policy_retriever()

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

        retrieval_result = self.retriever.search(
            question=question,
            top_k=top_k,
            knowledge_scope=knowledge_scope,
            region=region,
            doc_type=doc_type,
        )

        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "query": question,
                "knowledge_scope": knowledge_scope,
                "top_k": top_k,
                "hits": [hit.model_dump() for hit in retrieval_result.hits],
            },
            metadata={
                "trace_id": trace_id,
                "hit_count": retrieval_result.total_hits,
                "context_keys": sorted(context),
            },
        )
