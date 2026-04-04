import json
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import LOCAL_PROVIDER_CONFIG_PATH, get_settings


@dataclass(frozen=True)
class ChatProviderConfig:
    base_url: str
    api_key: str
    model_name: str
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class EmbeddingProviderConfig:
    base_url: str
    api_key: str
    model_name: str


@dataclass(frozen=True)
class AIRuntimeConfig:
    app_name: str
    app_version: str
    default_mode: str
    allowed_modes: tuple[str, ...]
    chat_provider: ChatProviderConfig
    embedding_provider: EmbeddingProviderConfig
    public_data_dir: str
    private_sample_dir: str
    factor_data_dir: str


@dataclass(frozen=True)
class LocalChatProviderOverride:
    base_url: str
    api_key: str
    model_name: str


def load_local_chat_provider_override() -> LocalChatProviderOverride | None:
    if not LOCAL_PROVIDER_CONFIG_PATH.exists():
        return None

    payload = json.loads(LOCAL_PROVIDER_CONFIG_PATH.read_text(encoding="utf-8"))
    return LocalChatProviderOverride(
        base_url=payload["base_url"],
        api_key=payload["api_key"],
        model_name=payload.get("model_name", "gpt-5.4")
    )


@lru_cache(maxsize=1)
def get_ai_runtime_config() -> AIRuntimeConfig:
    settings = get_settings()
    local_override = load_local_chat_provider_override()

    chat_provider = ChatProviderConfig(
        base_url=local_override.base_url if local_override else settings.model_api_base_url,
        api_key=local_override.api_key if local_override else settings.model_api_key,
        model_name=local_override.model_name if local_override else settings.model_name,
        temperature=settings.model_temperature,
        max_tokens=settings.model_max_tokens
    )
    embedding_provider = EmbeddingProviderConfig(
        base_url=settings.embedding_api_base_url,
        api_key=settings.embedding_api_key,
        model_name=settings.embedding_model
    )

    return AIRuntimeConfig(
        app_name=settings.app_name,
        app_version=settings.app_version,
        default_mode="ask",
        allowed_modes=("ask", "carbon", "report"),
        chat_provider=chat_provider,
        embedding_provider=embedding_provider,
        public_data_dir=settings.public_data_dir,
        private_sample_dir=settings.private_sample_dir,
        factor_data_dir=settings.factor_data_dir
    )
