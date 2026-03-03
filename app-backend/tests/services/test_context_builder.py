"""RoadmapContextBuilder 단위 테스트.

각 레이어 독립 검증 + build() 통합 + 토큰 예산 트리밍 검증.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.features.roadmaps.application.context_builder import (
    RoadmapContextBuilder,
    _trim_checklist,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_mock_roadmap(**overrides):
    """테스트용 Roadmap mock 객체."""
    roadmap = MagicMock()
    roadmap.business_type = overrides.get("business_type", "카페")
    roadmap.location = overrides.get("location", "서울특별시 강남구")
    roadmap.startup_type = overrides.get("startup_type", "개인사업자")
    roadmap.startup_method = overrides.get("startup_method", "신규")
    roadmap.open_timeline = overrides.get("open_timeline", "2026년 6월")
    roadmap.budget_range = overrides.get("budget_range", "5000만원~1억원")
    return roadmap


def _make_mock_step(title="영업 인허가 신청", status="IN_PROGRESS"):
    """테스트용 RoadmapStep mock 객체."""
    step = MagicMock()
    step.id = 1
    step.title = title
    step.status = status
    return step


def _make_mock_step_detail(**overrides):
    """테스트용 RoadmapStepDetail mock 객체."""
    detail = MagicMock()
    detail.phase = overrides.get("phase", "인허가")
    detail.objective = overrides.get("objective", "영업신고 완료")
    detail.estimated_days = overrides.get("estimated_days", 14)
    detail.risk_notes = overrides.get("risk_notes", ["지역별 처리 기간 상이"])
    return detail


def _make_mock_actions():
    """테스트용 RoadmapStepAction 목록 mock."""
    legal = MagicMock()
    legal.action_type = "LEGAL_BASIS"
    legal.title = "식품위생법"
    legal.description = "영업신고 근거 법령"
    legal.source_url = "/api/v1/actionkits/items/42"
    legal.metadata_json = {"actionkit_item_id": 42}

    document = MagicMock()
    document.action_type = "DOCUMENT"
    document.title = "영업신고서"
    document.description = "영업신고 신청서류"
    document.source_url = "/api/v1/actionkits/items/43"
    document.metadata_json = {}

    checklist1 = MagicMock()
    checklist1.action_type = "CHECKLIST"
    checklist1.title = "관할 구청 방문"
    checklist1.metadata_json = {"completed": True}

    checklist2 = MagicMock()
    checklist2.action_type = "CHECKLIST"
    checklist2.title = "위생교육 수료"
    checklist2.metadata_json = {"completed": False}

    return [legal, document, checklist1, checklist2]


def _make_mock_messages(count=3):
    """테스트용 최근 대화 메시지 mock."""
    messages = []
    for i in range(count):
        msg = MagicMock()
        msg.role = "user" if i % 2 == 0 else "assistant"
        msg.content = f"테스트 메시지 {i}"
        messages.append(msg)
    return messages


def _make_builder(step_details=None, step_actions=None):
    """모킹된 RoadmapRepository로 ContextBuilder 생성."""
    repo = MagicMock()
    repo.list_step_details = AsyncMock(
        return_value=step_details if step_details is not None else []
    )
    repo.list_step_actions = AsyncMock(
        return_value=step_actions if step_actions is not None else []
    )
    return RoadmapContextBuilder(roadmap_repo=repo)


# ---------------------------------------------------------------------------
# LAYER 1: 불변 팩트 테스트
# ---------------------------------------------------------------------------


def test_build_fact_layer_contains_business_info():
    """LAYER 1에 사업 정보(업종, 지역)가 포함된다."""
    builder = _make_builder()
    roadmap = _make_mock_roadmap()
    detail = _make_mock_step_detail()
    actions = _make_mock_actions()

    result = builder._build_fact_layer(roadmap, detail, actions)

    assert "<FACTS>" in result
    assert "</FACTS>" in result
    assert "카페" in result
    assert "서울특별시 강남구" in result
    assert "개인사업자" in result
    assert "신규" in result
    assert "2026년 6월" in result
    assert "5000만원~1억원" in result


def test_build_fact_layer_contains_legal_basis():
    """LAYER 1에 법령 정보가 [법령 N] 형식으로 포함된다."""
    builder = _make_builder()
    roadmap = _make_mock_roadmap()
    detail = _make_mock_step_detail()
    actions = _make_mock_actions()

    result = builder._build_fact_layer(roadmap, detail, actions)

    assert "[법령 1] 식품위생법" in result
    assert "영업신고 근거 법령" in result
    assert "/api/v1/actionkits/items/42" in result
    assert "ActionKit ID: 42" in result
    assert "관련 법령 (절대 수정 금지)" in result


def test_build_fact_layer_contains_documents():
    """LAYER 1에 필수 서류 정보가 [서류 N] 형식으로 포함된다."""
    builder = _make_builder()
    roadmap = _make_mock_roadmap()
    detail = _make_mock_step_detail()
    actions = _make_mock_actions()

    result = builder._build_fact_layer(roadmap, detail, actions)

    assert "[서류 1] 영업신고서" in result
    assert "영업신고 신청서류" in result
    assert "필수 서류 (절대 수정 금지)" in result


def test_build_fact_layer_no_optional_fields():
    """선택 필드가 None이면 해당 줄이 생략된다."""
    builder = _make_builder()
    roadmap = _make_mock_roadmap(
        startup_type=None,
        startup_method=None,
        open_timeline=None,
        budget_range=None,
    )

    result = builder._build_fact_layer(roadmap, None, [])

    assert "창업 형태" not in result
    assert "창업 방식" not in result
    assert "오픈 예정" not in result
    assert "예산" not in result


def test_build_fact_layer_no_step_detail():
    """step_detail이 None이면 단계 섹션이 생략된다."""
    builder = _make_builder()
    roadmap = _make_mock_roadmap()

    result = builder._build_fact_layer(roadmap, None, [])

    assert "현재 단계" not in result
    assert "<FACTS>" in result
    assert "</FACTS>" in result


def test_build_fact_layer_no_legal_or_doc():
    """법령/서류가 없으면 해당 섹션이 생략된다."""
    builder = _make_builder()
    roadmap = _make_mock_roadmap()
    checklist = MagicMock()
    checklist.action_type = "CHECKLIST"
    checklist.title = "테스트 항목"
    checklist.metadata_json = {}

    result = builder._build_fact_layer(roadmap, None, [checklist])

    assert "관련 법령" not in result
    assert "필수 서류" not in result


# ---------------------------------------------------------------------------
# LAYER 2: 실행 상태 테스트
# ---------------------------------------------------------------------------


def test_build_state_layer_contains_checklist_progress():
    """LAYER 2에 체크리스트 진행 현황이 포함된다."""
    builder = _make_builder()
    step = _make_mock_step()
    detail = _make_mock_step_detail()
    actions = _make_mock_actions()

    result = builder._build_state_layer(step, detail, actions)

    assert "<STATUS>" in result
    assert "</STATUS>" in result
    assert "체크리스트 진행 현황" in result
    assert "완료: 1/2" in result
    assert "[V] 관할 구청 방문" in result
    assert "[ ] 위생교육 수료" in result


def test_build_state_layer_contains_risk_notes():
    """LAYER 2에 위험 요소가 포함된다."""
    builder = _make_builder()
    step = _make_mock_step()
    detail = _make_mock_step_detail(risk_notes=["지역별 처리 기간 상이", "서류 누락 주의"])

    result = builder._build_state_layer(step, detail, [])

    assert "위험 요소" in result
    assert "지역별 처리 기간 상이" in result
    assert "서류 누락 주의" in result


def test_build_state_layer_step_status():
    """LAYER 2에 단계 상태가 포함된다."""
    builder = _make_builder()
    step = _make_mock_step(status="IN_PROGRESS")

    result = builder._build_state_layer(step, None, [])

    assert "단계 상태: IN_PROGRESS" in result


def test_build_state_layer_no_checklist():
    """체크리스트가 없으면 해당 섹션이 생략된다."""
    builder = _make_builder()
    step = _make_mock_step()
    legal = MagicMock()
    legal.action_type = "LEGAL_BASIS"

    result = builder._build_state_layer(step, None, [legal])

    assert "체크리스트 진행 현황" not in result


# ---------------------------------------------------------------------------
# LAYER 3: 안내 규칙 테스트
# ---------------------------------------------------------------------------


def test_build_instruction_layer_contains_rules():
    """LAYER 3에 AI 코치 행동 규칙 5가지가 포함된다."""
    builder = _make_builder()
    step = _make_mock_step()

    result = builder._build_instruction_layer(step)

    assert "<RULES>" in result
    assert "</RULES>" in result
    assert "팩트-지능 분리" in result
    assert "출처 강제 인용" in result
    assert "범위 제한" in result
    assert "전문가 권고" in result
    assert "불확실성 표현" in result


def test_build_instruction_layer_includes_step_title():
    """LAYER 3 범위 제한 규칙에 현재 단계 이름이 포함된다."""
    builder = _make_builder()
    step = _make_mock_step(title="영업 인허가 신청")

    result = builder._build_instruction_layer(step)

    assert "영업 인허가 신청" in result


def test_build_instruction_layer_no_recent_messages_section():
    """LAYER 3에 '최근 대화 맥락' 섹션이 없다 (LangChain 메시지 배열로 전달)."""
    builder = _make_builder()
    step = _make_mock_step()

    result = builder._build_instruction_layer(step)

    assert "최근 대화 맥락" not in result


# ---------------------------------------------------------------------------
# 통합: build() 메서드
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_returns_three_layers():
    """build()가 (<FACTS>+<STATUS>+<RULES> 프롬프트, actions) 튜플을 반환한다."""
    detail = _make_mock_step_detail()
    actions = _make_mock_actions()
    builder = _make_builder(step_details=[detail], step_actions=actions)
    roadmap = _make_mock_roadmap()
    step = _make_mock_step()

    prompt, returned_actions = await builder.build(roadmap, step)

    assert "<FACTS>" in prompt
    assert "</FACTS>" in prompt
    assert "<STATUS>" in prompt
    assert "</STATUS>" in prompt
    assert "<RULES>" in prompt
    assert "</RULES>" in prompt
    assert returned_actions == actions


@pytest.mark.asyncio
async def test_build_with_empty_details():
    """step_details가 빈 리스트일 때도 정상 동작한다."""
    builder = _make_builder(step_details=[], step_actions=[])
    roadmap = _make_mock_roadmap()
    step = _make_mock_step()

    prompt, returned_actions = await builder.build(roadmap, step)

    assert "<FACTS>" in prompt
    assert "<STATUS>" in prompt
    assert "<RULES>" in prompt
    assert returned_actions == []


# ---------------------------------------------------------------------------
# 토큰 예산 트리밍
# ---------------------------------------------------------------------------


def test_trim_to_budget_under_budget():
    """예산 내이면 원본 그대로 반환한다."""
    short_prompt = "짧은 프롬프트"
    result = RoadmapContextBuilder._trim_to_budget(short_prompt, max_tokens=1200)
    assert result == short_prompt


def test_trim_to_budget_over_budget_truncates():
    """예산 초과 시 길이가 줄어든다."""
    # 1200 토큰 = 4800 chars 기준
    long_prompt = (
        "<FACTS>\n## 사업 정보\n- 업종: 카페\n</FACTS>\n\n"
        "<STATUS>\n## 체크리스트 진행 현황\n"
    )
    # 체크리스트 라인 100개 추가 (예산 초과)
    for i in range(100):
        long_prompt += f"- [ ] 체크리스트 항목 {i}\n"
    long_prompt += "</STATUS>\n\n<RULES>\n안전 규칙\n</RULES>"

    result = RoadmapContextBuilder._trim_to_budget(long_prompt, max_tokens=300)

    # 원본보다 짧아야 함
    assert len(result) < len(long_prompt)


def test_trim_checklist_under_limit():
    """max_items 이하면 전체 반환."""
    lines = ["- [V] 항목 1", "- [ ] 항목 2", "- [V] 항목 3"]
    result = _trim_checklist(lines, max_items=10)
    assert result == lines


def test_trim_checklist_over_limit_prioritizes_incomplete():
    """max_items 초과 시 미완료 항목을 우선 유지한다."""
    lines = []
    for i in range(8):
        lines.append(f"- [ ] 미완료 {i}")
    for i in range(8):
        lines.append(f"- [V] 완료 {i}")

    result = _trim_checklist(lines, max_items=10)

    # 미완료 8개 + 완료 2개 = 10개
    incomplete_count = sum(1 for l in result if "[ ]" in l)
    assert incomplete_count == 8
    assert len([l for l in result if l.startswith("- [")]) == 10
    # 생략 메시지 포함
    assert any("생략" in l for l in result)


def test_trim_checklist_shows_omitted_count():
    """트리밍 시 생략된 항목 수가 표시된다."""
    lines = [f"- [ ] 항목 {i}" for i in range(15)]
    result = _trim_checklist(lines, max_items=5)

    omitted_line = [l for l in result if "생략" in l]
    assert len(omitted_line) == 1
    assert "10" in omitted_line[0]  # 15 - 5 = 10개 생략


# ---------------------------------------------------------------------------
# B-3: 안전장치 프롬프트 시나리오 20건
# ---------------------------------------------------------------------------


class TestSafetyGuardPrompts:
    """안전장치 프롬프트가 LAYER 3에 올바르게 포함되는지 검증 (20 시나리오)."""

    def setup_method(self):
        self.builder = _make_builder()
        self.step = _make_mock_step()

    def _get_layer3(self):
        return self.builder._build_instruction_layer(self.step)

    # -- 안전장치 1: 팩트-지능 분리 --

    def test_safety_01_fact_immutability_no_modify(self):
        """팩트 불변: '절대 수정' 금지 지시가 포함된다."""
        result = self._get_layer3()
        assert "절대 수정" in result

    def test_safety_02_fact_immutability_no_create(self):
        """팩트 불변: '새로 만들지' 금지 지시가 포함된다."""
        result = self._get_layer3()
        assert "새로 만들지" in result

    def test_safety_03_fact_immutability_no_arbitrary(self):
        """팩트 불변: <FACTS>에 없는 정보 임의 언급 금지."""
        result = self._get_layer3()
        assert "임의로 언급하지" in result

    def test_safety_04_actionkit_id_protection(self):
        """팩트 불변: ActionKit ID 보호 명시."""
        result = self._get_layer3()
        assert "ActionKit ID" in result

    # -- 안전장치 2: 출처 강제 인용 --

    def test_safety_05_citation_format_legal(self):
        """출처 인용: [법령 N] 형식 강제."""
        result = self._get_layer3()
        assert "[법령 N]" in result

    def test_safety_06_citation_format_document(self):
        """출처 인용: [서류 N] 형식 강제."""
        result = self._get_layer3()
        assert "[서류 N]" in result

    def test_safety_07_no_standalone_law_name(self):
        """출처 인용: 출처 번호 없이 법령명만 단독 언급 금지."""
        result = self._get_layer3()
        assert "단독으로 언급" in result

    # -- 안전장치 3: 범위 제한 --

    def test_safety_08_scope_includes_step_title(self):
        """범위 제한: 현재 단계 제목이 규칙에 포함된다."""
        result = self._get_layer3()
        assert self.step.title in result

    def test_safety_09_scope_out_of_range_message(self):
        """범위 제한: 범위 벗어남 안내 메시지가 포함된다."""
        result = self._get_layer3()
        assert "범위를 벗어납니다" in result

    # -- 안전장치 4: 전문가 권고 --

    def test_safety_10_expert_referral_tax(self):
        """전문가 권고: 세금 계산이 대상에 포함된다."""
        result = self._get_layer3()
        assert "세금 계산" in result

    def test_safety_11_expert_referral_lawsuit(self):
        """전문가 권고: 소송 전략이 대상에 포함된다."""
        result = self._get_layer3()
        assert "소송 전략" in result

    def test_safety_12_expert_referral_medical(self):
        """전문가 권고: 의료가 대상에 포함된다."""
        result = self._get_layer3()
        assert "의료" in result

    def test_safety_13_expert_referral_investment(self):
        """전문가 권고: 투자가 대상에 포함된다."""
        result = self._get_layer3()
        assert "투자" in result

    def test_safety_14_expert_referral_realestate(self):
        """전문가 권고: 부동산 가격 평가가 대상에 포함된다."""
        result = self._get_layer3()
        assert "부동산 가격 평가" in result

    # -- 안전장치 5: 불확실성 표현 --

    def test_safety_15_uncertainty_marker(self):
        """불확실성: '확인이 필요합니다' 표현 지시."""
        result = self._get_layer3()
        assert "확인이 필요합니다" in result

    def test_safety_16_no_speculation(self):
        """불확실성: 추측성 답변 방지 지시."""
        result = self._get_layer3()
        assert "추측성 답변" in result

    # -- Few-shot / 네거티브 예시 --

    def test_safety_17_few_shot_citation_example(self):
        """few-shot: 올바른 출처 인용 예시가 포함된다."""
        result = self._get_layer3()
        assert "올바른 답변 예시" in result
        assert "[법령 1]" in result

    def test_safety_18_negative_hallucinated_law(self):
        """네거티브: <FACTS>에 없는 법령명 사용 금지 예시."""
        result = self._get_layer3()
        assert "하지 말아야 할" in result
        assert "<FACTS>에 없는" in result

    def test_safety_19_negative_tax_calculation(self):
        """네거티브: 구체적 세금 계산 금지 예시."""
        result = self._get_layer3()
        assert "세무사 상담" in result

    def test_safety_20_negative_arbitrary_statute(self):
        """네거티브: 임의 법령 조항 생성 금지 예시."""
        result = self._get_layer3()
        assert "팩트에 있는 정보만" in result

    # -- 안전장치 6: 빈 데이터 처리 (D-1 추가) --

    def test_safety_21_empty_data_legal_guide(self):
        """빈 데이터: 법령 없을 때 안내 문구 지시가 포함된다."""
        result = self._get_layer3()
        assert "이 단계에는 등록된 법령이 없습니다" in result

    def test_safety_22_empty_data_document_guide(self):
        """빈 데이터: 서류 없을 때 안내 문구 지시가 포함된다."""
        result = self._get_layer3()
        assert "이 단계에는 등록된 서류가 없습니다" in result

    # -- 답변 스타일 가이드 (D-1 추가) --

    def test_safety_23_honorific_style_guide(self):
        """답변 스타일: 존댓말 패턴 가이드가 포함된다."""
        result = self._get_layer3()
        assert "존댓말" in result
        assert "답변 스타일" in result

    def test_safety_24_concise_answer_guide(self):
        """답변 스타일: 간결한 답변 길이 가이드가 포함된다."""
        result = self._get_layer3()
        assert "3~5문장" in result

    def test_safety_25_terminology_guide(self):
        """답변 스타일: 전문 용어 병기 가이드가 포함된다."""
        result = self._get_layer3()
        assert "쉬운 설명을 병기" in result

    # -- few-shot 추가 예시 (D-1 추가) --

    def test_safety_26_few_shot_expert_referral_example(self):
        """few-shot: 전문가 권고 답변 예시가 포함된다."""
        result = self._get_layer3()
        assert "전문가 상담을 권장합니다" in result

    def test_safety_27_few_shot_uncertainty_example(self):
        """few-shot: 불확실성 표현 답변 예시가 포함된다."""
        result = self._get_layer3()
        assert "확인이 필요합니다" in result
        assert "국가법령정보센터" in result

    # -- 프롬프트 인젝션 방어 네거티브 (D-1 추가) --

    def test_safety_28_negative_prompt_injection_defense(self):
        """네거티브: 사용자 지시로 규칙 변경 불가 예시가 포함된다."""
        result = self._get_layer3()
        assert "이전 지시 무시" in result
        assert "규칙을 변경할 수 없습니다" in result


# ---------------------------------------------------------------------------
# D-1: 다양한 업종 시나리오 (ContextBuilder 출력 품질)
# ---------------------------------------------------------------------------


class TestContextBuilderBusinessScenarios:
    """다양한 업종별 ContextBuilder 출력 검증 (D-1 추가)."""

    def setup_method(self):
        self.builder = _make_builder()

    def test_scenario_restaurant_business(self):
        """음식점 업종: 사업 정보가 올바르게 포함된다."""
        roadmap = _make_mock_roadmap(
            business_type="음식점",
            location="서울특별시 마포구",
            startup_type="법인사업자",
            startup_method="양도양수",
            budget_range="1억원~2억원",
        )
        detail = _make_mock_step_detail(
            phase="위생교육",
            objective="식품위생교육 수료",
            estimated_days=7,
        )
        result = self.builder._build_fact_layer(roadmap, detail, [])

        assert "음식점" in result
        assert "마포구" in result
        assert "법인사업자" in result
        assert "양도양수" in result
        assert "위생교육" in result

    def test_scenario_retail_business(self):
        """소매업 업종: 사업 정보가 올바르게 포함된다."""
        roadmap = _make_mock_roadmap(
            business_type="소매업",
            location="경기도 수원시",
            startup_type="개인사업자",
            startup_method="신규",
            budget_range="3000만원~5000만원",
        )
        result = self.builder._build_fact_layer(roadmap, None, [])

        assert "소매업" in result
        assert "수원시" in result

    def test_scenario_beauty_salon(self):
        """미용실 업종: 다중 법령 + 다중 서류 정상 출력."""
        roadmap = _make_mock_roadmap(
            business_type="미용실",
            location="부산광역시 해운대구",
        )

        legal1 = MagicMock()
        legal1.action_type = "LEGAL_BASIS"
        legal1.title = "공중위생관리법"
        legal1.description = "미용업 신고 근거"
        legal1.source_url = None
        legal1.metadata_json = {"actionkit_item_id": 10}

        legal2 = MagicMock()
        legal2.action_type = "LEGAL_BASIS"
        legal2.title = "소방시설법"
        legal2.description = "소방 안전 기준"
        legal2.source_url = None
        legal2.metadata_json = {"actionkit_item_id": 11}

        doc1 = MagicMock()
        doc1.action_type = "DOCUMENT"
        doc1.title = "미용업 신고서"
        doc1.description = "미용업 신고 서류"
        doc1.source_url = "/api/v1/actionkits/items/20"

        result = self.builder._build_fact_layer(
            roadmap, None, [legal1, legal2, doc1]
        )

        assert "[법령 1] 공중위생관리법" in result
        assert "[법령 2] 소방시설법" in result
        assert "[서류 1] 미용업 신고서" in result

    def test_scenario_tech_startup(self):
        """IT 스타트업 업종: 선택 필드 일부만 있는 경우."""
        roadmap = _make_mock_roadmap(
            business_type="소프트웨어 개발",
            location="서울특별시 강남구",
            startup_type="법인사업자",
            startup_method=None,
            open_timeline=None,
            budget_range=None,
        )
        result = self.builder._build_fact_layer(roadmap, None, [])

        assert "소프트웨어 개발" in result
        assert "법인사업자" in result
        assert "창업 방식" not in result
        assert "오픈 예정" not in result
        assert "예산" not in result

    def test_scenario_all_checklist_completed(self):
        """전체 체크리스트 완료 상태: 완료 카운트가 정확하다."""
        step = _make_mock_step(status="COMPLETED")
        checklist_items = []
        for i in range(5):
            item = MagicMock()
            item.action_type = "CHECKLIST"
            item.title = f"항목 {i+1}"
            item.metadata_json = {"completed": True}
            checklist_items.append(item)

        result = self.builder._build_state_layer(step, None, checklist_items)

        assert "완료: 5/5" in result
        assert "단계 상태: COMPLETED" in result

    def test_scenario_no_actions_at_all(self):
        """법령/서류/체크리스트가 모두 없는 단계."""
        roadmap = _make_mock_roadmap(business_type="기타")
        step = _make_mock_step()

        fact_layer = self.builder._build_fact_layer(roadmap, None, [])
        state_layer = self.builder._build_state_layer(step, None, [])

        assert "관련 법령" not in fact_layer
        assert "필수 서류" not in fact_layer
        assert "체크리스트 진행 현황" not in state_layer


# ---------------------------------------------------------------------------
# D-1: 토큰 예산 트리밍 확장 테스트
# ---------------------------------------------------------------------------


class TestTokenBudgetTrimming:
    """토큰 예산 트리밍 확장 검증 (D-1 추가)."""

    def test_large_checklist_50_items_trimmed(self):
        """체크리스트 50개 단계: 트리밍 후 예산 내 프롬프트 생성."""
        prompt = "<FACTS>\n## 사업 정보\n- 업종: 카페\n</FACTS>\n\n"
        prompt += "<STATUS>\n## 체크리스트 진행 현황\n완료: 5/50\n"
        for i in range(50):
            mark = "V" if i < 5 else " "
            prompt += f"- [{mark}] 체크리스트 항목 {i+1}\n"
        prompt += "</STATUS>\n\n<RULES>\n규칙\n</RULES>"

        result = RoadmapContextBuilder._trim_to_budget(prompt, max_tokens=400)

        assert len(result) <= 400 * 4  # max_tokens * CHARS_PER_TOKEN

    def test_massive_data_10_legal_10_doc_30_checklist(self):
        """법령 10개 + 서류 10개 + 체크리스트 30개: 예산 내 트리밍."""
        prompt = "<FACTS>\n## 사업 정보\n- 업종: 카페\n"
        prompt += "\n## 관련 법령 (절대 수정 금지)\n"
        for i in range(10):
            prompt += f"[법령 {i+1}] 테스트법령{i+1}\n  - 설명: 테스트\n"
        prompt += "\n## 필수 서류 (절대 수정 금지)\n"
        for i in range(10):
            prompt += f"[서류 {i+1}] 테스트서류{i+1}\n  - 설명: 테스트\n"
        prompt += "</FACTS>\n\n<STATUS>\n## 체크리스트 진행 현황\n완료: 3/30\n"
        for i in range(30):
            mark = "V" if i < 3 else " "
            prompt += f"- [{mark}] 체크리스트 항목 {i+1}\n"
        prompt += "</STATUS>\n\n<RULES>\n규칙\n</RULES>"

        result = RoadmapContextBuilder._trim_to_budget(prompt, max_tokens=500)

        assert len(result) <= 500 * 4

    def test_trim_preserves_facts_and_rules(self):
        """트리밍 후에도 <FACTS>와 <RULES> 태그는 유지된다."""
        prompt = "<FACTS>\n## 사업 정보\n- 업종: 카페\n</FACTS>\n\n"
        prompt += "<STATUS>\n## 체크리스트 진행 현황\n"
        for i in range(100):
            prompt += f"- [ ] 항목 {i}\n"
        prompt += "</STATUS>\n\n<RULES>\n규칙\n</RULES>"

        result = RoadmapContextBuilder._trim_to_budget(prompt, max_tokens=200)

        assert "<FACTS>" in result

    def test_trim_checklist_all_completed(self):
        """전부 완료된 체크리스트: 트리밍 시 완료 항목도 포함."""
        lines = [f"- [V] 완료 항목 {i}" for i in range(20)]
        result = _trim_checklist(lines, max_items=5)

        completed_count = sum(1 for l in result if "[V]" in l)
        assert completed_count == 5
        assert any("생략" in l for l in result)

    def test_trim_checklist_all_incomplete(self):
        """전부 미완료 체크리스트: 미완료 항목만 남음."""
        lines = [f"- [ ] 미완료 항목 {i}" for i in range(20)]
        result = _trim_checklist(lines, max_items=5)

        incomplete_count = sum(1 for l in result if "[ ]" in l)
        assert incomplete_count == 5
        assert any("15" in l for l in result if "생략" in l)  # 20 - 5 = 15
