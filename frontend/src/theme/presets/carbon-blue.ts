import { amber, amberDark, blue, blueDark, green, greenDark, slate, slateDark } from "@radix-ui/colors";
import { buildThemeVariant, createThemePreset } from "../tokens";

export const carbonBlueTheme = createThemePreset({
    id: "carbon-blue",
    label: "碳蓝",
    description: "专业、可信、冷静的默认主题。",
    preview: ["#1677FF", "#0F4C81", "#EEF4FF", "#F7FAFC"],
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
            pageStart: "#F7FAFC",
            pageEnd: "#EEF4FF",
            focusEnd: "#EEF4FF",
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
            pageStart: "#0B1220",
            pageEnd: "#111827",
            focusEnd: "#0C1729",
            siderBg: "#08101D",
        },
    }),
});
