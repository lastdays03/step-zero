#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MAX_STEPS="${MAX_MIGRATION_STEPS:-200}"
step=0

echo "[migrate_all] current revisions:"
./scripts/run_alembic.sh current || true
echo "[migrate_all] heads:"
./scripts/run_alembic.sh heads

while true; do
  current_line="$(./scripts/run_alembic.sh current 2>/dev/null | head -n1 || true)"
  head_line="$(./scripts/run_alembic.sh heads 2>/dev/null | head -n1 || true)"

  current_rev="$(echo "$current_line" | awk '{print $1}')"
  head_rev="$(echo "$head_line" | awk '{print $1}')"

  if [[ -n "$current_rev" && -n "$head_rev" && "$current_rev" == "$head_rev" ]]; then
    break
  fi

  step=$((step + 1))
  if (( step > MAX_STEPS )); then
    echo "[migrate_all] exceeded MAX_MIGRATION_STEPS=$MAX_STEPS"
    echo "[migrate_all] current: $current_line"
    echo "[migrate_all] head: $head_line"
    exit 1
  fi

  echo "[migrate_all] step=$step upgrade +1"
  ./scripts/run_alembic.sh upgrade +1
done

echo "[migrate_all] final current revision:"
./scripts/run_alembic.sh current
echo "[migrate_all] done"
