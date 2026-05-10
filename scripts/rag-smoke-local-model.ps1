param(
  [string]$PythonPath = ".\backend\.conda\python.exe",
  [string]$ModelCacheDir = ".\data\outputs\models",
  [string]$MilvusUri = "http://127.0.0.1:19530",
  [string]$HfEndpoint = "https://hf-mirror.com"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if ($PythonPath -ne "python") {
  $PythonPath = (Resolve-Path $PythonPath).Path
}

$env:PYTHONPATH = (Resolve-Path ".\backend").Path
$env:RAG_EMBEDDING_PROVIDER = "bge_m3"
$env:RAG_MODEL_AUTO_DOWNLOAD = "false"
$env:RAG_MODEL_CACHE_DIR = (New-Item -ItemType Directory -Force -Path $ModelCacheDir).FullName
$env:RAG_EMBEDDING_DEVICE = "cpu"
$env:RAG_VECTOR_BACKEND = "milvus"
$env:RAG_REQUIRE_REAL_VECTOR = "true"
$env:RAG_MILVUS_URI = $MilvusUri
$env:RAG_RERANK_ENABLED = "true"
$env:RAG_RERANK_PROVIDER = "bge_reranker"
$env:RAG_RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
$env:HF_ENDPOINT = $HfEndpoint
$env:HF_HOME = (New-Item -ItemType Directory -Force -Path ".\data\outputs\hf-cache").FullName
$env:HUGGINGFACE_HUB_CACHE = (New-Item -ItemType Directory -Force -Path ".\data\outputs\hf-cache\hub").FullName
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

Push-Location ".\backend"
try {
  $smokeScript = Join-Path $root "data/outputs/milvus-docker/rag_local_model_smoke.py"
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $smokeScript) | Out-Null
  @'
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
reranked, applied, warning = BgeReranker().rerank(
    query="why should an enterprise maintain an energy ledger?",
    hits=[],
    top_k=3,
)
assert applied is False and warning == "no_hits"
local_reranker = Path(settings.rag_model_cache_dir) / "BAAI" / "bge-reranker-v2-m3"
assert local_reranker.exists(), f"reranker model missing: {local_reranker}"

print("==> Docker Milvus Standalone KB smoke")
service = RagSpineService(store=RagKnowledgeStore())
kb = service.create_kb(owner_user_id="rag-smoke-user", payload=KnowledgeBaseCreate(name="V1.6.5 local model smoke"))
doc = service.create_document(
    owner_user_id="rag-smoke-user",
    kb_id=kb.kb_id,
    payload=RagDocumentCreate(
        title="smoke.md",
        text="Carbon peaking and carbon neutrality require an enterprise energy ledger with purchased electricity, gas, and emission factors.",
    ),
)
service.parse_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
service.chunk_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
indexed = service.index_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
print("index", indexed.status, indexed.vector_backend, indexed.degraded, indexed.error_message)
assert indexed.status == "indexed", indexed.error_message

result = service.search(
    owner_user_id="rag-smoke-user",
    request=RagSearchRequest(query="enterprise energy ledger", kb_id=kb.kb_id, mode="hybrid_rerank", top_k=3),
)
print("trace", result.trace.model_dump())
print("hits", len(result.hits))
assert result.hits
assert result.trace.vector_runtime == "milvus_standalone"
assert result.trace.dense_count >= 1
assert result.trace.sparse_count >= 1
assert result.trace.rerank_applied is True
assert result.trace.degraded is False
print("==> local RAG-Pro model smoke passed")
'@ | Set-Content -LiteralPath $smokeScript -Encoding UTF8
  & $PythonPath -W ignore $smokeScript
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}
finally {
  Pop-Location
}
