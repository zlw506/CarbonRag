import type { ThemeMode, ThemePresetId } from "./tokens";

export const THEME_MODE_STORAGE_KEY = "carbonrag-theme-mode";
export const THEME_PRESET_STORAGE_KEY = "carbonrag-theme-preset";

export function readStoredThemeMode(): ThemeMode {
    if (typeof window === "undefined") {
        return "system";
    }
    const stored = window.localStorage.getItem(THEME_MODE_STORAGE_KEY);
    if (stored === "light" || stored === "dark" || stored === "system") {
        return stored;
    }
    return "system";
}

export function readStoredThemePreset(): ThemePresetId {
    if (typeof window === "undefined") {
        return "carbon-blue";
    }
    const stored = window.localStorage.getItem(THEME_PRESET_STORAGE_KEY);
    return isThemePresetId(stored) ? stored : "carbon-blue";
}

export function writeStoredThemeMode(mode: ThemeMode) {
    if (typeof window === "undefined") {
        return;
    }
    window.localStorage.setItem(THEME_MODE_STORAGE_KEY, mode);
}

export function writeStoredThemePreset(presetId: ThemePresetId) {
    if (typeof window === "undefined") {
        return;
    }
    window.localStorage.setItem(THEME_PRESET_STORAGE_KEY, presetId);
}

function isThemePresetId(value: string | null): value is ThemePresetId {
    return value === "carbon-blue" ||
        value === "deep-space" ||
        value === "slate-neutral" ||
        value === "jade-green" ||
        value === "teal-professional" ||
        value === "indigo-focus" ||
        value === "purple-research" ||
        value === "rose-humanized" ||
        value === "amber-warm" ||
        value === "graphite-pro";
}
