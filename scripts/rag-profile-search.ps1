param(
    [string]$ApiBase = $env:CARBONRAG_API_BASE,
    [string]$KbId = $env:CARBONRAG_KB_ID,
    [string]$Query = $env:CARBONRAG_QUERY,
    [string]$Mode = "hybrid_rerank",
    [int]$TopK = 5,
    [string]$Cookie = $env:CARBONRAG_COOKIE,
    [string]$Output = "logs/rag/profile-v1.6.29.json"
)

$ErrorActionPreference = "Stop"
if (-not $ApiBase) { $ApiBase = "http://127.0.0.1:8000/api/v1" }
if (-not $KbId) { throw "Set -KbId or CARBONRAG_KB_ID." }
if (-not $Query) { $Query = "青木制造 2025 年第一季度合计外购电力是多少？" }

$headers = @{}
if ($Cookie) { $headers["Cookie"] = $Cookie }
$body = @{ kb_id = $KbId; query = $Query; mode = $Mode; top_k = $TopK } | ConvertTo-Json -Depth 8
$url = "$($ApiBase.TrimEnd('/'))/rag/search"
$result = Invoke-RestMethod -Method Post -Uri $url -Headers $headers -Body $body -ContentType "application/json"

$outDir = Split-Path -Parent $Output
if ($outDir) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
[pscustomobject]@{
    kind = "search"
    captured_at = (Get-Date).ToString("o")
    api_base = $ApiBase
    kb_id = $KbId
    query = $Query
    mode = $Mode
    top_k = $TopK
    result = $result
} | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $Output -Encoding UTF8

Write-Host "Wrote $Output"
