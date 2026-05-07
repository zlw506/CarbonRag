## Scope

This change is a contract and adapter pass only. It keeps the current retrieval engine, BM25 fallback, retrieval-only API, and RAG Lab surface intact.

## Model Strategy

- Reuse `backend/app/rag/contracts.py` as the single home for the unified contract.
- Keep Pydantic throughout, matching existing backend style.
- Add requested field names while preserving compatibility for existing helper names such as parser text, mime type, source path, and chunk hash.
- Prefer adapter functions over moving directories or rewriting retrieval internals.

## Adapter Strategy

- `RetrievedChunk` remains the old public/private retrieval object.
- `ChunkRecord` is the future-facing contract object.
- `RagEvidenceReference` remains the API reference object.
- `CitationRef` is the future-facing citation object.
- `RetrievalTrace` can be built from either retrieval components or an existing `RagRetrievalResult`.

## Non-Goals

- No pgvector, Qdrant, Docling, MinerU, GraphRAG, LangGraph, or heavy new dependencies.
- No default `/ask`, session, report, or carbon calculation behavior changes.
- No response field removal from retrieval-only API.
