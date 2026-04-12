import { type PropsWithChildren, createContext, useContext, useEffect, useLayoutEffect, useMemo, useState } from "react";
import { App as AntdApp, ConfigProvider } from "antd";
import { mapThemeToAntd } from "./antd-map";
import { getThemePreset, quickThemePresetIds, themePresets } from "./presets";
import {
    type ResolvedTheme,
    type ThemeMode,
    type ThemePreset,
    type ThemePresetId,
    buildCssVariables,
} from "./tokens";
import {
    readStoredThemeMode,
    readStoredThemePreset,
    writeStoredThemeMode,
    writeStoredThemePreset,
} from "./storage";

interface ThemeContextValue {
    themeMode: ThemeMode;
    resolvedTheme: ResolvedTheme;
    themePreset: ThemePresetId;
    activePreset: ThemePreset;
    quickPresets: ThemePreset[];
    allPresets: typeof themePresets;
    setThemeMode: (mode: ThemeMode) => void;
    setThemePreset: (presetId: ThemePresetId) => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function resolveSystemTheme(): ResolvedTheme {
    if (typeof window === "undefined") {
        return "light";
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }: PropsWithChildren) {
    const [themeMode, setThemeMode] = useState<ThemeMode>(() => readStoredThemeMode());
    const [themePreset, setThemePreset] = useState<ThemePresetId>(() => readStoredThemePreset());
    const [systemTheme, setSystemTheme] = useState<ResolvedTheme>(() => resolveSystemTheme());

    useEffect(() => {
        if (typeof window === "undefined") {
            return;
        }
        const media = window.matchMedia("(prefers-color-scheme: dark)");
        const update = (matches: boolean) => setSystemTheme(matches ? "dark" : "light");
        update(media.matches);
        const listener = (event: MediaQueryListEvent) => update(event.matches);
        media.addEventListener("change", listener);
        return () => media.removeEventListener("change", listener);
    }, []);

    useEffect(() => {
        if (typeof window === "undefined") {
            return;
        }

        const handleStorage = (event: StorageEvent) => {
            if (event.key === null || event.key === "carbonrag-theme-mode") {
                setThemeMode(readStoredThemeMode());
            }
            if (event.key === null || event.key === "carbonrag-theme-preset") {
                setThemePreset(readStoredThemePreset());
            }
        };

        window.addEventListener("storage", handleStorage);
        return () => window.removeEventListener("storage", handleStorage);
    }, []);

    const resolvedTheme = themeMode === "system" ? systemTheme : themeMode;
    const activePreset = useMemo(() => getThemePreset(themePreset), [themePreset]);
    const activeTokens = resolvedTheme === "dark" ? activePreset.dark : activePreset.light;
    const quickPresets = useMemo(
        () => quickThemePresetIds.map((presetId) => getThemePreset(presetId)),
        [],
    );

    useEffect(() => {
        writeStoredThemeMode(themeMode);
    }, [themeMode]);

    useEffect(() => {
        writeStoredThemePreset(themePreset);
    }, [themePreset]);

    useLayoutEffect(() => {
        if (typeof document === "undefined") {
            return;
        }
        const root = document.documentElement;
        root.dataset.theme = resolvedTheme;
        root.dataset.themeMode = themeMode;
        root.dataset.themePreset = activePreset.id;
        root.style.colorScheme = resolvedTheme;
        const cssVariables = buildCssVariables(activeTokens);
        Object.entries(cssVariables).forEach(([key, value]) => root.style.setProperty(key, value));
    }, [activePreset.id, activeTokens, resolvedTheme, themeMode]);

    const themeConfig = useMemo(
        () => mapThemeToAntd(activeTokens, resolvedTheme),
        [activeTokens, resolvedTheme],
    );

    const contextValue = useMemo<ThemeContextValue>(
        () => ({
            themeMode,
            resolvedTheme,
            themePreset,
            activePreset,
            quickPresets,
            allPresets: themePresets,
            setThemeMode,
            setThemePreset,
        }),
        [activePreset, quickPresets, resolvedTheme, themeMode, themePreset],
    );

    return (
        <ThemeContext.Provider value={contextValue}>
            <ConfigProvider theme={themeConfig}>
                <AntdApp>{children}</AntdApp>
            </ConfigProvider>
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error("useTheme must be used within ThemeProvider");
    }
    return context;
}
