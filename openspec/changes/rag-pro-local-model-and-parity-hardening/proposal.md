# Change: RAG-Pro local model and parity hardening

## Why

V1.6.4 built the RAG-Pro shaped spine, but the default model path was still ambiguous and could fall back to cloud embeddings or degraded paths. CarbonRag must prove the local RAG-Pro route: BGE-M3 dense/sparse embeddings, bge-reranker, Milvus Lite/Milvus vector indexing, and KB/Test QA/Ask citations.

## What Changes

- Default CarbonRag RAG embedding provider back to `bge_m3`.
- Add repeatable model download scripts for `BAAI/bge-m3` and `BAAI/bge-reranker-v2-m3`.
- Add local model smoke scripts that verify dense dimension, sparse weights, reranker availability, Milvus Lite indexing, RAG search hits, and non-degraded trace.
- Keep OpenAI-compatible embeddings as an advanced option only when a real `/v1/embeddings` endpoint exists.
- Document the C-drive cache pitfall and require large-disk model cache paths.

## Non-Goals

- Do not add another RAG facade.
- Do not switch Ask back to old RagEngine fallback.
- Do not vendor model files or third-party project source into Git.
