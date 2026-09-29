#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HEALTH_URL="http://127.0.0.1:8000/docs"

# Ensure script is runnable in CI
if [ -t 1 ]; then
  :
fi

usage() {
  echo "Usage: $0 [--wait seconds] [--run-tests]"
  exit 1
}

if [[ ${1:-} == "--wait" ]]; then
  shift
  TIMEOUT=${1:-30}
  echo "Waiting up to ${TIMEOUT}s for ${HEALTH_URL}..."
  SECONDS_PASSED=0
  until curl -sSf ${HEALTH_URL} >/dev/null 2>&1; do
    sleep 1
    SECONDS_PASSED=$((SECONDS_PASSED+1))
    if [ "$SECONDS_PASSED" -ge "$TIMEOUT" ]; then
      echo "Timed out waiting for ${HEALTH_URL}"
      exit 2
    fi
  done
  echo "Backend is responsive."
  exit 0
fi

if [[ ${1:-} == "--run-tests" ]]; then
  echo "Running API smoke tests against ${HEALTH_URL}"
  # Create a material
  echo "Creating material..."
  create_resp=$(curl -s -X POST http://127.0.0.1:8000/materials/ -H "Content-Type: application/json" -d '{"name":"CI-Material","description":"ci test","unit_price":5.5}') || (echo "Create material failed" && exit 3)
  echo "Create response: $create_resp"

  # Extract id (rudimentary)
  mat_id=$(echo "$create_resp" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
  if [[ -z "$mat_id" ]]; then
    echo "Failed to get material id" && exit 4
  fi

  echo "Creating purchase order for material ${mat_id}..."
  po_resp=$(curl -s -X POST http://127.0.0.1:8000/purchase_orders/ -H "Content-Type: application/json" -d "{\"material_id\":${mat_id},\"quantity\":10}") || (echo "Create PO failed" && exit 5)
  echo "PO response: $po_resp"

  echo "Smoke tests passed."
  exit 0
fi

usage
