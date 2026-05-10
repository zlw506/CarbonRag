from app.langchain_rag.config import LangChainRagConfig
from app.langchain_rag.retriever import HybridLangChainRetriever
from app.langchain_rag.schemas import LangChainRagDocument, LangChainRagHit, LangChainRagTrace


def _config() -> LangChainRagConfig:
    return LangChainRagConfig(
        enabled=True,
        vector_enabled=True,
        vector_backend="chroma",
        bm25_enabled=True,
        hyde_enabled=True,
        rerank_enabled=True,
        rerank_provider="cross_encoder",
        rerank_model="test-reranker",
        chroma_persist_dir="./tmp/chroma",
        chroma_collection="test",
        chunk_size=800,
        chunk_overlap=120,
        top_k=5,
        langsmith_tracing=False,
    )


class FakeVectorStore:
    def health(self) -> dict:
        return {"available": True}

    def search(self, *, query: str, top_k: int, candidate_documents: list[LangChainRagDocument]) -> list[LangChainRagHit]:
        return [
            LangChainRagHit(
                chunk_id="chunk-vector",
                doc_id="doc-vector",
                title="向量命中",
                snippet="长查询可以更多依赖语义向量召回。",
                source_type="public_policy",
                source="vector",
                score=0.8,
                vector_score=0.8,
                source_retrievers=["vector"],
            )
        ][:top_k]


class FakeReranker:
    reason = None

    def rerank(self, *, query: str, hits: list[LangChainRagHit], top_k: int) -> tuple[list[LangChainRagHit], bool]:
        return hits[:top_k], True


def test_hybrid_retriever_merges_bm25_vector_and_records_trace() -> None:
    documents = [
        LangChainRagDocument(
            page_content="短查询更依赖关键词 BM25 命中。",
            metadata={"chunk_id": "chunk-bm25", "knowledge_item_id": "doc-bm25", "title": "BM25 命中"},
        )
    ]
    retriever = HybridLangChainRetriever(config=_config(), vector_store=FakeVectorStore(), reranker=FakeReranker())  # type: ignore[arg-type]

    hits, trace = retriever.retrieve(
        query="双碳",
        retrieval_query="双碳 BM25",
        documents=documents,
        top_k=5,
        trace=LangChainRagTrace(hyde_enabled=True),
    )

    assert {hit.chunk_id for hit in hits} >= {"chunk-bm25", "chunk-vector"}
    assert trace.bm25_count == 1
    assert trace.vector_count == 1
    assert trace.merged_count == 2
    assert trace.rerank_applied is True
    assert trace.weights == {"bm25": 0.7, "vector": 0.3}
