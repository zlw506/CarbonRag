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
    LocalProviderOverride,
    LocalProviderProfile,
    ProviderListResponse,
    ProviderProfile,
    UpdateUserSettingsRequest,
    UpsertProviderProfileRequest,
    UserSettingsEnvelope,
} from "../types/settings";

const LOCAL_PROVIDER_STORAGE_KEY = "carbonrag-local-provider-profiles";

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
        root.dataset.chatDensity = settings.appearance.bubble_density;
        root.dataset.fontScale = settings.appearance.font_size;
        root.dataset.sidebarDefault = settings.appearance.sidebar_default;
    }, [settings]);

    async function refresh() {
        if (!user) {
            return;
        }
        setLoading(true);
        try {
            const [nextSettings, nextProviders] = await Promise.all([getSettings(), listProviderProfiles()]);
            setSettings(nextSettings);
            setProviderList(nextProviders);
        } finally {
            setLoading(false);
        }
    }

    async function saveSettings(payload: UpdateUserSettingsRequest) {
        const next = await patchSettings(payload);
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
