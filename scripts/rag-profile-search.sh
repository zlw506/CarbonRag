#!/usr/bin/env bash
set -euo pipefail

API_BASE="${CARBONRAG_API_BASE:-http://127.0.0.1:8000/api/v1}"
KB_ID="${CARBONRAG_KB_ID:-${1:-}}"
QUERY="${CARBONRAG_QUERY:-${2:-青木制造 2025 年第一季度合计外购电力是多少？}}"
MODE="${CARBONRAG_RAG_MODE:-${3:-hybrid_rerank}}"
TOP_K="${CARBONRAG_TOP_K:-5}"
COOKIE="${CARBONRAG_COOKIE:-}"
OUTPUT="${CARBONRAG_PROFILE_OUTPUT:-logs/rag/profile-v1.6.29.json}"

if [[ -z "$KB_ID" ]]; then
  echo "Usage: CARBONRAG_KB_ID=<id> $0 [kb_id] [query] [mode]" >&2
  exit 2
fi

mkdir -p "$(dirname "$OUTPUT")"
BODY="$(python - "$KB_ID" "$QUERY" "$MODE" "$TOP_K" <<'PY'
import json, sys
kb_id, query, mode, top_k = sys.argv[1:]
print(json.dumps({"kb_id": kb_id, "query": query, "mode": mode, "top_k": int(top_k)}))
PY
)"
if [[ -n "$COOKIE" ]]; then
  RESULT="$(curl -sS -X POST "$API_BASE/rag/search" -H "Content-Type: application/json" -H "Cookie: $COOKIE" -d "$BODY")"
else
  RESULT="$(curl -sS -X POST "$API_BASE/rag/search" -H "Content-Type: application/json" -d "$BODY")"
fi

python - "$OUTPUT" "$API_BASE" "$KB_ID" "$QUERY" "$MODE" "$TOP_K" "$RESULT" <<'PY'
import json, sys, datetime
path, api_base, kb_id, query, mode, top_k, raw = sys.argv[1:]
payload = {
    "kind": "search",
    "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "api_base": api_base,
    "kb_id": kb_id,
    "query": query,
    "mode": mode,
    "top_k": int(top_k),
    "result": json.loads(raw),
}
open(path, "w", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False, indent=2))
PY
echo "Wrote $OUTPUT"
