## Why

CarbonRag already has BM25 fallback, a `VectorStoreAdapter` boundary, retrieval-only metadata, and the RAG Lab verification page. V1.5.1 should add an explicit experimental retriever strategy layer so BM25 and vector results can be compared and merged without changing the default `/ask` behavior.

## What Changes

- Add a lightweight `RetrieverStrategy` boundary with BM25, vector, and BM25+vector hybrid implementations.
- Keep existing naive/mix planning and `/ask` defaults unchanged unless an experimental retrieval strategy is explicitly requested through retrieval-only parameters.
- Add `bm25_only`, `vector_only`, and `bm25_vector_hybrid` as RAG Lab selectable strategies.
- Merge hybrid results by `chunk_id`, preserve top-k behavior, and attach per-chunk source metadata such as BM25 score, vector score, merged score, and source retrievers.
- Degrade hybrid retrieval to BM25 when the vector adapter is unavailable, disabled, or errors.
- Preserve existing `chunks`, `references`, and `metadata` response fields.

## Capabilities

### Modified Capabilities

- `knowledge-rag`: Add an experimental retriever strategy layer and BM25+vector merge metadata for retrieval-only callers.
- `frontend-shell-settings`: Add RAG Lab strategy selection and result-source display without changing the primary ask/session UI.

## Impact

- Affected modules: M5 RAG/retrieval, M2 frontend RAG Lab.
- Apply-stage areas: `backend/app/rag`, retrieval-only endpoint schemas, RAG Lab types/page, and tests.
- No GraphRAG, Neo4j, LightRAG local/global/hybrid mode, calc/report/session change, or mandatory vector backend switch is proposed.
