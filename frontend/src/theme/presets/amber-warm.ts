import { amber, amberDark, bronze, bronzeDark, orange, orangeDark } from "@radix-ui/colors";
import { buildThemeVariant, createThemePreset } from "../tokens";

export const amberWarmTheme = createThemePreset({
    id: "amber-warm",
    label: "琥珀暖调",
    description: "更偏文档阅读和报告查看的暖色主题。",
    preview: ["#D97706", "#92400E", "#FEF3C7", "#FFFBEB"],
    light: buildThemeVariant({
        appearance: "light",
        neutral: bronze,
        neutralPrefix: "bronze",
        accent: amber,
        accentPrefix: "amber",
        warning: orange,
        warningPrefix: "orange",
        overrides: {
            pageStart: "#FFFBEB",
            pageEnd: "#FEF3C7",
            focusEnd: "#FFF7D6",
            siderBg: "#451A03",
            text: "#451A03",
            textSecondary: "#78350F",
        },
    }),
    dark: buildThemeVariant({
        appearance: "dark",
        neutral: bronzeDark,
        neutralPrefix: "bronze",
        accent: amberDark,
        accentPrefix: "amber",
        warning: orangeDark,
        warningPrefix: "orange",
        overrides: {
            pageStart: "#261606",
            pageEnd: "#3A1F08",
            focusEnd: "#2F1906",
            siderBg: "#1C1004",
        },
    }),
});
