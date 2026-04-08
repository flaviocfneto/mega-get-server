#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${ROOT_DIR}/flet-app"
FRONTEND_DIR="${ROOT_DIR}/react-new"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-5173}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but was not found."
  echo "Install Node.js from https://nodejs.org/ or via your package manager."
  exit 1
fi

if [ ! -f "${BACKEND_DIR}/requirements.txt" ]; then
  echo "Missing backend requirements file at ${BACKEND_DIR}/requirements.txt"
  exit 1
fi

if [ ! -d "${FRONTEND_DIR}/node_modules" ]; then
  echo "react-new/node_modules not found. Running npm install..."
  (cd "${FRONTEND_DIR}" && npm install)
fi

cleanup() {
  if [ -n "${BACKEND_PID:-}" ] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
    kill "${BACKEND_PID}" 2>/dev/null || true
  fi
  if [ -n "${FRONTEND_PID:-}" ] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Starting backend on http://${API_HOST}:${API_PORT} ..."
(cd "${BACKEND_DIR}" && python3 -m uvicorn api_main:app --host "${API_HOST}" --port "${API_PORT}") &
BACKEND_PID=$!

echo "Starting frontend on http://localhost:${UI_PORT} ..."
(cd "${FRONTEND_DIR}" && API_PROXY_TARGET="http://${API_HOST}:${API_PORT}" npm run dev) &
FRONTEND_PID=$!

echo "Backend PID: ${BACKEND_PID}"
echo "Frontend PID: ${FRONTEND_PID}"
echo "Press Ctrl+C to stop both processes."

wait "${BACKEND_PID}" "${FRONTEND_PID}"
