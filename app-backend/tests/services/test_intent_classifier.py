"""IntentClassifier 5카테고리 분류 단위 테스트.

SemanticRouter를 mock하여 IntentClassifier의 분류 로직만 검증한다.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.features.chat.application.intent_classifier import (
    IntentClassifier,
    IntentResult,
    StepInfo,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_router(classify_return: str = "general") -> MagicMock:
    """SemanticRouter mock 생성.

    classify()가 항상 ``classify_return``을 반환한다.
    """
    router = MagicMock()
    router.classify = AsyncMock(return_value=classify_return)
    return router


def _sample_steps() -> list[StepInfo]:
    """테스트용 로드맵 단계 3개."""
    return [
        StepInfo(step_id=10, step_order=1, title="사업자등록"),
        StepInfo(step_id=20, step_order=2, title="영업 인허가 신청"),
        StepInfo(step_id=30, step_order=3, title="인테리어 공사"),
    ]


# ---------------------------------------------------------------------------
# 1순위: out_of_scope
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_out_of_scope_via_semantic_router() -> None:
    """SemanticRouter가 out_of_scope를 반환하면 out_of_scope."""
    router = _make_router("out_of_scope")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify("세금 얼마나 내야 하나요")

    assert result.category == "out_of_scope"
    assert result.step_id is None


@pytest.mark.asyncio
async def test_out_of_scope_even_with_roadmap_steps() -> None:
    """out_of_scope는 로드맵 단계가 있어도 우선 적용."""
    router = _make_router("out_of_scope")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "주식 투자 추천해 주세요",
        roadmap_steps=_sample_steps(),
        current_step_id=10,
    )

    assert result.category == "out_of_scope"


# ---------------------------------------------------------------------------
# 2순위: current_step
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_current_step_context_keyword() -> None:
    """'현재 단계' 맥락 키워드 → current_step."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "현재 단계에서 뭘 해야 하나요",
        roadmap_steps=_sample_steps(),
        current_step_id=10,
    )

    assert result.category == "current_step"
    assert result.step_id == 10
    assert result.step_title == "사업자등록"


@pytest.mark.asyncio
async def test_current_step_checklist_keyword() -> None:
    """'체크리스트' 키워드 → current_step."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "체크리스트 확인하고 싶어요",
        roadmap_steps=_sample_steps(),
        current_step_id=20,
    )

    assert result.category == "current_step"
    assert result.step_id == 20


@pytest.mark.asyncio
async def test_current_step_jigeum_keyword() -> None:
    """'지금' 키워드 → current_step."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "지금 뭐 해야 해요?",
        roadmap_steps=_sample_steps(),
        current_step_id=30,
    )

    assert result.category == "current_step"
    assert result.step_id == 30


# ---------------------------------------------------------------------------
# 2순위: other_step (번호 패턴)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_other_step_number_pattern() -> None:
    """'2단계' 패턴 → other_step (현재 단계가 아닐 때)."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "2단계는 어떻게 진행하나요",
        roadmap_steps=_sample_steps(),
        current_step_id=10,
    )

    assert result.category == "other_step"
    assert result.step_id == 20
    assert result.step_title == "영업 인허가 신청"


@pytest.mark.asyncio
async def test_step_number_pattern_current() -> None:
    """'1단계' 패턴인데 현재 단계가 1단계면 → current_step."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "1단계 진행 상태 알려주세요",
        roadmap_steps=_sample_steps(),
        current_step_id=10,
    )

    assert result.category == "current_step"
    assert result.step_id == 10


@pytest.mark.asyncio
async def test_step_number_je_pattern() -> None:
    """'제3단계' 패턴 → other_step."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "제3단계에 대해 알려주세요",
        roadmap_steps=_sample_steps(),
        current_step_id=10,
    )

    assert result.category == "other_step"
    assert result.step_id == 30


@pytest.mark.asyncio
async def test_step_number_nonexistent() -> None:
    """존재하지 않는 단계 번호 → step 매칭 실패, 다음 분류로."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "5단계는 뭔가요",
        roadmap_steps=_sample_steps(),
        current_step_id=10,
    )

    # 5단계는 없으므로 step 매칭 실패 → general
    assert result.category == "general"


# ---------------------------------------------------------------------------
# 2순위: other_step (제목 키워드 매칭)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_other_step_title_keyword() -> None:
    """단계 제목 키워드 '인허가' → other_step."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "인허가 신청은 어떻게 하나요",
        roadmap_steps=_sample_steps(),
        current_step_id=10,
    )

    assert result.category == "other_step"
    assert result.step_id == 20


@pytest.mark.asyncio
async def test_title_keyword_current_step() -> None:
    """단계 제목 키워드가 현재 단계와 매칭 → current_step."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "사업자등록 서류가 뭐가 필요해요",
        roadmap_steps=_sample_steps(),
        current_step_id=10,  # step 10 = "사업자등록"
    )

    assert result.category == "current_step"
    assert result.step_id == 10


# ---------------------------------------------------------------------------
# 3순위: legal_general
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_legal_via_semantic_router() -> None:
    """SemanticRouter가 'legal'을 반환하면 → legal_general."""
    router = _make_router("legal")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify("영업신고 절차를 알려주세요")

    assert result.category == "legal_general"


@pytest.mark.asyncio
async def test_legal_keyword_fallback() -> None:
    """SemanticRouter는 general인데 법률 키워드 포함 → legal_general."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify("이 법률에 대해 알려주세요")

    assert result.category == "legal_general"


@pytest.mark.asyncio
async def test_legal_without_roadmap() -> None:
    """로드맵 없는 사용자도 legal_general 분류 가능."""
    router = _make_router("legal")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "인허가 절차가 궁금해요",
        roadmap_steps=None,
        current_step_id=None,
    )

    assert result.category == "legal_general"
    assert result.step_id is None


# ---------------------------------------------------------------------------
# 4순위: general (기본값)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_general_default() -> None:
    """어디에도 해당하지 않으면 → general."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify("카페 인테리어 추천해주세요")

    assert result.category == "general"
    assert result.step_id is None


@pytest.mark.asyncio
async def test_general_no_roadmap() -> None:
    """로드맵 없는 사용자의 일반 질문 → general."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "마케팅 전략을 알려주세요",
        roadmap_steps=None,
    )

    assert result.category == "general"


@pytest.mark.asyncio
async def test_general_with_empty_steps() -> None:
    """빈 단계 목록 → step 매칭 건너뜀, general."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "현재 단계에서 뭘 해야 하나요",
        roadmap_steps=[],
        current_step_id=None,
    )

    # roadmap_steps가 빈 리스트 (not None) → step 매칭 시도하지만 매칭 없음
    assert result.category == "general"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_current_step_cue_without_current_step_id() -> None:
    """current_step_id가 None이면 맥락 키워드가 있어도 current_step 안 됨."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    result = await classifier.classify(
        "현재 단계 알려주세요",
        roadmap_steps=_sample_steps(),
        current_step_id=None,
    )

    # current_step_id 없으므로 current_step 불가 → general
    assert result.category == "general"


@pytest.mark.asyncio
async def test_step_matching_best_score() -> None:
    """여러 단계와 부분 매칭 시 최다 매칭 단계 선택."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    steps = [
        StepInfo(step_id=1, step_order=1, title="사업자 등록 신청"),
        StepInfo(step_id=2, step_order=2, title="영업 신고 등록"),
    ]

    # "등록 신청"은 step 1과 2개 매칭, step 2와 1개 매칭
    result = await classifier.classify(
        "등록 신청 방법 알려주세요",
        roadmap_steps=steps,
        current_step_id=2,
    )

    assert result.step_id == 1
    assert result.category == "other_step"


@pytest.mark.asyncio
async def test_semantic_router_threshold_passed() -> None:
    """SemanticRouter.classify()에 올바른 threshold가 전달되는지 확인."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    await classifier.classify("테스트 질문")

    router.classify.assert_called_once_with(
        "테스트 질문", threshold=0.7, out_of_scope_threshold=0.75
    )


@pytest.mark.asyncio
async def test_custom_keywords_in_step_info() -> None:
    """StepInfo.keywords로 추가 키워드 매칭."""
    router = _make_router("general")
    classifier = IntentClassifier(semantic_router=router)

    steps = [
        StepInfo(
            step_id=1,
            step_order=1,
            title="사업자등록",
            keywords=["세무서", "사업자"],
        ),
    ]

    result = await classifier.classify(
        "세무서에 방문해야 하나요",
        roadmap_steps=steps,
        current_step_id=1,
    )

    assert result.category == "current_step"
    assert result.step_id == 1
