param(
  [string]$PythonPath = ".\backend\.conda\python.exe",
  [string]$ModelCacheDir = ".\data\outputs\models",
  [string]$HfEndpoint = "https://hf-mirror.com"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if ($PythonPath -ne "python") {
  $PythonPath = (Resolve-Path $PythonPath).Path
}

$modelCache = (New-Item -ItemType Directory -Force -Path $ModelCacheDir).FullName
$hfHome = (New-Item -ItemType Directory -Force -Path ".\data\outputs\hf-cache").FullName
$hubCache = (New-Item -ItemType Directory -Force -Path ".\data\outputs\hf-cache\hub").FullName

$env:HF_ENDPOINT = $HfEndpoint
$env:HF_HOME = $hfHome
$env:HUGGINGFACE_HUB_CACHE = $hubCache
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

Write-Host "==> Downloading RAG-Pro local models"
Write-Host "Model cache: $modelCache"
Write-Host "HF cache:    $hubCache"

@'
from pathlib import Path
from huggingface_hub import snapshot_download

base = Path(r"__MODEL_CACHE__")
ignore = ["imgs/*", "*.onnx", "*.onnx_data", "onnx/*"]

for repo_id, local_dir in [
    ("BAAI/bge-m3", base / "BAAI" / "bge-m3"),
    ("BAAI/bge-reranker-v2-m3", base / "BAAI" / "bge-reranker-v2-m3"),
]:
    print(f"downloading {repo_id} -> {local_dir}")
    snapshot_download(repo_id=repo_id, local_dir=str(local_dir), ignore_patterns=ignore)
    print(f"done {repo_id}")
'@.Replace("__MODEL_CACHE__", $modelCache.Replace("\", "\\")) | & $PythonPath -

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

Write-Host "==> RAG model download complete"
