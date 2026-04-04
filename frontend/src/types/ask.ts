export type AskStatus = "ok" | "provider_error" | "invalid_input";
export type KnowledgeScope = "public" | "private_sample" | "mixed";

export interface AskCitation {
    source_id: string;
    title: string;
    snippet: string;
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
