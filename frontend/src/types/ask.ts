export type AskStatus = "ok" | "provider_error" | "invalid_input";
export type KnowledgeScope = "public" | "private_sample" | "mixed";

export interface AskCitation {
    doc_id: string;
    title: string;
    source: string;
    source_url: string;
    snippet: string;
    chunk_id: string;
}

export interface AskRequest {
    question: string;
    knowledge_scope: KnowledgeScope;
    top_k: number;
}

export interface AskResponse {
    answer: string;
    mode: "ask";
    status: AskStatus;
    citations: AskCitation[];
    trace_id: string;
}
