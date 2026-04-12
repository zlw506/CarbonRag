import { amber, amberDark, mauve, mauveDark, violet, violetDark } from "@radix-ui/colors";
import { buildThemeVariant, createThemePreset } from "../tokens";

export const purpleResearchTheme = createThemePreset({
    id: "purple-research",
    label: "研究紫",
    description: "更偏研究与智能助手个性的主题。",
    preview: ["#7C3AED", "#581C87", "#E9D5FF", "#FAF5FF"],
    light: buildThemeVariant({
        appearance: "light",
        neutral: mauve,
        neutralPrefix: "mauve",
        accent: violet,
        accentPrefix: "violet",
        warning: amber,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#FAF5FF",
            pageEnd: "#F5F3FF",
            focusEnd: "#F5F3FF",
            siderBg: "#3B0764",
        },
    }),
    dark: buildThemeVariant({
        appearance: "dark",
        neutral: mauveDark,
        neutralPrefix: "mauve",
        accent: violetDark,
        accentPrefix: "violet",
        warning: amberDark,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#210A34",
            pageEnd: "#30114A",
            focusEnd: "#240C3A",
            siderBg: "#160720",
        },
    }),
});
