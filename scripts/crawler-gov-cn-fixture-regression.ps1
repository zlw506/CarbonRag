$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $repo "backend"
$python = Join-Path $backend ".conda\python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}
Push-Location $backend
$env:PYTHONPATH = "."
& $python -m pytest tests/test_gov_cn_policy_extractor.py tests/test_crawler_to_rag_bridge.py -q
Pop-Location
