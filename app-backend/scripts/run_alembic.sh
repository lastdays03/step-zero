#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if command -v uv >/dev/null 2>&1; then
  uv run alembic "$@"
  exit 0
fi

if command -v alembic >/dev/null 2>&1; then
  alembic "$@"
  exit 0
fi

echo "Alembic executable not found. Install uv and run 'uv sync --extra dev' first."
exit 1
