from app.ai_runtime.providers.factory import (
    get_chat_provider,
    get_embedding_provider,
    reset_provider_factory_cache,
)


def test_provider_factory_returns_chat_and_embedding_descriptors() -> None:
    reset_provider_factory_cache()

    chat_provider = get_chat_provider()
    embedding_provider = get_embedding_provider()

    chat_descriptor = chat_provider.describe()
    embedding_descriptor = embedding_provider.describe()

    assert chat_descriptor.provider_type == "chat"
    assert chat_descriptor.mode == "openai_compatible"
    assert chat_descriptor.default_model == "gpt-5.4"
    assert embedding_descriptor.provider_type == "embedding"
    assert embedding_descriptor.mode == "openai_compatible"
    assert embedding_descriptor.default_model is not None
