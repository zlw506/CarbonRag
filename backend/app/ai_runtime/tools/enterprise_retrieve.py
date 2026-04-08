from typing import Any, Mapping

from app.ai_runtime.schemas.tool import ToolResult
from app.ai_runtime.tools.base import BaseTool, ToolDefinition
from app.retrieval.private_retriever import PrivateSampleRetriever, get_private_sample_retriever


class EnterpriseRetrieveTool(BaseTool):
    def __init__(self, retriever: PrivateSampleRetriever | None = None) -> None:
        self.retriever = retriever or get_private_sample_retriever()

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
        allowed_doc_ids_raw = arguments.get("allowed_doc_ids") or payload.get("attached_private_sample_ids", [])
        allowed_doc_ids = {str(item) for item in allowed_doc_ids_raw if str(item).strip()}

        retrieval_result = self.retriever.search(
            question=question,
            top_k=top_k,
            knowledge_scope="private_sample",
            allowed_doc_ids=allowed_doc_ids,
        )
        return ToolResult(
            name=self.definition.name,
            status="success",
            output={
                "query": question,
                "knowledge_scope": "private_sample",
                "top_k": top_k,
                "allowed_doc_ids": sorted(allowed_doc_ids),
                "hits": [hit.model_dump() for hit in retrieval_result.hits],
            },
            metadata={
                "trace_id": trace_id,
                "hit_count": retrieval_result.total_hits,
                "context_keys": sorted(context),
            },
        )
