import type { ThemeConfig } from "antd";
import { theme as antdTheme } from "antd";
import type { ResolvedTheme, ThemeSemanticTokens } from "./tokens";

export function mapThemeToAntd(tokens: ThemeSemanticTokens, resolvedTheme: ResolvedTheme): ThemeConfig {
    return {
        algorithm: resolvedTheme === "dark" ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        token: {
            colorPrimary: tokens.primary,
            colorInfo: tokens.info,
            colorSuccess: tokens.success,
            colorWarning: tokens.warning,
            colorError: tokens.error,
            colorBgBase: tokens.background,
            colorBgContainer: tokens.surfaceStrong,
            colorBgElevated: tokens.surfaceElevated,
            colorBorder: tokens.border,
            colorText: tokens.text,
            colorTextSecondary: tokens.textSecondary,
            borderRadius: 18,
            wireframe: false,
            boxShadow: tokens.shadowSoft,
            boxShadowSecondary: tokens.shadowMedium,
        },
        components: {
            Layout: {
                bodyBg: "transparent",
                siderBg: tokens.siderBg,
                triggerBg: tokens.siderBg,
            },
            Menu: {
                itemBg: "transparent",
                itemColor: tokens.siderTextSecondary,
                itemHoverColor: tokens.siderText,
                itemSelectedColor: tokens.siderText,
                itemSelectedBg: tokens.primarySoft,
                subMenuItemBg: "transparent",
            },
            Card: {
                colorBgContainer: tokens.surfaceStrong,
                borderRadiusLG: 24,
            },
            Drawer: {
                colorBgElevated: tokens.surfaceOverlay,
            },
            Button: {
                borderRadius: 16,
                defaultBg: tokens.surfaceStrong,
                defaultBorderColor: tokens.border,
                defaultColor: tokens.text,
                primaryShadow: `0 12px 24px ${tokens.primaryGlow}`,
            },
            Input: {
                borderRadius: 16,
                activeBorderColor: tokens.primary,
                hoverBorderColor: tokens.primaryHover,
                activeShadow: `0 0 0 2px ${tokens.primarySoft}`,
            },
            Tag: {
                borderRadiusSM: 999,
            },
            Segmented: {
                itemSelectedBg: tokens.surfaceStrong,
                trackBg: tokens.surfaceMuted,
            },
        },
    };
}
