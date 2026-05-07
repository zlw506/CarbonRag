## Scope

This change adds an experimental strategy boundary around existing BM25 and vector retrieval. It is intended for RAG Lab and retrieval-only API verification only.

## Strategy Boundary

- `BM25Retriever` wraps the current BM25-backed adapter.
- `VectorRetriever` wraps the configured `VectorStoreAdapter`.
- `HybridRetriever` calls BM25 and vector retrievers, deduplicates by `chunk_id`, computes a simple merged score, and records the source retrievers for each chunk.

## Merge Strategy

- Request BM25 top-k and vector top-k independently.
- Normalize each retriever's scores against the maximum score returned by that retriever.
- For each `chunk_id`, keep one chunk and attach:
  - `bm25_score`
  - `vector_score`
  - `merged_score`
  - `from_bm25`
  - `from_vector`
  - `source_retrievers`
- Sort by `merged_score` and return the requested top-k.

## Fallback Strategy

- If the vector adapter healthcheck reports unavailable/degraded/error, vector retrieval returns zero hits with reason metadata.
- `HybridRetriever` still returns BM25 hits when vector retrieval is unavailable.
- Retrieval metadata records fallback status and fallback reason.

## Non-Goals

- No default `/ask` strategy change.
- No GraphRAG, Neo4j, rerank model, LightRAG local/global/hybrid implementation, or external code copy.
- No Qdrant, Milvus, Weaviate, or new mandatory dependency.
