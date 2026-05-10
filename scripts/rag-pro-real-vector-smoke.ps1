param(
  [string]$BackendPath = "backend",
  [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"

if (-not $PythonPath) {
  $condaPython = Join-Path $BackendPath ".conda\python.exe"
  $PythonPath = if (Test-Path $condaPython) { $condaPython } else { "python" }
}
if ($PythonPath -ne "python") {
  $PythonPath = (Resolve-Path $PythonPath).Path
}

$env:RAG_VECTOR_BACKEND = "milvus_lite"
$env:RAG_REQUIRE_REAL_VECTOR = "true"
$env:RAG_EMBEDDING_PROVIDER = "bge_m3"
$env:RAG_EMBEDDING_MODEL = "BAAI/bge-m3"
$env:RAG_MODEL_CACHE_DIR = "./data/outputs/models"
$env:RAG_MODEL_AUTO_DOWNLOAD = "true"
$env:RAG_RERANK_PROVIDER = "bge_reranker"
$env:RAG_RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
$env:RAG_MILVUS_URI = "./data/outputs/milvus_lite/carbonrag-smoke.db"
if (-not $env:HF_ENDPOINT) {
  $env:HF_ENDPOINT = "https://hf-mirror.com"
}
$env:HF_HOME = Join-Path (Get-Location) "data\outputs\hf-cache"
$env:HUGGINGFACE_HUB_CACHE = Join-Path (Get-Location) "data\outputs\hf-cache\hub"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

Push-Location $BackendPath
try {
  @'
from app.rag.embeddings import embed_documents, embed_query
from app.rag.kb.models import KnowledgeBaseCreate, RagDocumentCreate, RagSearchRequest
from app.rag.kb.storage import RagKnowledgeStore
from app.rag.spine import RagSpineService

print("==> loading BGE-M3 and Milvus Lite")
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
    request=RagSearchRequest(query="Why should an enterprise maintain an energy data ledger?", kb_id=kb.kb_id, mode="hybrid_rerank", top_k=3),
)
print("trace:", result.trace.model_dump())
print("hits:", len(result.hits))
if not result.hits:
    raise SystemExit(3)
'@ | & $PythonPath -
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}
finally {
  Pop-Location
}
