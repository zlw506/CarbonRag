# Tasks

## Proposal

- [x] Create V1.3.0 OpenSpec change for LightRAG-inspired RAG architecture.
- [x] Define affected capabilities and module boundaries.
- [x] Add M5/M1/M7 delta specs.
- [ ] Receive #1 review approval before apply-stage implementation.

## Apply

- [ ] Add internal RAG query parameter and retrieval result schemas for `naive` and `mix` modes.
- [ ] Add an M5 RAG engine service boundary that returns structured chunks, references, metadata, and fallback reason.
- [ ] Add vector retrieval adapter interfaces with a disabled/fallback-safe default.
- [ ] Preserve existing BM25 public/private/mixed retrieval as default fallback.
- [ ] Route embedding calls through M1 provider/runtime abstractions using test fakes for local tests.
- [ ] Add optional rerank hook through M1 provider/runtime abstractions.
- [ ] Add additive runtime DB bootstrap support if new metadata tables are required.
- [ ] Update env templates and docs for any experimental RAG configuration.
- [ ] Add backend tests for schema validation, fallback behavior, provider boundaries, and retrieval-only data output.
- [ ] Run `openspec validate adopt-lightrag-rag-architecture --strict`.
- [ ] Run `openspec validate --all`.
- [ ] Run backend tests.
- [ ] Run frontend typecheck/build if API types or frontend surfaces are changed.

## Archive

- [ ] After apply PR is merged, archive `adopt-lightrag-rag-architecture` and validate all specs.
