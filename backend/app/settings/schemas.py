from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ThemeMode = Literal["light", "dark", "system"]
ThemePresetId = Literal[
    "carbon-blue",
    "deep-space",
    "slate-neutral",
    "jade-green",
    "teal-professional",
    "indigo-focus",
    "purple-research",
    "rose-humanized",
    "amber-warm",
    "graphite-pro",
]
ProviderType = Literal[
    "carbonrag_cloud",
    "openai_compatible",
    "ollama",
    "openai",
    "anthropic",
    "gemini",
    "deepseek",
]
CredentialStorageMode = Literal["local_only", "account"]


class AppearanceSettings(BaseModel):
    theme_mode: ThemeMode = "system"
    theme_preset: ThemePresetId = "carbon-blue"
    bubble_density: Literal["comfortable", "compact"] = "comfortable"
    font_size: Literal["default", "large"] = "default"
    sidebar_default: Literal["expanded", "collapsed"] = "expanded"


class ChatPreferenceSettings(BaseModel):
    send_shortcut: Literal["enter", "ctrl_enter"] = "enter"
    expand_thinking_by_default: bool = False
    show_evidence_panel_by_default: bool = False
    show_context_debug_by_default: bool = False
    auto_generate_title_for_new_session: bool = True
    reconnect_notice_mode: Literal["message_only", "toast_and_message"] = "message_only"


class DataPrivacySettings(BaseModel):
    store_local_provider_keys_in_browser: bool = True
    allow_account_saved_provider_keys: bool = True


class AdvancedSettings(BaseModel):
    local_provider_profile_ids: list[str] = Field(default_factory=list)


class UserSettingsEnvelope(BaseModel):
    appearance: AppearanceSettings = Field(default_factory=AppearanceSettings)
    chat: ChatPreferenceSettings = Field(default_factory=ChatPreferenceSettings)
    data_privacy: DataPrivacySettings = Field(default_factory=DataPrivacySettings)
    advanced: AdvancedSettings = Field(default_factory=AdvancedSettings)
    active_provider_ref: str = "builtin:carbonrag-cloud"


class UpdateUserSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appearance: AppearanceSettings | None = None
    chat: ChatPreferenceSettings | None = None
    data_privacy: DataPrivacySettings | None = None
    advanced: AdvancedSettings | None = None
    active_provider_ref: str | None = None

    @field_validator("active_provider_ref")
    @classmethod
    def normalize_provider_ref(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ProviderProfile(BaseModel):
    profile_id: str
    provider_type: ProviderType
    display_name: str
    base_url: str | None = None
    model_name: str | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ProviderListResponse(BaseModel):
    builtin_provider_refs: list[str] = Field(default_factory=lambda: ["builtin:carbonrag-cloud"])
    active_provider_ref: str = "builtin:carbonrag-cloud"
    profiles: list[ProviderProfile] = Field(default_factory=list)


class UpsertProviderProfileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_type: ProviderType
    display_name: str
    base_url: str | None = None
    model_name: str | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)
    api_key: str | None = None
    storage_mode: CredentialStorageMode = "account"

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("display_name is required.")
        return normalized

    @field_validator("base_url", "model_name", "api_key")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ProviderConnectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_type: ProviderType
    display_name: str | None = None
    base_url: str | None = None
    model_name: str | None = None
    api_key: str | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("display_name", "base_url", "model_name", "api_key")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ModelDiscoveryResult(BaseModel):
    models: list[str] = Field(default_factory=list)
    provider_type: ProviderType
    normalized_base_url: str | None = None


class ProviderConnectionResult(BaseModel):
    ok: bool
    provider_type: ProviderType
    message: str
    discovered_models: list[str] = Field(default_factory=list)


class LocalProviderOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: str | None = None
    provider_type: ProviderType
    display_name: str | None = None
    base_url: str | None = None
    model_name: str | None = None
    api_key: str | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("profile_id", "display_name", "base_url", "model_name", "api_key")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ResolvedProviderConfig(BaseModel):
    provider_ref: str
    provider_type: ProviderType
    display_name: str
    base_url: str | None = None
    model_name: str | None = None
    api_key: str | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)
