from types import SimpleNamespace

from app.rag import embeddings
from app.rag.embeddings import BgeM3Embedder, OpenAICompatibleRagEmbedder


def test_get_rag_embedder_returns_bge_m3_for_default_provider(monkeypatch, tmp_path) -> None:
    embeddings.get_rag_embedder.cache_clear()
    monkeypatch.setattr(
        "app.rag.embeddings.get_settings",
        lambda: SimpleNamespace(
            rag_embedding_provider="bge_m3",
            rag_embedding_model="BAAI/bge-m3",
            rag_embedding_device="cpu",
            rag_model_cache_dir=str(tmp_path / "models"),
            rag_hf_endpoint="https://hf-mirror.com",
            rag_model_auto_download=False,
            embedding_api_base_url="https://api.example.com/v1",
            embedding_api_key="replace-with-embedding-api-key",
            embedding_model="replace-with-embedding-model",
        ),
    )

    try:
        embedder = embeddings.get_rag_embedder()
        assert isinstance(embedder, BgeM3Embedder)
    finally:
        embeddings.get_rag_embedder.cache_clear()


def test_get_rag_embedder_returns_openai_compatible_when_configured(monkeypatch, tmp_path) -> None:
    embeddings.get_rag_embedder.cache_clear()
    monkeypatch.setattr(
        "app.rag.embeddings.get_settings",
        lambda: SimpleNamespace(
            rag_embedding_provider="openai_compatible",
            rag_embedding_model="BAAI/bge-m3",
            rag_embedding_device="cpu",
            rag_model_cache_dir=str(tmp_path / "models"),
            rag_hf_endpoint="https://hf-mirror.com",
            rag_model_auto_download=False,
            embedding_api_base_url="https://embedding.example.com/v1",
            embedding_api_key="test-key",
            embedding_model="text-embedding-test",
        ),
    )

    try:
        embedder = embeddings.get_rag_embedder()
        assert isinstance(embedder, OpenAICompatibleRagEmbedder)
    finally:
        embeddings.get_rag_embedder.cache_clear()
