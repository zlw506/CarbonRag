export type FilePreviewSourceType = "session_file" | "rag_document" | "crawler_candidate" | "knowledge_item";

export interface FilePreviewTarget {
    sourceType: FilePreviewSourceType;
    sourceId: string;
    kbId?: string | null;
}

export interface FilePreviewChunk {
    chunk_id: string;
    doc_id?: string | null;
    kb_id?: string | null;
    order_index: number;
    text: string;
    title?: string | null;
    source_type?: string | null;
    source_url?: string | null;
    page_number?: number | null;
    sheet_name?: string | null;
    slide_number?: number | null;
    section_title?: string | null;
    vector_status?: string | null;
    metadata: Record<string, unknown>;
}

export interface FilePreviewResponse {
    source_type: FilePreviewSourceType;
    source_id: string;
    title: string;
    filename?: string | null;
    mime_type?: string | null;
    size?: number | null;
    status: string;
    source_url?: string | null;
    markdown?: string | null;
    text?: string | null;
    chunks: FilePreviewChunk[];
    metadata: Record<string, unknown>;
    raw_available: boolean;
    raw_preview_url?: string | null;
    raw_download_url?: string | null;
    can_inline_raw: boolean;
    available_tabs: string[];
    truncated: boolean;
}
