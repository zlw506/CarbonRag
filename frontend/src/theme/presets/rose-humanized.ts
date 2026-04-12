import { amber, amberDark, ruby, rubyDark, slate, slateDark } from "@radix-ui/colors";
import { buildThemeVariant, createThemePreset } from "../tokens";

export const roseHumanizedTheme = createThemePreset({
    id: "rose-humanized",
    label: "玫瑰柔和",
    description: "更温和、亲近，降低后台系统感。",
    preview: ["#E11D48", "#9F1239", "#FFE4E6", "#FFF7F9"],
    light: buildThemeVariant({
        appearance: "light",
        neutral: slate,
        neutralPrefix: "slate",
        accent: ruby,
        accentPrefix: "ruby",
        warning: amber,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#FFF7F9",
            pageEnd: "#FFF1F2",
            focusEnd: "#FFF1F2",
            siderBg: "#4C0519",
        },
    }),
    dark: buildThemeVariant({
        appearance: "dark",
        neutral: slateDark,
        neutralPrefix: "slate",
        accent: rubyDark,
        accentPrefix: "ruby",
        warning: amberDark,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#2F0A16",
            pageEnd: "#431022",
            focusEnd: "#330C18",
            siderBg: "#1E070F",
        },
    }),
});
