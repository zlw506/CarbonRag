import { blue, blueDark, gray, grayDark, slate, slateDark } from "@radix-ui/colors";
import { buildThemeVariant, createThemePreset } from "../tokens";

export const graphiteProTheme = createThemePreset({
    id: "graphite-pro",
    label: "石墨专业",
    description: "克制、商务、适合长时间使用的高级灰主题。",
    preview: ["#334155", "#2563EB", "#E2E8F0", "#F8FAFC"],
    light: buildThemeVariant({
        appearance: "light",
        neutral: gray,
        neutralPrefix: "gray",
        accent: slate,
        accentPrefix: "slate",
        info: blue,
        infoPrefix: "blue",
        overrides: {
            pageStart: "#F8FAFC",
            pageEnd: "#F1F5F9",
            focusEnd: "#F1F5F9",
            siderBg: "#111827",
            primary: "#334155",
            primaryHover: "#1F2937",
            primaryActive: "#111827",
            primarySoft: "rgba(51, 65, 85, 0.12)",
            primaryGlow: "rgba(37, 99, 235, 0.22)",
        },
    }),
    dark: buildThemeVariant({
        appearance: "dark",
        neutral: grayDark,
        neutralPrefix: "gray",
        accent: slateDark,
        accentPrefix: "slate",
        info: blueDark,
        infoPrefix: "blue",
        overrides: {
            pageStart: "#0C111B",
            pageEnd: "#111827",
            focusEnd: "#0F172A",
            siderBg: "#060A11",
            primary: "#CBD5E1",
            primaryHover: "#E2E8F0",
            primaryActive: "#F8FAFC",
            primarySoft: "rgba(203, 213, 225, 0.18)",
            primaryGlow: "rgba(37, 99, 235, 0.24)",
        },
    }),
});
