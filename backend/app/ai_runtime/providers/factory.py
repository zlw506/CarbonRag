from functools import lru_cache

from app.ai_runtime.config import get_ai_runtime_config
from app.ai_runtime.providers.base import BaseChatProvider, BaseEmbeddingProvider, BaseRerankProvider
from app.ai_runtime.providers.chat_openai_compatible import OpenAICompatibleChatProvider
from app.ai_runtime.providers.embedding_openai_compatible import OpenAICompatibleEmbeddingProvider
from app.ai_runtime.providers.ollama_chat import OllamaChatProvider
from app.ai_runtime.providers.rerank_local import NoopRerankProvider
from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_chat_provider() -> BaseChatProvider:
    settings = get_settings()
    config = get_ai_runtime_config().chat_provider
    provider_type = (settings.ai_chat_provider or settings.model_provider_mode or "openai_compatible").strip().lower()
    if provider_type == "ollama":
        return OllamaChatProvider(
            base_url=settings.ollama_base_url or config.base_url or "http://localhost:11434",
            model_name=settings.ollama_model or config.model_name or "deepseek-r1:8b",
            temperature=config.temperature,
            timeout_seconds=settings.ollama_timeout_seconds or config.timeout_seconds,
            max_retries=settings.ollama_max_retries or config.max_retries,
            num_ctx=settings.ollama_num_ctx,
            keep_alive=settings.ollama_keep_alive,
            think=settings.ollama_think,
        )

    return OpenAICompatibleChatProvider(
        base_url=config.base_url,
        api_key=config.api_key,
        model_name=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
        mode="openai_compatible" if provider_type == "openai_compatible" else provider_type,
    )


@lru_cache(maxsize=1)
def get_embedding_provider() -> BaseEmbeddingProvider:
    config = get_ai_runtime_config().embedding_provider
    return OpenAICompatibleEmbeddingProvider(
        base_url=config.base_url,
        api_key=config.api_key,
        model_name=config.model_name
    )


@lru_cache(maxsize=1)
def get_rerank_provider() -> BaseRerankProvider:
    return NoopRerankProvider()


def reset_provider_factory_cache() -> None:
    get_ai_runtime_config.cache_clear()
    get_settings.cache_clear()
    get_chat_provider.cache_clear()
    get_embedding_provider.cache_clear()
    get_rerank_provider.cache_clear()
