param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9][a-z0-9-]*[a-z0-9]$')]
    [string]$Id,

    [Parameter(Mandatory = $true)]
    [string]$Goal,

    [Parameter(Mandatory = $false)]
    [string]$Domain = "<domain>"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Get-Command openspec -ErrorAction SilentlyContinue)) {
    throw "OpenSpec CLI not found. Install it with: npm install -g @fission-ai/openspec@latest"
}

Write-Host "== CarbonRag OpenSpec change bootstrap ==" -ForegroundColor Cyan
Write-Host "Repo: $repoRoot"
Write-Host "Change ID: $Id"
Write-Host "Goal: $Goal"
Write-Host ""

openspec list
openspec validate --all

$changeDir = Join-Path $repoRoot "openspec\changes\$Id"
if (Test-Path -LiteralPath $changeDir) {
    Write-Host "Change already exists: openspec/changes/$Id" -ForegroundColor Yellow
} else {
    openspec new change $Id --description $Goal
}

Write-Host ""
Write-Host "== Change status =="
openspec status --change $Id

Write-Host ""
Write-Host "== Paste this to Codex =="
$promptLines = @(
    "Run the CarbonRag OpenSpec propose stage.",
    "Change ID: $Id",
    "Goal: $Goal",
    "Affected spec/domain: $Domain",
    "",
    "First read AGENTS.md, openspec/AGENTS.md, openspec/specs/**, docs/governance/**, and docs/architecture/**.",
    "You own OpenSpec housekeeping: check branch, worktree, unignored files, openspec list, and openspec validate --all.",
    "Do not run openspec init again.",
    "If openspec/changes/$Id already exists, read it and continue. If proposal/design/tasks/delta spec are missing, create them.",
    "Propose only: create or review proposal.md, design.md, tasks.md, and specs/$Domain/spec.md.",
    "Stop after propose and wait for #1 review. Do not apply."
)

$promptLines -join [Environment]::NewLine
