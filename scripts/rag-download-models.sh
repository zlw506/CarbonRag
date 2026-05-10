#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_PATH="${PYTHON_PATH:-python}"
if [ -x "backend/.conda/python.exe" ]; then
  PYTHON_PATH="backend/.conda/python.exe"
fi

MODEL_CACHE_DIR="${RAG_MODEL_CACHE_DIR:-./data/outputs/models}"
export HF_ENDPOINT="${HF_ENDPOINT:-https://hf-mirror.com}"
export HF_HOME="${HF_HOME:-$ROOT_DIR/data/outputs/hf-cache}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-$ROOT_DIR/data/outputs/hf-cache/hub}"
export HF_HUB_DISABLE_SYMLINKS_WARNING=1

mkdir -p "$MODEL_CACHE_DIR" "$HF_HOME" "$HUGGINGFACE_HUB_CACHE"

echo "==> Downloading RAG-Pro local models"
echo "Model cache: $MODEL_CACHE_DIR"
echo "HF cache:    $HUGGINGFACE_HUB_CACHE"

"$PYTHON_PATH" - <<PY
from pathlib import Path
from huggingface_hub import snapshot_download

base = Path(r"$MODEL_CACHE_DIR")
ignore = ["imgs/*", "*.onnx", "*.onnx_data", "onnx/*"]

for repo_id, local_dir in [
    ("BAAI/bge-m3", base / "BAAI" / "bge-m3"),
    ("BAAI/bge-reranker-v2-m3", base / "BAAI" / "bge-reranker-v2-m3"),
]:
    print(f"downloading {repo_id} -> {local_dir}")
    snapshot_download(repo_id=repo_id, local_dir=str(local_dir), ignore_patterns=ignore)
    print(f"done {repo_id}")
PY

echo "==> RAG model download complete"
