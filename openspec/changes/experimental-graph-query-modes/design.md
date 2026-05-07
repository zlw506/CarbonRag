## Scope

This change adds experimental graph query modes over the existing rule-based graph candidate builder. It does not implement a production graph database or LightRAG's full algorithm.

## Query Modes

- `off`: do not run graph candidate filtering.
- `graph_local`: prioritize candidates whose entities match the query.
- `graph_global`: prioritize candidates with relation/community evidence.
- `graph_hybrid`: combine local candidates, global candidates, and the existing retrieved chunks while deduplicating by candidate id and source chunk ids.

## Metadata Strategy

Retrieval-only metadata will include:

- `graph_mode`
- `graph_entity_count`
- `graph_relation_count`
- `graph_candidate_count`
- `graph_used`
- `graph_fallback_reason`

Graph candidates will include:

- `entity_name`
- `relation_type`
- `source_chunk_ids`
- `score`
- `reason`

## Store Strategy

- `RuntimeGraphStoreAdapter` wraps the current in-memory graph candidate store.
- `FakeGraphStoreAdapter` supports deterministic tests.
- `Neo4jGraphStoreAdapter` is a stub that reports unavailable and does not require Neo4j dependencies.

## Non-Goals

- No fork or copy of LightRAG.
- No Neo4j dependency.
- No default ask behavior change.
- No large refactor or community detection implementation.
