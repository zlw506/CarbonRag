import type { AskCitation, AskRequest, AskResponse, AskSourceSummary, KnowledgeScope, MessageStatus } from "./ask";

export interface UploadedFile {
    file_id: string;
    session_id: string;
    filename: string;
    size: number;
    mime_type: string;
    stored_at: string;
    storage_path?: string | null;
    stored_filename?: string | null;
    file_ext?: string | null;
    sha256?: string | null;
    parse_status?: string | null;
    parser_name?: string | null;
    parser_version?: string | null;
    ocr_used?: boolean;
    page_count?: number | null;
    sheet_count?: number | null;
    slide_count?: number | null;
    error_message?: string | null;
    updated_at?: string | null;
    summary?: string | null;
    chunk_count?: number;
    knowledge_item_id?: string | null;
}

export interface SessionAttachment {
    file_id: string;
    filename: string;
    source_type: "uploaded_file" | "private_sample" | "private_sample_repo" | "knowledge_item";
    knowledge_item_id?: string | null;
    attached_at: string;
    parse_status?: string | null;
    index_status?: string | null;
    summary?: string | null;
    page_count?: number | null;
    sheet_count?: number | null;
    slide_count?: number | null;
    chunk_count?: number | null;
    error_message?: string | null;
}

export interface SessionMemoryState {
    context_usage_estimate: number;
    context_budget_estimate: number;
    summary_present: boolean;
    summary_updated_at?: string | null;
    compacted_message_count: number;
    compaction_status: "idle" | "compacted" | "failed";
    summary_estimated_tokens: number;
}

export interface SessionSummary {
    session_id: string;
    title: string;
    created_at: string;
    updated_at: string;
    message_count: number;
    file_count: number;
    attached_private_sample_count: number;
    attached_knowledge_item_count?: number;
}

export interface SessionMessage {
    message_id: string;
    role: "user" | "assistant" | "system";
    content: string;
    thinking_content?: string | null;
    created_at: string;
    status?: MessageStatus | null;
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
    memory_state?: SessionMemoryState | null;
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
