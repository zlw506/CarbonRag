param(
    [string]$ApiBaseUrl = $env:CARBONRAG_API_BASE_URL,
    [string]$Username = $env:CARBONRAG_ADMIN_USERNAME,
    [string]$Password = $env:CARBONRAG_ADMIN_PASSWORD,
    [string]$Query = "碳达峰"
)

$ErrorActionPreference = "Stop"

if (-not $ApiBaseUrl) { $ApiBaseUrl = "http://127.0.0.1:8000/api" }
if (-not $Username -or -not $Password) {
    throw "Set CARBONRAG_ADMIN_USERNAME and CARBONRAG_ADMIN_PASSWORD before running this smoke script."
}

$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$loginBody = @{ username = $Username; password = $Password } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$ApiBaseUrl/v1/auth/login" -Body $loginBody -ContentType "application/json" -WebSession $session | Out-Null

$candidates = Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/v1/admin/policy-crawler/candidates?status=pending_review&limit=10" -WebSession $session
if (-not $candidates -or $candidates.Count -lt 1) {
    throw "No pending policy crawler candidate found. Run scripts/crawler-smoke-local-scrapy.ps1 first."
}

$candidate = $candidates[0]
"==> publish candidate to RAG: $($candidate.candidate_id)"
$published = Invoke-RestMethod -Method Post -Uri "$ApiBaseUrl/v1/admin/policy-crawler/candidates/$($candidate.candidate_id)/publish-to-rag" -Body "{}" -ContentType "application/json" -WebSession $session
$published | ConvertTo-Json -Depth 8

if (-not $published.rag_kb_id) {
    throw "Candidate did not return rag_kb_id; publish-to-rag failed before RAG search smoke."
}

"==> rag search: $Query"
$searchBody = @{
    query = $Query
    kb_id = $published.rag_kb_id
    mode = "hybrid_rerank"
    top_k = 5
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$ApiBaseUrl/v1/rag/search" -Body $searchBody -ContentType "application/json" -WebSession $session | ConvertTo-Json -Depth 8
