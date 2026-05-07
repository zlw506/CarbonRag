# Tasks

## Proposal

- [x] Create V1.8.0 OpenSpec change for experimental graph query modes.
- [x] Confirm graph models, builder, and RAG Lab graph candidates exist.

## Apply

- [x] Add graph query mode schema and retrieval-only request support.
- [x] Add graph metadata fields and per-candidate reason fields.
- [x] Add GraphStoreAdapter boundary with runtime, fake, and Neo4j stub implementations.
- [x] Implement graph_local, graph_global, and graph_hybrid candidate selection.
- [x] Keep graph mode off by default and preserve `/ask` behavior.
- [x] Add RAG Lab graph mode selector and fallback reason display.
- [x] Add tests for graph_local, graph_global, graph_hybrid dedupe, graph fallback, RAG Lab-safe metadata, and ask default compatibility.
- [x] Run `openspec validate experimental-graph-query-modes --strict`.
- [x] Run `openspec validate --all`.
- [x] Run backend tests.
- [x] Run frontend typecheck/build.
- [x] Commit locally without push or PR.
