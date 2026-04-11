export interface ParsedSseEvent {
    event: string;
    data: string;
}

interface SseParserState {
    eventName: string;
    dataLines: string[];
    pendingLine: string;
}

export function createSseParserState(): SseParserState {
    return {
        eventName: "message",
        dataLines: [],
        pendingLine: "",
    };
}

export function consumeSseTextChunk(chunkText: string, state: SseParserState): ParsedSseEvent[] {
    const parsedEvents: ParsedSseEvent[] = [];
    const normalizedText = `${state.pendingLine}${chunkText}`.replace(/\r\n/g, "\n");
    const lines = normalizedText.split("\n");
    state.pendingLine = lines.pop() ?? "";

    for (const line of lines) {
        const event = processSseLine(line, state);
        if (event) {
            parsedEvents.push(event);
        }
    }

    return parsedEvents;
}

export function flushSseState(state: SseParserState): ParsedSseEvent | null {
    if (state.pendingLine) {
        const event = processSseLine(state.pendingLine, state);
        state.pendingLine = "";
        if (event) {
            return event;
        }
    }
    return flushCompletedEvent(state);
}

function processSseLine(line: string, state: SseParserState): ParsedSseEvent | null {
    if (!line) {
        return flushCompletedEvent(state);
    }

    if (line.startsWith(":")) {
        return null;
    }

    if (line.startsWith("event:")) {
        state.eventName = line.slice("event:".length).trim() || "message";
        return null;
    }

    if (line.startsWith("data:")) {
        state.dataLines.push(line.slice("data:".length).replace(/^ /, ""));
    }
    return null;
}

function flushCompletedEvent(state: SseParserState): ParsedSseEvent | null {
    if (state.eventName === "message" && state.dataLines.length === 0) {
        return null;
    }

    const event: ParsedSseEvent = {
        event: state.eventName,
        data: state.dataLines.join("\n"),
    };
    state.eventName = "message";
    state.dataLines = [];
    return event;
}
