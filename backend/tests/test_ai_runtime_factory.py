from app.ai_runtime.providers.factory import (
    get_chat_provider,
    get_embedding_provider,
    get_rerank_provider,
    reset_provider_factory_cache,
)


def test_provider_factory_returns_chat_and_embedding_descriptors() -> None:
    reset_provider_factory_cache()

    chat_provider = get_chat_provider()
    embedding_provider = get_embedding_provider()
    rerank_provider = get_rerank_provider()

    chat_descriptor = chat_provider.describe()
    embedding_descriptor = embedding_provider.describe()
    rerank_descriptor = rerank_provider.describe()

    assert chat_descriptor.provider_type == "chat"
    assert chat_descriptor.mode == "ollama"
    assert chat_descriptor.default_model == "deepseek-r1:8b"
    assert embedding_descriptor.provider_type == "embedding"
    assert embedding_descriptor.mode == "openai_compatible"
    assert embedding_descriptor.default_model is not None
    assert rerank_descriptor.provider_type == "rerank"
    assert rerank_descriptor.mode == "disabled"
