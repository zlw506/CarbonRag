import { amber, amberDark, mint, mintDark, slate, slateDark, teal, tealDark } from "@radix-ui/colors";
import { buildThemeVariant, createThemePreset } from "../tokens";

export const tealProfessionalTheme = createThemePreset({
    id: "teal-professional",
    label: "专业青",
    description: "科技感更强的青绿色工作台主题。",
    preview: ["#0EA5A4", "#155E75", "#99F6E4", "#F0FDFA"],
    light: buildThemeVariant({
        appearance: "light",
        neutral: slate,
        neutralPrefix: "slate",
        accent: teal,
        accentPrefix: "teal",
        success: mint,
        successPrefix: "mint",
        warning: amber,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#F0FDFA",
            pageEnd: "#ECFEFF",
            focusEnd: "#ECFEFF",
            siderBg: "#134E4A",
        },
    }),
    dark: buildThemeVariant({
        appearance: "dark",
        neutral: slateDark,
        neutralPrefix: "slate",
        accent: tealDark,
        accentPrefix: "teal",
        success: mintDark,
        successPrefix: "mint",
        warning: amberDark,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#052A2C",
            pageEnd: "#0B3A40",
            focusEnd: "#0A2E34",
            siderBg: "#04181A",
        },
    }),
});
