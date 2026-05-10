param(
  [string]$RuntimeDir = "data/outputs/milvus-docker",
  [string]$MilvusUri = "http://127.0.0.1:19530",
  [string]$PythonPath = ".\backend\.conda\python.exe",
  [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "==> Checking Docker Desktop"
docker --version | Out-Host
docker compose version | Out-Host
docker info | Out-Null

if ($PythonPath -ne "python") {
  $PythonPath = (Resolve-Path $PythonPath).Path
}

$runtimePath = New-Item -ItemType Directory -Force -Path $RuntimeDir
$scriptPath = Join-Path $runtimePath.FullName "standalone_embed.bat"
$scriptUrl = "https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.bat"

if (-not (Test-Path $scriptPath)) {
  Write-Host "==> Downloading official Milvus standalone script"
  try {
    Invoke-WebRequest -Uri $scriptUrl -OutFile $scriptPath -UseBasicParsing
  }
  catch {
    throw "Failed to download Milvus standalone script from $scriptUrl. Check network/proxy or update the script URL from official Milvus docs."
  }
}

Write-Host "==> Starting Milvus Standalone via Docker"
Push-Location $runtimePath.FullName
try {
  cmd /c "`"$scriptPath`" start"
}
finally {
  Pop-Location
}

Write-Host "==> Waiting for Milvus at $MilvusUri"
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
do {
  $env:CARBONRAG_MILVUS_SMOKE_URI = $MilvusUri
  & $PythonPath -W ignore -c "import os; from pymilvus import MilvusClient; MilvusClient(uri=os.environ['CARBONRAG_MILVUS_SMOKE_URI']); print('milvus ok')" 2>$null
  if ($LASTEXITCODE -eq 0) {
    Write-Host "==> Milvus Standalone is ready"
    exit 0
  }
  Start-Sleep -Seconds 5
} while ((Get-Date) -lt $deadline)

throw "Milvus Standalone did not become ready within $TimeoutSeconds seconds. Check Docker Desktop, WSL2, port 19530, and Docker disk space."
