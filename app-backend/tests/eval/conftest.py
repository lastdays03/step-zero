"""RAG 평가 테스트 공통 fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

EVAL_DATA_DIR = Path(__file__).parent / "data"
EVAL_RESULTS_DIR = Path(__file__).parent / "results"


@pytest.fixture(scope="session")
def golden_dataset() -> list[dict[str, Any]]:
    """골든 데이터셋 로드."""
    path = EVAL_DATA_DIR / "golden_dataset.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def legal_cases(golden_dataset: list[dict]) -> list[dict]:
    """법률 RAG 대상 케이스만 필터링."""
    return [c for c in golden_dataset if c["expected_source"] == "legal_rag"]


@pytest.fixture(scope="session")
def general_cases(golden_dataset: list[dict]) -> list[dict]:
    """일반 대화 케이스만 필터링."""
    return [c for c in golden_dataset if c["expected_source"] == "general"]


@pytest.fixture(scope="session")
def routing_edge_cases(golden_dataset: list[dict]) -> list[dict]:
    """라우팅 경계 케이스 필터링."""
    return [c for c in golden_dataset if c["category"] == "routing_edge"]


@pytest.fixture(scope="session")
def out_of_scope_cases(golden_dataset: list[dict]) -> list[dict]:
    """범위 밖 케이스 필터링."""
    return [c for c in golden_dataset if c["category"] == "out_of_scope"]


def ensure_results_dir() -> Path:
    """결과 저장 디렉토리 보장."""
    EVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return EVAL_RESULTS_DIR
