"""RoadmapChatService 단위/통합 테스트.

LLM 호출은 모킹하여 SSE 스트리밍 동작, 출처 파싱, 에러 핸들링을 검증.
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.features.roadmaps.application.roadmap_chat_service import (
    RoadmapChatService,
    _sse_event,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_mock_roadmap():
    """테스트용 Roadmap mock."""
    roadmap = MagicMock()
    roadmap.business_type = "카페"
    roadmap.location = "서울특별시"
    return roadmap


def _make_mock_step(step_id=1, title="영업 인허가 신청"):
    """테스트용 RoadmapStep mock."""
    step = MagicMock()
    step.id = step_id
    step.title = title
    return step


def _make_mock_thread():
    """테스트용 RoadmapChatThread mock."""
    from uuid import uuid4

    thread = MagicMock()
    thread.id = uuid4()
    return thread


def _make_mock_actions():
    """테스트용 actions — 법령 1개 + 서류 1개."""
    legal = MagicMock()
    legal.action_type = "LEGAL_BASIS"
    legal.title = "식품위생법"
    legal.source_url = "/api/v1/actionkits/items/42"
    legal.metadata_json = {"actionkit_item_id": 42}

    doc = MagicMock()
    doc.action_type = "DOCUMENT"
    doc.title = "영업신고서"
    doc.source_url = "/api/v1/actionkits/items/43"
    doc.metadata_json = {}

    return [legal, doc]


def _make_service(
    *,
    classify_result="legal",
    llm_tokens=None,
    llm_error=None,
):
    """모킹된 의존성으로 RoadmapChatService 생성.

    Args:
        classify_result: SemanticRouter 분류 결과
        llm_tokens: LLM이 반환할 토큰 리스트 (기본: ["안녕", "하세요"])
        llm_error: LLM에서 발생시킬 예외
    """
    context_builder = MagicMock()
    mock_actions = _make_mock_actions()
    context_builder.build = AsyncMock(
        return_value=(
            "<FACTS>...</FACTS>\n<STATUS>...</STATUS>\n<RULES>...</RULES>",
            mock_actions,
        )
    )

    semantic_router = MagicMock()
    semantic_router.classify = AsyncMock(return_value=classify_result)

    chat_repo = MagicMock()
    chat_repo.get_recent_messages = AsyncMock(return_value=[])
    mock_msg = MagicMock()
    mock_msg.id = 42
    chat_repo.add_message = AsyncMock(return_value=mock_msg)

    service = RoadmapChatService.__new__(RoadmapChatService)
    service.context_builder = context_builder
    service.semantic_router = semantic_router
    service.chat_repo = chat_repo

    # LLM 모킹
    if llm_tokens is None:
        llm_tokens = ["안녕", "하세요"]

    async def _mock_astream(messages):
        if llm_error:
            raise llm_error
        for token in llm_tokens:
            yield AIMessage(content=token)

    service.llm = MagicMock()
    service.llm.astream = _mock_astream

    return service


async def _collect_events(service, **stream_kwargs):
    """stream()의 SSE 이벤트를 수집."""
    events = []
    async for event_str in service.stream(**stream_kwargs):
        # SSE 포맷 파싱: "data: {...}\n\n"
        if event_str.startswith("data: "):
            data = json.loads(event_str[6:].strip())
            events.append(data)
    return events


# ---------------------------------------------------------------------------
# _sse_event 유틸리티
# ---------------------------------------------------------------------------


def test_sse_event_format():
    """_sse_event가 올바른 SSE 포맷 문자열을 반환한다."""
    result = _sse_event("token", {"token": "안녕"})
    assert result.startswith("data: ")
    assert result.endswith("\n\n")
    data = json.loads(result[6:].strip())
    assert data["type"] == "token"
    assert data["token"] == "안녕"


def test_sse_event_korean_not_escaped():
    """한국어가 escape되지 않고 원문 그대로 포함된다."""
    result = _sse_event("token", {"token": "한국어"})
    assert "한국어" in result
    assert "\\u" not in result


# ---------------------------------------------------------------------------
# SSE 스트리밍 동작
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_yields_token_events():
    """stream()이 token 타입 SSE 이벤트를 yield한다."""
    service = _make_service(llm_tokens=["영업", "신고는", " 이렇게"])
    session = AsyncMock()

    events = await _collect_events(
        service,
        roadmap=_make_mock_roadmap(),
        step=_make_mock_step(),
        thread=_make_mock_thread(),
        user_message="영업신고 어떻게 해요?",
        session=session,
    )

    token_events = [e for e in events if e["type"] == "token"]
    assert len(token_events) == 3
    assert token_events[0]["token"] == "영업"
    assert token_events[1]["token"] == "신고는"
    assert token_events[2]["token"] == " 이렇게"


@pytest.mark.asyncio
async def test_stream_yields_meta_and_done_events():
    """스트리밍 완료 시 meta + done 이벤트가 순서대로 yield된다."""
    service = _make_service()
    session = AsyncMock()

    events = await _collect_events(
        service,
        roadmap=_make_mock_roadmap(),
        step=_make_mock_step(),
        thread=_make_mock_thread(),
        user_message="테스트",
        session=session,
    )

    event_types = [e["type"] for e in events]
    assert "meta" in event_types
    assert "done" in event_types
    # meta가 done 전에 와야 함
    assert event_types.index("meta") < event_types.index("done")


@pytest.mark.asyncio
async def test_stream_saves_user_and_assistant_messages():
    """stream() 완료 후 user + assistant 메시지가 DB에 저장된다."""
    service = _make_service()
    session = AsyncMock()

    events = await _collect_events(
        service,
        roadmap=_make_mock_roadmap(),
        step=_make_mock_step(),
        thread=_make_mock_thread(),
        user_message="테스트 질문",
        session=session,
    )

    # add_message가 최소 2번 호출 (user + assistant)
    calls = service.chat_repo.add_message.call_args_list
    assert len(calls) >= 2
    # 첫 번째: user 메시지
    assert calls[0].kwargs["role"] == "user"
    assert calls[0].kwargs["content"] == "테스트 질문"
    # 두 번째: assistant 메시지
    assert calls[1].kwargs["role"] == "assistant"


# ---------------------------------------------------------------------------
# 범위 외 질문 차단
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_rejects_out_of_scope_query():
    """SemanticRouter가 out_of_scope로 분류하면 에러 이벤트를 반환한다."""
    service = _make_service(classify_result="out_of_scope")
    session = AsyncMock()

    events = await _collect_events(
        service,
        roadmap=_make_mock_roadmap(),
        step=_make_mock_step(),
        thread=_make_mock_thread(),
        user_message="세금 얼마나 내야 해?",
        session=session,
    )

    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert events[0]["code"] == "OUT_OF_SCOPE"
    assert "전문가 상담" in events[0]["message"]


@pytest.mark.asyncio
async def test_stream_continues_on_semantic_router_error():
    """SemanticRouter 오류 시 차단하지 않고 계속 진행한다."""
    service = _make_service()
    service.semantic_router.classify = AsyncMock(side_effect=RuntimeError("임베딩 실패"))
    session = AsyncMock()

    events = await _collect_events(
        service,
        roadmap=_make_mock_roadmap(),
        step=_make_mock_step(),
        thread=_make_mock_thread(),
        user_message="테스트",
        session=session,
    )

    # 에러 이벤트가 아닌 정상 토큰이 나와야 함
    token_events = [e for e in events if e["type"] == "token"]
    assert len(token_events) > 0


@pytest.mark.asyncio
async def test_stream_without_semantic_router():
    """semantic_router가 None이면 분류 없이 진행한다."""
    service = _make_service()
    service.semantic_router = None
    session = AsyncMock()

    events = await _collect_events(
        service,
        roadmap=_make_mock_roadmap(),
        step=_make_mock_step(),
        thread=_make_mock_thread(),
        user_message="테스트",
        session=session,
    )

    token_events = [e for e in events if e["type"] == "token"]
    assert len(token_events) > 0


# ---------------------------------------------------------------------------
# 출처 파싱
# ---------------------------------------------------------------------------


def test_parse_citations_extracts_legal_references():
    """[법령 N] 패턴을 정확히 파싱한다."""
    actions = _make_mock_actions()
    response = "영업신고는 [법령 1]에 따라 진행합니다."

    result = RoadmapChatService._parse_citations(response, actions)

    assert len(result) == 1
    assert result[0]["type"] == "legal_basis"
    assert result[0]["title"] == "식품위생법"
    assert result[0]["id"] == 1


def test_parse_citations_extracts_document_references():
    """[서류 N] 패턴을 정확히 파싱한다."""
    actions = _make_mock_actions()
    response = "[서류 1]을 작성하여 제출하세요."

    result = RoadmapChatService._parse_citations(response, actions)

    assert len(result) == 1
    assert result[0]["type"] == "document"
    assert result[0]["title"] == "영업신고서"
    assert result[0]["id"] == 1


def test_parse_citations_deduplicates():
    """동일 출처가 여러 번 언급되면 중복 제거한다."""
    actions = _make_mock_actions()
    response = "[법령 1]에 따르면... [법령 1]에 의해..."

    result = RoadmapChatService._parse_citations(response, actions)

    assert len(result) == 1


def test_parse_citations_multiple_types():
    """법령 + 서류 혼합 인용을 파싱한다."""
    actions = _make_mock_actions()
    response = "[법령 1]에 따라 [서류 1]을 제출하세요."

    result = RoadmapChatService._parse_citations(response, actions)

    assert len(result) == 2
    types = {r["type"] for r in result}
    assert "legal_basis" in types
    assert "document" in types


def test_parse_citations_out_of_range():
    """범위 외 인덱스(예: [법령 99])는 무시한다."""
    actions = _make_mock_actions()
    response = "[법령 99]에 따르면..."

    result = RoadmapChatService._parse_citations(response, actions)

    assert len(result) == 0


def test_parse_citations_no_citations():
    """출처 인용이 없는 응답은 빈 리스트를 반환한다."""
    actions = _make_mock_actions()
    response = "일반적인 안내 내용입니다."

    result = RoadmapChatService._parse_citations(response, actions)

    assert result == []


def test_parse_citations_with_spaces():
    """[법령  1] 등 공백 변형도 파싱한다."""
    actions = _make_mock_actions()
    response = "[법령  1]에 따르면... [서류 1]을 제출하세요."

    result = RoadmapChatService._parse_citations(response, actions)

    # 정규식에 \s* 포함되어 있으므로 공백 허용
    assert len(result) == 2


# ---------------------------------------------------------------------------
# 출처 이벤트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_yields_sources_event_when_citations_exist():
    """응답에 출처 인용이 있으면 sources 이벤트가 yield된다."""
    service = _make_service(llm_tokens=["[법령 1]에 따르면 영업신고를 해야 합니다."])
    session = AsyncMock()

    events = await _collect_events(
        service,
        roadmap=_make_mock_roadmap(),
        step=_make_mock_step(),
        thread=_make_mock_thread(),
        user_message="영업신고 방법?",
        session=session,
    )

    source_events = [e for e in events if e["type"] == "sources"]
    assert len(source_events) == 1
    assert len(source_events[0]["sources"]) == 1
    assert source_events[0]["sources"][0]["title"] == "식품위생법"


@pytest.mark.asyncio
async def test_stream_no_sources_event_when_no_citations():
    """응답에 출처 인용이 없으면 sources 이벤트가 없다."""
    service = _make_service(llm_tokens=["일반적인 안내입니다."])
    session = AsyncMock()

    events = await _collect_events(
        service,
        roadmap=_make_mock_roadmap(),
        step=_make_mock_step(),
        thread=_make_mock_thread(),
        user_message="안녕하세요",
        session=session,
    )

    source_events = [e for e in events if e["type"] == "sources"]
    assert len(source_events) == 0


# ---------------------------------------------------------------------------
# 에러 핸들링
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_handles_llm_error():
    """LLM 오류 시 에러 이벤트를 반환한다."""
    service = _make_service(llm_error=RuntimeError("API 오류"))
    session = AsyncMock()

    events = await _collect_events(
        service,
        roadmap=_make_mock_roadmap(),
        step=_make_mock_step(),
        thread=_make_mock_thread(),
        user_message="테스트",
        session=session,
    )

    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) == 1
    assert error_events[0]["code"] == "LLM_ERROR"


@pytest.mark.asyncio
async def test_stream_handles_empty_response():
    """LLM이 빈 응답을 반환하면 EMPTY_RESPONSE 에러 이벤트."""
    service = _make_service(llm_tokens=[])
    session = AsyncMock()

    events = await _collect_events(
        service,
        roadmap=_make_mock_roadmap(),
        step=_make_mock_step(),
        thread=_make_mock_thread(),
        user_message="테스트",
        session=session,
    )

    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) == 1
    assert error_events[0]["code"] == "EMPTY_RESPONSE"


# ---------------------------------------------------------------------------
# _build_chat_messages
# ---------------------------------------------------------------------------


def test_build_chat_messages_structure():
    """_build_chat_messages가 system + history + user 순서로 구성한다."""
    recent = []
    msg1 = MagicMock()
    msg1.role = "user"
    msg1.content = "이전 질문"
    msg2 = MagicMock()
    msg2.role = "assistant"
    msg2.content = "이전 답변"
    recent = [msg1, msg2]

    result = RoadmapChatService._build_chat_messages(
        "시스템 프롬프트", recent, "새 질문"
    )

    assert result[0].content == "시스템 프롬프트"  # SystemMessage
    assert result[1].content == "이전 질문"  # HumanMessage
    assert result[2].content == "이전 답변"  # AIMessage
    assert result[3].content == "새 질문"  # HumanMessage (현재)


def test_build_chat_messages_no_duplicate_last():
    """마지막 이력 메시지와 현재 질문이 같으면 중복 추가하지 않는다."""
    msg = MagicMock()
    msg.role = "user"
    msg.content = "동일한 질문"
    recent = [msg]

    result = RoadmapChatService._build_chat_messages(
        "시스템", recent, "동일한 질문"
    )

    # system + history(1) = 2개 (현재 질문 중복 제거)
    human_msgs = [m for m in result if hasattr(m, "content") and m.content == "동일한 질문"]
    assert len(human_msgs) == 1


def test_build_chat_messages_empty_history():
    """이력이 없으면 system + user만 구성된다."""
    result = RoadmapChatService._build_chat_messages(
        "시스템", [], "질문"
    )

    assert len(result) == 2
    assert result[0].content == "시스템"
    assert result[1].content == "질문"
