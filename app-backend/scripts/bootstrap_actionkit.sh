#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${ACTIONKIT_BOOTSTRAP_MODE:-auto}" # auto | docker | local
COMPOSE_FILE="${ACTIONKIT_BOOTSTRAP_COMPOSE_FILE:-$ROOT_DIR/../docker-compose.dev.yml}"
BACKEND_SERVICE="${ACTIONKIT_BOOTSTRAP_BACKEND_SERVICE:-app-backend}"

run_local() {
  echo "[bootstrap_actionkit] mode=local"
  echo "[bootstrap_actionkit] applying alembic migrations..."
  ./scripts/run_alembic.sh upgrade head

  if command -v uv >/dev/null 2>&1; then
    PYTHON_BIN="uv run python"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  else
    echo "[bootstrap_actionkit] python executable not found"
    echo "expected: uv or python3 in PATH"
    exit 1
  fi

  echo "[bootstrap_actionkit] seeding actionkit data..."
  "$PYTHON_BIN" scripts/seed_actionkit.py
}

run_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "[bootstrap_actionkit] docker command not found"
    return 1
  fi
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "[bootstrap_actionkit] compose file not found: $COMPOSE_FILE"
    return 1
  fi

  if ! docker compose -f "$COMPOSE_FILE" ps --status running --services | grep -qx "$BACKEND_SERVICE"; then
    echo "[bootstrap_actionkit] backend service is not running: $BACKEND_SERVICE"
    echo "start first: docker compose -f \"$COMPOSE_FILE\" up -d $BACKEND_SERVICE app-db app-redis"
    return 1
  fi

  echo "[bootstrap_actionkit] mode=docker"
  echo "[bootstrap_actionkit] running migration + seed inside container..."
  docker compose -f "$COMPOSE_FILE" exec -T "$BACKEND_SERVICE" bash -lc \
    "cd /app && ./scripts/run_alembic.sh upgrade head && python scripts/seed_actionkit.py"
}

case "$MODE" in
  docker)
    run_docker
    ;;
  local)
    run_local
    ;;
  auto)
    if ! run_docker; then
      echo "[bootstrap_actionkit] docker mode unavailable, fallback to local mode"
      run_local
    fi
    ;;
  *)
    echo "[bootstrap_actionkit] invalid ACTIONKIT_BOOTSTRAP_MODE: $MODE"
    echo "allowed: auto | docker | local"
    exit 1
    ;;
esac

echo "[bootstrap_actionkit] done"
