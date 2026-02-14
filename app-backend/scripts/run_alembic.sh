#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -x ".venv/bin/alembic" ]]; then
  .venv/bin/alembic "$@"
  exit 0
fi

if command -v alembic >/dev/null 2>&1; then
  alembic "$@"
  exit 0
fi

echo "Alembic executable not found. Install backend dependencies first."
echo "Expected: .venv/bin/alembic"
exit 1
