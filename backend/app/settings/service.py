from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import httpx

from app.ai_runtime.config import get_ai_runtime_config
from app.ai_runtime.providers.anthropic_chat import AnthropicChatProvider
from app.ai_runtime.providers.base import BaseChatProvider
from app.ai_runtime.providers.chat_openai_compatible import OpenAICompatibleChatProvider
from app.ai_runtime.providers.gemini_chat import GeminiChatProvider
from app.ai_runtime.providers.ollama_chat import OllamaChatProvider
from app.ai_runtime.providers.ollama_client import OllamaClient
from app.core.config import get_settings
from app.settings.crypto import decrypt_secret, encrypt_secret
from app.settings.schemas import (
    LocalProviderOverride,
    ModelDiscoveryResult,
    ProviderConnectionRequest,
    ProviderConnectionResult,
    ProviderListResponse,
    ProviderProfile,
    ResolvedProviderConfig,
    UpdateUserSettingsRequest,
    UpsertProviderProfileRequest,
    UserSettingsEnvelope,
)
from app.settings.storage import SettingsStorage, get_settings_storage


class SettingsValidationError(ValueError):
    pass


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_base_url(provider_type: str, base_url: str | None) -> str | None:
    normalized = (base_url or "").strip().rstrip("/")
    if normalized:
        return normalized
    defaults = {
        "openai": "https://api.openai.com/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta",
        "ollama": "http://localhost:11434/api",
    }
    return defaults.get(provider_type)


def _default_display_name(provider_type: str) -> str:
    return {
        "carbonrag_cloud": "CarbonRag 默认云端",
        "openai_compatible": "自定义 OpenAI-compatible",
        "ollama": "Ollama",
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "gemini": "Gemini",
        "deepseek": "DeepSeek",
    }.get(provider_type, provider_type)


def _is_local_provider_ref(provider_ref: str | None) -> bool:
    return bool(provider_ref and provider_ref.startswith("local:"))


class SettingsService:
    def __init__(self, *, storage: SettingsStorage | None = None) -> None:
        self.storage = storage or get_settings_storage()
        self.settings = get_settings()

    def get_user_settings(self, *, owner_user_id: str) -> UserSettingsEnvelope:
        stored = self.storage.get_user_settings(owner_user_id=owner_user_id)
        if stored is not None:
            if _is_local_provider_ref(stored.active_provider_ref):
                stored.active_provider_ref = "builtin:carbonrag-cloud"
                stored.advanced.local_provider_profile_ids = []
                timestamp = utcnow_iso()
                self.storage.upsert_user_settings(
                    owner_user_id=owner_user_id,
                    payload=stored,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
            return stored

        payload = UserSettingsEnvelope()
        timestamp = utcnow_iso()
        self.storage.upsert_user_settings(
            owner_user_id=owner_user_id,
            payload=payload,
            created_at=timestamp,
            updated_at=timestamp,
        )
        return payload

    def update_user_settings(self, *, owner_user_id: str, payload: UpdateUserSettingsRequest | dict) -> UserSettingsEnvelope:
        request = payload if isinstance(payload, UpdateUserSettingsRequest) else UpdateUserSettingsRequest.model_validate(payload)
        current = self.get_user_settings(owner_user_id=owner_user_id)
        merged = UserSettingsEnvelope(
            appearance=request.appearance or current.appearance,
            chat=request.chat or current.chat,
            data_privacy=request.data_privacy or current.data_privacy,
            advanced=request.advanced or current.advanced,
            active_provider_ref=request.active_provider_ref or current.active_provider_ref,
        )
        if _is_local_provider_ref(merged.active_provider_ref):
            raise SettingsValidationError("本地 Provider 已停用，请保存为账号 Provider 后再启用。")
        merged.data_privacy.store_local_provider_keys_in_browser = False
        merged.advanced.local_provider_profile_ids = []
        timestamp = utcnow_iso()
        self.storage.upsert_user_settings(
            owner_user_id=owner_user_id,
            payload=merged,
            created_at=timestamp,
            updated_at=timestamp,
        )
        return merged

    def list_provider_profiles(self, *, owner_user_id: str) -> ProviderListResponse:
        current = self.get_user_settings(owner_user_id=owner_user_id)
        active_provider_ref = (
            "builtin:carbonrag-cloud"
            if _is_local_provider_ref(current.active_provider_ref)
            else current.active_provider_ref
        )
        return ProviderListResponse(
            active_provider_ref=active_provider_ref,
            profiles=self.storage.list_provider_profiles(owner_user_id=owner_user_id),
        )

    def create_provider_profile(self, *, owner_user_id: str, payload: UpsertProviderProfileRequest | dict) -> ProviderProfile:
        request = payload if isinstance(payload, UpsertProviderProfileRequest) else UpsertProviderProfileRequest.model_validate(payload)
        if request.storage_mode != "account":
            raise SettingsValidationError("仅账号保存的 provider 配置可以写入后端。")
        timestamp = utcnow_iso()
        return self.storage.upsert_provider_profile(
            owner_user_id=owner_user_id,
            profile_id=f"profile-{uuid4().hex[:12]}",
            provider_type=request.provider_type,
            display_name=request.display_name or _default_display_name(request.provider_type),
            base_url=_normalize_base_url(request.provider_type, request.base_url),
            model_name=request.model_name,
            config_json=request.config_json,
            api_key_encrypted=encrypt_secret(request.api_key),
            created_at=timestamp,
            updated_at=timestamp,
        )

    def update_provider_profile(self, *, owner_user_id: str, profile_id: str, payload: UpsertProviderProfileRequest | dict) -> ProviderProfile | None:
        existing = self.storage.get_provider_profile(owner_user_id=owner_user_id, profile_id=profile_id)
        if existing is None:
            return None
        request = payload if isinstance(payload, UpsertProviderProfileRequest) else UpsertProviderProfileRequest.model_validate(payload)
        timestamp = utcnow_iso()
        return self.storage.upsert_provider_profile(
            owner_user_id=owner_user_id,
            profile_id=profile_id,
            provider_type=request.provider_type,
            display_name=request.display_name or existing["display_name"],
            base_url=_normalize_base_url(request.provider_type, request.base_url or existing.get("base_url")),
            model_name=request.model_name or existing.get("model_name"),
            config_json=request.config_json or existing.get("config_json") or {},
            api_key_encrypted=encrypt_secret(request.api_key) if request.api_key else None,
            created_at=existing["created_at"],
            updated_at=timestamp,
        )

    def delete_provider_profile(self, *, owner_user_id: str, profile_id: str) -> bool:
        deleted = self.storage.delete_provider_profile(owner_user_id=owner_user_id, profile_id=profile_id)
        if deleted:
            current = self.get_user_settings(owner_user_id=owner_user_id)
            if current.active_provider_ref == f"account:{profile_id}":
                self.update_user_settings(owner_user_id=owner_user_id, payload={"active_provider_ref": "builtin:carbonrag-cloud"})
        return deleted

    def resolve_provider_config(
        self,
        *,
        owner_user_id: str,
        provider_override: LocalProviderOverride | dict | None = None,
    ) -> ResolvedProviderConfig:
        if provider_override is not None:
            raise SettingsValidationError("本地 Provider 覆盖已停用，请使用账号级 Provider 配置。")

        current = self.get_user_settings(owner_user_id=owner_user_id)
        provider_ref = current.active_provider_ref or "builtin:carbonrag-cloud"
        if provider_ref == "builtin:carbonrag-cloud":
            runtime = get_ai_runtime_config().chat_provider
            return ResolvedProviderConfig(
                provider_ref="builtin:carbonrag-cloud",
                provider_type="carbonrag_cloud",
                display_name="CarbonRag 默认云端",
                base_url=runtime.base_url,
                model_name=runtime.model_name,
                api_key=runtime.api_key,
                config_json={"timeout_seconds": runtime.timeout_seconds, "max_retries": runtime.max_retries},
            )

        if provider_ref.startswith("account:"):
            profile_id = provider_ref.split(":", 1)[1]
            profile = self.storage.get_provider_profile(owner_user_id=owner_user_id, profile_id=profile_id)
            if profile is None:
                raise SettingsValidationError("当前激活的账号 provider 不存在。")
            return ResolvedProviderConfig(
                provider_ref=provider_ref,
                provider_type=profile["provider_type"],
                display_name=profile["display_name"],
                base_url=_normalize_base_url(profile["provider_type"], profile.get("base_url")),
                model_name=profile.get("model_name"),
                api_key=decrypt_secret(profile.get("api_key_encrypted")),
                config_json=profile.get("config_json") or {},
            )

        if provider_ref.startswith("local:"):
            self.update_user_settings(
                owner_user_id=owner_user_id,
                payload={"active_provider_ref": "builtin:carbonrag-cloud"},
            )
            return self.resolve_provider_config(owner_user_id=owner_user_id)

        raise SettingsValidationError("当前激活的 provider_ref 无法识别。")

    def build_chat_provider(self, *, owner_user_id: str, provider_override: LocalProviderOverride | dict | None = None) -> tuple[ResolvedProviderConfig, BaseChatProvider]:
        resolved = self.resolve_provider_config(owner_user_id=owner_user_id, provider_override=provider_override)
        return resolved, build_chat_provider_from_resolved(resolved)

    def discover_models(self, payload: ProviderConnectionRequest | dict) -> ModelDiscoveryResult:
        request = payload if isinstance(payload, ProviderConnectionRequest) else ProviderConnectionRequest.model_validate(payload)
        normalized_base_url = _normalize_base_url(request.provider_type, request.base_url)
        models = discover_models_for_connection(
            provider_type=request.provider_type,
            base_url=normalized_base_url,
            api_key=request.api_key,
        )
        if request.provider_type == "carbonrag_cloud":
            runtime_model = get_ai_runtime_config().chat_provider.model_name
            models = list(dict.fromkeys([runtime_model, *models]))
        return ModelDiscoveryResult(
            models=models,
            provider_type=request.provider_type,
            normalized_base_url=normalized_base_url,
        )

    def test_provider_connection(self, payload: ProviderConnectionRequest | dict) -> ProviderConnectionResult:
        request = payload if isinstance(payload, ProviderConnectionRequest) else ProviderConnectionRequest.model_validate(payload)
        try:
            discovery = self.discover_models(request)
        except Exception as exc:
            return ProviderConnectionResult(
                ok=False,
                provider_type=request.provider_type,
                message=f"连接失败：{exc}",
                discovered_models=[],
            )
        return ProviderConnectionResult(
            ok=True,
            provider_type=request.provider_type,
            message="连接成功。",
            discovered_models=discovery.models,
        )


def discover_models_for_connection(*, provider_type: str, base_url: str | None, api_key: str | None) -> list[str]:
    if provider_type == "carbonrag_cloud":
        return [get_ai_runtime_config().chat_provider.model_name]

    if provider_type == "ollama":
        if not base_url:
            raise SettingsValidationError("Ollama 需要 Base URL。")
        return OllamaClient(base_url=base_url, timeout_seconds=15.0).list_models()

    if provider_type in {"openai_compatible", "openai", "deepseek"}:
        if not base_url:
            raise SettingsValidationError("当前 provider 需要 Base URL。")
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        response = httpx.get(f"{base_url.rstrip('/')}/models", headers=headers, timeout=15.0)
        response.raise_for_status()
        payload = response.json()
        return [item["id"] for item in payload.get("data", []) if isinstance(item, dict) and item.get("id")]

    if provider_type == "anthropic":
        if not api_key:
            raise SettingsValidationError("Anthropic 需要 API Key。")
        response = httpx.get(
            f"{base_url.rstrip('/')}/models",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            timeout=15.0,
        )
        response.raise_for_status()
        payload = response.json()
        return [item["id"] for item in payload.get("data", []) if isinstance(item, dict) and item.get("id")]

    if provider_type == "gemini":
        if not api_key:
            raise SettingsValidationError("Gemini 需要 API Key。")
        response = httpx.get(
            f"{base_url.rstrip('/')}/models",
            params={"key": api_key},
            timeout=15.0,
        )
        response.raise_for_status()
        payload = response.json()
        return [item["name"].replace("models/", "") for item in payload.get("models", []) if isinstance(item, dict) and item.get("name")]

    raise SettingsValidationError(f"暂不支持的 provider 类型：{provider_type}")


def build_chat_provider_from_resolved(resolved: ResolvedProviderConfig) -> BaseChatProvider:
    timeout_seconds = float(resolved.config_json.get("timeout_seconds") or get_settings().model_timeout_seconds)
    max_tokens = int(resolved.config_json.get("max_tokens") or get_settings().model_max_tokens)
    temperature = float(resolved.config_json.get("temperature") or get_settings().model_temperature)
    max_retries = int(resolved.config_json.get("max_retries") or get_settings().model_max_retries)
    num_ctx = resolved.config_json.get("num_ctx")
    keep_alive = resolved.config_json.get("keep_alive")
    think = resolved.config_json.get("think")

    if resolved.provider_type in {"carbonrag_cloud", "openai_compatible", "openai", "deepseek"}:
        runtime = get_ai_runtime_config().chat_provider
        return OpenAICompatibleChatProvider(
            base_url=resolved.base_url or runtime.base_url,
            api_key=resolved.api_key or runtime.api_key,
            model_name=resolved.model_name or runtime.model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            mode="openai_compatible" if resolved.provider_type == "openai_compatible" else resolved.provider_type,
        )

    if resolved.provider_type == "ollama":
        settings = get_settings()
        return OllamaChatProvider(
            base_url=resolved.base_url or settings.ollama_base_url or _normalize_base_url("ollama", None) or "http://localhost:11434",
            model_name=resolved.model_name or settings.ollama_model or "deepseek-r1:8b",
            temperature=temperature,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            num_ctx=int(num_ctx) if num_ctx is not None else settings.ollama_num_ctx,
            keep_alive=str(keep_alive) if keep_alive is not None else settings.ollama_keep_alive,
            think=_coerce_bool(think) if think is not None else settings.ollama_think,
        )

    if resolved.provider_type == "anthropic":
        if not resolved.api_key:
            raise SettingsValidationError("Anthropic 需要 API Key。")
        return AnthropicChatProvider(
            base_url=resolved.base_url or _normalize_base_url("anthropic", None) or "https://api.anthropic.com/v1",
            api_key=resolved.api_key,
            model_name=resolved.model_name or "claude-sonnet-4-20250514",
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
        )

    if resolved.provider_type == "gemini":
        if not resolved.api_key:
            raise SettingsValidationError("Gemini 需要 API Key。")
        return GeminiChatProvider(
            base_url=resolved.base_url or _normalize_base_url("gemini", None) or "https://generativelanguage.googleapis.com/v1beta",
            api_key=resolved.api_key,
            model_name=resolved.model_name or "gemini-2.5-flash",
            temperature=temperature,
            max_tokens=max_tokens,
            timeout_seconds=timeout_seconds,
        )

    raise SettingsValidationError(f"不支持的 provider 类型：{resolved.provider_type}")


def get_settings_service() -> SettingsService:
    return SettingsService()


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)
