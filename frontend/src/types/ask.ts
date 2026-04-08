export type AskStatus = "ok" | "provider_error" | "invalid_input";
export type KnowledgeScope = "public" | "private_sample" | "mixed";
export type CitationSourceType = "public_policy" | "private_sample";

export interface AskCitation {
    doc_id: string;
    title: string;
    source_type: CitationSourceType;
    source: string;
    source_url: string | null;
    snippet: string;
    chunk_id: string;
}

export interface AskSourceSummary {
    knowledge_scope: KnowledgeScope;
    public_policy_count: number;
    private_sample_count: number;
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
