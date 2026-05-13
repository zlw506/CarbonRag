#!/usr/bin/env bash
set -euo pipefail

API_BASE="${CARBONRAG_API_BASE:-http://127.0.0.1:8000/api/v1}"
KB_ID="${CARBONRAG_KB_ID:-${1:-}}"
DOC_ID="${CARBONRAG_DOC_ID:-${2:-}}"
PIPELINE_MODE="${CARBONRAG_PIPELINE_MODE:-${3:-quick}}"
COOKIE="${CARBONRAG_COOKIE:-}"
OUTPUT="${CARBONRAG_PROFILE_OUTPUT:-logs/rag/profile-v1.6.29.json}"

if [[ -z "$KB_ID" || -z "$DOC_ID" ]]; then
  echo "Usage: CARBONRAG_KB_ID=<id> CARBONRAG_DOC_ID=<id> $0 [kb_id] [doc_id] [quick|acceptance]" >&2
  exit 2
fi

mkdir -p "$(dirname "$OUTPUT")"
BODY="{\"pipeline_mode\":\"$PIPELINE_MODE\"}"
if [[ -n "$COOKIE" ]]; then
  RESULT="$(curl -sS -X POST "$API_BASE/kb/$KB_ID/documents/$DOC_ID/run-pipeline" -H "Content-Type: application/json" -H "Cookie: $COOKIE" -d "$BODY")"
else
  RESULT="$(curl -sS -X POST "$API_BASE/kb/$KB_ID/documents/$DOC_ID/run-pipeline" -H "Content-Type: application/json" -d "$BODY")"
fi

python - "$OUTPUT" "$API_BASE" "$KB_ID" "$DOC_ID" "$PIPELINE_MODE" "$RESULT" <<'PY'
import json, sys, datetime
path, api_base, kb_id, doc_id, mode, raw = sys.argv[1:]
payload = {
    "kind": "pipeline",
    "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "api_base": api_base,
    "kb_id": kb_id,
    "doc_id": doc_id,
    "pipeline_mode": mode,
    "result": json.loads(raw),
}
open(path, "w", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False, indent=2))
PY
echo "Wrote $OUTPUT"
