import { amberWarmTheme } from "./amber-warm";
import { carbonBlueTheme } from "./carbon-blue";
import { deepSpaceTheme } from "./deep-space";
import { graphiteProTheme } from "./graphite-pro";
import { indigoFocusTheme } from "./indigo-focus";
import { jadeGreenTheme } from "./jade-green";
import { purpleResearchTheme } from "./purple-research";
import { roseHumanizedTheme } from "./rose-humanized";
import { slateNeutralTheme } from "./slate-neutral";
import { tealProfessionalTheme } from "./teal-professional";
import type { ThemePresetId } from "../tokens";

export const themePresets = [
    carbonBlueTheme,
    deepSpaceTheme,
    slateNeutralTheme,
    jadeGreenTheme,
    tealProfessionalTheme,
    indigoFocusTheme,
    purpleResearchTheme,
    roseHumanizedTheme,
    amberWarmTheme,
    graphiteProTheme,
];

export const quickThemePresetIds: ThemePresetId[] = [
    "carbon-blue",
    "deep-space",
    "jade-green",
    "indigo-focus",
];

export function getThemePreset(presetId: ThemePresetId) {
    return themePresets.find((preset) => preset.id === presetId) ?? carbonBlueTheme;
}
