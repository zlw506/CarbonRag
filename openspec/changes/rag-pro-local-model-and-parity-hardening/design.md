# Design: local RAG-Pro model hardening

## Model Cache Contract

Model files are local runtime assets and must stay out of Git. The default cache is:

- `RAG_MODEL_CACHE_DIR=./data/outputs/models`
- `HF_HOME=./data/outputs/hf-cache`
- `HUGGINGFACE_HUB_CACHE=./data/outputs/hf-cache/hub`

The smoke scripts explicitly set these values so Hugging Face does not use `C:\Users\<user>\.cache\huggingface` by accident.

## Default Provider

`RAG_EMBEDDING_PROVIDER=bge_m3` is the default. `openai_compatible` remains supported only for teams with a real embedding endpoint.

## Smoke Gates

The local smoke must verify:

- BGE-M3 returns two dense vectors for two inputs.
- Dense vector dimension is 1024.
- Sparse lexical weights are non-empty.
- The reranker model directory exists and the reranker can initialize or fail explicitly.
- Milvus Lite/Milvus can index at least one chunk and search it back.

If Milvus Lite is unavailable on Windows, the smoke must fail visibly and document the blocker instead of reporting success.
