#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_PATH="${PYTHON_PATH:-python}"
if [ -x "backend/.conda/python.exe" ]; then
  PYTHON_PATH="backend/.conda/python.exe"
fi

export PYTHONPATH="$ROOT_DIR/backend"
export RAG_EMBEDDING_PROVIDER=bge_m3
export RAG_MODEL_AUTO_DOWNLOAD=false
export RAG_MODEL_CACHE_DIR="${RAG_MODEL_CACHE_DIR:-$ROOT_DIR/data/outputs/models}"
export RAG_EMBEDDING_DEVICE=cpu
export RAG_VECTOR_BACKEND=milvus
export RAG_REQUIRE_REAL_VECTOR=true
export RAG_MILVUS_URI="${RAG_MILVUS_URI:-http://127.0.0.1:19530}"
export RAG_RERANK_ENABLED=true
export RAG_RERANK_PROVIDER=bge_reranker
export RAG_RERANK_MODEL=BAAI/bge-reranker-v2-m3
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HOME="${HF_HOME:-$ROOT_DIR/data/outputs/hf-cache}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-$ROOT_DIR/data/outputs/hf-cache/hub}"
export HF_HUB_DISABLE_SYMLINKS_WARNING=1

mkdir -p "$RAG_MODEL_CACHE_DIR" "$HF_HOME" "$HUGGINGFACE_HUB_CACHE"

cd backend
"$PYTHON_PATH" - <<'PY'
from pathlib import Path

from app.core.config import get_settings
from app.rag.embeddings import embed_documents, embed_query
from app.rag.kb.models import KnowledgeBaseCreate, RagDocumentCreate, RagSearchRequest
from app.rag.kb.storage import RagKnowledgeStore
from app.rag.retrieval.rerank import BgeReranker
from app.rag.spine import RagSpineService

settings = get_settings()
print("==> BGE-M3 smoke")
emb = embed_documents(["carbon peaking", "enterprise carbon accounting"])
print(emb.provider, len(emb.dense), len(emb.dense[0]), bool(emb.sparse and emb.sparse[0]))
assert emb.provider in {"bge_m3", "bge-m3", "bge"}
assert len(emb.dense) == 2
assert len(emb.dense[0]) == 1024
assert bool(emb.sparse and emb.sparse[0])

query_dense, query_sparse = embed_query("purchased electricity emission factor")
assert len(query_dense) == 1024
assert query_sparse

print("==> BGE reranker smoke")
reranked, applied, warning = BgeReranker().rerank(query="why should an enterprise maintain an energy ledger?", hits=[], top_k=3)
assert applied is False and warning == "no_hits"
local_reranker = Path(settings.rag_model_cache_dir) / "BAAI" / "bge-reranker-v2-m3"
assert local_reranker.exists(), f"reranker model missing: {local_reranker}"

print("==> Docker Milvus Standalone KB smoke")
service = RagSpineService(store=RagKnowledgeStore())
kb = service.create_kb(owner_user_id="rag-smoke-user", payload=KnowledgeBaseCreate(name="V1.6.5 local model smoke"))
doc = service.create_document(
    owner_user_id="rag-smoke-user",
    kb_id=kb.kb_id,
    payload=RagDocumentCreate(title="smoke.md", text="Carbon peaking and carbon neutrality require an enterprise energy ledger with purchased electricity, gas, and emission factors."),
)
service.parse_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
service.chunk_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
indexed = service.index_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
print("index", indexed.status, indexed.vector_backend, indexed.degraded, indexed.error_message)
assert indexed.status == "indexed", indexed.error_message

result = service.search(owner_user_id="rag-smoke-user", request=RagSearchRequest(query="why should an enterprise maintain an energy ledger?", kb_id=kb.kb_id, mode="hybrid_rerank", top_k=3))
print("trace", result.trace.model_dump())
print("hits", len(result.hits))
assert result.hits
assert result.trace.vector_runtime == "milvus_standalone"
assert result.trace.degraded is False
print("==> local RAG-Pro model smoke passed")
PY
