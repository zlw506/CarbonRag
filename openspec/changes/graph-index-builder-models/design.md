## Scope

This change adds a minimal graph index boundary and experimental graph candidate output. It does not add a persistent production graph database or graph-augmented answer generation.

## Model Strategy

- `GraphEntity` stores a normalized entity id, display name, type, source chunk ids, confidence, and metadata.
- `GraphRelation` links two graph entities with a relation type, description, source chunk ids, confidence, and metadata.
- `GraphCommunitySummary` groups extracted entities and relations into a first-pass summary.
- `GraphCandidate` is the RAG Lab-facing display object for graph metadata.

## Builder Strategy

- The first builder is rule based and dependency-light.
- It extracts known policy names, regions, enterprise names, standard/measurement terms, and carbon-accounting terms from chunk text.
- It creates simple co-occurrence relations when multiple entities appear in the same chunk.
- Empty chunk input returns a successful empty result.

## Storage Strategy

- Use an in-memory store for V1.7.0.
- Store entities, relations, summaries, and candidates keyed by source chunk id.
- Do not connect Neo4j or any graph database.

## RAG Lab Strategy

- Retrieval-only builds graph candidates from the returned evidence chunks and exposes them under metadata/provider metadata.
- RAG Lab displays graph entities, relations, and candidates when present and remains stable when fields are missing or empty.

## Non-Goals

- No full GraphRAG.
- No LightRAG local/global/hybrid query implementation.
- No community detection algorithm.
- No ingestion-blocking graph build.
