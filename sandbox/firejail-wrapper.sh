#!/usr/bin/env bash
# Run a command in firejail if available, otherwise fallback to unshare sandbox
set -euo pipefail
CMD="$*"
if command -v firejail >/dev/null 2>&1; then
  firejail --private --net=none --quiet bash -lc "$CMD"
elif command -v unshare >/dev/null 2>&1; then
  # Minimal unshare sandbox: new mount, pid, uts, and user namespace
  unshare --fork --pid --mount --uts --ipc --user --map-root-user bash -lc "$CMD"
else
  echo "No sandboxing tool (firejail/unshare) found. Running directly."
  bash -lc "$CMD"
fi
