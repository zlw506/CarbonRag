export type RagDocumentStatus = "uploaded" | "parsed" | "chunked" | "indexed" | "failed";
export type RagRetrievalMode = "dense" | "sparse" | "hybrid" | "hybrid_rerank";

export interface KnowledgeBase {
    kb_id: string;
    owner_user_id?: string | null;
    name: string;
    description?: string | null;
    visibility: "private" | "shared" | "public";
    retrieval_mode: RagRetrievalMode;
    is_default: boolean;
    created_at: string;
    updated_at: string;
    metadata?: Record<string, unknown>;
}

export interface RagDocument {
    doc_id: string;
    kb_id: string;
    owner_user_id?: string | null;
    knowledge_item_id?: string | null;
    file_id?: string | null;
    title: string;
    source_type: string;
    status: RagDocumentStatus;
    parse_status: string;
    chunk_status: string;
    index_status: string;
    chunk_count: number;
    indexed_chunk_count: number;
    error_message?: string | null;
    vector_backend?: string | null;
    degraded?: boolean;
    index_warnings?: string[];
    created_at: string;
    updated_at: string;
    metadata?: Record<string, unknown>;
}

export interface RagChunk {
    rag_chunk_id: string;
    kb_id: string;
    doc_id: string;
    knowledge_chunk_id?: string | null;
    chunk_index: number;
    text: string;
    token_estimate: number;
    page_number?: number | null;
    sheet_name?: string | null;
    slide_number?: number | null;
    section_title?: string | null;
    vector_status: string;
}

export interface RagTrace {
    dense_count: number;
    sparse_count: number;
    merged_count: number;
    rerank_applied: boolean;
    vector_backend: string;
    degraded: boolean;
    warnings: string[];
    retrieval_mode: RagRetrievalMode;
    kb_id?: string | null;
}

export interface RagHit {
    chunk_id: string;
    doc_id: string;
    kb_id?: string | null;
    title: string;
    snippet: string;
    source_type: string;
    dense_score?: number | null;
    sparse_score?: number | null;
    rrf_score?: number | null;
    rerank_score?: number | null;
    page_number?: number | null;
    sheet_name?: string | null;
    slide_number?: number | null;
}

export interface RagSearchResult {
    query: string;
    kb_id?: string | null;
    hits: RagHit[];
    trace: RagTrace;
}

export interface RagTestQAResult {
    run_id?: string | null;
    answer: string;
    citations: Record<string, unknown>[];
    hits: RagHit[];
    retrieval_trace: RagTrace;
}

