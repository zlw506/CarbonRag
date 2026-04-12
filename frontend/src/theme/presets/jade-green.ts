import { amber, amberDark, green, greenDark, jade, jadeDark, sage, sageDark } from "@radix-ui/colors";
import { buildThemeVariant, createThemePreset } from "../tokens";

export const jadeGreenTheme = createThemePreset({
    id: "jade-green",
    label: "玉绿",
    description: "更贴合双碳语义的绿色主题。",
    preview: ["#12B981", "#0F766E", "#D1FAE5", "#F3FCF8"],
    light: buildThemeVariant({
        appearance: "light",
        neutral: sage,
        neutralPrefix: "sage",
        accent: jade,
        accentPrefix: "jade",
        success: green,
        successPrefix: "green",
        warning: amber,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#F3FCF8",
            pageEnd: "#ECFDF5",
            focusEnd: "#ECFDF5",
            siderBg: "#083344",
        },
    }),
    dark: buildThemeVariant({
        appearance: "dark",
        neutral: sageDark,
        neutralPrefix: "sage",
        accent: jadeDark,
        accentPrefix: "jade",
        success: greenDark,
        successPrefix: "green",
        warning: amberDark,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#062A24",
            pageEnd: "#0B3B36",
            focusEnd: "#062F2A",
            siderBg: "#041B18",
        },
    }),
});
