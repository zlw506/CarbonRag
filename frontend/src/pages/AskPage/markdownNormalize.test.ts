import { describe, expect, it } from "vitest";
import { normalizeAssistantMarkdown } from "./markdownNormalize";

describe("normalizeAssistantMarkdown", () => {
    it("does not split decimals inside carbon accounting tables", () => {
        const input = [
            "| 排放源 | 消耗量 | 匹配碳因子 | 因子来源 | 排放量 |",
            "|---|---:|---:|---|---:|",
            "| 外购电力 | 4,860,000 kWh | 0.5306 kgCO2/kWh | 生态环境部、国家统计局 | 2,578.72 tCO2e |",
            "| 天然气 | 318,000 m³ | 2.184 kgCO2e/m³ | JS/T 303-2026 缺省因子 | 694.51 tCO2e |",
            "| 柴油 | 12,500 L | 0.718 kgCO2e/L | JS/T 303-2026 缺省因子 | 8.98 tCO2e |",
            "| 合计 | — | — | — | 3,307.20 tCO2e |",
        ].join("\n");

        const output = normalizeAssistantMarkdown(input);

        expect(output).toContain("2.184 kgCO2e/m³");
        expect(output).toContain("694.51 tCO2e");
        expect(output).toContain("0.718 kgCO2e/L");
        expect(output).toContain("8.98 tCO2e");
        expect(output).toContain("3,307.20 tCO2e");
        expect(output).not.toContain("2.\n184");
        expect(output).not.toContain("694.\n51");
        expect(output).not.toContain("0.\n718");
        expect(output).not.toContain("8.\n98");
    });

    it("still repairs plain ordered lists that use number dot space", () => {
        const output = normalizeAssistantMarkdown("说明如下 1. 第一项 2. 第二项");

        expect(output).toContain("说明如下\n1. 第一项\n2. 第二项");
    });

    it("keeps fenced code blocks unchanged", () => {
        const input = [
            "```text",
            "2.184 kgCO2e/m³",
            "1. code item",
            "```",
        ].join("\n");

        expect(normalizeAssistantMarkdown(input)).toBe(input);
    });

    it("does not split decimals in plain text", () => {
        const output = normalizeAssistantMarkdown("天然气因子为 2.184 kgCO2e/m³，柴油因子为 0.718 kgCO2e/L。");

        expect(output).toContain("2.184 kgCO2e/m³");
        expect(output).toContain("0.718 kgCO2e/L");
        expect(output).not.toContain("2.\n184");
        expect(output).not.toContain("0.\n718");
    });
});
