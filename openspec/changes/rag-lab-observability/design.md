## Scope

This change is intentionally narrow. It improves observability for the existing V1.3 RAG Lab and retrieval-only API only.

## Backend

- Extend retrieval metadata additively, keeping existing keys intact.
- Treat BM25 fallback as an observable retrieval layer with both a boolean `fallback_used` and a string `fallback_reason`.
- Populate public/private counts from returned chunks when possible; otherwise leave the values nullable.
- Wrap unexpected retrieval failures in a structured `HTTPException` detail so the frontend can display status, message, and backend detail.

## Frontend

- Derive `backendBaseUrl` from `env.apiBaseUrl` and show it alongside the retrieval endpoint.
- Show the current request body fields before and after a retrieval run.
- Render optional metadata defensively so older or partial responses do not crash the page.
- Convert Axios/FastAPI error shapes into a visible status/message/detail block.

## Non-Goals

- No Docling, MinerU, pgvector, Qdrant, Neo4j, GraphRAG, LangGraph, Keycloak, Kubernetes, or large dependency integration.
- No changes to answer generation, sessions, report generation, or carbon calculation.
