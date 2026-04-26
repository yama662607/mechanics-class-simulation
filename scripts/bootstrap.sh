#!/usr/bin/env bash
# Thin wrapper that locates Python 3 and re-execs scripts/bootstrap.py.
# Works on macOS and Linux. See scripts/bootstrap.py for the actual logic.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Error: Python 3 is required to run the bootstrap script."
  echo "Install Python 3.12+ from https://www.python.org/ and retry."
  exit 1
fi

exec "$PY" "$SCRIPT_DIR/bootstrap.py" "$@"
