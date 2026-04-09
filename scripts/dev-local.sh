#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$REPO_ROOT/frontend"
BACKEND_DIR="$REPO_ROOT/backend"
ROOT_ENV="$REPO_ROOT/.env"
ROOT_ENV_TEMPLATE="$REPO_ROOT/.env.example"
FRONTEND_ENV_LOCAL="$FRONTEND_DIR/.env.local"
FRONTEND_ENV_TEMPLATE="$FRONTEND_DIR/.env.example"
BACKEND_VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"
BACKEND_CONDA_PYTHON="$BACKEND_DIR/.conda/bin/python"

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

resolve_backend_python() {
    if [[ -x "$BACKEND_CONDA_PYTHON" ]]; then
        printf '%s\n' "$BACKEND_CONDA_PYTHON"
        return
    fi

    if [[ -x "$BACKEND_VENV_PYTHON" ]]; then
        printf '%s\n' "$BACKEND_VENV_PYTHON"
        return
    fi

    echo "Backend Python environment is unavailable. Run scripts/bootstrap.sh first." >&2
    exit 1
}

port_is_busy() {
    local port="$1"

    if command -v lsof >/dev/null 2>&1; then
        lsof -iTCP:"$port" -sTCP:LISTEN -t >/dev/null 2>&1
        return $?
    fi

    if command -v ss >/dev/null 2>&1; then
        ss -ltn | grep -E "[\:\.]$port " >/dev/null 2>&1
        return $?
    fi

    if command -v netstat >/dev/null 2>&1; then
        netstat -an | grep -E "[\:\.]$port " | grep LISTEN >/dev/null 2>&1
        return $?
    fi

    return 1
}

step "Preparing local development environment"
copy_template_if_missing "$ROOT_ENV_TEMPLATE" "$ROOT_ENV"
copy_template_if_missing "$FRONTEND_ENV_TEMPLATE" "$FRONTEND_ENV_LOCAL"

if port_is_busy 8000; then
    echo "Port 8000 is already in use. Stop the existing process before running local dev." >&2
    exit 1
fi

if port_is_busy 5173; then
    echo "Port 5173 is already in use. Stop the existing process before running local dev." >&2
    exit 1
fi

BACKEND_PYTHON="$(resolve_backend_python)"

step "Starting backend in background"
(
    cd "$BACKEND_DIR"
    APP_ENV=development DATABASE_URL='' "$BACKEND_PYTHON" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

cleanup() {
    if kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
        kill "$BACKEND_PID" >/dev/null 2>&1 || true
    fi
}

trap cleanup EXIT

sleep 2

step "Starting frontend in foreground"
echo "Frontend: http://127.0.0.1:5173"
echo "Backend:  http://127.0.0.1:8000"
echo "Mode:     local-dev (frontend -> local backend, backend -> SQLite fallback)"

cd "$FRONTEND_DIR"
npm run dev -- --host 127.0.0.1 --port 5173
