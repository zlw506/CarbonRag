## MODIFIED Requirements

### Requirement: Knowledge/RAG uses a real vector runtime for RAG-Pro acceptance

CarbonRag SHALL distinguish configured vector backend from the actual vector runtime and SHALL not present development fallback as successful RAG-Pro acceptance.

#### Scenario: Windows developer uses Docker Milvus

- **WHEN** `RAG_VECTOR_BACKEND=milvus` and `RAG_MILVUS_URI=http://127.0.0.1:19530`
- **THEN** RAG health, stats, search, index, and Ask traces report `vector_runtime=milvus_standalone`

#### Scenario: Milvus Lite profile is used

- **WHEN** `RAG_VECTOR_BACKEND=milvus_lite` with a local `.db` URI
- **THEN** CarbonRag treats the runtime as `milvus_lite` and documents that native Windows is not supported

#### Scenario: Memory fallback is used

- **WHEN** `RAG_VECTOR_BACKEND=memory`
- **THEN** CarbonRag reports `vector_runtime=memory_dev` and marks the path degraded for RAG-Pro acceptance
