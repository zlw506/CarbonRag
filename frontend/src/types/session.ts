import type { AskCitation, AskRequest, AskResponse, AskStatus } from "./ask";

export interface UploadedFile {
    file_id: string;
    session_id: string;
    filename: string;
    size: number;
    mime_type: string;
    stored_at: string;
}

export interface SessionSummary {
    session_id: string;
    title: string;
    created_at: string;
    updated_at: string;
    message_count: number;
    file_count: number;
}

export interface SessionMessage {
    message_id: string;
    role: "user" | "assistant";
    content: string;
    created_at: string;
    status?: AskStatus | null;
    trace_id?: string | null;
    citations: AskCitation[];
}

export interface SessionDetail extends SessionSummary {
    messages: SessionMessage[];
    files: UploadedFile[];
}

export interface CreateSessionRequest {
    title?: string;
}

export interface UpdateSessionRequest {
    title: string;
}

export type SessionAskRequest = AskRequest;
export type SessionAskResponse = AskResponse;
