export type ThemeMode = "light" | "dark" | "system";
export type ThemePresetId =
    | "carbon-blue"
    | "deep-space"
    | "slate-neutral"
    | "jade-green"
    | "teal-professional"
    | "indigo-focus"
    | "purple-research"
    | "rose-humanized"
    | "amber-warm"
    | "graphite-pro";

export type ProviderType =
    | "carbonrag_cloud"
    | "openai_compatible"
    | "ollama"
    | "openai"
    | "anthropic"
    | "gemini"
    | "deepseek";

export type CredentialStorageMode = "account";
export type ActiveProviderRef = `builtin:${string}` | `account:${string}`;

export interface AppearanceSettings {
    theme_mode: ThemeMode;
    theme_preset: ThemePresetId;
    bubble_density: "comfortable" | "compact";
    font_size: "default" | "large";
    sidebar_default: "expanded" | "collapsed";
}

export interface ChatPreferenceSettings {
    send_shortcut: "enter" | "ctrl_enter";
    expand_thinking_by_default: boolean;
    show_evidence_panel_by_default: boolean;
    show_context_debug_by_default: boolean;
    auto_generate_title_for_new_session: boolean;
    reconnect_notice_mode: "message_only" | "toast_and_message";
}

export interface DataPrivacySettings {
    store_local_provider_keys_in_browser: boolean;
    allow_account_saved_provider_keys: boolean;
}

export interface AdvancedSettings {
    local_provider_profile_ids: string[];
}

export interface UserSettingsEnvelope {
    appearance: AppearanceSettings;
    chat: ChatPreferenceSettings;
    data_privacy: DataPrivacySettings;
    advanced: AdvancedSettings;
    active_provider_ref: ActiveProviderRef | string;
}

export interface UpdateUserSettingsRequest {
    appearance?: AppearanceSettings;
    chat?: ChatPreferenceSettings;
    data_privacy?: DataPrivacySettings;
    advanced?: AdvancedSettings;
    active_provider_ref?: ActiveProviderRef | string;
}

export interface ProviderProfile {
    profile_id: string;
    provider_type: ProviderType;
    display_name: string;
    base_url?: string | null;
    model_name?: string | null;
    config_json: Record<string, unknown>;
    created_at: string;
    updated_at: string;
}

export interface ProviderListResponse {
    builtin_provider_refs: string[];
    active_provider_ref: string;
    profiles: ProviderProfile[];
}

export interface ProviderConnectionRequest {
    provider_type: ProviderType;
    display_name?: string | null;
    base_url?: string | null;
    model_name?: string | null;
    api_key?: string | null;
    config_json?: Record<string, unknown>;
}

export interface ProviderConnectionResult {
    ok: boolean;
    provider_type: ProviderType;
    message: string;
    discovered_models: string[];
}

export interface ModelDiscoveryResult {
    models: string[];
    provider_type: ProviderType;
    normalized_base_url?: string | null;
}

export interface UpsertProviderProfileRequest extends ProviderConnectionRequest {
    display_name: string;
    storage_mode: CredentialStorageMode;
}

export interface LocalProviderProfile {
    profile_id: string;
    provider_type: ProviderType;
    display_name: string;
    base_url?: string | null;
    model_name?: string | null;
    api_key?: string | null;
    config_json: Record<string, unknown>;
}

/**
 * 兼容旧请求类型保留。V1.6.34 起前端不再发送本地 Provider 覆盖，
 * Provider 配置必须走内置云端或账号级加密配置。
 */
export interface LocalProviderOverride {
    profile_id?: string | null;
    provider_type: ProviderType;
    display_name?: string | null;
    base_url?: string | null;
    model_name?: string | null;
    api_key?: string | null;
    config_json?: Record<string, unknown>;
}
