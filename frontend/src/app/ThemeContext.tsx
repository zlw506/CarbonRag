import { type PropsWithChildren, createContext, useContext, useEffect, useMemo, useState } from "react";
import { App as AntdApp, ConfigProvider, theme as antdTheme } from "antd";

export type ThemeMode = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

interface ThemeContextValue {
    themeMode: ThemeMode;
    resolvedTheme: ResolvedTheme;
    setThemeMode: (mode: ThemeMode) => void;
}

const STORAGE_KEY = "carbonrag-theme-mode";
const ThemeContext = createContext<ThemeContextValue | null>(null);

function resolveSystemTheme(): ResolvedTheme {
    if (typeof window === "undefined") {
        return "light";
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function readStoredThemeMode(): ThemeMode {
    if (typeof window === "undefined") {
        return "system";
    }
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark" || stored === "system") {
        return stored;
    }
    return "system";
}

export function ThemeProvider({ children }: PropsWithChildren) {
    const [themeMode, setThemeMode] = useState<ThemeMode>(() => readStoredThemeMode());
    const [systemTheme, setSystemTheme] = useState<ResolvedTheme>(() => resolveSystemTheme());

    useEffect(() => {
        if (typeof window === "undefined") {
            return;
        }
        const media = window.matchMedia("(prefers-color-scheme: dark)");
        const legacyMedia = media as MediaQueryList & {
            addListener?: (listener: (event: MediaQueryListEvent) => void) => void;
            removeListener?: (listener: (event: MediaQueryListEvent) => void) => void;
        };
        const update = (matches: boolean) => setSystemTheme(matches ? "dark" : "light");

        update(media.matches);

        const listener = (event: MediaQueryListEvent) => update(event.matches);
        if ("addEventListener" in media) {
            media.addEventListener("change", listener);
            return () => media.removeEventListener("change", listener);
        }

        legacyMedia.addListener?.(listener);
        return () => legacyMedia.removeListener?.(listener);
    }, []);

    const resolvedTheme: ResolvedTheme = themeMode === "system" ? systemTheme : themeMode;

    useEffect(() => {
        if (typeof window === "undefined") {
            return;
        }
        window.localStorage.setItem(STORAGE_KEY, themeMode);
    }, [themeMode]);

    useEffect(() => {
        if (typeof document === "undefined") {
            return;
        }
        document.documentElement.dataset.theme = resolvedTheme;
        document.documentElement.style.colorScheme = resolvedTheme;
    }, [resolvedTheme]);

    const themeConfig = useMemo(
        () => ({
            algorithm: resolvedTheme === "dark" ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
            token: {
                colorPrimary: "#1677ff",
                borderRadius: 16,
            },
        }),
        [resolvedTheme],
    );

    const contextValue = useMemo<ThemeContextValue>(
        () => ({
            themeMode,
            resolvedTheme,
            setThemeMode,
        }),
        [resolvedTheme, themeMode],
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
