param(
  [string]$BaseUrl = $env:MODEL_API_BASE_URL,
  [string]$ApiKey = $env:MODEL_API_KEY,
  [string]$Model = $env:MODEL_NAME,
  [int]$TimeoutSeconds = 120
)

$ErrorActionPreference = "Stop"

if (-not $BaseUrl) { $BaseUrl = "http://127.0.0.1:11434/v1" }
if (-not $ApiKey) { $ApiKey = "local-key" }
if (-not $Model) { $Model = "deepseek-r1:8b" }

$repoRoot = Split-Path -Parent $PSScriptRoot
$pythonCandidates = @(
  (Join-Path $repoRoot "backend\.conda\python.exe"),
  (Join-Path $repoRoot "backend\.venv\Scripts\python.exe"),
  "python"
)

$python = $null
foreach ($candidate in $pythonCandidates) {
  try {
    & $candidate --version *> $null
    if ($LASTEXITCODE -eq 0) {
      $python = $candidate
      break
    }
  } catch {
    continue
  }
}

if (-not $python) {
  throw "No Python executable found. Expected backend\.conda\python.exe, backend\.venv\Scripts\python.exe, or python on PATH."
}

$env:MODEL_API_BASE_URL = $BaseUrl
$env:MODEL_API_KEY = $ApiKey
$env:MODEL_NAME = $Model
$env:MODEL_TIMEOUT_SECONDS = [string]$TimeoutSeconds

Write-Host "==> Smoke testing OpenAI-compatible chat endpoint"
Write-Host "Base URL: $BaseUrl"
Write-Host "Model:    $Model"

$script = @'
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
'@

$script | & $python -

Write-Host "==> Done"
