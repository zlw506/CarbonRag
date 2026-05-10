from app.langchain_rag.config import LangChainRagConfig
from app.langchain_rag.reranker import CrossEncoderReranker
from app.langchain_rag.schemas import LangChainRagHit


def test_reranker_disabled_is_explicit_fallback() -> None:
    config = LangChainRagConfig(
        enabled=True,
        vector_enabled=True,
        vector_backend="chroma",
        bm25_enabled=True,
        hyde_enabled=True,
        rerank_enabled=False,
        rerank_provider="cross_encoder",
        rerank_model="test-reranker",
        chroma_persist_dir="./tmp/chroma",
        chroma_collection="test",
        chunk_size=800,
        chunk_overlap=120,
        top_k=5,
        langsmith_tracing=False,
    )
    hits = [
        LangChainRagHit(
            chunk_id="chunk-1",
            doc_id="doc-1",
            title="片段",
            snippet="内容",
            source_type="public_policy",
            source="test",
        )
    ]

    reranked, applied = CrossEncoderReranker(config=config).rerank(query="问题", hits=hits, top_k=5)

    assert reranked == hits
    assert applied is False
