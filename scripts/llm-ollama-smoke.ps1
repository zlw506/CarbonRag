param(
  [string]$BaseUrl = $env:OLLAMA_BASE_URL,
  [string]$Model = $env:OLLAMA_MODEL
)

$ErrorActionPreference = "Stop"

if (-not $BaseUrl) { $BaseUrl = "http://localhost:11434" }
if (-not $Model) { $Model = "deepseek-r1:8b" }
$BaseUrl = $BaseUrl.TrimEnd("/")
if ($BaseUrl.EndsWith("/api")) { $BaseUrl = $BaseUrl.Substring(0, $BaseUrl.Length - 4) }
if ($BaseUrl.EndsWith("/v1")) { $BaseUrl = $BaseUrl.Substring(0, $BaseUrl.Length - 3) }

Write-Host "==> Checking Ollama tags at $BaseUrl/api/tags"
$tags = Invoke-RestMethod -Method Get -Uri "$BaseUrl/api/tags" -TimeoutSec 30
$modelNames = @($tags.models | ForEach-Object { $_.name })
if ($modelNames -notcontains $Model) {
  Write-Warning "Model '$Model' was not found. Current models: $($modelNames -join ', ')"
  throw "Run 'ollama pull $Model' or confirm the local tag name."
}

Write-Host "==> Running Ollama chat smoke with $Model"
$body = @{
  model = $Model
  messages = @(@{ role = "user"; content = "只回答 OK" })
  stream = $false
  keep_alive = "10m"
  think = $false
  options = @{ num_ctx = 8192; temperature = 0.0 }
} | ConvertTo-Json -Depth 8

$response = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/chat" -ContentType "application/json" -Body $body -TimeoutSec 180
$content = [string]$response.message.content
Write-Host "Ollama response: $content"
if (-not $content.Trim()) {
  throw "Ollama returned empty content."
}

Write-Host "==> Ollama smoke passed"
