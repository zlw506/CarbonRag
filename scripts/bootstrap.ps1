param(
    [switch]$SkipInstall,
    [switch]$SkipChecks
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot "frontend"
$BackendDir = Join-Path $RepoRoot "backend"
$BackendVenv = Join-Path $BackendDir ".venv"
$BackendPython = Join-Path $BackendVenv "Scripts\\python.exe"
$BackendCondaPython = Join-Path $BackendDir ".conda\\python.exe"

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

function Test-Python311Launcher {
    $null = & cmd /c "py -3.11 --version" 2>$null
    return $LASTEXITCODE -eq 0
}

function Resolve-BackendPython {
    if (Test-Path $BackendCondaPython) {
        return $BackendCondaPython
    }

    if (Test-Path $BackendPython) {
        return $BackendPython
    }

    return $null
}

Write-Step "Preparing environment templates"
Copy-TemplateIfMissing -TemplatePath (Join-Path $RepoRoot ".env.example") -TargetPath (Join-Path $RepoRoot ".env")
Copy-TemplateIfMissing -TemplatePath (Join-Path $FrontendDir ".env.example") -TargetPath (Join-Path $FrontendDir ".env")

if (-not $SkipInstall) {
    Write-Step "Installing frontend dependencies"
    Push-Location $FrontendDir
    npm install
    Pop-Location

    Write-Step "Preparing backend Python 3.11 environment"
    if (Test-Path $BackendCondaPython) {
        $BackendPython = $BackendCondaPython
    } elseif (Test-Python311Launcher) {
        if (-not (Test-Path $BackendPython)) {
            py -3.11 -m venv $BackendVenv
        }
    } elseif (Get-Command conda -ErrorAction SilentlyContinue) {
        conda create -p (Join-Path $BackendDir ".conda") python=3.11 -y
        $BackendPython = $BackendCondaPython
    } else {
        throw "Python 3.11 is unavailable. Install it or provide conda before running bootstrap."
    }

    Write-Step "Installing backend dependencies"
    & $BackendPython -m pip install --upgrade pip
    & $BackendPython -m pip install -r (Join-Path $BackendDir "requirements.txt")
}

$ResolvedBackendPython = Resolve-BackendPython
if (-not $ResolvedBackendPython) {
    throw "Backend Python environment is unavailable. Run bootstrap without -SkipInstall or create .venv/.conda first."
}
$BackendPython = $ResolvedBackendPython

if (-not $SkipChecks) {
    Write-Step "Running frontend checks"
    Push-Location $FrontendDir
    npm run typecheck
    npm run build
    Pop-Location

    Write-Step "Running backend checks"
    Push-Location $BackendDir
    & $BackendPython -m pytest tests
    Pop-Location
}

Write-Step "Next steps"
Write-Host "Frontend dev server: cd frontend && npm run dev"
Write-Host "Backend dev server (venv): cd backend && ..\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
Write-Host "Backend dev server (conda fallback): cd backend && .\\.conda\\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
Write-Host "Bootstrap guide: docs/DEVELOPMENT_BOOTSTRAP.md"
