#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${RAG_BOOTSTRAP_MODE:-auto}" # auto | docker | local
COMPOSE_FILE="${RAG_BOOTSTRAP_COMPOSE_FILE:-$ROOT_DIR/../docker-compose.dev.yml}"
BACKEND_SERVICE="${RAG_BOOTSTRAP_BACKEND_SERVICE:-app-backend}"
SOURCE_DIR="${RAG_BOOTSTRAP_SOURCE_DIR:-$ROOT_DIR/.temp/rag}"
LIMIT="${RAG_BOOTSTRAP_LIMIT:-0}"

run_local() {
  echo "[bootstrap_rag] mode=local"
  echo "[bootstrap_rag] applying migrations..."
  ./scripts/run_alembic.sh upgrade head

  PYTHON_BIN=".venv/bin/python"
  if [[ ! -x "$PYTHON_BIN" ]]; then
    if command -v python3 >/dev/null 2>&1; then
      PYTHON_BIN="python3"
    else
      echo "[bootstrap_rag] python executable not found"
      echo "expected: .venv/bin/python or python3 in PATH"
      exit 1
    fi
  fi

  if [[ "$LIMIT" -gt 0 ]]; then
    "$PYTHON_BIN" scripts/seed_rag_vectors.py --source-dir "$SOURCE_DIR" --limit "$LIMIT"
  else
    "$PYTHON_BIN" scripts/seed_rag_vectors.py --source-dir "$SOURCE_DIR"
  fi
}

run_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "[bootstrap_rag] docker command not found"
    return 1
  fi
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "[bootstrap_rag] compose file not found: $COMPOSE_FILE"
    return 1
  fi
  if ! docker compose -f "$COMPOSE_FILE" ps --status running --services | grep -qx "$BACKEND_SERVICE"; then
    echo "[bootstrap_rag] backend service is not running: $BACKEND_SERVICE"
    echo "start first: docker compose -f \"$COMPOSE_FILE\" up -d $BACKEND_SERVICE app-db app-redis"
    return 1
  fi

  echo "[bootstrap_rag] mode=docker"
  if [[ "$LIMIT" -gt 0 ]]; then
    docker compose -f "$COMPOSE_FILE" exec -T "$BACKEND_SERVICE" bash -lc \
      "cd /app && ./scripts/run_alembic.sh upgrade head && python scripts/seed_rag_vectors.py --source-dir \"$SOURCE_DIR\" --limit \"$LIMIT\""
  else
    docker compose -f "$COMPOSE_FILE" exec -T "$BACKEND_SERVICE" bash -lc \
      "cd /app && ./scripts/run_alembic.sh upgrade head && python scripts/seed_rag_vectors.py --source-dir \"$SOURCE_DIR\""
  fi
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
      echo "[bootstrap_rag] docker mode unavailable, fallback to local mode"
      run_local
    fi
    ;;
  *)
    echo "[bootstrap_rag] invalid RAG_BOOTSTRAP_MODE: $MODE"
    echo "allowed: auto | docker | local"
    exit 1
    ;;
esac

echo "[bootstrap_rag] done"
