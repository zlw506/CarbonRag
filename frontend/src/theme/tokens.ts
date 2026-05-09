export type ThemeMode = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

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

export interface ThemeScale {
    [key: string]: string;
}

export interface ThemeSemanticTokens {
    background: string;
    backgroundSecondary: string;
    pageStart: string;
    pageEnd: string;
    pageRadial: string;
    focusEnd: string;
    focusRadial: string;
    surface: string;
    surfaceStrong: string;
    surfaceMuted: string;
    surfaceElevated: string;
    surfaceOverlay: string;
    border: string;
    borderStrong: string;
    text: string;
    textSecondary: string;
    textInverse: string;
    primary: string;
    primaryHover: string;
    primaryActive: string;
    primarySoft: string;
    primaryGlow: string;
    info: string;
    success: string;
    warning: string;
    error: string;
    siderBg: string;
    siderSurface: string;
    siderText: string;
    siderTextSecondary: string;
    siderTriggerBorder: string;
    sessionItemBg: string;
    sessionItemHoverBg: string;
    sessionItemHoverBorder: string;
    sessionActiveBg: string;
    sessionMiniBg: string;
    sessionMiniText: string;
    chatUserBubble: string;
    chatUserBubbleAlt: string;
    chatUserBubbleText: string;
    chatAssistantBubble: string;
    systemBg: string;
    thinkingBg: string;
    composerBg: string;
    contextCoreBg: string;
    contextCoreText: string;
    evidencePublic: string;
    evidencePrivate: string;
    evidenceCarbon: string;
    thinkingGlow: string;
    shadowSoft: string;
    shadowMedium: string;
    shadowStrong: string;
}

export interface ThemePreset {
    id: ThemePresetId;
    label: string;
    description: string;
    preview: [string, string, string, string];
    light: ThemeSemanticTokens;
    dark: ThemeSemanticTokens;
}

interface BuildThemeVariantOptions {
    appearance: ResolvedTheme;
    neutral: ThemeScale;
    neutralPrefix: string;
    accent: ThemeScale;
    accentPrefix: string;
    info?: ThemeScale;
    infoPrefix?: string;
    success?: ThemeScale;
    successPrefix?: string;
    warning?: ThemeScale;
    warningPrefix?: string;
    error?: ThemeScale;
    errorPrefix?: string;
    overrides?: Partial<ThemeSemanticTokens>;
}

export function createThemePreset(preset: ThemePreset): ThemePreset {
    return preset;
}

export function buildThemeVariant(options: BuildThemeVariantOptions): ThemeSemanticTokens {
    const {
        appearance,
        neutral,
        neutralPrefix,
        accent,
        accentPrefix,
        info = accent,
        infoPrefix = accentPrefix,
        success = accent,
        successPrefix = accentPrefix,
        warning = accent,
        warningPrefix = accentPrefix,
        error = accent,
        errorPrefix = accentPrefix,
        overrides,
    } = options;

    const bg1 = getScale(neutral, neutralPrefix, 1);
    const bg2 = getScale(neutral, neutralPrefix, 2);
    const bg3 = getScale(neutral, neutralPrefix, 3);
    const borderBase = getScale(neutral, neutralPrefix, 6);
    const text = getScale(neutral, neutralPrefix, 12);
    const textSecondary = getScale(neutral, neutralPrefix, 11);
    const primary = getScale(accent, accentPrefix, 9);
    const primaryHover = getScale(accent, accentPrefix, 10);
    const primaryActive = getScale(accent, accentPrefix, 11);

    const tokens: ThemeSemanticTokens = {
        background: bg1,
        backgroundSecondary: bg2,
        pageStart: bg1,
        pageEnd: bg2,
        pageRadial: withAlpha(primary, appearance === "dark" ? 0.18 : 0.12),
        focusEnd: bg2,
        focusRadial: withAlpha(primary, appearance === "dark" ? 0.24 : 0.1),
        surface: withAlpha(bg1, appearance === "dark" ? 0.92 : 0.88),
        surfaceStrong: withAlpha(bg1, appearance === "dark" ? 0.98 : 0.96),
        surfaceMuted: withAlpha(bg2, appearance === "dark" ? 0.84 : 0.92),
        surfaceElevated: bg2,
        surfaceOverlay: withAlpha(bg1, 0.92),
        border: withAlpha(borderBase, appearance === "dark" ? 0.36 : 0.22),
        borderStrong: withAlpha(primaryHover, 0.62),
        text,
        textSecondary,
        textInverse: "#f8fafc",
        primary,
        primaryHover,
        primaryActive,
        primarySoft: withAlpha(primary, appearance === "dark" ? 0.18 : 0.12),
        primaryGlow: withAlpha(primary, appearance === "dark" ? 0.42 : 0.22),
        info: getScale(info, infoPrefix, 9),
        success: getScale(success, successPrefix, 9),
        warning: getScale(warning, warningPrefix, 9),
        error: getScale(error, errorPrefix, 9),
        siderBg: appearance === "dark" ? bg1 : text,
        siderSurface: appearance === "dark" ? withAlpha(bg2, 0.92) : withAlpha("#ffffff", 0.08),
        siderText: "#f8fafc",
        siderTextSecondary: withAlpha("#f8fafc", 0.82),
        siderTriggerBorder: withAlpha(primaryHover, appearance === "dark" ? 0.26 : 0.18),
        sessionItemBg: "transparent",
        sessionItemHoverBg: appearance === "dark" ? withAlpha("#f8fafc", 0.08) : withAlpha(text, 0.07),
        sessionItemHoverBorder: "transparent",
        sessionActiveBg: appearance === "dark" ? withAlpha("#f8fafc", 0.13) : withAlpha(text, 0.1),
        sessionMiniBg: `linear-gradient(180deg, ${withAlpha(getScale(accent, accentPrefix, appearance === "dark" ? 9 : 4), appearance === "dark" ? 0.42 : 0.16)}, ${withAlpha(
            getScale(accent, accentPrefix, appearance === "dark" ? 11 : 6),
            appearance === "dark" ? 0.9 : 0.24,
        )})`,
        sessionMiniText: appearance === "dark" ? "#eff6ff" : text,
        chatUserBubble: withAlpha(getScale(accent, accentPrefix, appearance === "dark" ? 4 : 3), appearance === "dark" ? 0.36 : 0.42),
        chatUserBubbleAlt: withAlpha(getScale(accent, accentPrefix, appearance === "dark" ? 5 : 4), appearance === "dark" ? 0.48 : 0.52),
        chatUserBubbleText: text,
        chatAssistantBubble: `linear-gradient(180deg, ${withAlpha(bg1, 0.98)}, ${withAlpha(bg3, appearance === "dark" ? 0.94 : 0.92)})`,
        systemBg: withAlpha(getScale(neutral, neutralPrefix, appearance === "dark" ? 5 : 8), appearance === "dark" ? 0.56 : 0.08),
        thinkingBg: withAlpha(getScale(accent, accentPrefix, appearance === "dark" ? 4 : 3), appearance === "dark" ? 0.88 : 0.72),
        composerBg: withAlpha(bg1, 0.92),
        contextCoreBg: appearance === "dark" ? bg1 : "#ffffff",
        contextCoreText: primary,
        evidencePublic: primary,
        evidencePrivate: getScale(success, successPrefix, 9),
        evidenceCarbon: getScale(warning, warningPrefix, 9),
        thinkingGlow: primary,
        shadowSoft: shadow(withAlpha("#0f172a", appearance === "dark" ? 0.42 : 0.1), "0 14px 30px"),
        shadowMedium: shadow(withAlpha("#0f172a", appearance === "dark" ? 0.46 : 0.06), "0 18px 42px"),
        shadowStrong: shadow(withAlpha("#0f172a", appearance === "dark" ? 0.56 : 0.14), "0 20px 54px"),
    };

    return { ...tokens, ...overrides };
}

export function buildCssVariables(tokens: ThemeSemanticTokens) {
    return {
        "--cr-text-primary": tokens.text,
        "--cr-text-secondary": tokens.textSecondary,
        "--cr-page-radial": tokens.pageRadial,
        "--cr-page-start": tokens.pageStart,
        "--cr-page-end": tokens.pageEnd,
        "--cr-focus-radial": tokens.focusRadial,
        "--cr-focus-end": tokens.focusEnd,
        "--cr-sider-bg": tokens.siderBg,
        "--cr-sider-surface": tokens.siderSurface,
        "--cr-sider-text": tokens.siderText,
        "--cr-sider-text-secondary": tokens.siderTextSecondary,
        "--cr-sider-trigger-border": tokens.siderTriggerBorder,
        "--cr-surface": tokens.surface,
        "--cr-surface-strong": tokens.surfaceStrong,
        "--cr-surface-muted": tokens.surfaceMuted,
        "--cr-surface-elevated": tokens.surfaceElevated,
        "--cr-surface-overlay": tokens.surfaceOverlay,
        "--cr-border": tokens.border,
        "--cr-border-strong": tokens.borderStrong,
        "--cr-primary": tokens.primary,
        "--cr-primary-hover": tokens.primaryHover,
        "--cr-primary-active": tokens.primaryActive,
        "--cr-primary-soft": tokens.primarySoft,
        "--cr-primary-glow": tokens.primaryGlow,
        "--cr-session-item-bg": tokens.sessionItemBg,
        "--cr-session-item-hover-bg": tokens.sessionItemHoverBg,
        "--cr-session-item-hover-border": tokens.sessionItemHoverBorder,
        "--cr-session-mini-bg": tokens.sessionMiniBg,
        "--cr-session-mini-text": tokens.sessionMiniText,
        "--cr-session-active-bg": tokens.sessionActiveBg,
        "--cr-assistant-bg": tokens.chatAssistantBubble,
        "--cr-user-bubble": tokens.chatUserBubble,
        "--cr-user-bubble-alt": tokens.chatUserBubbleAlt,
        "--cr-user-bubble-text": tokens.chatUserBubbleText,
        "--cr-system-bg": tokens.systemBg,
        "--cr-thinking-bg": tokens.thinkingBg,
        "--cr-composer-bg": tokens.composerBg,
        "--cr-context-core-bg": tokens.contextCoreBg,
        "--cr-context-core-text": tokens.contextCoreText,
        "--cr-evidence-public": tokens.evidencePublic,
        "--cr-evidence-private": tokens.evidencePrivate,
        "--cr-evidence-carbon": tokens.evidenceCarbon,
        "--cr-thinking-glow": tokens.thinkingGlow,
        "--cr-shadow-soft": tokens.shadowSoft,
        "--cr-shadow-medium": tokens.shadowMedium,
        "--cr-shadow-strong": tokens.shadowStrong,
    } satisfies Record<string, string>;
}

function getScale(scale: ThemeScale, prefix: string, step: number) {
    const value = scale[`${prefix}${step}`];
    if (!value) {
        throw new Error(`Missing theme scale value: ${prefix}${step}`);
    }
    return value;
}

export function withAlpha(color: string, alpha: number) {
    const normalized = color.replace("#", "");
    const full = normalized.length === 3
        ? normalized.split("").map((char) => `${char}${char}`).join("")
        : normalized;
    const red = Number.parseInt(full.slice(0, 2), 16);
    const green = Number.parseInt(full.slice(2, 4), 16);
    const blue = Number.parseInt(full.slice(4, 6), 16);
    return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}

function shadow(color: string, offset: string) {
    return `${offset} ${color}`;
}
