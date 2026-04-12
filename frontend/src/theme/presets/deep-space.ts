import { amber, amberDark, blue, blueDark, gray, grayDark, green, greenDark } from "@radix-ui/colors";
import { buildThemeVariant, createThemePreset } from "../tokens";

export const deepSpaceTheme = createThemePreset({
    id: "deep-space",
    label: "深空",
    description: "高对比、夜间高专注的深色主题。",
    preview: ["#4C8DFF", "#0B1220", "#172033", "#E5EEF8"],
    light: buildThemeVariant({
        appearance: "light",
        neutral: gray,
        neutralPrefix: "gray",
        accent: blue,
        accentPrefix: "blue",
        success: green,
        successPrefix: "green",
        warning: amber,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#EEF3F8",
            pageEnd: "#DCE7F4",
            focusEnd: "#E6EEF8",
            siderBg: "#111827",
            surfaceStrong: "rgba(255,255,255,0.94)",
        },
    }),
    dark: buildThemeVariant({
        appearance: "dark",
        neutral: grayDark,
        neutralPrefix: "gray",
        accent: blueDark,
        accentPrefix: "blue",
        success: greenDark,
        successPrefix: "green",
        warning: amberDark,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#0B1220",
            pageEnd: "#111827",
            focusEnd: "#0F172A",
            siderBg: "#050B14",
        },
    }),
});
