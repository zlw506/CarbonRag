## Why

CarbonRag has unified chunk contracts, retrieval traces, RAG Lab observability, and BM25/vector/hybrid retrieval experiments. V1.7.0 should add the first graph-index data model and builder boundary so chunks can produce entity, relation, summary, and candidate metadata without introducing a graph database or changing default ask behavior.

## What Changes

- Extend the existing graph skeleton into concrete `GraphEntity`, `GraphRelation`, `GraphCommunitySummary`, and `GraphCandidate` models.
- Add a lightweight `GraphIndexBuilder` implementation that rule-extracts candidate entities and relations from `ChunkRecord` text.
- Add an in-memory graph candidate store that can return graph candidates by `chunk_id`.
- Attach graph candidate metadata to retrieval-only/RAG Lab responses only.
- Keep `/ask`, calc, report, session, BM25/vector/hybrid, and ingestion defaults unchanged.

## Capabilities

### Modified Capabilities

- `knowledge-rag`: Add experimental graph-index models, builder, and graph candidate metadata.
- `frontend-shell-settings`: Display optional graph entities, relations, and candidates in RAG Lab without breaking empty metadata states.

## Impact

- Affected modules: M5 Knowledge/RAG, M2 RAG Lab display.
- Apply-stage areas: `backend/app/rag/graph.py`, RAG retrieval metadata, frontend RAG types/page, and tests.
- No Neo4j, graph database dependency, GraphRAG query mode, LightRAG local/global/hybrid query, calc/report/session change, or default `/ask` change is proposed.
