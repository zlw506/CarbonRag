param(
  [string]$RuntimeDir = "data/outputs/milvus-docker"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$scriptPath = Join-Path (Resolve-Path $RuntimeDir).Path "standalone_embed.bat"
if (-not (Test-Path $scriptPath)) {
  throw "Milvus standalone script not found at $scriptPath. Start Milvus first with scripts/rag-start-milvus-docker-windows.ps1."
}

Write-Host "==> Stopping Milvus Standalone"
Push-Location (Split-Path -Parent $scriptPath)
try {
  cmd /c "`"$scriptPath`" stop"
}
finally {
  Pop-Location
}

Write-Host "==> Done"
