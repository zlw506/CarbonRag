# Tasks

## Proposal

- [x] Create OpenSpec change `langchain-rag-core-port`.
- [x] Define reference-project mapping and licensing boundary.
- [x] Define affected `knowledge-rag` requirements.

## Apply

- [x] Add `backend/app/langchain_rag/` service modules.
- [x] Add LangChain/Chroma/rerank dependencies to backend requirements.
- [x] Enable LangChain RAG defaults in `.env.example` and backend settings.
- [x] Convert CarbonRag knowledge chunks to metadata-rich LangChain documents.
- [x] Add Chroma vector store adapter with visible unavailable state.
- [x] Add BM25 store and dynamic hybrid retriever.
- [x] Add HyDE and CrossEncoder rerank with explicit fallback warnings.
- [x] Add RAG health, stats, rebuild, file index, search, and answer APIs.
- [x] Register `langchain_rag_search` and `langchain_rag_answer` runtime tools.
- [x] Route ask mode to LangChain RAG when enabled.
- [x] Surface retrieval trace in ask responses and stream metadata.
- [x] Add backend tests for documents, BM25, hybrid retriever, HyDE, rerank, answer, tool output, and ask integration.
- [x] Add frontend trace display and run typecheck/build.
- [x] Run `openspec validate langchain-rag-core-port --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.

## Archive

- [ ] Archive after implementation PR is merged and specs are synced.
