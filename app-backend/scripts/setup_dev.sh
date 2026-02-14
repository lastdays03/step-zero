#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
export UV_CACHE_DIR="${UV_CACHE_DIR:-$ROOT_DIR/.uv-cache}"
USE_UV="${USE_UV:-1}"
PINNED_UV_VERSION="$(cat "$ROOT_DIR/.uv-version" 2>/dev/null || true)"

if [[ "$USE_UV" == "1" ]]; then
  if ! command -v uv >/dev/null 2>&1; then
    echo "[WARN] uv가 설치되어 있지 않아 python/pip 경로를 사용합니다."
    USE_UV=0
  elif [[ -n "$PINNED_UV_VERSION" ]]; then
    CURRENT_UV_VERSION="$(uv --version | awk '{print $2}')"
    if [[ "$CURRENT_UV_VERSION" != "$PINNED_UV_VERSION" && "${FORCE_UV:-0}" != "1" ]]; then
      echo "[WARN] uv 버전 불일치: current=$CURRENT_UV_VERSION pinned=$PINNED_UV_VERSION"
      echo "[WARN] python/pip 경로로 우회합니다. (강제 사용: FORCE_UV=1)"
      USE_UV=0
    fi
  fi
fi

if [[ "$(uname -s)" == "Darwin" && "${FORCE_UV:-0}" != "1" ]]; then
  # macOS 26 계열에서 uv(system-configuration crate) 패닉이 재현되어 기본 우회한다.
  USE_UV=0
  echo "[INFO] macOS 감지: uv 경로를 기본 비활성화하고 python/pip 경로를 사용합니다."
  echo "[INFO] uv를 강제로 사용하려면 FORCE_UV=1 ./scripts/setup_dev.sh"
fi

echo "[1/4] Python 3.11 가상환경 생성/갱신"
if [[ "$USE_UV" == "1" ]] && ! uv venv .venv --python 3.11; then
  echo "[WARN] uv venv 실패. python venv로 대체합니다."
fi
if [[ ! -x ".venv/bin/python" ]]; then
  if command -v python3.11 >/dev/null 2>&1; then
    python3.11 -m venv .venv
  else
    python3 -m venv .venv
  fi
fi

echo "[2/4] 의존성 동기화 (dev 포함)"
if [[ "$USE_UV" == "1" ]] && ! uv sync --extra dev --python 3.11; then
  echo "[WARN] uv sync 실패. pip install -e \".[dev]\"로 대체합니다."
fi
if ! .venv/bin/python -m pip show pytest >/dev/null 2>&1; then
  if ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
    .venv/bin/python -m ensurepip --upgrade
  fi
  .venv/bin/python -m pip install --upgrade pip || true
  .venv/bin/python -m pip install -e ".[dev]"
fi

if [[ ! -f .env ]]; then
  echo "[3/4] .env 생성 (.env.example 복사)"
  cp .env.example .env
else
  echo "[3/4] .env 파일이 이미 있어 복사를 건너뜁니다"
fi

echo "[4/4] 완료"
echo "실행: .venv/bin/uvicorn app.main:app --reload --port 8000"
echo "테스트: .venv/bin/python -m pytest -q"
