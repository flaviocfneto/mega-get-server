#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

STANDARD_TAG="linktugger:smoke-standard"
HARDENED_TAG="linktugger:smoke-hardened"
SMOKE_CONTAINER="linktugger-smoke"
SMOKE_PORT="${SMOKE_PORT:-18080}"

cleanup() {
  docker rm -f "${SMOKE_CONTAINER}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "[smoke] checking docker daemon..."
if ! docker info >/dev/null 2>&1; then
  echo "[smoke] Docker daemon is unavailable."
  echo "[smoke] Start Docker Desktop, wait until Docker is running, then retry."
  exit 1
fi

echo "[smoke] building image..."
docker build -f Dockerfile -t "${STANDARD_TAG}" .

echo "[smoke] starting container..."
docker rm -f "${SMOKE_CONTAINER}" >/dev/null 2>&1 || true
docker run -d --name "${SMOKE_CONTAINER}" -p "${SMOKE_PORT}:8080" "${STANDARD_TAG}" >/dev/null

echo "[smoke] waiting for health endpoint..."
for attempt in $(seq 1 20); do
  if curl -fsS "http://127.0.0.1:${SMOKE_PORT}/api/diag/tools" >/dev/null 2>&1; then
    echo "[smoke] container responded successfully."
    break
  fi
  if [ "${attempt}" -eq 20 ]; then
    echo "[smoke] container failed readiness check."
    docker logs "${SMOKE_CONTAINER}" || true
    exit 1
  fi
  sleep 2
done

echo "[smoke] all smoke checks passed."
