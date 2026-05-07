CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS rag_embeddings (
    embedding_id TEXT PRIMARY KEY,
    chunk_id TEXT NOT NULL UNIQUE,
    document_id TEXT NOT NULL,
    source_type TEXT,
    title TEXT,
    source TEXT,
    source_url TEXT,
    visibility TEXT,
    text TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding VECTOR NOT NULL,
    model_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rag_embeddings_document_id
    ON rag_embeddings (document_id);

CREATE INDEX IF NOT EXISTS idx_rag_embeddings_source_type
    ON rag_embeddings (source_type);

CREATE INDEX IF NOT EXISTS idx_rag_embeddings_visibility
    ON rag_embeddings (visibility);

-- Add a dimension-specific ivfflat or hnsw index after the embedding model
-- dimension is fixed for the deployment.
