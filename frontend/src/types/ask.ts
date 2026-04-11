export type AskStatus = "ok" | "provider_error" | "invalid_input";
export type KnowledgeScope = "public" | "private_sample" | "mixed";
export type CitationSourceType = "public_policy" | "private_sample" | "private_upload";
export type AskStreamLifecycleStatus = "pending" | "thinking" | "streaming" | "done" | "error";
export type MessageStatus = AskStatus | AskStreamLifecycleStatus;
export type AskStreamEventName =
    | "message_start"
    | "status"
    | "thinking_delta"
    | "answer_delta"
    | "metadata"
    | "done"
    | "error";

export interface AskCitation {
    doc_id: string;
    knowledge_item_id?: string | null;
    title: string;
    source_type: CitationSourceType;
    source: string;
    source_url: string | null;
    snippet: string;
    chunk_id: string;
    library_scope?: "personal" | "shared" | null;
}

export interface AskSourceSummary {
    knowledge_scope: KnowledgeScope;
    public_policy_count: number;
    private_sample_count: number;
    private_upload_count?: number;
    total_citation_count: number;
}

export interface AskRequest {
    question: string;
    knowledge_scope: KnowledgeScope;
    top_k: number;
    attached_file_ids?: string[];
}

export interface AskResponse {
    answer: string;
    mode: "ask";
    status: AskStatus;
    citations: AskCitation[];
    source_summary: AskSourceSummary;
    trace_id: string;
}

export interface AskStreamMessageStartEvent {
    user_message_id?: string | null;
    assistant_message_id?: string | null;
    trace_id?: string | null;
}

export interface AskStreamStatusEvent {
    status: AskStreamLifecycleStatus;
    user_message_id?: string | null;
    assistant_message_id?: string | null;
    trace_id?: string | null;
}

export interface AskStreamDeltaEvent {
    delta?: string | null;
    text?: string | null;
    content?: string | null;
    user_message_id?: string | null;
    assistant_message_id?: string | null;
    trace_id?: string | null;
}

export interface AskStreamMetadataEvent extends Partial<AskResponse> {
    user_message_id?: string | null;
    assistant_message_id?: string | null;
    memory_state?: {
        context_usage_estimate: number;
        context_budget_estimate: number;
        summary_present: boolean;
        summary_updated_at?: string | null;
        compacted_message_count: number;
        compaction_status: "idle" | "compacted" | "failed";
        summary_estimated_tokens?: number;
    } | null;
    context_source?: {
        recent_message_count: number;
        summary_present: boolean;
        citation_count: number;
    } | null;
}

export interface AskStreamErrorEvent {
    message?: string | null;
    detail?: string | null;
    status?: AskStatus | null;
    trace_id?: string | null;
    user_message_id?: string | null;
    assistant_message_id?: string | null;
}

export interface AskStreamCallbacks {
    onMessageStart?: (event: AskStreamMessageStartEvent) => void;
    onStatus?: (event: AskStreamStatusEvent) => void;
    onThinkingDelta?: (event: AskStreamDeltaEvent) => void;
    onAnswerDelta?: (event: AskStreamDeltaEvent) => void;
    onMetadata?: (event: AskStreamMetadataEvent) => void;
    onDone?: (event: AskStreamMetadataEvent) => void;
    onError?: (event: AskStreamErrorEvent) => void;
}
