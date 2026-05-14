export function normalizeAssistantMarkdown(content: string) {
    return content
        .split(/(```[\s\S]*?```)/g)
        .map((segment) => (segment.startsWith("```") ? segment : normalizeMarkdownTextSegment(segment)))
        .join("");
}

function normalizeMarkdownTextSegment(segment: string) {
    const normalizedLines = segment
        .split("\n")
        .map((line) => (isTableLikeLine(line) ? line : normalizePlainMarkdownLine(line)))
        .join("\n");
    const headingNormalized = normalizedLines.replace(/(^|\n)\s{0,3}#{1,6}\s*([^\n]+)/g, (_match, prefix: string, title: string) => {
        const cleanTitle = title.trim();
        return cleanTitle ? `${prefix}**${cleanTitle}**` : prefix;
    });
    return normalizeMalformedMarkdownTableRows(headingNormalized);
}

function normalizePlainMarkdownLine(line: string) {
    return line
        .replace(/^\s*#{1,6}\s+(?=\d+\.)/g, "")
        .replace(/^\s*[-*]\s*$/g, "")
        .replace(/([^\n])(\s+)(#{1,6})\s+(?=\S)/g, "$1\n\n$3 ")
        .replace(/([^\n])(\s*)(#{1,6})(?=\S)/g, "$1\n\n$3 ")
        .replace(/^(#{1,6})(?=\S)/g, "$1 ")
        .replace(/([^\n])(\s+)-(?=[\p{Script=Han}A-Za-z0-9*])/gu, "$1\n- ")
        .replace(/^-(?=[\p{Script=Han}A-Za-z0-9*])/u, "- ")
        .replace(/([^\n])(\s+)(\d+)\.\s+(?=\S)/gu, "$1\n$3. ")
        .replace(/([。！？:：])(\s*)([-*]\s)/g, "$1\n$3")
        .replace(/([。！？:：])(\s*)(\d+\.\s)/g, "$1\n$3");
}

function isTableLikeLine(line: string) {
    const trimmed = line.trim();
    if (!trimmed.includes("|")) {
        return false;
    }
    if (trimmed.startsWith("|") || trimmed.endsWith("|")) {
        return true;
    }
    return /\s\|\s/.test(trimmed);
}

function normalizeMalformedMarkdownTableRows(content: string) {
    const lines = content.split("\n");
    let inPipeTable = false;
    let carbonTable = false;
    let pendingCarbonRow: string[] | null = null;

    const output: string[] = [];
    for (const line of lines) {
        const trimmed = line.trim();
        if (looksLikePipeTableHeader(trimmed)) {
            inPipeTable = true;
            carbonTable = isCarbonAccountingTableHeader(trimmed);
            pendingCarbonRow = null;
            output.push(line);
            continue;
        }
        if (inPipeTable && looksLikePipeTableSeparator(trimmed)) {
            output.push(line);
            continue;
        }
        if (inPipeTable && trimmed.includes("|")) {
            const normalizedRow = normalizePipeTableRow(trimmed, carbonTable, pendingCarbonRow);
            if (normalizedRow?.pending) {
                pendingCarbonRow = normalizedRow.pending;
                continue;
            }
            if (normalizedRow?.row) {
                pendingCarbonRow = null;
                output.push(normalizedRow.row);
                continue;
            }
        }
        if (pendingCarbonRow) {
            output.push(`| ${[pendingCarbonRow[0], pendingCarbonRow[1], "—", "—", "—"].join(" | ")} |`);
            pendingCarbonRow = null;
        }
        if (inPipeTable && (!trimmed || !trimmed.includes("|"))) {
            inPipeTable = false;
            carbonTable = false;
        }
        output.push(line);
    }
    if (pendingCarbonRow) {
        output.push(`| ${[pendingCarbonRow[0], pendingCarbonRow[1], "—", "—", "—"].join(" | ")} |`);
    }
    return output.join("\n");
}

function looksLikePipeTableHeader(line: string) {
    return line.startsWith("|")
        && line.endsWith("|")
        && line.includes("|")
        && ["排放源", "消耗量", "碳因子", "因子来源", "排放量"].some((keyword) => line.includes(keyword));
}

function isCarbonAccountingTableHeader(line: string) {
    return ["排放源", "消耗量", "碳因子", "因子来源", "排放量"].every((keyword) => line.includes(keyword));
}

function looksLikePipeTableSeparator(line: string) {
    return /^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line);
}

function normalizePipeTableRow(line: string, carbonTable: boolean, pendingCarbonRow: string[] | null) {
    if (looksLikePipeTableSeparator(line)) {
        return { row: line };
    }

    const rowBody = line
        .replace(/^\s*\d+\.\s+/, "")
        .replace(/^\|+/, "")
        .replace(/\|+$/, "")
        .trim();

    if (!rowBody) {
        return null;
    }

    const cells = rowBody.split("|").map((cell) => cell.trim()).filter(Boolean);
    if (!carbonTable) {
        return { row: `| ${cells.join(" | ")} |` };
    }

    const normalizedCells = normalizeCarbonAccountingCells(cells, pendingCarbonRow);
    if (normalizedCells?.pending) {
        return { pending: normalizedCells.pending };
    }
    return normalizedCells?.cells ? { row: `| ${normalizedCells.cells.join(" | ")} |` } : null;
}

function normalizeCarbonAccountingCells(cells: string[], pendingCarbonRow: string[] | null) {
    if (pendingCarbonRow && cells.length >= 3) {
        const lastCell = cells[cells.length - 1];
        if (looksLikeFactorValue(cells[0]) || looksLikeEmissionAmount(lastCell)) {
            return {
                cells: [
                    pendingCarbonRow[0],
                    pendingCarbonRow[1],
                    cells[0],
                    cells.slice(1, cells.length - 1).join(" | ") || "—",
                    lastCell || "—",
                ],
            };
        }
    }
    if (cells.length === 2 && looksLikeActivityAmount(cells[1]) && !looksLikeEmissionAmount(cells[0])) {
        return { pending: cells };
    }
    if (cells.length === 5 && looksLikeEmissionAmount(cells[0])) {
        return { cells: [cells[1], cells[2] || "—", cells[3] || "—", cells[4] || "—", cells[0]] };
    }
    if (cells.length === 5) {
        return { cells };
    }
    if (cells.length > 5) {
        if (looksLikeEmissionAmount(cells[0])) {
            const lastCell = cells[cells.length - 1];
            return {
                cells: [
                    cells[1],
                    cells[2] || "—",
                    cells[3] || "—",
                    cells.slice(4, looksLikeEmissionAmount(lastCell) ? cells.length - 1 : cells.length).join(" | ") || "—",
                    looksLikeEmissionAmount(lastCell) ? lastCell : cells[0],
                ],
            };
        }
        return {
            cells: [
                cells[0],
                cells[1],
                cells[2],
                cells.slice(3, cells.length - 1).join(" | "),
                cells[cells.length - 1],
            ],
        };
    }
    return null;
}

function looksLikeEmissionAmount(value: string) {
    return /\d[\d,.]*\s*(kg|t|吨|千克)?\s*co2e?\b/i.test(value.replace(/₂/g, "2"));
}

function looksLikeFactorValue(value: string) {
    return /\d[\d,.]*\s*(kg|g|t|吨|千克)?\s*co2e?\s*[\/／]/i.test(value.replace(/₂/g, "2"));
}

function looksLikeActivityAmount(value: string) {
    return /\d[\d,.]*\s*(kwh|kw·h|m3|m³|l|升|吨|t|kg|公里|km|站|人公里)\b/i.test(value);
}
