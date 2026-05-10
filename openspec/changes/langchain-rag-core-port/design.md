## Context

CarbonRag has strong product scaffolding around sessions, authentication, file parsing, knowledge chunks, and citations. The missing piece is a real RAG engine that can combine sparse retrieval, vector retrieval, query expansion, reranking, and answer traces. The existing `backend/app/rag` skeleton remains useful as a compatibility layer, but it is not sufficient as the competition-facing RAG core.

## Goals / Non-Goals

**Goals:**

- Make LangChain RAG the default ask retrieval path when `RAG_LANGCHAIN_ENABLED=true`.
- Index CarbonRag knowledge chunks into a local Chroma collection.
- Build BM25 and vector candidates over the same metadata-rich document set.
- Apply dynamic BM25/vector weights based on query length.
- Generate a HyDE query when configured, and record warnings on failure.
- Apply CrossEncoder rerank when configured, with explicit fallback if the model cannot load.
- Return citations and retrieval traces through ask and direct RAG APIs.

**Non-Goals:**

- Do not port the reference project's Django/JWT/MySQL/Redis/Vue surfaces.
- Do not replace CarbonRag's existing session, auth, file parsing, or knowledge governance systems.
- Do not vendor the whole reference repository into tracked source.
- Do not implement graph RAG, distributed vector stores, LangGraph agents, or full evaluation tooling in this change.

## Design Decisions

### Decision 1: Add `backend/app/langchain_rag/`

The new module owns LangChain document conversion, embeddings, Chroma vector store access, BM25 store, splitting defaults, HyDE, rerank, hybrid retrieval, answer generation, tools, and citation conversion. This keeps the port auditable and avoids further overloading the older retrieval modules.

### Decision 2: Reuse existing knowledge chunks

V1.5.x file parsing and V1.3.x knowledge ingestion already normalize documents into `knowledge_items` and `knowledge_chunks`. V1.6.1 maps those chunks to LangChain document metadata instead of introducing a separate document database.

### Decision 3: Metadata is mandatory

Every document and hit must preserve chunk, knowledge item, file, owner, library scope, source type, title, location, and URL metadata. Retrieval without metadata is treated as insufficient because CarbonRag answers must cite and enforce user isolation.

### Decision 4: Optional dependencies fail visibly

Chroma, HyDE, and CrossEncoder can fail on local machines or VPS. The system records `vector unavailable`, HyDE warnings, and rerank fallback reasons instead of pretending that a full RAG pass succeeded.

### Decision 5: Ask uses the new tool by default

When LangChain RAG is enabled, ask mode resolves to `langchain_rag_search`. The legacy tool sequence remains reachable only when LangChain RAG is disabled.

## Risks / Trade-offs

- Dependency weight increases backend installation cost. The implementation keeps optional fallbacks for missing Chroma and rerank packages, but competition validation should install the full set.
- HyDE adds model calls before retrieval. Failures are non-blocking and logged in trace warnings.
- Chroma local persistence is suitable for the first stage, but future cloud scale may require pgvector, Milvus, or another managed backend.
- Direct reference-code copying is avoided unless attribution is explicit.

## Migration Plan

1. Add module and config defaults.
2. Add RAG APIs and runtime tools.
3. Wire ask and streaming metadata to expose retrieval traces.
4. Add tests around document conversion, BM25, hybrid retrieval, HyDE/rerank fallback, answer citations, and user isolation.
5. Validate OpenSpec, backend tests, and frontend typecheck/build.
