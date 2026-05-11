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
import type {
    AppearanceSettings,
    ChatPreferenceSettings,
    DataPrivacySettings,
    AdvancedSettings,
    LocalProviderOverride,
    LocalProviderProfile,
    ProviderListResponse,
    ProviderProfile,
    UpdateUserSettingsRequest,
    UpsertProviderProfileRequest,
    UserSettingsEnvelope,
} from "../types/settings";

const LOCAL_PROVIDER_STORAGE_KEY = "carbonrag-local-provider-profiles";
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
    store_local_provider_keys_in_browser: true,
    allow_account_saved_provider_keys: true,
};

const DEFAULT_ADVANCED_SETTINGS: AdvancedSettings = {
    local_provider_profile_ids: [],
};

interface SettingsContextValue {
    settings: UserSettingsEnvelope | null;
    providerList: ProviderListResponse | null;
    localProfiles: LocalProviderProfile[];
    loading: boolean;
    refresh: () => Promise<void>;
    saveSettings: (payload: UpdateUserSettingsRequest) => Promise<UserSettingsEnvelope>;
    createAccountProviderProfile: (payload: UpsertProviderProfileRequest) => Promise<ProviderProfile>;
    updateAccountProviderProfile: (profileId: string, payload: UpsertProviderProfileRequest) => Promise<ProviderProfile>;
    deleteAccountProviderProfile: (profileId: string) => Promise<void>;
    upsertLocalProfile: (profile: LocalProviderProfile) => Promise<void>;
    deleteLocalProfile: (profileId: string) => Promise<void>;
    getActiveProviderOverride: () => LocalProviderOverride | undefined;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

function readLocalProfiles(): LocalProviderProfile[] {
    if (typeof window === "undefined") {
        return [];
    }
    try {
        const raw = window.localStorage.getItem(LOCAL_PROVIDER_STORAGE_KEY);
        if (!raw) {
            return [];
        }
        const parsed = JSON.parse(raw) as LocalProviderProfile[];
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
}

function writeLocalProfiles(profiles: LocalProviderProfile[]) {
    if (typeof window === "undefined") {
        return;
    }
    window.localStorage.setItem(LOCAL_PROVIDER_STORAGE_KEY, JSON.stringify(profiles));
}

function normalizeSettingsEnvelope(settings: UserSettingsEnvelope | null | undefined): UserSettingsEnvelope {
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
            local_provider_profile_ids: Array.isArray(settings?.advanced?.local_provider_profile_ids)
                ? settings.advanced.local_provider_profile_ids
                : [],
        },
        active_provider_ref: settings?.active_provider_ref || BUILTIN_PROVIDER_REF,
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
    const [settings, setSettings] = useState<UserSettingsEnvelope | null>(null);
    const [providerList, setProviderList] = useState<ProviderListResponse | null>(null);
    const [localProfiles, setLocalProfiles] = useState<LocalProviderProfile[]>(() => readLocalProfiles());
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        writeLocalProfiles(localProfiles);
    }, [localProfiles]);

    useEffect(() => {
        if (!user) {
            setSettings(null);
            setProviderList(null);
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
            setSettings(nextSettings);
            try {
                const nextProviders = await listProviderProfiles();
                setProviderList({
                    builtin_provider_refs: nextProviders.builtin_provider_refs?.length
                        ? nextProviders.builtin_provider_refs
                        : [BUILTIN_PROVIDER_REF],
                    active_provider_ref: nextProviders.active_provider_ref || nextSettings.active_provider_ref,
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
        const next = normalizeSettingsEnvelope(await patchSettings(payload));
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

    async function upsertLocalProfile(profile: LocalProviderProfile) {
        const nextProfiles = [...localProfiles];
        const existingIndex = nextProfiles.findIndex((item) => item.profile_id === profile.profile_id);
        if (existingIndex >= 0) {
            nextProfiles[existingIndex] = profile;
        } else {
            nextProfiles.unshift(profile);
        }
        setLocalProfiles(nextProfiles);
        if (settings) {
            await saveSettings({
                advanced: {
                    ...settings.advanced,
                    local_provider_profile_ids: nextProfiles.map((item) => item.profile_id),
                },
            });
        }
    }

    async function deleteLocalProfileInternal(profileId: string) {
        const nextProfiles = localProfiles.filter((item) => item.profile_id !== profileId);
        setLocalProfiles(nextProfiles);
        if (settings) {
            const nextPayload: UpdateUserSettingsRequest = {
                advanced: {
                    ...settings.advanced,
                    local_provider_profile_ids: nextProfiles.map((item) => item.profile_id),
                },
            };
            if (settings.active_provider_ref === `local:${profileId}`) {
                nextPayload.active_provider_ref = "builtin:carbonrag-cloud";
            }
            await saveSettings(nextPayload);
        }
    }

    function getActiveProviderOverride() {
        const activeProviderRef = settings?.active_provider_ref;
        if (!activeProviderRef?.startsWith("local:")) {
            return undefined;
        }
        const profileId = activeProviderRef.split(":", 2)[1];
        const profile = localProfiles.find((item) => item.profile_id === profileId);
        if (!profile) {
            return undefined;
        }
        return {
            profile_id: profile.profile_id,
            provider_type: profile.provider_type,
            display_name: profile.display_name,
            base_url: profile.base_url,
            model_name: profile.model_name,
            api_key: profile.api_key,
            config_json: profile.config_json,
        } satisfies LocalProviderOverride;
    }

    const value = useMemo<SettingsContextValue>(
        () => ({
            settings,
            providerList,
            localProfiles,
            loading,
            refresh,
            saveSettings,
            createAccountProviderProfile: createAccountProviderProfileInternal,
            updateAccountProviderProfile: updateAccountProviderProfileInternal,
            deleteAccountProviderProfile: deleteAccountProviderProfileInternal,
            upsertLocalProfile,
            deleteLocalProfile: deleteLocalProfileInternal,
            getActiveProviderOverride,
        }),
        [settings, providerList, localProfiles, loading],
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
