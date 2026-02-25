"""Tests for SemanticRouter and format_docs_with_metadata."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest

from app.features.rag.application.rag_service import format_docs_with_metadata
from app.features.rag.application.semantic_router import SemanticRouter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_mock_embeddings(legal_sim: float = 0.9, general_sim: float = 0.3):
    """Create a mock OpenAIEmbeddings that returns controllable vectors.

    The mock produces:
    - anchor embeddings: unit vectors along sequential axes
    - query embedding: a vector whose cosine similarity with the *first*
      legal anchor equals ``legal_sim`` (approximate).
    """
    embeddings = MagicMock()

    # For aembed_documents: return unit vectors (dim=16 is enough for tests)
    dim = 16

    async def _aembed_documents(texts):
        vecs = []
        for i, _ in enumerate(texts):
            v = np.zeros(dim)
            v[i % dim] = 1.0
            vecs.append(v.tolist())
        return vecs

    embeddings.aembed_documents = AsyncMock(side_effect=_aembed_documents)

    # For aembed_query: return a vector that is ``legal_sim`` close to axis-0
    async def _aembed_query_legal(_text):
        v = np.zeros(dim)
        v[0] = legal_sim
        # Add a small component in an unused direction so magnitude != 0
        v[dim - 1] = np.sqrt(1.0 - legal_sim**2)
        return v.tolist()

    embeddings.aembed_query = AsyncMock(side_effect=_aembed_query_legal)
    return embeddings


@pytest.fixture
def mock_embeddings():
    return _make_mock_embeddings(legal_sim=0.9)


@pytest.fixture
def mock_embeddings_low_sim():
    """Embeddings where semantic similarity is below threshold."""
    return _make_mock_embeddings(legal_sim=0.3)


# ---------------------------------------------------------------------------
# T-2A.6 — SemanticRouter initialization
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_semantic_router_initialize(mock_embeddings) -> None:
    router = SemanticRouter(embeddings=mock_embeddings)
    assert not router._initialized

    await router.initialize()

    assert router._initialized
    assert "legal" in router._anchor_embeddings
    assert "general" in router._anchor_embeddings
    # aembed_documents should have been called once per category
    assert mock_embeddings.aembed_documents.call_count == 2


# ---------------------------------------------------------------------------
# T-2A.6 — Legal query classification (5 cases)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "창업 시 필요한 인허가 절차가 무엇인가요?",
        "음식점 영업신고는 어떻게 하나요?",
        "법인 설립 등록 절차를 알려주세요",
        "4대보험 가입은 어떻게 하나요?",
        "근로계약서 작성 시 주의사항",
    ],
)
async def test_classify_legal_queries(mock_embeddings, query: str) -> None:
    """Legal queries should be routed to 'legal' via semantic similarity."""
    router = SemanticRouter(embeddings=mock_embeddings)
    result = await router.classify(query)
    assert result == "legal"


# ---------------------------------------------------------------------------
# T-2A.6 — General query classification (3 cases)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "카페 인테리어 추천해주세요",
        "좋은 마케팅 전략 알려줘",
        "투자 유치 방법이 궁금해요",
    ],
)
async def test_classify_general_queries(query: str) -> None:
    """General queries with low semantic sim and no keywords -> 'general'."""
    embeddings = _make_mock_embeddings(legal_sim=0.3)

    # Override aembed_query to return a vector far from all anchors
    dim = 16

    async def _aembed_query_general(_text):
        v = np.zeros(dim)
        v[dim - 1] = 1.0  # orthogonal to all anchor vectors
        return v.tolist()

    embeddings.aembed_query = AsyncMock(side_effect=_aembed_query_general)

    router = SemanticRouter(embeddings=embeddings)
    result = await router.classify(query)
    assert result == "general"


# ---------------------------------------------------------------------------
# T-2A.6 — Keyword fallback behavior
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_keyword_fallback_routes_to_legal(mock_embeddings_low_sim) -> None:
    """When semantic similarity is low but keyword matches, route to legal."""
    dim = 16

    # Override query embedding to be far from legal anchors
    async def _aembed_query_far(_text):
        v = np.zeros(dim)
        v[dim - 1] = 1.0
        return v.tolist()

    mock_embeddings_low_sim.aembed_query = AsyncMock(side_effect=_aembed_query_far)

    router = SemanticRouter(embeddings=mock_embeddings_low_sim)
    # Query contains "법률" keyword
    result = await router.classify("이 법률 관련해서 알려줘")
    assert result == "legal"


@pytest.mark.asyncio
async def test_keyword_fallback_no_match(mock_embeddings_low_sim) -> None:
    """When both semantic sim and keyword fail, route to general."""
    dim = 16

    async def _aembed_query_far(_text):
        v = np.zeros(dim)
        v[dim - 1] = 1.0
        return v.tolist()

    mock_embeddings_low_sim.aembed_query = AsyncMock(side_effect=_aembed_query_far)

    router = SemanticRouter(embeddings=mock_embeddings_low_sim)
    result = await router.classify("오늘 날씨가 어때?")
    assert result == "general"


# ---------------------------------------------------------------------------
# T-2A.6 — format_docs_with_metadata output format
# ---------------------------------------------------------------------------


def _make_doc(content: str, metadata: dict) -> SimpleNamespace:
    """Create a lightweight document-like object for testing."""
    return SimpleNamespace(page_content=content, metadata=metadata)


def test_format_docs_with_metadata_empty() -> None:
    result = format_docs_with_metadata([])
    assert result == "관련 법령 문서를 찾을 수 없습니다."


def test_format_docs_with_metadata_single_doc() -> None:
    doc = _make_doc(
        content="사업자등록은 관할 세무서에 신청합니다.",
        metadata={
            "title": "사업자등록 안내",
            "category": "세무",
            "law_reference": "부가가치세법 제8조",
        },
    )
    result = format_docs_with_metadata([doc])

    assert "[출처 1]" in result
    assert "사업자등록 안내" in result
    assert "세무" in result
    assert "법령 참조: 부가가치세법 제8조" in result
    assert "사업자등록은 관할 세무서에 신청합니다." in result


def test_format_docs_with_metadata_no_law_reference() -> None:
    doc = _make_doc(
        content="창업 관련 내용입니다.",
        metadata={"title": "일반 가이드", "category": "창업"},
    )
    result = format_docs_with_metadata([doc])

    assert "[출처 1]" in result
    assert "일반 가이드" in result
    assert "법령 참조" not in result


def test_format_docs_with_metadata_multiple_docs() -> None:
    docs = [
        _make_doc(
            content="첫 번째 문서 내용",
            metadata={"title": "문서1", "category": "행정"},
        ),
        _make_doc(
            content="두 번째 문서 내용",
            metadata={
                "title": "문서2",
                "category": "세무",
                "law_reference": "소득세법 제1조",
            },
        ),
    ]
    result = format_docs_with_metadata(docs)

    # Check separator
    assert "\n\n---\n\n" in result
    assert "[출처 1]" in result
    assert "[출처 2]" in result
    assert "문서1" in result
    assert "문서2" in result
    assert "법령 참조: 소득세법 제1조" in result


def test_format_docs_with_metadata_missing_title_and_category() -> None:
    doc = _make_doc(
        content="메타데이터 없는 문서",
        metadata={},
    )
    result = format_docs_with_metadata([doc])

    assert "[출처 1]" in result
    assert "제목 없음" in result
