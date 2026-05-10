## Why

CarbonRag already has uploaded files, knowledge chunks, public/private scopes, and a RAG Lab surface, but the main RAG path still relies on lightweight BM25/fallback behavior and vector retrieval is not a real default capability. For the competition-facing product, RAG must become a visible core system rather than a disabled or simulated backend.

The local reference project `3rdparty/LangChain-RAG-FastAPI-Service-master` demonstrates the shape CarbonRag needs: FastAPI services around LangChain documents, Chroma vector storage, BM25 retrieval, HyDE query expansion, CrossEncoder rerank, answer generation, and structured trace data.

## What Changes

- Add a CarbonRag-native `backend/app/langchain_rag/` module instead of replacing existing auth/session/frontend code.
- Convert existing `knowledge_chunks` and uploaded-file chunks into LangChain-compatible document records with citation metadata.
- Add Chroma-backed vector indexing, BM25 sparse retrieval, dynamic hybrid weighting, optional HyDE query expansion, and optional CrossEncoder rerank.
- Expose RAG health, stats, index rebuild, file index, search, and answer APIs under `/api/v1/rag`.
- Route ask mode to the new LangChain RAG search tool by default while retaining the older RAG engine as an explicit fallback path.
- Surface retrieval trace metadata so frontend and reviewers can see HyDE, BM25, vector, rerank, and fallback status.
- Record the reference-project mapping and licensing note in `docs/research/rag/langchain-rag-fastapi-service-review.md`.

## Capabilities

### Modified Capabilities

- `knowledge-rag`: Adds the LangChain/Chroma/BM25/HyDE/rerank RAG core, traceable citations, index APIs, and default ask integration.

## Impact

- Affected modules: M5 primary; M1/M2/M3 secondary.
- Likely code areas: `backend/app/langchain_rag/**`, RAG API endpoints, AI runtime tool registry, ask orchestration, ask response schemas, frontend ask types/UI, requirements, env templates, tests, and docs.
- This change does not copy the reference project wholesale into the repository; it ports the business logic into CarbonRag-native boundaries.
