"""IntentClassifier — 5카테고리 질문 의도 분류기.

기존 SemanticRouter를 조합 활용하여 사용자 질문을 분류한다.

분류 우선순위:
1. out_of_scope (SemanticRouter, threshold 0.75)
2. step_related (로드맵 보유 사용자만, 키워드 매칭)
3. legal vs general (SemanticRouter, threshold 0.7)
4. 기본값: general
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, Optional

from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.features.rag.application.semantic_router import SemanticRouter

logger = get_logger(__name__)

IntentCategory = Literal[
    "current_step", "other_step", "legal_general", "general", "out_of_scope"
]

# 현재 단계를 가리키는 맥락 키워드
_CURRENT_STEP_KEYWORDS: frozenset[str] = frozenset(
    {
        "이 단계",
        "지금 단계",
        "현재 단계",
        "현재",
        "지금",
        "체크리스트",
        "이번 단계",
        "이 스텝",
        "지금 하는",
        "현재 진행",
    }
)

# 다른 단계를 특정하는 패턴 (숫자 + 단계/스텝)
_OTHER_STEP_PATTERN = re.compile(r"(\d+)\s*단계|(\d+)\s*스텝|제\s*(\d+)\s*단계")

# legal 키워드 폴백 (SemanticRouter의 LEGAL_KEYWORDS와 동일 + 확장)
_LEGAL_KEYWORDS: frozenset[str] = frozenset(
    {
        "법",
        "법률",
        "규정",
        "허가",
        "인허가",
        "등록",
        "신고",
        "계약",
        "근로",
        "면허",
        "인가",
        "법령",
        "조례",
        "신청",
        "영업",
        "위생",
        "행정심판",
        "행정조사",
        "소방",
        "개인정보",
        "근로계약",
        "보험",
        "세금",
    }
)


@dataclass
class StepInfo:
    """로드맵 단계 요약 정보 (분류기 입력용)."""

    step_id: int
    step_order: int
    title: str
    keywords: list[str] = field(default_factory=list)


@dataclass
class IntentResult:
    """의도 분류 결과."""

    category: IntentCategory
    step_id: Optional[int] = None
    step_title: Optional[str] = None
    confidence: Optional[float] = None


class IntentClassifier:
    """5카테고리 질문 의도 분류기.

    기존 SemanticRouter를 조합 활용하여 분류 수행.
    """

    def __init__(self, semantic_router: SemanticRouter) -> None:
        self._router = semantic_router

    async def classify(
        self,
        query: str,
        roadmap_steps: list[StepInfo] | None = None,
        current_step_id: int | None = None,
    ) -> IntentResult:
        """질문을 5카테고리로 분류.

        Args:
            query: 사용자 질문
            roadmap_steps: 로드맵 단계 목록 (없으면 step 매칭 건너뜀)
            current_step_id: 현재 활성 단계 ID

        Returns:
            IntentResult with category, optional step info, confidence
        """
        # 1순위: out_of_scope 체크 (SemanticRouter 위임)
        route = await self._router.classify(
            query, threshold=0.7, out_of_scope_threshold=0.75
        )
        if route == "out_of_scope":
            logger.debug("Intent: out_of_scope (via SemanticRouter)")
            return IntentResult(category="out_of_scope")

        # 2순위: step_related 매칭 (로드맵 보유 사용자만)
        if roadmap_steps is not None:
            step_result = self._match_step(query, roadmap_steps, current_step_id)
            if step_result is not None:
                logger.debug(
                    "Intent: %s (step_id=%s)",
                    step_result.category,
                    step_result.step_id,
                )
                return step_result

        # 3순위: legal vs general (SemanticRouter 결과 재활용)
        if route == "legal":
            logger.debug("Intent: legal_general (via SemanticRouter)")
            return IntentResult(category="legal_general")

        # legal 키워드 폴백
        if self._has_legal_keyword(query):
            logger.debug("Intent: legal_general (keyword fallback)")
            return IntentResult(category="legal_general")

        # 4순위: 기본값
        logger.debug("Intent: general")
        return IntentResult(category="general")

    def _match_step(
        self,
        query: str,
        steps: list[StepInfo],
        current_step_id: int | None,
    ) -> IntentResult | None:
        """로드맵 단계 키워드 매칭.

        Returns:
            IntentResult if matched, None otherwise
        """
        # 현재 단계 맥락 키워드 체크
        if current_step_id is not None and self._has_current_step_cue(query):
            current = next((s for s in steps if s.step_id == current_step_id), None)
            if current is not None:
                return IntentResult(
                    category="current_step",
                    step_id=current.step_id,
                    step_title=current.title,
                )

        # 다른 단계 번호 패턴 매칭 ("2단계", "3스텝", "제2단계")
        other = self._match_step_number(query, steps, current_step_id)
        if other is not None:
            return other

        # 단계 제목 키워드 매칭
        title_match = self._match_step_title(query, steps, current_step_id)
        if title_match is not None:
            return title_match

        return None

    @staticmethod
    def _has_current_step_cue(query: str) -> bool:
        """질문에 현재 단계를 가리키는 맥락 키워드가 있는지."""
        return any(kw in query for kw in _CURRENT_STEP_KEYWORDS)

    @staticmethod
    def _match_step_number(
        query: str,
        steps: list[StepInfo],
        current_step_id: int | None,
    ) -> IntentResult | None:
        """'N단계', 'N스텝' 패턴으로 단계 매칭."""
        match = _OTHER_STEP_PATTERN.search(query)
        if match is None:
            return None

        # 매칭된 그룹 중 숫자 추출
        step_num = int(next(g for g in match.groups() if g is not None))

        # step_order로 매칭
        matched = next((s for s in steps if s.step_order == step_num), None)
        if matched is None:
            return None

        category: IntentCategory = (
            "current_step" if matched.step_id == current_step_id else "other_step"
        )
        return IntentResult(
            category=category,
            step_id=matched.step_id,
            step_title=matched.title,
        )

    @staticmethod
    def _match_step_title(
        query: str,
        steps: list[StepInfo],
        current_step_id: int | None,
    ) -> IntentResult | None:
        """단계 제목 또는 커스텀 키워드로 매칭.

        제목의 각 키워드를 질문에서 찾는다.
        """
        best_match: StepInfo | None = None
        best_score = 0

        for step in steps:
            # 기본 키워드: 제목을 공백으로 분리
            all_keywords = step.title.split() + step.keywords
            if not all_keywords:
                continue

            matched_count = sum(1 for kw in all_keywords if kw in query)
            if matched_count > best_score:
                best_score = matched_count
                best_match = step

        if best_match is None or best_score == 0:
            return None

        category: IntentCategory = (
            "current_step"
            if best_match.step_id == current_step_id
            else "other_step"
        )
        return IntentResult(
            category=category,
            step_id=best_match.step_id,
            step_title=best_match.title,
        )

    @staticmethod
    def _has_legal_keyword(query: str) -> bool:
        """질문에 법률 관련 키워드가 포함되어 있는지."""
        return any(kw in query for kw in _LEGAL_KEYWORDS)
