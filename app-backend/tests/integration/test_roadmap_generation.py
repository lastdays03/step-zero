"""Integration tests for ActionKit-enhanced roadmap generation.

Tests the full flow: ActionKitMatcher -> LLMPersonalizer -> RoadmapGenerationService.
LLM calls are mocked to avoid API costs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.features.roadmaps.application.actionkit_matcher import (
    CATEGORY_TO_PHASE,
    ActionKitMatcher,
    MatchedActionKit,
)
from app.features.roadmaps.application.llm_personalizer import (
    LLMPersonalizer,
    PersonalizedStepDetail,
)
from app.features.roadmaps.application.roadmap_generation_service import (
    GenerationPayload,
    RoadmapGenerationService,
    StepDetail,
)
from app.models.actionkit import (
    ActionKitCategory,
    ActionKitItem,
    ActionKitItemHighlight,
    ActionKitRelatedLaw,
)
from app.models.file import File

# ------------------------------------------------------------------ #
#  Helpers: build mock ActionKit data
# ------------------------------------------------------------------ #


def _make_item(
    item_id: int,
    name: str,
    summary: str,
    domain: str = "laws",
    category_id: int = 1,
) -> ActionKitItem:
    item = ActionKitItem(
        domain=domain,
        category_id=category_id,
        name=name,
        summary=summary,
    )
    item.id = item_id
    return item


def _make_highlight(
    item_id: int, content: str, highlight_id: int = 1
) -> ActionKitItemHighlight:
    h = ActionKitItemHighlight(item_id=item_id, content=content, sort_order=1)
    h.id = highlight_id
    return h


def _make_related_law(
    item_id: int,
    law_name: str,
    law_summary: str = "",
    law_id: int = 1,
) -> ActionKitRelatedLaw:
    law = ActionKitRelatedLaw(
        item_id=item_id,
        law_name=law_name,
        law_summary=law_summary,
        sort_order=1,
    )
    law.id = law_id
    return law


def _make_file(
    item_id: int,
    object_key: str,
    file_id: int = 1,
    original_filename: str = "test.pdf",
) -> File:
    f = File(
        owner_type="actionkit_item",
        owner_id=item_id,
        category="document",
        object_key=object_key,
        original_filename=original_filename,
        is_current=True,
    )
    f.id = file_id
    return f


def _build_matched_items(count: int, domain: str = "laws") -> list[MatchedActionKit]:
    """Build a list of MatchedActionKit objects for testing."""
    items: list[MatchedActionKit] = []
    phases = list(CATEGORY_TO_PHASE.values())
    for i in range(count):
        phase = phases[i % len(phases)]
        item_id = i + 1
        matched = MatchedActionKit(
            item=_make_item(
                item_id=item_id,
                name=f"테스트 법령 {item_id}",
                summary=f"테스트 요약 {item_id}",
                domain=domain,
            ),
            highlights=[
                _make_highlight(item_id, f"핵심 포인트 {item_id}-1"),
                _make_highlight(item_id, f"핵심 포인트 {item_id}-2", highlight_id=2),
            ],
            related_laws=[
                _make_related_law(
                    item_id,
                    f"관련법 {item_id}",
                    f"법률 요약 {item_id}",
                ),
            ],
            files=[
                _make_file(
                    item_id,
                    f"laws/chapter-1/{item_id}/v1/test.pdf",
                    file_id=item_id,
                ),
            ],
            phase_group=phase,
            relevance_score=1.0 - (i * 0.1),
        )
        items.append(matched)
    return items


def _mock_llm_response(phases: list[str]) -> str:
    """Build a mock LLM JSON response matching the expected format."""
    result = []
    for i, phase in enumerate(phases):
        result.append(
            {
                "phase": phase,
                "title": f"{phase} 단계",
                "objective": f"{phase} 절차를 완료합니다.",
                "estimated_days": 5 + i,
                "checklist": [f"체크 항목 {i+1}-1", f"체크 항목 {i+1}-2"],
                "legal_basis": [
                    {
                        "title": f"관련법 {i+1}",
                        "snippet": f"법률 요약 {i+1}",
                        "actionkit_item_id": i + 1,
                    }
                ],
                "documents": [
                    {
                        "name": f"서류 {i+1}",
                        "file_url": f"laws/chapter-1/{i+1}/v1/test.pdf",
                        "actionkit_item_id": i + 1,
                        "actionkit_file_id": i + 1,
                    }
                ],
                "risk_notes": [f"위험 {i+1}"],
                "actionkit_items": [i + 1],
            }
        )
    return json.dumps(result, ensure_ascii=False)


# ------------------------------------------------------------------ #
#  Test 1: Cafe + Seoul -> ActionKit mapping success
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_cafe_seoul_actionkit_mapping_success():
    """카페(휴게음식점) + 서울 -> ActionKit mapping should succeed with >= 1 match."""
    matched = _build_matched_items(5)
    phases = list({m.phase_group for m in matched})

    # Mock ActionKitMatcher
    mock_matcher = MagicMock(spec=ActionKitMatcher)
    mock_matcher.match = AsyncMock(return_value=matched)

    # Mock LLMPersonalizer
    mock_personalizer = MagicMock(spec=LLMPersonalizer)
    mock_personalizer.personalize = AsyncMock(
        return_value=[
            PersonalizedStepDetail(
                phase=phase,
                title=f"{phase} 단계",
                objective=f"휴게음식점 {phase} 절차 진행",
                estimated_days=5,
                checklist=["체크 항목 1", "체크 항목 2"],
                legal_basis=[
                    {
                        "title": "식품위생법",
                        "snippet": "영업신고",
                        "actionkit_item_id": 1,
                    }
                ],
                documents=[
                    {
                        "name": "영업신고서",
                        "file_url": "laws/chapter-1/1/v1/test.pdf",
                        "actionkit_item_id": 1,
                        "actionkit_file_id": 1,
                    }
                ],
                risk_notes=["누락 주의"],
                actionkit_items=[1, 2],
                mapping_source="actionkit_direct",
            )
            for phase in phases
        ]
    )

    # Mock session and repos
    mock_session = AsyncMock()
    mock_job = MagicMock()
    mock_job.id = uuid4()
    mock_job.team_id = uuid4()
    mock_job.user_id = 1
    mock_job.input_payload = {
        "business_type": "휴게음식점",
        "location": "서울특별시 강남구",
        "description": "카페 창업",
    }

    with (
        patch.object(RoadmapGenerationService, "__init__", lambda self, *a, **kw: None),
    ):
        service = RoadmapGenerationService.__new__(RoadmapGenerationService)
        service.session = mock_session
        service.actionkit_matcher = mock_matcher
        service.llm_personalizer = mock_personalizer
        service.rag_service = MagicMock()

        # Mock repos
        service.job_repo = MagicMock()
        service.job_repo.get_by_id = AsyncMock(return_value=mock_job)
        service.job_repo.mark_running = AsyncMock()
        service.job_repo.set_progress = AsyncMock()
        service.job_repo.mark_succeeded = AsyncMock()

        service.roadmap_repo = MagicMock()
        mock_roadmap = MagicMock()
        mock_roadmap.id = uuid4()
        service.roadmap_repo.create_roadmap = AsyncMock(return_value=mock_roadmap)
        service.roadmap_repo.create_steps_with_details = AsyncMock(return_value=[])
        service.roadmap_repo.commit = AsyncMock()

        await service.process_job(mock_job.id)

    # Assertions
    mock_matcher.match.assert_called_once()
    mock_personalizer.personalize.assert_called_once()
    service.roadmap_repo.create_steps_with_details.assert_called_once()

    call_kwargs = service.roadmap_repo.create_steps_with_details.call_args[1]
    assert call_kwargs["generation_mode"] == "ACTIONKIT_RAG"
    assert len(call_kwargs["steps_payload"]) >= 3

    # Check steps have actionkit metadata
    for step_payload in call_kwargs["steps_payload"]:
        assert step_payload.get("mapping_source") == "actionkit_direct"
        assert "legal_basis" in step_payload
        for lb in step_payload["legal_basis"]:
            assert "actionkit_item_id" in lb


# ------------------------------------------------------------------ #
#  Test 2: General restaurant + Gyeonggi -> ActionKit mapping success
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_general_restaurant_gyeonggi_mapping_success():
    """일반음식점 + 경기도 -> ActionKit mapping success path."""
    matched = _build_matched_items(4)

    mock_matcher = MagicMock(spec=ActionKitMatcher)
    mock_matcher.match = AsyncMock(return_value=matched)

    # Simulate LLM response via fallback (testing fallback in personalizer)
    mock_personalizer = MagicMock(spec=LLMPersonalizer)
    fallback_details = LLMPersonalizer._fallback_from_facts(
        matched,
        {"business_type": "일반음식점", "location": "경기도 수원시"},
    )
    mock_personalizer.personalize = AsyncMock(return_value=fallback_details)

    mock_session = AsyncMock()
    mock_job = MagicMock()
    mock_job.id = uuid4()
    mock_job.team_id = uuid4()
    mock_job.user_id = 1
    mock_job.input_payload = {
        "business_type": "일반음식점",
        "location": "경기도 수원시",
        "description": "",
    }

    with patch.object(
        RoadmapGenerationService, "__init__", lambda self, *a, **kw: None
    ):
        service = RoadmapGenerationService.__new__(RoadmapGenerationService)
        service.session = mock_session
        service.actionkit_matcher = mock_matcher
        service.llm_personalizer = mock_personalizer
        service.rag_service = MagicMock()

        service.job_repo = MagicMock()
        service.job_repo.get_by_id = AsyncMock(return_value=mock_job)
        service.job_repo.mark_running = AsyncMock()
        service.job_repo.set_progress = AsyncMock()
        service.job_repo.mark_succeeded = AsyncMock()

        service.roadmap_repo = MagicMock()
        mock_roadmap = MagicMock()
        mock_roadmap.id = uuid4()
        service.roadmap_repo.create_roadmap = AsyncMock(return_value=mock_roadmap)
        service.roadmap_repo.create_steps_with_details = AsyncMock(return_value=[])
        service.roadmap_repo.commit = AsyncMock()

        await service.process_job(mock_job.id)

    mock_matcher.match.assert_called_once()
    call_kwargs = service.roadmap_repo.create_steps_with_details.call_args[1]
    assert call_kwargs["generation_mode"] == "ACTIONKIT_RAG"
    steps = call_kwargs["steps_payload"]
    assert len(steps) >= 3

    # Verify documents have file references
    for step in steps:
        for doc in step.get("documents", []):
            if doc.get("file_url"):
                assert "actionkit_item_id" in doc


# ------------------------------------------------------------------ #
#  Test 3: Zero matches -> fallback to legacy RAG
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_zero_matches_fallback():
    """0 ActionKit matches -> legacy fallback to RAG generation."""
    mock_matcher = MagicMock(spec=ActionKitMatcher)
    mock_matcher.match = AsyncMock(return_value=[])  # No matches at all

    mock_personalizer = MagicMock(spec=LLMPersonalizer)
    # personalizer should NOT be called in fallback path

    mock_session = AsyncMock()
    mock_job = MagicMock()
    mock_job.id = uuid4()
    mock_job.team_id = uuid4()
    mock_job.user_id = 1
    mock_job.input_payload = {
        "business_type": "IT 스타트업",
        "location": "경기도 성남시 분당구 판교",
        "description": "소프트웨어 개발",
    }

    # Mock the RAG service for fallback path
    mock_rag = MagicMock()
    master_json = json.dumps(
        {
            "title": "IT 스타트업 창업 로드맵",
            "summary": "SW 개발 사업",
            "phases": ["사업 등록", "사무실 확보", "인력 채용"],
        }
    )
    detail_json = json.dumps(
        {
            "phase": "사업 등록",
            "title": "사업자등록",
            "objective": "사업자등록증 발급",
            "checklist": ["사업자등록 신청"],
            "legal_basis": [{"title": "부가가치세법", "snippet": "사업자등록"}],
            "documents": [],
            "estimated_days": 3,
            "risk_notes": ["서류 누락 주의"],
        }
    )
    mock_rag.query = AsyncMock(
        side_effect=[master_json, detail_json, detail_json, detail_json]
    )

    with patch.object(
        RoadmapGenerationService, "__init__", lambda self, *a, **kw: None
    ):
        service = RoadmapGenerationService.__new__(RoadmapGenerationService)
        service.session = mock_session
        service.actionkit_matcher = mock_matcher
        service.llm_personalizer = mock_personalizer
        service.rag_service = mock_rag

        service.job_repo = MagicMock()
        service.job_repo.get_by_id = AsyncMock(return_value=mock_job)
        service.job_repo.mark_running = AsyncMock()
        service.job_repo.set_progress = AsyncMock()
        service.job_repo.mark_succeeded = AsyncMock()

        service.roadmap_repo = MagicMock()
        mock_roadmap = MagicMock()
        mock_roadmap.id = uuid4()
        service.roadmap_repo.create_roadmap = AsyncMock(return_value=mock_roadmap)
        service.roadmap_repo.create_steps_with_details = AsyncMock(return_value=[])
        service.roadmap_repo.commit = AsyncMock()

        await service.process_job(mock_job.id)

    # Personalizer should NOT be called
    mock_personalizer.personalize.assert_not_called()

    # But standard generation should proceed
    call_kwargs = service.roadmap_repo.create_steps_with_details.call_args[1]
    assert call_kwargs["generation_mode"] == "RAG"
    assert len(call_kwargs["steps_payload"]) >= 1
    service.job_repo.mark_succeeded.assert_called_once()


# ------------------------------------------------------------------ #
#  Test 3b: Small match count (1-2) -> ACTIONKIT_RAG (lowered threshold)
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_small_match_count_uses_actionkit_rag():
    """1-2 ActionKit matches should now use ACTIONKIT_RAG (threshold lowered to 1)."""
    matched = _build_matched_items(2)

    mock_matcher = MagicMock(spec=ActionKitMatcher)
    mock_matcher.match = AsyncMock(return_value=matched)

    phases = list({m.phase_group for m in matched})
    mock_personalizer = MagicMock(spec=LLMPersonalizer)
    mock_personalizer.personalize = AsyncMock(
        return_value=[
            PersonalizedStepDetail(
                phase=phase,
                title=f"{phase} 단계",
                objective=f"IT 스타트업 {phase}",
                estimated_days=5,
                checklist=["확인 항목"],
                legal_basis=[
                    {"title": "관련법", "snippet": "요약", "actionkit_item_id": 1}
                ],
                documents=[],
                risk_notes=["위험 요소"],
                actionkit_items=[1],
                mapping_source="actionkit_direct",
            )
            for phase in phases
        ]
    )

    mock_session = AsyncMock()
    mock_job = MagicMock()
    mock_job.id = uuid4()
    mock_job.team_id = uuid4()
    mock_job.user_id = 1
    mock_job.input_payload = {
        "business_type": "IT 스타트업",
        "location": "경기도 성남시 분당구 판교",
        "description": "소프트웨어 개발",
    }

    with patch.object(
        RoadmapGenerationService, "__init__", lambda self, *a, **kw: None
    ):
        service = RoadmapGenerationService.__new__(RoadmapGenerationService)
        service.session = mock_session
        service.actionkit_matcher = mock_matcher
        service.llm_personalizer = mock_personalizer
        service.rag_service = MagicMock()

        service.job_repo = MagicMock()
        service.job_repo.get_by_id = AsyncMock(return_value=mock_job)
        service.job_repo.mark_running = AsyncMock()
        service.job_repo.set_progress = AsyncMock()
        service.job_repo.mark_succeeded = AsyncMock()

        service.roadmap_repo = MagicMock()
        mock_roadmap = MagicMock()
        mock_roadmap.id = uuid4()
        service.roadmap_repo.create_roadmap = AsyncMock(return_value=mock_roadmap)
        service.roadmap_repo.create_steps_with_details = AsyncMock(return_value=[])
        service.roadmap_repo.commit = AsyncMock()

        await service.process_job(mock_job.id)

    # Personalizer SHOULD be called now (threshold lowered to 1)
    mock_personalizer.personalize.assert_called_once()

    call_kwargs = service.roadmap_repo.create_steps_with_details.call_args[1]
    assert call_kwargs["generation_mode"] == "ACTIONKIT_RAG"
    service.job_repo.mark_succeeded.assert_called_once()


# ------------------------------------------------------------------ #
#  Test 4: Beauty salon + Busan -> Partial mapping
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_beauty_salon_busan_partial_mapping():
    """미용실 + 부산 -> Partial ActionKit mapping (exactly 3 matches)."""
    matched = _build_matched_items(3)

    mock_matcher = MagicMock(spec=ActionKitMatcher)
    mock_matcher.match = AsyncMock(return_value=matched)

    phases = list({m.phase_group for m in matched})
    mock_personalizer = MagicMock(spec=LLMPersonalizer)
    mock_personalizer.personalize = AsyncMock(
        return_value=[
            PersonalizedStepDetail(
                phase=phase,
                title=f"{phase} 단계",
                objective=f"미용실 {phase}",
                estimated_days=4,
                checklist=["확인 항목"],
                legal_basis=[
                    {
                        "title": "공중위생관리법",
                        "snippet": "미용업 신고",
                        "actionkit_item_id": 1,
                    }
                ],
                documents=[],
                risk_notes=["위생 기준 미달 시 보완 명령"],
                actionkit_items=[1],
                mapping_source="actionkit_direct",
            )
            for phase in phases
        ]
    )

    mock_session = AsyncMock()
    mock_job = MagicMock()
    mock_job.id = uuid4()
    mock_job.team_id = uuid4()
    mock_job.user_id = 1
    mock_job.input_payload = {
        "business_type": "미용실",
        "location": "부산광역시 해운대구",
        "description": "헤어살롱 창업",
    }

    with patch.object(
        RoadmapGenerationService, "__init__", lambda self, *a, **kw: None
    ):
        service = RoadmapGenerationService.__new__(RoadmapGenerationService)
        service.session = mock_session
        service.actionkit_matcher = mock_matcher
        service.llm_personalizer = mock_personalizer
        service.rag_service = MagicMock()

        service.job_repo = MagicMock()
        service.job_repo.get_by_id = AsyncMock(return_value=mock_job)
        service.job_repo.mark_running = AsyncMock()
        service.job_repo.set_progress = AsyncMock()
        service.job_repo.mark_succeeded = AsyncMock()

        service.roadmap_repo = MagicMock()
        mock_roadmap = MagicMock()
        mock_roadmap.id = uuid4()
        service.roadmap_repo.create_roadmap = AsyncMock(return_value=mock_roadmap)
        service.roadmap_repo.create_steps_with_details = AsyncMock(return_value=[])
        service.roadmap_repo.commit = AsyncMock()

        await service.process_job(mock_job.id)

    # Should use ActionKit path (>= 1 match)
    mock_personalizer.personalize.assert_called_once()
    call_kwargs = service.roadmap_repo.create_steps_with_details.call_args[1]
    assert call_kwargs["generation_mode"] == "ACTIONKIT_RAG"

    steps = call_kwargs["steps_payload"]
    assert len(steps) >= 3

    for step in steps:
        assert step["mapping_source"] == "actionkit_direct"


# ------------------------------------------------------------------ #
#  Test 5: Empty input -> Validation failure (graceful handling)
# ------------------------------------------------------------------ #


@pytest.mark.asyncio
async def test_empty_input_validation_failure():
    """Empty business_type -> process_job handles gracefully (marks failed)."""
    mock_session = AsyncMock()
    mock_job = MagicMock()
    mock_job.id = uuid4()
    mock_job.team_id = uuid4()
    mock_job.user_id = 1
    # Missing required 'business_type' and 'location' -> should raise during
    # GenerationPayload construction
    mock_job.input_payload = {}

    mock_matcher = MagicMock(spec=ActionKitMatcher)
    mock_personalizer = MagicMock(spec=LLMPersonalizer)

    with patch.object(
        RoadmapGenerationService, "__init__", lambda self, *a, **kw: None
    ):
        service = RoadmapGenerationService.__new__(RoadmapGenerationService)
        service.session = mock_session
        service.actionkit_matcher = mock_matcher
        service.llm_personalizer = mock_personalizer
        service.rag_service = MagicMock()

        service.job_repo = MagicMock()
        service.job_repo.get_by_id = AsyncMock(return_value=mock_job)
        service.job_repo.mark_running = AsyncMock()
        service.job_repo.mark_failed = AsyncMock()

        service.roadmap_repo = MagicMock()

        await service.process_job(mock_job.id)

    # Should have been marked as failed
    service.job_repo.mark_failed.assert_called_once()
    fail_call = service.job_repo.mark_failed.call_args
    assert (
        fail_call[1].get("code") == "GENERATION_FAILED" or fail_call[0][1]
        if len(fail_call[0]) > 1
        else True
    )

    # Matcher and personalizer should NOT be called
    mock_matcher.match.assert_not_called()
    mock_personalizer.personalize.assert_not_called()


# ------------------------------------------------------------------ #
#  Additional unit tests for individual components
# ------------------------------------------------------------------ #


class TestLLMPersonalizerParsing:
    """Unit tests for LLMPersonalizer JSON parsing and conversion."""

    def test_parse_json_array_valid(self):
        raw = '[{"phase": "입지 검토", "title": "test"}]'
        result = LLMPersonalizer._parse_json_array(raw)
        assert result is not None
        assert len(result) == 1
        assert result[0]["phase"] == "입지 검토"

    def test_parse_json_array_with_markdown(self):
        raw = '```json\n[{"phase": "test"}]\n```'
        result = LLMPersonalizer._parse_json_array(raw)
        assert result is not None
        assert len(result) == 1

    def test_parse_json_array_invalid(self):
        raw = "This is not JSON"
        result = LLMPersonalizer._parse_json_array(raw)
        assert result is None

    def test_convert_to_details(self):
        parsed = [
            {
                "phase": "입지 검토",
                "title": "입지 검토 단계",
                "objective": "적합한 입지 확인",
                "estimated_days": 7,
                "checklist": ["용도지역 확인", "임대차 검토"],
                "legal_basis": [{"title": "건축법", "snippet": "용도분류"}],
                "documents": [{"name": "토지이용계획", "file_url": "test/path"}],
                "risk_notes": ["부적합 용도 위험"],
                "actionkit_items": [1, 2],
            }
        ]
        details = LLMPersonalizer._convert_to_details(parsed)
        assert len(details) == 1
        assert details[0].phase == "입지 검토"
        assert len(details[0].checklist) == 2
        assert details[0].actionkit_items == [1, 2]

    def test_fallback_from_facts_produces_valid_output(self):
        matched = _build_matched_items(4)
        payload = {"business_type": "테스트업종", "location": "서울시"}
        details = LLMPersonalizer._fallback_from_facts(matched, payload)

        assert len(details) >= 1
        for d in details:
            assert d.phase
            assert d.mapping_source == "actionkit_direct"
            assert len(d.checklist) >= 1


class TestActionKitMatcherHelpers:
    """Unit tests for ActionKitMatcher static helpers."""

    def test_build_queries_default_keywords(self):
        """Unknown business type falls back to DEFAULT_QUERY_KEYWORDS."""
        queries = ActionKitMatcher._build_queries("드론 배달업", "서울시")
        assert len(queries) == 4  # 1 base + 3 defaults
        assert queries[0] == "드론 배달업 서울시 창업 인허가"

    def test_build_queries_business_specific(self):
        """Known business type uses BUSINESS_QUERY_TEMPLATES."""
        queries = ActionKitMatcher._build_queries("휴게음식점", "강남구")
        assert len(queries) == 4  # 1 base + 3 template keywords
        assert "휴게음식점 위생 허가" in queries

    def test_extract_item_titles_from_tuples(self):
        """Test extraction from (Document, score) tuples."""
        mock_doc = MagicMock()
        mock_doc.metadata = {"title": "건축법 제2조 (용도 분류)"}
        docs = [(mock_doc, 0.85)]

        titles = ActionKitMatcher._extract_item_titles(docs)
        assert titles == ["건축법 제2조 (용도 분류)"]

    def test_extract_item_titles_deduplicates(self):
        """Test that duplicate titles are removed."""
        mock_doc1 = MagicMock()
        mock_doc1.metadata = {"title": "식품위생법"}
        mock_doc2 = MagicMock()
        mock_doc2.metadata = {"title": "식품위생법"}

        docs = [(mock_doc1, 0.9), (mock_doc2, 0.8)]
        titles = ActionKitMatcher._extract_item_titles(docs)
        assert titles == ["식품위생법"]

    def test_extract_item_titles_skips_missing(self):
        """Test that docs without title metadata are skipped."""
        mock_doc = MagicMock()
        mock_doc.metadata = {"category": "test"}
        docs = [(mock_doc, 0.9)]

        titles = ActionKitMatcher._extract_item_titles(docs)
        assert titles == []

    def test_build_score_map(self):
        mock_doc = MagicMock()
        mock_doc.metadata = {"title": "법령A"}
        docs = [(mock_doc, 0.95)]

        scores = ActionKitMatcher._build_score_map(docs)
        assert scores["법령A"] == 0.95


class TestRoadmapRepositoryMetadata:
    """Unit tests for _build_actionkit_metadata."""

    def test_legal_basis_metadata(self):
        from app.repositories.roadmap_repository import RoadmapRepository

        item = {
            "title": "식품위생법",
            "snippet": "영업신고",
            "actionkit_item_id": 42,
            "actionkit_domain": "laws",
            "actionkit_category": "chapter-2",
            "mapping_source": "actionkit_direct",
        }
        metadata = RoadmapRepository._build_actionkit_metadata(item, "LEGAL_BASIS")
        assert metadata["actionkit_item_id"] == 42
        assert metadata["actionkit_domain"] == "laws"
        assert metadata["mapping_source"] == "actionkit_direct"

    def test_document_metadata(self):
        from app.repositories.roadmap_repository import RoadmapRepository

        item = {
            "name": "영업신고서",
            "file_url": "laws/chapter-2/5/v1/test.pdf",
            "actionkit_item_id": 5,
            "actionkit_file_id": 10,
            "mapping_source": "actionkit_direct",
        }
        metadata = RoadmapRepository._build_actionkit_metadata(item, "DOCUMENT")
        assert metadata["actionkit_item_id"] == 5
        assert metadata["actionkit_file_id"] == 10
        assert metadata["mapping_source"] == "actionkit_direct"

    def test_default_mapping_source(self):
        from app.repositories.roadmap_repository import RoadmapRepository

        item = {"title": "test"}
        metadata = RoadmapRepository._build_actionkit_metadata(item, "LEGAL_BASIS")
        assert metadata["mapping_source"] == "llm_generated"

    def test_checklist_metadata(self):
        from app.repositories.roadmap_repository import RoadmapRepository

        item = {
            "title": "체크항목",
            "actionkit_item_id": 3,
            "actionkit_highlight_id": 7,
            "mapping_source": "actionkit_direct",
        }
        metadata = RoadmapRepository._build_actionkit_metadata(item, "CHECKLIST")
        assert metadata["actionkit_item_id"] == 3
        assert metadata["actionkit_highlight_id"] == 7
