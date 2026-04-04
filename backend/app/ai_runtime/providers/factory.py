from functools import lru_cache

from app.ai_runtime.config import get_ai_runtime_config
from app.ai_runtime.providers.base import BaseChatProvider, BaseEmbeddingProvider
from app.ai_runtime.providers.chat_openai_compatible import OpenAICompatibleChatProvider
from app.ai_runtime.providers.embedding_openai_compatible import OpenAICompatibleEmbeddingProvider


@lru_cache(maxsize=1)
def get_chat_provider() -> BaseChatProvider:
    config = get_ai_runtime_config().chat_provider
    return OpenAICompatibleChatProvider(
        base_url=config.base_url,
        api_key=config.api_key,
        model_name=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout_seconds=config.timeout_seconds,
    )


@lru_cache(maxsize=1)
def get_embedding_provider() -> BaseEmbeddingProvider:
    config = get_ai_runtime_config().embedding_provider
    return OpenAICompatibleEmbeddingProvider(
        base_url=config.base_url,
        api_key=config.api_key,
        model_name=config.model_name
    )


def reset_provider_factory_cache() -> None:
    get_ai_runtime_config.cache_clear()
    get_chat_provider.cache_clear()
    get_embedding_provider.cache_clear()
