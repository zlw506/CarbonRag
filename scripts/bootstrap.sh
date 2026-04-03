#!/usr/bin/env bash
set -euo pipefail

SKIP_INSTALL=0
SKIP_CHECKS=0

for arg in "$@"; do
    case "$arg" in
        --skip-install) SKIP_INSTALL=1 ;;
        --skip-checks) SKIP_CHECKS=1 ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 1
            ;;
    esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"
BACKEND_DIR="$REPO_ROOT/backend"
BACKEND_VENV="$BACKEND_DIR/.venv"
BACKEND_PYTHON="$BACKEND_VENV/bin/python"

step() {
    printf '\n==> %s\n' "$1"
}

copy_template_if_missing() {
    local template_path="$1"
    local target_path="$2"
    if [[ ! -f "$target_path" ]]; then
        cp "$template_path" "$target_path"
        echo "Created $target_path from template."
    else
        echo "Kept existing $target_path."
    fi
}

step "Preparing environment templates"
copy_template_if_missing "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
copy_template_if_missing "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"

if [[ "$SKIP_INSTALL" -eq 0 ]]; then
    step "Installing frontend dependencies"
    (cd "$FRONTEND_DIR" && npm install)

    step "Creating backend virtual environment"
    if [[ ! -x "$BACKEND_PYTHON" ]]; then
        python3.11 -m venv "$BACKEND_VENV"
    fi

    step "Installing backend dependencies"
    "$BACKEND_PYTHON" -m pip install --upgrade pip
    "$BACKEND_PYTHON" -m pip install -r "$BACKEND_DIR/requirements.txt"
fi

if [[ "$SKIP_CHECKS" -eq 0 ]]; then
    step "Running frontend checks"
    (cd "$FRONTEND_DIR" && npm run typecheck && npm run build)

    step "Running backend checks"
    (cd "$BACKEND_DIR" && "$BACKEND_PYTHON" -m pytest tests)
fi

step "Next steps"
echo "Frontend dev server: cd frontend && npm run dev"
echo "Backend dev server: cd backend && ./.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
echo "Bootstrap guide: docs/DEVELOPMENT_BOOTSTRAP.md"
