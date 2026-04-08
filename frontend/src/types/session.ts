import type { AskCitation, AskRequest, AskResponse, AskSourceSummary, AskStatus, KnowledgeScope } from "./ask";

export interface UploadedFile {
    file_id: string;
    session_id: string;
    filename: string;
    size: number;
    mime_type: string;
    stored_at: string;
}

export interface SessionAttachment {
    file_id: string;
    filename: string;
    source_type: "uploaded_file" | "private_sample";
    attached_at: string;
}

export interface SessionSummary {
    session_id: string;
    title: string;
    created_at: string;
    updated_at: string;
    message_count: number;
    file_count: number;
    attached_private_sample_count: number;
}

export interface SessionMessage {
    message_id: string;
    role: "user" | "assistant";
    content: string;
    created_at: string;
    status?: AskStatus | null;
    trace_id?: string | null;
    citations: AskCitation[];
    source_summary?: AskSourceSummary | null;
}

export interface SessionDetail extends SessionSummary {
    messages: SessionMessage[];
    files: UploadedFile[];
    attached_files: SessionAttachment[];
    knowledge_scope_last_used?: KnowledgeScope | null;
    source_summary?: AskSourceSummary | null;
}

export interface CreateSessionRequest {
    title?: string;
}

export interface UpdateSessionRequest {
    title: string;
}

export interface ReplaceAttachedPrivateSamplesRequest {
    doc_ids: string[];
}

export type SessionAskRequest = AskRequest;
export type SessionAskResponse = AskResponse;
