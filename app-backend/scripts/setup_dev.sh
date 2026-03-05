#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "[ERROR] uv가 설치되어 있지 않습니다."
  echo "설치: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

echo "[1/3] 의존성 동기화 (dev 포함)"
uv sync --extra dev

if [[ ! -f .env ]]; then
  echo "[2/3] .env 생성 (.env.example 복사)"
  cp .env.example .env
else
  echo "[2/3] .env 파일이 이미 있어 복사를 건너뜁니다"
fi

echo "[3/3] 완료"
echo "실행: uv run uvicorn app.main:app --reload --port 8000"
echo "테스트: uv run pytest -q"
