#!/usr/bin/env bash
# Helper to run a command inside a disposable container for sandboxed execution
set -euo pipefail
IMAGE="${1:-python:3.11-slim}"
shift || true
CMD="$*"
if [ -z "$CMD" ]; then
  echo "Usage: $0 [image] command..."
  exit 2
fi
docker run --rm "$IMAGE" bash -lc "$CMD"
