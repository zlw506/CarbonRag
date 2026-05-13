param(
    [string]$ApiBase = $env:CARBONRAG_API_BASE,
    [string]$KbId = $env:CARBONRAG_KB_ID,
    [string]$DocId = $env:CARBONRAG_DOC_ID,
    [ValidateSet("quick", "acceptance")]
    [string]$PipelineMode = "quick",
    [string]$Cookie = $env:CARBONRAG_COOKIE,
    [string]$Output = "logs/rag/profile-v1.6.29.json"
)

$ErrorActionPreference = "Stop"
if (-not $ApiBase) { $ApiBase = "http://127.0.0.1:8000/api/v1" }
if (-not $KbId) { throw "Set -KbId or CARBONRAG_KB_ID." }
if (-not $DocId) { throw "Set -DocId or CARBONRAG_DOC_ID." }

$headers = @{}
if ($Cookie) { $headers["Cookie"] = $Cookie }
$body = @{ pipeline_mode = $PipelineMode } | ConvertTo-Json -Depth 8
$url = "$($ApiBase.TrimEnd('/'))/kb/$KbId/documents/$DocId/run-pipeline"
$result = Invoke-RestMethod -Method Post -Uri $url -Headers $headers -Body $body -ContentType "application/json"

$outDir = Split-Path -Parent $Output
if ($outDir) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
[pscustomobject]@{
    kind = "pipeline"
    captured_at = (Get-Date).ToString("o")
    api_base = $ApiBase
    kb_id = $KbId
    doc_id = $DocId
    pipeline_mode = $PipelineMode
    result = $result
} | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $Output -Encoding UTF8

Write-Host "Wrote $Output"
