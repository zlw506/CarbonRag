# Design: RAG-Pro Milvus Runtime Profiles

## Runtime Profiles

CarbonRag now distinguishes requested vector backend from actual runtime:

- `milvus` with `http://127.0.0.1:19530` means Docker Milvus Standalone.
- `milvus_lite` with a local `.db` path means Milvus Lite and is only for WSL/Linux/macOS.
- `memory` means development-only lexical fallback and is always degraded for RAG-Pro acceptance.

## Windows Delivery

Native Windows does not use Milvus Lite. Windows developers run Docker Desktop and start Milvus Standalone through the official `standalone_embed.bat` script downloaded into `data/outputs/milvus-docker/`.

## Trace Contract

RAG trace and health responses expose both:

- `vector_backend`: configured product backend family.
- `vector_runtime`: actual runtime such as `milvus_standalone`, `milvus_lite`, or `memory_dev`.

If `RAG_REQUIRE_REAL_VECTOR=true`, a memory fallback or unavailable Milvus/BGE path cannot be presented as successful RAG-Pro acceptance.
