#!/usr/bin/env bash
set -euo pipefail

BACKEND_PATH="${1:-backend}"
MILVUS_URI="${MILVUS_URI:-http://127.0.0.1:19530}"
PYTHON_PATH="${PYTHON_PATH:-python}"
if [ -x "$BACKEND_PATH/.conda/python.exe" ]; then
  PYTHON_PATH="$BACKEND_PATH/.conda/python.exe"
fi

export RAG_VECTOR_BACKEND=milvus
export RAG_REQUIRE_REAL_VECTOR=true
export RAG_EMBEDDING_PROVIDER=bge_m3
export RAG_EMBEDDING_MODEL=BAAI/bge-m3
export RAG_MODEL_CACHE_DIR=./data/outputs/models
export RAG_MODEL_AUTO_DOWNLOAD=true
export RAG_RERANK_PROVIDER=bge_reranker
export RAG_RERANK_MODEL=BAAI/bge-reranker-v2-m3
export RAG_MILVUS_URI="$MILVUS_URI"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"

cd "$BACKEND_PATH"
"$PYTHON_PATH" - <<'PY'
from app.rag.embeddings import embed_documents, embed_query
from app.rag.kb.models import KnowledgeBaseCreate, RagDocumentCreate, RagSearchRequest
from app.rag.kb.storage import RagKnowledgeStore
from app.rag.spine import RagSpineService

print("==> loading BGE-M3 and Docker Milvus Standalone")
embed_documents(["双碳目标包括碳达峰和碳中和。"])
embed_query("双碳目标")

service = RagSpineService(store=RagKnowledgeStore())
kb = service.create_kb(owner_user_id="rag-smoke-user", payload=KnowledgeBaseCreate(name="V1.6.4 real vector smoke"))
doc = service.create_document(
    owner_user_id="rag-smoke-user",
    kb_id=kb.kb_id,
    payload=RagDocumentCreate(title="smoke.md", text="双碳目标包括碳达峰和碳中和。企业需要建立能源数据台账。"),
)
service.parse_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
service.chunk_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
indexed = service.index_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
print("index:", indexed.status, indexed.vector_backend, indexed.error_message)
if indexed.status != "indexed":
    raise SystemExit(2)
result = service.search(
    owner_user_id="rag-smoke-user",
    request=RagSearchRequest(query="企业为什么要建立能源数据台账？", kb_id=kb.kb_id, mode="hybrid_rerank", top_k=3),
)
print("trace:", result.trace.model_dump())
print("hits:", len(result.hits))
if not result.hits:
    raise SystemExit(3)
if result.trace.vector_runtime != "milvus_standalone":
    raise SystemExit(f"unexpected vector runtime: {result.trace.vector_runtime}")
PY
