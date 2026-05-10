## 1. Configuration

- [x] Default `RAG_EMBEDDING_PROVIDER` to `bge_m3`.
- [x] Keep `RAG_MODEL_AUTO_DOWNLOAD=false` outside explicit smoke/download scripts.
- [x] Keep model caches under ignored `data/outputs`.

## 2. Dependencies

- [x] Require `FlagEmbedding`.
- [x] Require `pymilvus[model]`.
- [x] Explicitly require `huggingface_hub`.

## 3. Scripts

- [x] Add Windows/Linux model download scripts.
- [x] Add Windows/Linux local model smoke scripts.
- [ ] Run local BGE-M3 + reranker + Milvus Lite smoke on a platform where Milvus Lite is available.

## 4. Validation

- [ ] Confirm KB create -> document parse -> chunk -> Milvus index -> test QA -> Ask trace end to end.
- [ ] Confirm missing BGE/Milvus/reranker reports degraded or failed.
