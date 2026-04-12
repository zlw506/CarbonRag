import { amber, amberDark, blue, blueDark, green, greenDark, slate, slateDark } from "@radix-ui/colors";
import { buildThemeVariant, createThemePreset } from "../tokens";

export const slateNeutralTheme = createThemePreset({
    id: "slate-neutral",
    label: "石板中性",
    description: "低饱和、阅读优先、压低后台感。",
    preview: ["#475569", "#3B82F6", "#F8FAFC", "#F1F5F9"],
    light: buildThemeVariant({
        appearance: "light",
        neutral: slate,
        neutralPrefix: "slate",
        accent: blue,
        accentPrefix: "blue",
        success: green,
        successPrefix: "green",
        warning: amber,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#F8FAFC",
            pageEnd: "#F1F5F9",
            focusEnd: "#F1F5F9",
            siderBg: "#0F172A",
        },
    }),
    dark: buildThemeVariant({
        appearance: "dark",
        neutral: slateDark,
        neutralPrefix: "slate",
        accent: blueDark,
        accentPrefix: "blue",
        success: greenDark,
        successPrefix: "green",
        warning: amberDark,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#0F172A",
            pageEnd: "#111827",
            focusEnd: "#0F172A",
            siderBg: "#020617",
        },
    }),
});
