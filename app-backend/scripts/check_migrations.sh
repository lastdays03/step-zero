#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -x ".venv/bin/python" ]]; then
  echo "Missing .venv/bin/python. Run setup first."
  exit 1
fi

echo "[1/3] Running Alembic upgrade head"
./scripts/run_alembic.sh upgrade head

echo "[2/3] Showing Alembic current revision"
./scripts/run_alembic.sh current

echo "[3/3] Verifying migrated schema"
.venv/bin/python scripts/verify_schema.py

echo "Migration check completed successfully"
