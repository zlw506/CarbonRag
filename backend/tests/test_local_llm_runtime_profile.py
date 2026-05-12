from app.core.config import Settings
from app.settings.schemas import ResolvedProviderConfig
from app.settings.service import build_chat_provider_from_resolved


def test_default_settings_use_local_openai_compatible_llm() -> None:
    settings = Settings(_env_file=None)

    assert settings.model_api_base_url == "http://127.0.0.1:11434/v1"
    assert settings.model_api_key == "ollama-local-key"
    assert settings.model_name == "deepseek-r1:8b"


def test_ollama_profile_builds_native_ollama_provider() -> None:
    provider = build_chat_provider_from_resolved(
        ResolvedProviderConfig(
            provider_ref="local:ollama",
            provider_type="ollama",
            display_name="本地 Ollama",
            base_url="http://localhost:11434/api",
            model_name="deepseek-r1:8b",
            api_key=None,
            config_json={"timeout_seconds": 120},
        )
    )

    descriptor = provider.describe()
    assert descriptor.mode == "ollama"
    assert descriptor.default_model == "deepseek-r1:8b"


def test_vllm_can_use_openai_compatible_provider() -> None:
    provider = build_chat_provider_from_resolved(
        ResolvedProviderConfig(
            provider_ref="local:vllm",
            provider_type="openai_compatible",
            display_name="本地 vLLM",
            base_url="http://127.0.0.1:8001/v1",
            model_name="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
            api_key="vllm-local-key",
            config_json={"timeout_seconds": 120},
        )
    )

    descriptor = provider.describe()
    assert descriptor.mode == "openai_compatible"
    assert descriptor.default_model == "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
