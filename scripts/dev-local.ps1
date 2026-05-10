$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot "frontend"
$BackendDir = Join-Path $RepoRoot "backend"
$BackendVenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$BackendVenvDir = Join-Path $BackendDir ".venv"
$BackendVenvScripts = Join-Path $BackendVenvDir "Scripts"
$BackendVenvSitePackages = Join-Path $BackendVenvDir "Lib\site-packages"
$BackendCondaPython = Join-Path $BackendDir ".conda\python.exe"
$RootEnv = Join-Path $RepoRoot ".env"
$RootEnvTemplate = Join-Path $RepoRoot ".env.example"
$FrontendEnvLocal = Join-Path $FrontendDir ".env.local"
$FrontendEnvTemplate = Join-Path $FrontendDir ".env.example"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message"
}

function Copy-TemplateIfMissing {
    param(
        [string]$TemplatePath,
        [string]$TargetPath
    )

    if (-not (Test-Path $TargetPath)) {
        Copy-Item $TemplatePath $TargetPath
        Write-Host "Created $TargetPath from template."
    } else {
        Write-Host "Kept existing $TargetPath."
    }
}

function Resolve-BackendPython {
    if (Test-Path $BackendCondaPython) {
        return $BackendCondaPython
    }

    if (Test-Path $BackendVenvPython) {
        return $BackendVenvPython
    }

    throw "Backend Python environment is unavailable. Run scripts/bootstrap.ps1 first."
}

function Assert-PortFree {
    param([int]$Port)

    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($listener) {
        throw "Port $Port is already in use. Stop the existing process before running local dev."
    }
}

Write-Step "Preparing local development environment"
Copy-TemplateIfMissing -TemplatePath $RootEnvTemplate -TargetPath $RootEnv
Copy-TemplateIfMissing -TemplatePath $FrontendEnvTemplate -TargetPath $FrontendEnvLocal

Assert-PortFree -Port 8000
Assert-PortFree -Port 5173

$BackendPython = Resolve-BackendPython

$BackendCommand = "Set-Location '$BackendDir'; `$env:APP_ENV='development'; `$env:DATABASE_URL=''; `$env:VIRTUAL_ENV='$BackendVenvDir'; `$env:Path='$BackendVenvScripts;' + `$env:Path; `$env:PYTHONPATH='$BackendVenvSitePackages'; & '$BackendPython' -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
$FrontendCommand = "Set-Location '$FrontendDir'; npm.cmd run dev -- --host 127.0.0.1 --port 5173"

Write-Step "Starting backend in a new window"
Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-Command",
    $BackendCommand
) | Out-Null

Start-Sleep -Seconds 2

Write-Step "Starting frontend in a new window"
Start-Process -FilePath "powershell.exe" -ArgumentList @(
    "-NoExit",
    "-Command",
    $FrontendCommand
) | Out-Null

Write-Step "Local development is ready"
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Mode:     local-dev (frontend -> local backend, backend -> SQLite fallback)"
