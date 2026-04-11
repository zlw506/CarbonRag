import axios from "axios";
import { httpClient } from "./http";
import { consumeSseTextChunk, createSseParserState, flushSseState } from "./sse";
import type {
    AskStreamCallbacks,
    AskStreamDeltaEvent,
    AskStreamErrorEvent,
    AskStreamMetadataEvent,
    AskStreamMessageStartEvent,
    AskStreamStatusEvent,
} from "../types/ask";
import type {
    CreateSessionRequest,
    ReplaceAttachedPrivateSamplesRequest,
    SessionAskRequest,
    SessionAskResponse,
    SessionDetail,
    SessionSummary,
    SessionMemoryState,
    UpdateSessionRequest,
} from "../types/session";

export async function listSessions() {
    const response = await httpClient.get<SessionSummary[]>("/v1/sessions");
    return response.data;
}

export async function createSession(payload: CreateSessionRequest = {}) {
    const response = await httpClient.post<SessionSummary>("/v1/sessions", payload);
    return response.data;
}

export async function getSession(sessionId: string) {
    const response = await httpClient.get<SessionDetail>(`/v1/sessions/${sessionId}`);
    return response.data;
}

export async function updateSessionTitle(sessionId: string, payload: UpdateSessionRequest) {
    const response = await httpClient.patch<SessionSummary>(`/v1/sessions/${sessionId}`, payload);
    return response.data;
}

export async function replaceAttachedPrivateSamples(
    sessionId: string,
    payload: ReplaceAttachedPrivateSamplesRequest,
) {
    const response = await httpClient.put<SessionDetail>(
        `/v1/sessions/${sessionId}/attached-files/private-samples`,
        payload,
    );
    return response.data;
}

export async function submitSessionAskRequest(
    sessionId: string,
    payload: SessionAskRequest,
    options?: { signal?: AbortSignal },
) {
    try {
        const response = await httpClient.post<SessionAskResponse>(
            `/v1/sessions/${sessionId}/ask`,
            payload,
            { signal: options?.signal },
        );
        return response.data;
    } catch (error) {
        if (axios.isAxiosError<SessionAskResponse>(error) && error.response?.data) {
            throw error.response.data;
        }
        throw error;
    }
}

export async function submitSessionAskStreamRequest(
    sessionId: string,
    payload: SessionAskRequest,
    callbacks: AskStreamCallbacks = {},
    options?: { signal?: AbortSignal },
) {
    const streamUrl = buildApiUrl(`/v1/sessions/${sessionId}/ask/stream`);
    const fallbackResponse = await fetch(streamUrl, {
        method: "POST",
        headers: {
            Accept: "text/event-stream",
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        credentials: "include",
        signal: options?.signal,
    }).catch(async (error) => {
        if (options?.signal?.aborted) {
            throw error;
        }
        return null;
    });

    if (!fallbackResponse) {
        const response = await submitSessionAskRequest(sessionId, payload, options);
        emitSyntheticStreamEvents(response, callbacks);
        return response;
    }

    if (fallbackResponse.status === 404) {
        const response = await submitSessionAskRequest(sessionId, payload, options);
        emitSyntheticStreamEvents(response, callbacks);
        return response;
    }

    const contentType = fallbackResponse.headers.get("content-type") ?? "";
    if (!fallbackResponse.ok || !contentType.includes("text/event-stream")) {
        const responseText = await fallbackResponse.text();
        let parsedJson: SessionAskResponse | null = null;
        if (contentType.includes("application/json")) {
            try {
                parsedJson = JSON.parse(responseText) as SessionAskResponse;
            } catch {
                parsedJson = null;
            }
        }

        if (parsedJson?.mode === "ask") {
            throw parsedJson;
        }

        const response = await submitSessionAskRequest(sessionId, payload, options);
        emitSyntheticStreamEvents(response, callbacks);
        return response;
    }

    if (!fallbackResponse.body) {
        const response = await submitSessionAskRequest(sessionId, payload, options);
        emitSyntheticStreamEvents(response, callbacks);
        return response;
    }

    const parserState = createSseParserState();
    const decoder = new TextDecoder();
    const state = {
        answer: "",
        thinking: "",
        citations: [] as SessionAskResponse["citations"],
        source_summary: undefined as SessionAskResponse["source_summary"] | undefined,
        trace_id: "" as string,
        mode: "ask" as const,
        status: "ok" as SessionAskResponse["status"],
        user_message_id: null as string | null,
        assistant_message_id: null as string | null,
        memory_state: undefined as SessionMemoryState | undefined,
    };

    callbacks.onStatus?.({ status: "pending" });

    const reader = fallbackResponse.body.getReader();
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (value) {
                const text = decoder.decode(value, { stream: !done });
                const events = consumeSseTextChunk(text, parserState);
                for (const event of events) {
                    applyStreamEvent(event, state, callbacks);
                }
            }
            if (done) {
                const finalEvent = flushSseState(parserState);
                if (finalEvent) {
                    applyStreamEvent(finalEvent, state, callbacks);
                }
                break;
            }
        }
    } finally {
        reader.releaseLock();
    }

    return buildAskResponseFromStreamState(state);
}

function buildApiUrl(path: string) {
    const baseUrl = httpClient.defaults.baseURL ?? "";
    const normalizedBase = baseUrl.replace(/\/+$/, "");
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    return `${normalizedBase}${normalizedPath}`;
}

function emitSyntheticStreamEvents(response: SessionAskResponse, callbacks: AskStreamCallbacks) {
    callbacks.onStatus?.({ status: "pending" });
    callbacks.onMessageStart?.({
        user_message_id: null,
        assistant_message_id: null,
        trace_id: response.trace_id,
    });
    callbacks.onStatus?.({ status: "thinking", trace_id: response.trace_id });
    callbacks.onThinkingDelta?.({
        delta: "模型正在组织上下文与回答，请稍候。",
        trace_id: response.trace_id,
    });
    if (response.answer) {
        callbacks.onStatus?.({ status: "streaming", trace_id: response.trace_id });
        callbacks.onAnswerDelta?.({ delta: response.answer, trace_id: response.trace_id });
    }
    callbacks.onMetadata?.({
        ...response,
        memory_state: undefined,
        assistant_message_id: null,
        user_message_id: null,
    });
    callbacks.onStatus?.({ status: "done", trace_id: response.trace_id });
    callbacks.onDone?.({
        ...response,
        memory_state: undefined,
        assistant_message_id: null,
        user_message_id: null,
    });
}

function applyStreamEvent(
    event: { event: string; data: string },
    state: {
        answer: string;
        thinking: string;
        citations: SessionAskResponse["citations"];
        source_summary: SessionAskResponse["source_summary"] | undefined;
        trace_id: string;
        mode: SessionAskResponse["mode"];
        status: SessionAskResponse["status"];
        user_message_id: string | null;
        assistant_message_id: string | null;
        memory_state: SessionMemoryState | undefined;
    },
    callbacks: AskStreamCallbacks,
) {
    const payload = parseStreamEventData(event.data);
    switch (event.event) {
        case "message_start": {
            const start = payload as AskStreamMessageStartEvent;
            state.trace_id = start.trace_id ?? state.trace_id;
            state.user_message_id = start.user_message_id ?? state.user_message_id;
            state.assistant_message_id = start.assistant_message_id ?? state.assistant_message_id;
            callbacks.onMessageStart?.(start);
            return;
        }
        case "status": {
            const statusEvent = payload as AskStreamStatusEvent;
            if (statusEvent.status) {
                state.status = mapLifecycleStatusToAskStatus(statusEvent.status);
            }
            state.trace_id = statusEvent.trace_id ?? state.trace_id;
            state.user_message_id = statusEvent.user_message_id ?? state.user_message_id;
            state.assistant_message_id = statusEvent.assistant_message_id ?? state.assistant_message_id;
            callbacks.onStatus?.(statusEvent);
            return;
        }
        case "thinking_delta": {
            const thinkingEvent = payload as AskStreamDeltaEvent;
            const delta = extractDeltaText(thinkingEvent);
            if (delta) {
                state.thinking += delta;
            }
            state.trace_id = thinkingEvent.trace_id ?? state.trace_id;
            callbacks.onThinkingDelta?.(thinkingEvent);
            return;
        }
        case "answer_delta": {
            const answerEvent = payload as AskStreamDeltaEvent;
            const delta = extractDeltaText(answerEvent);
            if (delta) {
                state.answer += delta;
            }
            state.trace_id = answerEvent.trace_id ?? state.trace_id;
            callbacks.onAnswerDelta?.(answerEvent);
            return;
        }
        case "metadata": {
            const metadata = payload as AskStreamMetadataEvent;
            state.trace_id = metadata.trace_id ?? state.trace_id;
            state.citations = metadata.citations ?? state.citations;
            state.source_summary = metadata.source_summary ?? state.source_summary;
            state.status = metadata.status ?? state.status;
            if (typeof metadata.answer === "string" && metadata.answer) {
                state.answer = metadata.answer;
            }
            state.memory_state = normalizeMemoryState(metadata.memory_state, state.memory_state);
            callbacks.onMetadata?.(metadata);
            return;
        }
        case "done": {
            const doneEvent = payload as AskStreamMetadataEvent;
            state.trace_id = doneEvent.trace_id ?? state.trace_id;
            state.citations = doneEvent.citations ?? state.citations;
            state.source_summary = doneEvent.source_summary ?? state.source_summary;
            state.status = doneEvent.status ?? state.status;
            if (typeof doneEvent.answer === "string" && doneEvent.answer) {
                state.answer = doneEvent.answer;
            }
            state.memory_state = normalizeMemoryState(doneEvent.memory_state, state.memory_state);
            callbacks.onDone?.(doneEvent);
            return;
        }
        case "error": {
            const errorEvent = payload as AskStreamErrorEvent;
            state.status = errorEvent.status ?? "provider_error";
            state.trace_id = errorEvent.trace_id ?? state.trace_id;
            callbacks.onError?.(errorEvent);
            return;
        }
        default: {
            return;
        }
    }
}

function buildAskResponseFromStreamState(state: {
    answer: string;
    thinking: string;
    citations: SessionAskResponse["citations"];
    source_summary: SessionAskResponse["source_summary"] | undefined;
    trace_id: string;
    mode: SessionAskResponse["mode"];
    status: SessionAskResponse["status"];
    user_message_id: string | null;
    assistant_message_id: string | null;
    memory_state: SessionMemoryState | undefined;
}): SessionAskResponse {
    return {
        answer: state.answer.trim(),
        mode: state.mode,
        status: state.status,
        citations: state.citations,
        source_summary:
            state.source_summary ?? {
                knowledge_scope: "public",
                public_policy_count: 0,
                private_sample_count: 0,
                private_upload_count: 0,
                total_citation_count: 0,
            },
        trace_id: state.trace_id,
    };
}

function normalizeMemoryState(
    memoryState: AskStreamMetadataEvent["memory_state"],
    fallback?: SessionMemoryState,
): SessionMemoryState | undefined {
    if (!memoryState || typeof memoryState !== "object") {
        return fallback;
    }

    const candidate = memoryState as Partial<SessionMemoryState>;
    if (
        typeof candidate.context_usage_estimate !== "number" ||
        typeof candidate.context_budget_estimate !== "number" ||
        typeof candidate.summary_present !== "boolean" ||
        typeof candidate.compacted_message_count !== "number" ||
        typeof candidate.summary_estimated_tokens !== "number"
    ) {
        return fallback;
    }

    const compactionStatus = candidate.compaction_status;
    if (compactionStatus !== "idle" && compactionStatus !== "compacted" && compactionStatus !== "failed") {
        return fallback;
    }

    return {
        context_usage_estimate: candidate.context_usage_estimate,
        context_budget_estimate: candidate.context_budget_estimate,
        summary_present: candidate.summary_present,
        summary_updated_at: candidate.summary_updated_at ?? null,
        compacted_message_count: candidate.compacted_message_count,
        compaction_status: compactionStatus,
        summary_estimated_tokens: candidate.summary_estimated_tokens,
    };
}

function parseStreamEventData(rawData: string) {
    const trimmed = rawData.trim();
    if (!trimmed) {
        return {};
    }
    try {
        return JSON.parse(trimmed) as unknown;
    } catch {
        return { delta: trimmed };
    }
}

function extractDeltaText(payload: AskStreamDeltaEvent) {
    return payload.delta ?? payload.text ?? payload.content ?? "";
}

function mapLifecycleStatusToAskStatus(status: AskStreamStatusEvent["status"]): SessionAskResponse["status"] {
    if (status === "error") {
        return "provider_error";
    }
    return "ok";
}
