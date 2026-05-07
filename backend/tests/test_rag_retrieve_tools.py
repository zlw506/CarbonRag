from app.ai_runtime.tools.mixed_retrieve import MixedRetrieveTool
from app.rag.schemas import RagEvidenceChunk, RagEvidenceReference, RagRetrievalMetadata, RagRetrievalResult


class FakeRagEngine:
    def __init__(self) -> None:
        self.last_params = None

    def retrieve(self, params):
        self.last_params = params
        chunk = RagEvidenceChunk(
            reference_id="ref-1",
            doc_id="policy_001",
            title="Policy 001",
            source_type="public_policy",
            source="test-source",
            chunk_id="policy_001_chunk_01",
            snippet="policy snippet",
            score=1.0,
            retrieval_layer="bm25_fallback",
        )
        return RagRetrievalResult(
            query=params.question,
            total_hits=1,
            chunks=[chunk],
            references=[
                RagEvidenceReference(
                    reference_id="ref-1",
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    title=chunk.title,
                    source_type=chunk.source_type,
                    source=chunk.source,
                )
            ],
            metadata=RagRetrievalMetadata(
                mode=params.mode,
                knowledge_scope=params.knowledge_scope,
                top_k=params.top_k,
                chunk_top_k=params.top_k,
                retrieval_only=True,
                vector_status="disabled",
                graph_status="unavailable",
                rerank_status="disabled",
                fallback_reason="rag_engine_disabled",
            ),
        )


def test_mixed_retrieve_tool_preserves_hits_and_exposes_rag_data() -> None:
    rag_engine = FakeRagEngine()
    tool = MixedRetrieveTool(rag_engine=rag_engine)  # type: ignore[arg-type]

    result = tool.invoke(
        arguments={
            "question": "结合政策和样例分析。",
            "top_k": 1,
            "payload": {
                "attached_knowledge_item_ids": ["enterprise_doc_001"],
                "rag_mode": "mix",
            },
        },
        context={"mode": "ask"},
        trace_id="trace-rag-tool",
    )

    assert rag_engine.last_params.knowledge_scope == "mixed"
    assert rag_engine.last_params.allowed_knowledge_item_ids == ["enterprise_doc_001"]
    assert result.output["hits"][0]["chunk_id"] == "policy_001_chunk_01"
    assert result.output["retrieval_data"]["metadata"]["fallback_reason"] == "rag_engine_disabled"
    assert result.metadata["rag_metadata"]["graph_status"] == "unavailable"
