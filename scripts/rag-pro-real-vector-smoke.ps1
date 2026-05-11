param(
  [string]$BackendPath = "backend",
  [string]$PythonPath = "",
  [string]$MilvusUri = "http://127.0.0.1:19530"
)

$ErrorActionPreference = "Stop"

if (-not $PythonPath) {
  $condaPython = Join-Path $BackendPath ".conda\python.exe"
  $PythonPath = if (Test-Path $condaPython) { $condaPython } else { "python" }
}
if ($PythonPath -ne "python") {
  $PythonPath = (Resolve-Path $PythonPath).Path
}

$env:RAG_VECTOR_BACKEND = "milvus"
$env:RAG_REQUIRE_REAL_VECTOR = "true"
$env:RAG_EMBEDDING_PROVIDER = "bge_m3"
$env:RAG_EMBEDDING_MODEL = "BAAI/bge-m3"
$env:RAG_MODEL_CACHE_DIR = (New-Item -ItemType Directory -Force -Path ".\data\outputs\models").FullName
$env:RAG_MODEL_AUTO_DOWNLOAD = "false"
$env:RAG_RERANK_PROVIDER = "bge_reranker"
$env:RAG_RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
$env:RAG_MILVUS_URI = $MilvusUri
if (-not $env:HF_ENDPOINT) {
  $env:HF_ENDPOINT = "https://hf-mirror.com"
}
$env:HF_HOME = Join-Path (Get-Location) "data\outputs\hf-cache"
$env:HUGGINGFACE_HUB_CACHE = Join-Path (Get-Location) "data\outputs\hf-cache\hub"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
$env:PYTHONPATH = (Resolve-Path $BackendPath).Path

Push-Location $BackendPath
try {
  $smokeScript = Join-Path (Split-Path -Parent (Get-Location)) "data/outputs/milvus-docker/rag_pro_real_vector_smoke.py"
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $smokeScript) | Out-Null
  @'
from app.rag.embeddings import embed_documents, embed_query
from app.rag.kb.models import KnowledgeBaseCreate, RagDocumentCreate, RagSearchRequest
from app.rag.kb.storage import RagKnowledgeStore
from app.rag.spine import RagSpineService

print("==> loading BGE-M3 and Docker Milvus Standalone")
embed_documents(["Carbon neutrality and carbon peaking require an enterprise energy data ledger."])
embed_query("energy data ledger")

service = RagSpineService(store=RagKnowledgeStore())
kb = service.create_kb(owner_user_id="rag-smoke-user", payload=KnowledgeBaseCreate(name="V1.6.4 real vector smoke"))
doc = service.create_document(
    owner_user_id="rag-smoke-user",
    kb_id=kb.kb_id,
    payload=RagDocumentCreate(title="smoke.md", text="Carbon neutrality and carbon peaking require an enterprise energy data ledger with electricity and gas records."),
)
service.parse_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
service.chunk_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
indexed = service.index_document(owner_user_id="rag-smoke-user", kb_id=kb.kb_id, doc_id=doc.doc_id)
print("index:", indexed.status, indexed.vector_backend, indexed.error_message)
if indexed.status != "indexed":
    raise SystemExit(2)
result = service.search(
    owner_user_id="rag-smoke-user",
    request=RagSearchRequest(query="enterprise energy data ledger", kb_id=kb.kb_id, mode="hybrid_rerank", top_k=3),
)
print("trace:", result.trace.model_dump())
print("hits:", len(result.hits))
if not result.hits:
    raise SystemExit(3)
if result.trace.vector_runtime != "milvus_standalone":
    raise SystemExit(f"unexpected vector runtime: {result.trace.vector_runtime}")
if result.trace.dense_count < 1:
    raise SystemExit(f"dense retrieval did not return hits: {result.trace.model_dump()}")
if result.trace.sparse_count < 1:
    raise SystemExit(f"sparse retrieval did not return hits: {result.trace.model_dump()}")
if not result.trace.rerank_applied:
    raise SystemExit(f"rerank was not applied: {result.trace.model_dump()}")
if result.trace.degraded:
    raise SystemExit(f"RAG trace degraded unexpectedly: {result.trace.model_dump()}")
'@ | Set-Content -LiteralPath $smokeScript -Encoding UTF8
  & $PythonPath -W ignore $smokeScript
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}
finally {
  Pop-Location
}
