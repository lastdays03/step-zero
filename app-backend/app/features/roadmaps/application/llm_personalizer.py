"""LLM Personalizer: Intelligence layer for roadmap generation.

Takes ActionKit fact data + user context and produces personalized
roadmap step details.  ActionKit-provided law names and file paths
are NEVER modified; the LLM only judges, reorders, and supplements.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from langchain_openai import ChatOpenAI

from app.core.logging import get_logger
from app.features.roadmaps.application.actionkit_matcher import MatchedActionKit

logger = get_logger(__name__)


@dataclass
class PersonalizedStepDetail:
    """Output of LLM personalization for one roadmap phase/step."""

    phase: str
    title: str = ""
    objective: str = ""
    estimated_days: int = 0
    checklist: list[str] = field(default_factory=list)
    legal_basis: list[dict] = field(default_factory=list)
    documents: list[dict] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    actionkit_items: list[int] = field(default_factory=list)
    mapping_source: str = "actionkit_direct"


# ------------------------------------------------------------------ #
#  Prompt template (Korean, user-facing)
# ------------------------------------------------------------------ #

_SYSTEM_PROMPT = """\
당신은 대한민국 소상공인 창업 전문 컨설턴트입니다.
아래 제공되는 **ActionKit 팩트 데이터**(법령, 하이라이트, 파일)와 **사용자 정보**를 결합하여
맞춤형 창업 로드맵 단계(phase)별 상세 정보를 생성합니다.

## 절대 규칙
1. ActionKit에서 제공된 **법령명**(law_name)과 **파일 경로**(object_key)는 **절대로 수정하지 마세요.**
   그대로 인용하세요.
2. 체크리스트, 목표, 위험 사항은 사용자 맥락에 맞게 **재정렬, 필터링, 보충**할 수 있습니다.
3. ActionKit에 없는 추가 법령이나 서류를 **임의로 생성하지 마세요.**
   보충이 필요하면 "추가 확인 필요" 로 표시하세요.

## 개인화 7가지 영역
1. **checklist**: 하이라이트를 사용자 업종/상황에 맞게 재정렬·필터링·보충
2. **legal_basis**: 사용자 업종에 관련 높은 법령을 강조
3. **documents**: 제출 순서 + 준비 가이드 추가
4. **phases**: 사용자 일정에 따라 순서 조정·병렬 실행 결정
5. **objective**: 업종/지역 특화 목표
6. **risk_notes**: 업종 특화 위험 요소
7. **estimated_days**: open_timeline 기반 일수 산정

## 창업 형태별 차이
- 신규: 전 과정 진행
- 양수양도: 기존 인허가 승계 절차 포함
- 프랜차이즈: 본사 지원 항목 구분

## 경험 수준별 차이
- BEGINNER: 각 단계를 상세히, 체크리스트 항목 세분화
- EXPERIENCED: 핵심만 간결하게

## 출력 형식
JSON 배열을 반환하세요. 각 요소의 구조:
```json
{{
  "phase": "단계명",
  "title": "단계 제목",
  "objective": "이 단계의 목표 (1~2문장)",
  "estimated_days": 숫자,
  "checklist": ["항목1", "항목2", ...],
  "legal_basis": [
    {{"title": "법령명 (ActionKit 원본 그대로)", "snippet": "요약 설명", "actionkit_item_id": 숫자}}
  ],
  "documents": [
    {{"name": "서류명", "file_url": "object_key (ActionKit 원본 그대로)", "actionkit_item_id": 숫자}}
  ],
  "risk_notes": ["위험요소1", ...],
  "actionkit_items": [사용한 item_id 목록]
}}
```

**반드시 유효한 JSON 배열만 반환하세요. 추가 설명 없이.**
"""

_USER_PROMPT_TEMPLATE = """\
## 사용자 정보
- 업종: {business_type}
- 지역: {location}
- 창업 형태: {startup_type}
- 오픈 목표: {open_timeline}
- 예산 범위: {budget_range}
- 경험 수준: {experience_level}
- 추가 설명: {description}
- 추가 메모: {additional_notes}

## ActionKit 팩트 데이터
{fact_data}

위 데이터를 기반으로 로드맵 단계별 상세를 JSON 배열로 생성하세요.
"""


class LLMPersonalizer:
    """Intelligence Layer: personalizes roadmap steps from ActionKit facts.

    7 personalization areas:
    1. checklist: reorder + filter + supplement highlights
    2. legal_basis: emphasize relevant laws for business type
    3. documents: add submission order + preparation guide
    4. phases: adjust order + parallel execution decisions
    5. objective: business/location-specific goals
    6. risk_notes: business-specific risks
    7. estimated_days: based on open_timeline

    RULE: ActionKit-provided law names and file paths MUST NOT be modified.
    """

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    async def personalize(
        self,
        matched_items: list[MatchedActionKit],
        payload: dict,
    ) -> list[PersonalizedStepDetail]:
        """Generate personalized step details from ActionKit facts + user payload."""
        fact_data = self._format_fact_data(matched_items)
        user_prompt = _USER_PROMPT_TEMPLATE.format(
            business_type=payload.get("business_type", ""),
            location=payload.get("location", ""),
            startup_type=payload.get("startup_type") or "신규",
            open_timeline=payload.get("open_timeline") or "미입력",
            budget_range=payload.get("budget_range") or "미입력",
            experience_level=payload.get("experience_level", "BEGINNER"),
            description=payload.get("description", ""),
            additional_notes=payload.get("additional_notes", ""),
            fact_data=fact_data,
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            from fastapi.concurrency import run_in_threadpool

            response = await run_in_threadpool(
                self.llm.invoke, messages
            )
            raw_text = response.content if hasattr(response, "content") else str(response)
        except Exception:
            logger.exception("LLM personalization call failed")
            return self._fallback_from_facts(matched_items, payload)

        # Parse JSON array from LLM response
        parsed = self._parse_json_array(raw_text)
        if not parsed:
            logger.warning("LLM returned unparsable response; using fallback")
            return self._fallback_from_facts(matched_items, payload)

        # Convert to PersonalizedStepDetail objects
        details = self._convert_to_details(parsed)

        # Post-processing validation: verify law names and file paths
        original_law_names, original_file_keys = self._collect_originals(matched_items)
        details = self._validate_references(details, original_law_names, original_file_keys)

        return details

    # ------------------------------------------------------------------ #
    #  Fact data formatting
    # ------------------------------------------------------------------ #

    @staticmethod
    def _format_fact_data(matched_items: list[MatchedActionKit]) -> str:
        """Format matched ActionKit items as structured text for the LLM prompt."""
        groups: dict[str, list[str]] = {}

        for m in matched_items:
            phase = m.phase_group or "기타"
            parts: list[str] = []
            parts.append(f"### [{m.item.domain}] {m.item.name} (item_id={m.item.id})")
            parts.append(f"  요약: {m.item.summary}")

            if m.highlights:
                parts.append("  핵심 포인트:")
                for h in m.highlights:
                    parts.append(f"    - {h.content}")

            if m.related_laws:
                parts.append("  관련 법령:")
                for law in m.related_laws:
                    summary_part = f" - {law.law_summary}" if law.law_summary else ""
                    parts.append(f"    - {law.law_name}{summary_part}")

            if m.files:
                parts.append("  파일:")
                for f in m.files:
                    parts.append(
                        f"    - {f.original_filename or f.object_key} "
                        f"(object_key={f.object_key}, file_id={f.id})"
                    )

            groups.setdefault(phase, []).append("\n".join(parts))

        sections: list[str] = []
        for phase, items in groups.items():
            sections.append(f"\n## 단계: {phase}")
            sections.extend(items)

        return "\n".join(sections)

    # ------------------------------------------------------------------ #
    #  JSON parsing
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_json_array(raw: str) -> list[dict] | None:
        """Parse a JSON array from LLM response text."""
        text = raw.strip()
        # Strip markdown code fences
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

        # Try to find array boundaries
        try:
            start = text.find("[")
            end = text.rfind("]")
            if start >= 0 and end > start:
                result = json.loads(text[start : end + 1])
                if isinstance(result, list):
                    return result
        except json.JSONDecodeError:
            pass

        return None

    # ------------------------------------------------------------------ #
    #  Conversion & validation
    # ------------------------------------------------------------------ #

    @staticmethod
    def _convert_to_details(parsed: list[dict]) -> list[PersonalizedStepDetail]:
        """Convert parsed JSON dicts to PersonalizedStepDetail objects."""
        details: list[PersonalizedStepDetail] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            risk_notes_raw = item.get("risk_notes", [])
            if isinstance(risk_notes_raw, str):
                risk_notes_raw = [risk_notes_raw]

            detail = PersonalizedStepDetail(
                phase=item.get("phase", "기본"),
                title=item.get("title", item.get("phase", "단계")),
                objective=item.get("objective", ""),
                estimated_days=int(item.get("estimated_days") or 0),
                checklist=item.get("checklist", []),
                legal_basis=item.get("legal_basis", []),
                documents=item.get("documents", []),
                risk_notes=risk_notes_raw,
                actionkit_items=item.get("actionkit_items", []),
                mapping_source="actionkit_direct",
            )
            details.append(detail)
        return details

    @staticmethod
    def _collect_originals(
        matched_items: list[MatchedActionKit],
    ) -> tuple[set[str], set[str]]:
        """Collect original law names and file keys from ActionKit data."""
        law_names: set[str] = set()
        file_keys: set[str] = set()
        for m in matched_items:
            for law in m.related_laws:
                law_names.add(law.law_name)
            for f in m.files:
                file_keys.add(f.object_key)
        return law_names, file_keys

    @staticmethod
    def _validate_references(
        details: list[PersonalizedStepDetail],
        original_law_names: set[str],
        original_file_keys: set[str],
    ) -> list[PersonalizedStepDetail]:
        """Validate that LLM output references match ActionKit originals.

        If a law name or file path was modified by the LLM, log a warning
        but keep the entry (the LLM may have reformatted slightly).
        """
        for detail in details:
            for lb in detail.legal_basis:
                title = lb.get("title", "")
                if title and original_law_names and title not in original_law_names:
                    logger.debug(
                        "LLM modified law name: '%s' not in originals", title
                    )

            for doc in detail.documents:
                file_url = doc.get("file_url", "")
                if file_url and original_file_keys and file_url not in original_file_keys:
                    logger.debug(
                        "LLM modified file path: '%s' not in originals", file_url
                    )

        return details

    # ------------------------------------------------------------------ #
    #  Fallback (when LLM fails)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _fallback_from_facts(
        matched_items: list[MatchedActionKit],
        payload: dict,
    ) -> list[PersonalizedStepDetail]:
        """Generate basic details from ActionKit facts without LLM.

        This fallback path preserves ActionKit data with mapping_source='actionkit_direct'
        since we have real source data, just without LLM personalization.
        """
        phase_groups: dict[str, list[MatchedActionKit]] = {}
        for m in matched_items:
            phase = m.phase_group or "기타"
            phase_groups.setdefault(phase, []).append(m)

        business_type = payload.get("business_type", "사업체")
        details: list[PersonalizedStepDetail] = []
        for phase, items in phase_groups.items():
            checklist: list[str] = []
            legal_basis: list[dict] = []
            documents: list[dict] = []
            actionkit_ids: list[int] = []

            for m in items:
                if m.item.id is not None:
                    actionkit_ids.append(m.item.id)

                for h in m.highlights:
                    checklist.append(h.content)

                for law in m.related_laws:
                    legal_basis.append({
                        "title": law.law_name,
                        "snippet": law.law_summary or "",
                        "actionkit_item_id": m.item.id,
                    })

                for f in m.files:
                    documents.append({
                        "name": f.original_filename or f.object_key,
                        "file_url": f.object_key,
                        "actionkit_item_id": m.item.id,
                        "actionkit_file_id": f.id,
                    })

            if not checklist:
                checklist = [f"{business_type} {phase} 관련 필수 요건 확인"]

            detail = PersonalizedStepDetail(
                phase=phase,
                title=f"{business_type} {phase} 단계 진행",
                objective=f"{business_type} 창업을 위한 {phase} 절차를 진행합니다.",
                estimated_days=5,
                checklist=checklist,
                legal_basis=legal_basis if legal_basis else [{"title": "관련 법령 확인 필요", "snippet": f"{business_type} {phase} 관련 법령을 확인하세요."}],
                documents=documents,
                risk_notes=[f"{phase} 세부 요건 미확인 시 보완 명령 가능성"],
                actionkit_items=actionkit_ids,
                mapping_source="actionkit_direct",
            )
            details.append(detail)

        return details
