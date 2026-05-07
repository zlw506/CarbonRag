# Tasks

## Proposal

- [x] Create V1.3.0 OpenSpec change for LightRAG-inspired RAG architecture.
- [x] Define affected capabilities and module boundaries.
- [x] Add M5/M1/M7 delta specs.
- [x] Receive V1.3 local apply authorization from #2/tbx for RAG development without per-change PR updates.
- [x] Expand V1.3 scope to include an M3 protected RAG Lab retrieval-testing surface.
- [ ] Receive #1 final review approval before merge/archive.

## Apply

- [x] Add internal RAG query parameter and retrieval result schemas for `naive` and `mix` modes.
- [x] Add an M5 RAG engine service boundary that returns structured chunks, references, metadata, and fallback reason.
- [x] Add vector retrieval adapter interfaces with a disabled/fallback-safe default.
- [x] Preserve existing BM25 public/private/mixed retrieval as default fallback.
- [x] Route embedding calls through M1 provider/runtime abstractions using test fakes for local tests.
- [x] Add optional rerank hook through M1 provider/runtime abstractions.
- [x] Add additive runtime DB bootstrap support if new metadata tables are required. No DB changes were required for this minimal skeleton.
- [x] Update env templates and docs for experimental RAG configuration.
- [x] Add backend tests for schema validation, fallback behavior, provider boundaries, and retrieval-only data output.
- [x] Add a protected retrieval-only API endpoint for the RAG Lab.
- [x] Add frontend service/types and a protected RAG Lab page for mode/scope/top-k/rerank retrieval checks.
- [x] Add unified RAG contracts for parsed documents, document blocks, chunk records, embedding records, citation refs, and retrieval traces.
- [x] Add a lightweight `ParserProvider` boundary and local parser provider that wraps existing parsing behavior.
- [x] Add a `VectorStoreAdapter` boundary with disabled-safe default behavior and future pgvector-compatible semantics.
- [x] Add hybrid retrieval strategy names/plans for dense-only, BM25+dense, citation-first, and graph-augmented retrieval.
- [x] Add graph index builder skeleton models for entities, relations, community summaries, and graph candidates.
- [x] Add workflow checkpoint skeleton models for future parse/index/vector/graph task orchestration.
- [x] Improve RAG Lab with backend URL visibility, current retrieval path, richer zero-hit guidance, and request error detail.
- [x] Run `openspec validate adopt-lightrag-rag-architecture --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build because frontend API types and surfaces are changed.

## Archive

- [ ] After apply PR is merged, archive `adopt-lightrag-rag-architecture` and validate all specs.
