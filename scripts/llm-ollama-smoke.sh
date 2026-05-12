#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
MODEL="${OLLAMA_MODEL:-deepseek-r1:8b}"
BASE_URL="${BASE_URL%/}"
BASE_URL="${BASE_URL%/api}"
BASE_URL="${BASE_URL%/v1}"

echo "==> Checking Ollama tags at ${BASE_URL}/api/tags"
MODELS="$(curl -fsS "${BASE_URL}/api/tags")"
if ! printf '%s' "$MODELS" | grep -Fq "\"name\":\"${MODEL}\""; then
  echo "Model '${MODEL}' was not found. Run: ollama pull ${MODEL}" >&2
  echo "$MODELS" >&2
  exit 1
fi

echo "==> Running Ollama chat smoke with ${MODEL}"
RESPONSE="$(
  curl -fsS "${BASE_URL}/api/chat" \
    -H 'Content-Type: application/json' \
    -d "{
      \"model\": \"${MODEL}\",
      \"messages\": [{\"role\": \"user\", \"content\": \"只回答 OK\"}],
      \"stream\": false,
      \"keep_alive\": \"10m\",
      \"think\": false,
      \"options\": {\"num_ctx\": 8192, \"temperature\": 0}
    }"
)"
echo "$RESPONSE"
echo "==> Ollama smoke passed"
