import axios from "axios";
import { httpClient } from "./http";
import type {
    CreateSessionRequest,
    SessionAskRequest,
    SessionAskResponse,
    SessionDetail,
    SessionSummary,
    UpdateSessionRequest,
} from "../types/session";

export async function listSessions() {
    const response = await httpClient.get<SessionSummary[]>("/api/v1/sessions");
    return response.data;
}

export async function createSession(payload: CreateSessionRequest = {}) {
    const response = await httpClient.post<SessionSummary>("/api/v1/sessions", payload);
    return response.data;
}

export async function getSession(sessionId: string) {
    const response = await httpClient.get<SessionDetail>(`/api/v1/sessions/${sessionId}`);
    return response.data;
}

export async function updateSessionTitle(sessionId: string, payload: UpdateSessionRequest) {
    const response = await httpClient.patch<SessionSummary>(`/api/v1/sessions/${sessionId}`, payload);
    return response.data;
}

export async function submitSessionAskRequest(sessionId: string, payload: SessionAskRequest) {
    try {
        const response = await httpClient.post<SessionAskResponse>(
            `/api/v1/sessions/${sessionId}/ask`,
            payload,
        );
        return response.data;
    } catch (error) {
        if (axios.isAxiosError<SessionAskResponse>(error) && error.response?.data) {
            throw error.response.data;
        }
        throw error;
    }
}
