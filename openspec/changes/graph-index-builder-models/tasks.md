# Tasks

## Proposal

- [x] Create V1.7.0 OpenSpec change for graph index builder models.
- [x] Confirm `ChunkRecord`, `RetrievalTrace`, RAG Lab metadata, and existing graph skeleton.

## Apply

- [x] Add/extend graph core models with confidence and summary/source fields.
- [x] Add lightweight rule-based `GraphIndexBuilder` implementation.
- [x] Add in-memory graph candidate storage and chunk-id lookup.
- [x] Attach graph entities/relations/candidates to retrieval-only metadata without changing `/ask`.
- [x] Add RAG Lab display for optional graph entities, relations, and candidates.
- [x] Add tests for model creation, build output, empty chunks, chunk-id lookup, and ask default compatibility.
- [x] Run `openspec validate graph-index-builder-models --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build.
- [x] Commit locally without push or PR.
