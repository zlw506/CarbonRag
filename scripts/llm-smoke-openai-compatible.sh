#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${MODEL_API_BASE_URL:-http://127.0.0.1:11434/v1}"
API_KEY="${MODEL_API_KEY:-local-key}"
MODEL="${MODEL_NAME:-deepseek-r1:8b}"
TIMEOUT_SECONDS="${MODEL_TIMEOUT_SECONDS:-120}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="python"
if [[ -x "$REPO_ROOT/backend/.conda/python" ]]; then
  PYTHON_BIN="$REPO_ROOT/backend/.conda/python"
elif [[ -x "$REPO_ROOT/backend/.venv/bin/python" ]]; then
  PYTHON_BIN="$REPO_ROOT/backend/.venv/bin/python"
fi

export MODEL_API_BASE_URL="$BASE_URL"
export MODEL_API_KEY="$API_KEY"
export MODEL_NAME="$MODEL"
export MODEL_TIMEOUT_SECONDS="$TIMEOUT_SECONDS"

echo "==> Smoke testing OpenAI-compatible chat endpoint"
echo "Base URL: $BASE_URL"
echo "Model:    $MODEL"

"$PYTHON_BIN" - <<'PY'
import json
import os
import sys
import urllib.error
import urllib.request

base_url = os.environ["MODEL_API_BASE_URL"].rstrip("/")
api_key = os.environ.get("MODEL_API_KEY", "")
model = os.environ["MODEL_NAME"]
timeout = float(os.environ.get("MODEL_TIMEOUT_SECONDS") or 120)

headers = {"Content-Type": "application/json"}
if api_key:
    headers["Authorization"] = f"Bearer {api_key}"

def request(path, *, payload=None, method=None):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        headers=headers,
        method=method or ("POST" if payload is not None else "GET"),
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
        return response.status, body

try:
    status, body = request("/models")
    print(f"models ok: HTTP {status}")
except Exception as exc:
    print(f"models warning: {exc}")

payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You are a CarbonRag local model smoke test. Reply briefly."},
        {"role": "user", "content": "Reply with: local model connected"},
    ],
    "temperature": 0.1,
    "max_tokens": 64,
    "stream": False,
}

try:
    status, body = request("/chat/completions", payload=payload)
except urllib.error.HTTPError as exc:
    detail = exc.read().decode("utf-8", errors="replace")
    print(f"chat failed: HTTP {exc.code}\n{detail}", file=sys.stderr)
    raise

data = json.loads(body)
content = data.get("choices", [{}])[0].get("message", {}).get("content") or ""
content = content.strip()
if not content:
    raise SystemExit("chat failed: empty content")

print(f"chat ok: HTTP {status}")
print(f"answer: {content[:200]}")
PY

echo "==> Done"
