import { amber, amberDark, blue, blueDark, indigo, indigoDark, slate, slateDark } from "@radix-ui/colors";
import { buildThemeVariant, createThemePreset } from "../tokens";

export const indigoFocusTheme = createThemePreset({
    id: "indigo-focus",
    label: "靛蓝专注",
    description: "偏 AI 工具与深度思考的冷色主题。",
    preview: ["#4F46E5", "#312E81", "#C7D2FE", "#F5F7FF"],
    light: buildThemeVariant({
        appearance: "light",
        neutral: slate,
        neutralPrefix: "slate",
        accent: indigo,
        accentPrefix: "indigo",
        info: blue,
        infoPrefix: "blue",
        warning: amber,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#F5F7FF",
            pageEnd: "#EEF2FF",
            focusEnd: "#EEF2FF",
            siderBg: "#1E1B4B",
        },
    }),
    dark: buildThemeVariant({
        appearance: "dark",
        neutral: slateDark,
        neutralPrefix: "slate",
        accent: indigoDark,
        accentPrefix: "indigo",
        info: blueDark,
        infoPrefix: "blue",
        warning: amberDark,
        warningPrefix: "amber",
        overrides: {
            pageStart: "#12163A",
            pageEnd: "#181F52",
            focusEnd: "#11183F",
            siderBg: "#0B102B",
        },
    }),
});
