## Why

CarbonRag now has graph index models, a rule-based graph builder, and RAG Lab graph candidate display. V1.8.0 should add LightRAG-style experimental graph query modes so developers can inspect local entity-centric, global relation-centric, and hybrid graph candidates without copying LightRAG code or changing default ask behavior.

## What Changes

- Add experimental graph query modes: `off`, `graph_local`, `graph_global`, and `graph_hybrid`.
- Add graph retrieval metadata for mode, counts, usage, and fallback reason.
- Add per-candidate graph fields for entity name, relation type, source chunks, score, and reason.
- Add a `GraphStoreAdapter` boundary with runtime/in-memory, fake, and optional Neo4j stub implementations.
- Expose graph mode selection in RAG Lab with an explicit experimental notice.
- Keep `/ask`, calc, report, session, BM25/vector/hybrid, and default graph mode unchanged.

## Capabilities

### Modified Capabilities

- `knowledge-rag`: Add experimental graph query modes and graph store adapter boundary.
- `frontend-shell-settings`: Add RAG Lab graph mode selector and fallback reason display.

## Impact

- Affected modules: M5 Knowledge/RAG, M2 RAG Lab.
- Apply-stage areas: RAG graph models/store/query, retrieval-only API schemas, RAG Lab types/page, and tests.
- No Neo4j dependency, GraphRAG production mode, LightRAG code copy, calc/report/session change, or default `/ask` change is proposed.
