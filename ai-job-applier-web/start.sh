#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="${PYTHON_CMD:-python}"
NPM_CMD="${NPM_CMD:-npm}"
PORT="${PORT:-8765}"
REQ_MARKER="$ROOT_DIR/.backend-deps-installed"
FRONTEND_DIST="$ROOT_DIR/frontend/dist"
FRONTEND_ENTRY="$FRONTEND_DIST/index.html"

install_backend_deps() {
  if [ "${SKIP_BACKEND_REQUIREMENTS:-0}" = "1" ]; then
    echo "Skipping backend dependency installation (SKIP_BACKEND_REQUIREMENTS=1)"
    return
  fi

  if [ -f "$REQ_MARKER" ]; then
    echo "Backend requirements already installed."
    return
  fi

  echo "Installing backend requirements with $PYTHON_CMD -m pip install -r backend/requirements.txt"
  "$PYTHON_CMD" -m pip install -r backend/requirements.txt
  touch "$REQ_MARKER"
}

build_frontend() {
  echo "Installing frontend dependencies..."
  pushd "$ROOT_DIR/frontend" >/dev/null
  "$NPM_CMD" ci
  echo "Building frontend assets (NODE_ENV=production)..."
  NODE_ENV=production "$NPM_CMD" run build
  popd >/dev/null
}

if [ "${1:-}" = "--build" ]; then
  install_backend_deps
  build_frontend
  exit 0
fi

install_backend_deps

if [ ! -f "$FRONTEND_ENTRY" ]; then
  echo "Frontend build missing at $FRONTEND_ENTRY. Running build..."
  build_frontend
else
  echo "Frontend build already present at $FRONTEND_ENTRY."
fi

echo "Starting backend on port $PORT"
exec "$PYTHON_CMD" -m uvicorn backend.main:app --host 0.0.0.0 --port "$PORT"
