param(
  [string]$MilvusUri = "http://127.0.0.1:19530",
  [string]$PythonPath = ".\backend\.conda\python.exe"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if ($PythonPath -ne "python") {
  $PythonPath = (Resolve-Path $PythonPath).Path
}

$env:CARBONRAG_MILVUS_SMOKE_URI = $MilvusUri
$env:RAG_VECTOR_BACKEND = "milvus"
$env:RAG_MILVUS_URI = $MilvusUri
$env:RAG_REQUIRE_REAL_VECTOR = "true"
$env:PYTHONPATH = (Resolve-Path ".\backend").Path

Push-Location ".\backend"
try {
  $smokeScript = Join-Path $root "data/outputs/milvus-docker/milvus_standalone_smoke.py"
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $smokeScript) | Out-Null
  @'
import os
from uuid import uuid4

from pymilvus import MilvusClient

uri = os.environ["CARBONRAG_MILVUS_SMOKE_URI"]
collection = "carbonrag_smoke_" + uuid4().hex[:8]
client = MilvusClient(uri=uri)
print("connected", uri)

try:
    client.create_collection(collection_name=collection, dimension=4, metric_type="COSINE", auto_id=False)
    rows = [
        {"id": 1, "vector": [0.1, 0.2, 0.3, 0.4]},
        {"id": 2, "vector": [0.4, 0.3, 0.2, 0.1]},
    ]
    client.insert(collection_name=collection, data=rows)
    result = client.search(collection_name=collection, data=[[0.1, 0.2, 0.3, 0.4]], limit=1)
    assert result and result[0], "empty search result"
    print("search ok", result[0][0].get("id"))
finally:
    if client.has_collection(collection):
        client.drop_collection(collection_name=collection)

print("milvus standalone smoke passed")
'@ | Set-Content -LiteralPath $smokeScript -Encoding UTF8
  & $PythonPath -W ignore $smokeScript
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}
finally {
  Pop-Location
}
