"""RoadmapContextBuilder: 3레이어 시스템 프롬프트 빌더.

로드맵 단계 컨텍스트를 조합하여 AI 코치의 시스템 프롬프트를 생성한다.
- LAYER 1 (<FACTS>): 불변 팩트 — 업종, 지역, 법령, 서류
- LAYER 2 (<STATUS>): 실행 상태 — 체크리스트 진행, 위험 요소
- LAYER 3 (<RULES>): 안내 규칙 — 안전장치 5개 + 최근 대화 요약
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger
from app.repositories.roadmap_repository import RoadmapRepository

if TYPE_CHECKING:
    from app.models.roadmap import (
        Roadmap,
        RoadmapStep,
        RoadmapStepAction,
        RoadmapStepDetail,
    )

logger = get_logger(__name__)

# 토큰 추정: 한국어 1글자 ≈ 1.5~2 토큰, 영어 1단어 ≈ 1.3 토큰
# char/4 근사치 사용 (OpenAI tiktoken 대비 보수적)
_CHARS_PER_TOKEN = 4
_DEFAULT_TOKEN_BUDGET = 1200


class RoadmapContextBuilder:
    """3레이어 시스템 프롬프트를 조합하여 AI 코치 컨텍스트를 생성한다."""

    def __init__(self, roadmap_repo: RoadmapRepository):
        self.roadmap_repo = roadmap_repo

    async def build(
        self,
        roadmap: Roadmap,
        step: RoadmapStep,
        token_budget: int = _DEFAULT_TOKEN_BUDGET,
    ) -> tuple[str, list[RoadmapStepAction]]:
        """3레이어 시스템 프롬프트 생성.

        Args:
            roadmap: 대상 로드맵
            step: 현재 단계
            token_budget: 최대 토큰 예산 (기본 1,200)

        Returns:
            (시스템 프롬프트 문자열, step actions 목록) 튜플
        """
        # 단계 상세 + 액션 조회
        details = await self.roadmap_repo.list_step_details([step.id])
        actions = await self.roadmap_repo.list_step_actions([step.id])

        step_detail = details[0] if details else None

        # 3레이어 조합
        layer1 = self._build_fact_layer(roadmap, step_detail, actions)
        layer2 = self._build_state_layer(step, step_detail, actions)
        layer3 = self._build_instruction_layer(step)

        prompt = f"{layer1}\n\n{layer2}\n\n{layer3}"

        return self._trim_to_budget(prompt, max_tokens=token_budget), actions

    # ------------------------------------------------------------------ #
    #  LAYER 1: 불변 팩트 (<FACTS>)
    # ------------------------------------------------------------------ #

    def _build_fact_layer(
        self,
        roadmap: Roadmap,
        step_detail: RoadmapStepDetail | None,
        actions: list[RoadmapStepAction],
    ) -> str:
        """LAYER 1: 불변 팩트 — 업종, 지역, 법령, 서류."""
        parts: list[str] = ["<FACTS>"]

        # 사업 정보
        parts.append("## 사업 정보")
        parts.append(f"- 업종: {roadmap.business_type}")
        parts.append(f"- 지역: {roadmap.location}")
        if roadmap.startup_type:
            parts.append(f"- 창업 형태: {roadmap.startup_type}")
        if roadmap.startup_method:
            parts.append(f"- 창업 방식: {roadmap.startup_method}")
        if roadmap.open_timeline:
            parts.append(f"- 오픈 예정: {roadmap.open_timeline}")
        if roadmap.budget_range:
            parts.append(f"- 예산: {roadmap.budget_range}")

        # 현재 단계
        if step_detail:
            parts.append("")
            parts.append(f"## 현재 단계: {step_detail.phase}")
            if step_detail.objective:
                parts.append(f"- 목표: {step_detail.objective}")
            if step_detail.estimated_days:
                parts.append(f"- 예상 소요: {step_detail.estimated_days}일")

        # 법령 분류
        legal_actions = [a for a in actions if a.action_type == "LEGAL_BASIS"]
        if legal_actions:
            parts.append("")
            parts.append("## 관련 법령 (절대 수정 금지)")
            for idx, action in enumerate(legal_actions, 1):
                parts.append(f"[법령 {idx}] {action.title}")
                if action.description:
                    parts.append(f"  - 설명: {action.description}")
                if action.source_url:
                    parts.append(f"  - 링크: {action.source_url}")
                item_id = (action.metadata_json or {}).get("actionkit_item_id")
                if item_id:
                    parts.append(f"  - ActionKit ID: {item_id}")

        # 서류 분류
        doc_actions = [a for a in actions if a.action_type == "DOCUMENT"]
        if doc_actions:
            parts.append("")
            parts.append("## 필수 서류 (절대 수정 금지)")
            for idx, action in enumerate(doc_actions, 1):
                parts.append(f"[서류 {idx}] {action.title}")
                if action.description:
                    parts.append(f"  - 설명: {action.description}")
                if action.source_url:
                    parts.append(f"  - 다운로드: {action.source_url}")

        parts.append("</FACTS>")
        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    #  LAYER 2: 실행 상태 (<STATUS>)
    # ------------------------------------------------------------------ #

    def _build_state_layer(
        self,
        step: RoadmapStep,
        step_detail: RoadmapStepDetail | None,
        actions: list[RoadmapStepAction],
    ) -> str:
        """LAYER 2: 실행 상태 — 체크리스트 완료/미완료, 위험 요소."""
        parts: list[str] = ["<STATUS>"]

        # 체크리스트 진행 현황
        checklist_actions = [a for a in actions if a.action_type == "CHECKLIST"]
        if checklist_actions:
            completed = sum(
                1
                for a in checklist_actions
                if (a.metadata_json or {}).get("completed")
            )
            total = len(checklist_actions)
            parts.append("## 체크리스트 진행 현황")
            parts.append(f"완료: {completed}/{total}")
            for action in checklist_actions:
                is_done = (action.metadata_json or {}).get("completed", False)
                mark = "V" if is_done else " "
                parts.append(f"- [{mark}] {action.title}")

        # 단계 상태
        parts.append("")
        parts.append(f"## 단계 상태: {step.status}")

        # 위험 요소
        if step_detail and step_detail.risk_notes:
            parts.append("")
            parts.append("## 위험 요소")
            for note in step_detail.risk_notes:
                parts.append(f"- {note}")

        parts.append("</STATUS>")
        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    #  LAYER 3: 안내 규칙 (<RULES>)
    # ------------------------------------------------------------------ #

    def _build_instruction_layer(
        self,
        step: RoadmapStep,
    ) -> str:
        """LAYER 3: 안내 규칙 — 안전장치 + few-shot."""
        parts: list[str] = ["<RULES>"]

        # 역할 정의
        parts.append("## 당신의 역할")
        parts.append(
            "당신은 한국 창업자를 위한 AI 코치입니다. "
            "현재 진행 중인 로드맵 단계에 대해 친절하고 정확하게 안내합니다. "
            "한국어 존댓말을 사용하며, 간결하고 실용적인 답변을 제공합니다."
        )

        # 행동 규칙 5가지
        parts.append("")
        parts.append("## AI 코치 행동 규칙")
        parts.append("")
        parts.append(
            "1. 팩트-지능 분리: <FACTS> 섹션의 법령명, ActionKit ID, URL은 "
            "절대 수정하거나 새로 만들지 마세요. <FACTS>에 없는 법령이나 서류를 "
            "임의로 언급하지 마세요."
        )
        parts.append(
            "2. 출처 강제 인용: 법령이나 서류를 언급할 때 반드시 "
            "[법령 N] 또는 [서류 N] 형식으로 인용하세요. "
            "출처 번호 없이 법령명만 단독으로 언급하지 마세요."
        )
        parts.append(
            f"3. 범위 제한: 현재 단계({step.title})와 관련 없는 질문에는 "
            '"이 질문은 현재 단계의 범위를 벗어납니다. '
            '해당 단계에서 다시 질문해 주세요."라고 안내하세요.'
        )
        parts.append(
            "4. 전문가 권고: 구체적인 세금 계산, 소송 전략, 의료 판단, "
            "투자 수익 예측, 부동산 가격 평가 질문에는 "
            '"이 분야는 전문가 상담을 권장합니다"라고 답하세요.'
        )
        parts.append(
            "5. 불확실성 표현: 확실하지 않은 정보에는 "
            '"확인이 필요합니다"를 명시하고, 추측성 답변을 피하세요.'
        )

        # few-shot 예시 (올바른 답변 패턴)
        parts.append("")
        parts.append("## 올바른 답변 예시")
        parts.append("")
        parts.append("질문: 영업신고는 어떻게 하나요?")
        parts.append(
            "답변: 영업신고는 관할 구청에 방문하여 신청합니다. "
            "[법령 1]에 따라 영업신고서와 함께 [서류 1]을 제출해야 합니다. "
            "구체적인 절차는 관할 구청 위생과에 문의하시면 안내받으실 수 있습니다."
        )
        parts.append("")
        parts.append("질문: 이 서류는 어디서 다운받나요?")
        parts.append(
            "답변: [서류 2]는 위 다운로드 링크에서 받으실 수 있습니다. "
            "작성 시 사업자 정보와 대표자 인적사항을 정확히 기재해 주세요."
        )

        # 네거티브 예시 (하지 말아야 할 패턴)
        parts.append("")
        parts.append("## 하지 말아야 할 답변 패턴")
        parts.append("")
        parts.append(
            "X 잘못된 예: \"식품안전법에 따르면...\" "
            "→ <FACTS>에 없는 법령명을 사용. [법령 N] 형식으로만 인용할 것."
        )
        parts.append(
            "X 잘못된 예: \"세금은 약 300만원 정도 예상됩니다\" "
            "→ 구체적 세금 계산은 전문가 영역. 세무사 상담 권고로 답변할 것."
        )
        parts.append(
            "X 잘못된 예: \"건축법 시행령 제12조에 의하면...\" "
            "→ <FACTS>에 없는 법령 조항을 생성. 팩트에 있는 정보만 인용할 것."
        )

        parts.append("</RULES>")
        return "\n".join(parts)

    # ------------------------------------------------------------------ #
    #  토큰 예산 트리밍
    # ------------------------------------------------------------------ #

    @staticmethod
    def _trim_to_budget(prompt: str, max_tokens: int = _DEFAULT_TOKEN_BUDGET) -> str:
        """토큰 예산 초과 시 CHECKLIST 항목부터 트리밍.

        트리밍 전략:
        1. 전체가 예산 내이면 그대로 반환
        2. 체크리스트가 20개 이상이면 미완료 항목만 남기고 완료 항목 요약
        3. 그래도 초과면 체크리스트를 상위 10개로 제한
        """
        estimated_tokens = len(prompt) // _CHARS_PER_TOKEN
        if estimated_tokens <= max_tokens:
            return prompt

        logger.debug(
            "프롬프트 토큰 초과: %d > %d, 트리밍 시작",
            estimated_tokens,
            max_tokens,
        )

        lines = prompt.split("\n")
        trimmed_lines: list[str] = []
        checklist_lines: list[str] = []
        in_checklist = False
        checklist_count = 0

        for line in lines:
            # 체크리스트 섹션 감지
            if "## 체크리스트 진행 현황" in line:
                in_checklist = True
                trimmed_lines.append(line)
                continue

            if in_checklist:
                if line.startswith("- ["):
                    checklist_count += 1
                    checklist_lines.append(line)
                    continue
                elif line.startswith("##") or line.startswith("</"):
                    # 체크리스트 섹션 종료 — 트리밍 적용
                    in_checklist = False
                    trimmed_lines.extend(
                        _trim_checklist(checklist_lines, max_items=10)
                    )
                    trimmed_lines.append(line)
                    continue
                else:
                    # 완료 카운트 등 메타 라인
                    trimmed_lines.append(line)
                    continue

            trimmed_lines.append(line)

        # 마지막까지 체크리스트인 경우 (닫는 태그 전)
        if in_checklist and checklist_lines:
            trimmed_lines.extend(_trim_checklist(checklist_lines, max_items=10))

        result = "\n".join(trimmed_lines)

        # 최종 안전장치: 여전히 초과면 끝에서 자름
        max_chars = max_tokens * _CHARS_PER_TOKEN
        if len(result) > max_chars:
            result = result[:max_chars]
            # 마지막 완전한 줄까지만 유지
            last_newline = result.rfind("\n")
            if last_newline > 0:
                result = result[:last_newline]

        return result


def _trim_checklist(lines: list[str], max_items: int = 10) -> list[str]:
    """체크리스트 항목을 최대 max_items개로 트리밍.

    미완료 항목([ ])을 우선 유지하고, 완료 항목([V])은 카운트 요약.
    """
    if len(lines) <= max_items:
        return lines

    incomplete = [l for l in lines if "[ ]" in l]
    completed = [l for l in lines if "[V]" in l]

    result: list[str] = []

    # 미완료 항목 우선 (최대 max_items개)
    result.extend(incomplete[:max_items])

    remaining = max_items - len(result)
    if remaining > 0 and completed:
        result.extend(completed[:remaining])

    # 생략된 항목 수 표시
    omitted = len(lines) - len(result)
    if omitted > 0:
        result.append(f"  (... 외 {omitted}개 항목 생략)")

    return result
