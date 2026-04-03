import json
from dataclasses import dataclass

from app.core.config import LOCAL_PROVIDER_CONFIG_PATH, get_settings
from app.providers.base import BaseProvider
from app.providers.cloud_llm_stub import CloudLLMStubProvider
from app.providers.openai_compatible import OpenAICompatibleProvider


@dataclass(frozen=True)
class LocalProviderConfig:
    base_url: str
    api_key: str
    model_name: str


def load_local_provider_config() -> LocalProviderConfig | None:
    if not LOCAL_PROVIDER_CONFIG_PATH.exists():
        return None

    payload = json.loads(LOCAL_PROVIDER_CONFIG_PATH.read_text(encoding="utf-8"))
    return LocalProviderConfig(
        base_url=payload["base_url"],
        api_key=payload["api_key"],
        model_name=payload.get("model_name", "gpt-5.4")
    )


def get_model_provider() -> BaseProvider:
    settings = get_settings()
    local_config = load_local_provider_config()

    if local_config:
        return OpenAICompatibleProvider(
            base_url=local_config.base_url,
            api_key=local_config.api_key,
            model_name=local_config.model_name
        )

    return CloudLLMStubProvider(mode=settings.model_provider_mode, model_name=settings.model_name)
