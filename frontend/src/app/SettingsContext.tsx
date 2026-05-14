import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { PropsWithChildren } from "react";
import { useAuth } from "./AuthContext";
import {
    createProviderProfile,
    deleteProviderProfile,
    getSettings,
    listProviderProfiles,
    patchSettings,
    updateProviderProfile,
} from "../services/settings";
import { useTheme } from "./ThemeContext";
import type {
    AppearanceSettings,
    ChatPreferenceSettings,
    DataPrivacySettings,
    AdvancedSettings,
    ProviderListResponse,
    ProviderProfile,
    UpdateUserSettingsRequest,
    UpsertProviderProfileRequest,
    UserSettingsEnvelope,
} from "../types/settings";

const BUILTIN_PROVIDER_REF = "builtin:carbonrag-cloud";

const DEFAULT_APPEARANCE_SETTINGS: AppearanceSettings = {
    theme_mode: "system",
    theme_preset: "carbon-blue",
    bubble_density: "comfortable",
    font_size: "default",
    sidebar_default: "expanded",
};

const DEFAULT_CHAT_SETTINGS: ChatPreferenceSettings = {
    send_shortcut: "enter",
    expand_thinking_by_default: false,
    show_evidence_panel_by_default: false,
    show_context_debug_by_default: false,
    auto_generate_title_for_new_session: true,
    reconnect_notice_mode: "message_only",
};

const DEFAULT_DATA_PRIVACY_SETTINGS: DataPrivacySettings = {
    store_local_provider_keys_in_browser: false,
    allow_account_saved_provider_keys: true,
};

const DEFAULT_ADVANCED_SETTINGS: AdvancedSettings = {
    local_provider_profile_ids: [],
};

interface SettingsContextValue {
    settings: UserSettingsEnvelope | null;
    providerList: ProviderListResponse | null;
    loading: boolean;
    refresh: () => Promise<void>;
    saveSettings: (payload: UpdateUserSettingsRequest) => Promise<UserSettingsEnvelope>;
    createAccountProviderProfile: (payload: UpsertProviderProfileRequest) => Promise<ProviderProfile>;
    updateAccountProviderProfile: (profileId: string, payload: UpsertProviderProfileRequest) => Promise<ProviderProfile>;
    deleteAccountProviderProfile: (profileId: string) => Promise<void>;
    getActiveProviderOverride: () => undefined;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

function normalizeSettingsEnvelope(settings: UserSettingsEnvelope | null | undefined): UserSettingsEnvelope {
    const activeProviderRef = settings?.active_provider_ref?.startsWith("local:")
        ? BUILTIN_PROVIDER_REF
        : settings?.active_provider_ref || BUILTIN_PROVIDER_REF;
    return {
        appearance: {
            ...DEFAULT_APPEARANCE_SETTINGS,
            ...(settings?.appearance ?? {}),
        },
        chat: {
            ...DEFAULT_CHAT_SETTINGS,
            ...(settings?.chat ?? {}),
        },
        data_privacy: {
            ...DEFAULT_DATA_PRIVACY_SETTINGS,
            ...(settings?.data_privacy ?? {}),
        },
        advanced: {
            ...DEFAULT_ADVANCED_SETTINGS,
            ...(settings?.advanced ?? {}),
            local_provider_profile_ids: [],
        },
        active_provider_ref: activeProviderRef,
    };
}

function buildProviderListFallback(activeProviderRef: string): ProviderListResponse {
    return {
        builtin_provider_refs: [BUILTIN_PROVIDER_REF],
        active_provider_ref: activeProviderRef || BUILTIN_PROVIDER_REF,
        profiles: [],
    };
}

export function SettingsProvider({ children }: PropsWithChildren) {
    const { user } = useAuth();
    const { setThemeMode, setThemePreset } = useTheme();
    const [settings, setSettings] = useState<UserSettingsEnvelope | null>(null);
    const [providerList, setProviderList] = useState<ProviderListResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) {
            setSettings(null);
            setProviderList(null);
            setThemeMode(DEFAULT_APPEARANCE_SETTINGS.theme_mode);
            setThemePreset(DEFAULT_APPEARANCE_SETTINGS.theme_preset);
            setLoading(false);
            return;
        }
        void refresh();
    }, [user?.user_id]);

    useEffect(() => {
        const root = document.documentElement;
        if (!settings) {
            root.dataset.chatDensity = "comfortable";
            root.dataset.fontScale = "default";
            root.dataset.sidebarDefault = "expanded";
            return;
        }
        const normalized = normalizeSettingsEnvelope(settings);
        setThemeMode(normalized.appearance.theme_mode);
        setThemePreset(normalized.appearance.theme_preset);
        root.dataset.chatDensity = normalized.appearance.bubble_density;
        root.dataset.fontScale = normalized.appearance.font_size;
        root.dataset.sidebarDefault = normalized.appearance.sidebar_default;
    }, [settings]);

    async function refresh() {
        if (!user) {
            return;
        }
        setLoading(true);
        try {
            const nextSettings = normalizeSettingsEnvelope(await getSettings());
            setThemeMode(nextSettings.appearance.theme_mode);
            setThemePreset(nextSettings.appearance.theme_preset);
            setSettings(nextSettings);
            try {
                const nextProviders = await listProviderProfiles();
                const nextActiveProviderRef = nextProviders.active_provider_ref?.startsWith("local:")
                    ? BUILTIN_PROVIDER_REF
                    : nextProviders.active_provider_ref || nextSettings.active_provider_ref;
                setProviderList({
                    builtin_provider_refs: nextProviders.builtin_provider_refs?.length
                        ? nextProviders.builtin_provider_refs
                        : [BUILTIN_PROVIDER_REF],
                    active_provider_ref: nextActiveProviderRef,
                    profiles: Array.isArray(nextProviders.profiles) ? nextProviders.profiles : [],
                });
            } catch {
                setProviderList(buildProviderListFallback(nextSettings.active_provider_ref));
            }
        } finally {
            setLoading(false);
        }
    }

    async function saveSettings(payload: UpdateUserSettingsRequest) {
        const normalizedPayload = {
            ...payload,
            active_provider_ref: payload.active_provider_ref?.startsWith("local:")
                ? BUILTIN_PROVIDER_REF
                : payload.active_provider_ref,
            advanced: payload.advanced
                ? { ...payload.advanced, local_provider_profile_ids: [] }
                : payload.advanced,
        };
        const next = normalizeSettingsEnvelope(await patchSettings(normalizedPayload));
        setThemeMode(next.appearance.theme_mode);
        setThemePreset(next.appearance.theme_preset);
        setSettings(next);
        setProviderList((current) =>
            current ? { ...current, active_provider_ref: next.active_provider_ref } : current,
        );
        return next;
    }

    async function createAccountProviderProfileInternal(payload: UpsertProviderProfileRequest) {
        const created = await createProviderProfile(payload);
        await refresh();
        return created;
    }

    async function updateAccountProviderProfileInternal(profileId: string, payload: UpsertProviderProfileRequest) {
        const updated = await updateProviderProfile(profileId, payload);
        await refresh();
        return updated;
    }

    async function deleteAccountProviderProfileInternal(profileId: string) {
        await deleteProviderProfile(profileId);
        await refresh();
    }

    function getActiveProviderOverride() {
        return undefined;
    }

    const value = useMemo<SettingsContextValue>(
        () => ({
            settings,
            providerList,
            loading,
            refresh,
            saveSettings,
            createAccountProviderProfile: createAccountProviderProfileInternal,
            updateAccountProviderProfile: updateAccountProviderProfileInternal,
            deleteAccountProviderProfile: deleteAccountProviderProfileInternal,
            getActiveProviderOverride,
        }),
        [settings, providerList, loading],
    );

    return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings() {
    const context = useContext(SettingsContext);
    if (!context) {
        throw new Error("useSettings must be used within SettingsProvider.");
    }
    return context;
}
