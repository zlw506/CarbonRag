param(
    [string]$ApiBaseUrl = $env:CARBONRAG_API_BASE_URL,
    [string]$Username = $env:CARBONRAG_ADMIN_USERNAME,
    [string]$Password = $env:CARBONRAG_ADMIN_PASSWORD,
    [string]$SourceId = "gov-cn-policy-library"
)

$ErrorActionPreference = "Stop"

if (-not $ApiBaseUrl) { $ApiBaseUrl = "http://127.0.0.1:8000/api" }
if (-not $Username -or -not $Password) {
    throw "Set CARBONRAG_ADMIN_USERNAME and CARBONRAG_ADMIN_PASSWORD before running this smoke script."
}

$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$loginBody = @{ username = $Username; password = $Password } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$ApiBaseUrl/v1/auth/login" -Body $loginBody -ContentType "application/json" -WebSession $session | Out-Null

"==> crawler status"
Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/v1/admin/policy-crawler/status" -WebSession $session | ConvertTo-Json -Depth 8

"==> sources"
Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/v1/admin/policy-crawler/sources" -WebSession $session | ConvertTo-Json -Depth 8

"==> run source: $SourceId"
Invoke-RestMethod -Method Post -Uri "$ApiBaseUrl/v1/admin/policy-crawler/sources/$SourceId/run" -Body "{}" -ContentType "application/json" -WebSession $session | ConvertTo-Json -Depth 8

"==> latest runs"
Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/v1/admin/policy-crawler/runs?limit=5" -WebSession $session | ConvertTo-Json -Depth 8

"==> latest candidates"
Invoke-RestMethod -Method Get -Uri "$ApiBaseUrl/v1/admin/policy-crawler/candidates?limit=10" -WebSession $session | ConvertTo-Json -Depth 8
