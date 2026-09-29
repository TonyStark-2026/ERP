#!/usr/bin/env bash
set -euo pipefail

echo "Starting ERP services via Docker Compose..."
if command -v docker-compose >/dev/null 2>&1; then
    compose_cmd="docker-compose"
elif command -v docker >/dev/null 2>&1; then
    compose_cmd="docker compose"
else
    echo "Error: Docker Compose not found. Install Docker Desktop or Docker engine with Compose support." >&2
    exit 1
fi

$compose_cmd up --build -d

echo "Waiting for backend to respond on http://127.0.0.1:8000/docs"
./scripts/ci_healthcheck.sh --wait 60

echo "ERP services started. Open http://127.0.0.1:8000/docs in your browser."
