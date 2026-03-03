"""통합 챗봇 SSE 스트리밍 API 테스트.

POST /api/v1/chat/stream — 5카테고리 분기 SSE 스트리밍

LLM/RAG를 mock하여 OpenAI API 키 없이 실행 가능.
라우터(A-6)가 등록된 후 활성화된다.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core import db
from app.models.roadmap import Roadmap, RoadmapStep, RoadmapStepDetail
from app.models.team import Team, TeamMember
from app.models.user import User
from sqlmodel import select

# 라우터 등록 전이면 전체 skip
_CHAT_ROUTER_PATH = (
    Path(__file__).parents[2] / "app" / "api" / "v1" / "chat"
)
pytestmark = pytest.mark.skipif(
    not _CHAT_ROUTER_PATH.exists(),
    reason="chat router not yet created (A-6 pending)",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STREAM_URL = "/api/v1/chat/stream"


async def _login_headers(client: AsyncClient) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    data = resp.json()
    return {
        "Authorization": f"Bearer {data['access_token']}",
        "X-Team-Id": data["current_team_id"],
    }


async def _get_test_user_and_team():
    async with db.async_session() as session:
        user = (
            await session.execute(
                select(User).where(User.email == "test@example.com")
            )
        ).scalar_one()
        team = (
            await session.execute(
                select(Team)
                .join(TeamMember, TeamMember.team_id == Team.id)
                .where(TeamMember.user_id == user.id)
            )
        ).scalar_one()
        return user.id, team.id


async def _create_roadmap_with_step(
    *, team_id, user_id, step_status="IN_PROGRESS"
):
    """테스트용 로드맵 + 단계 생성. (roadmap_id, step_id) 반환."""
    async with db.async_session() as session:
        roadmap = Roadmap(
            team_id=team_id,
            title="SSE 스트리밍 테스트",
            business_type="카페",
            location="서울특별시 강남구",
            created_by=user_id,
            updated_by=user_id,
        )
        session.add(roadmap)
        await session.flush()

        step = RoadmapStep(
            roadmap_id=roadmap.id,
            step_order=1,
            title="영업 인허가 신청",
            status=step_status,
        )
        session.add(step)
        await session.flush()

        detail = RoadmapStepDetail(
            roadmap_step_id=step.id,
            phase="인허가",
            objective="영업신고 완료",
            estimated_days=14,
        )
        session.add(detail)
        await session.commit()
        return roadmap.id, step.id


def _parse_sse_events(raw_text: str) -> list[dict]:
    """SSE 텍스트를 파싱하여 이벤트 목록 반환."""
    events = []
    for line in raw_text.strip().split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass
    return events


# ---------------------------------------------------------------------------
# 비인증 → 401
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_unauthenticated(client: AsyncClient) -> None:
    resp = await client.post(
        _STREAM_URL, json={"message": "테스트"}
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 빈 메시지 → 422
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_empty_message(client: AsyncClient) -> None:
    headers = await _login_headers(client)
    resp = await client.post(
        _STREAM_URL, json={"message": ""}, headers=headers
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# general 분류 + LLM mock 스트리밍
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_general(client: AsyncClient) -> None:
    """일반 질문 → general 분류 → LLM 스트리밍 응답."""
    headers = await _login_headers(client)

    # ChatService.stream을 mock
    async def _mock_stream(*args, **kwargs):
        yield 'data: {"type":"meta","session_id":"test-id","intent":"general","step_id":null,"step_title":null}\n\n'
        yield 'data: {"type":"token","token":"안녕하세요"}\n\n'
        yield 'data: {"type":"done"}\n\n'

    with patch(
        "app.features.chat.application.chat_service.ChatService.stream",
        side_effect=_mock_stream,
    ):
        resp = await client.post(
            _STREAM_URL,
            json={"message": "카페 인테리어 추천해주세요"},
            headers=headers,
        )

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")

    events = _parse_sse_events(resp.text)
    types = [e["type"] for e in events]
    assert "meta" in types
    assert "token" in types
    assert "done" in types


# ---------------------------------------------------------------------------
# out_of_scope 분류
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_out_of_scope(client: AsyncClient) -> None:
    """전문 분야 질문 → out_of_scope → error 이벤트."""
    headers = await _login_headers(client)

    async def _mock_stream(*args, **kwargs):
        yield 'data: {"type":"meta","session_id":"test-id","intent":"out_of_scope","step_id":null,"step_title":null}\n\n'
        yield 'data: {"type":"error","code":"OUT_OF_SCOPE","message":"이 질문은 전문가 상담을 권장합니다."}\n\n'

    with patch(
        "app.features.chat.application.chat_service.ChatService.stream",
        side_effect=_mock_stream,
    ):
        resp = await client.post(
            _STREAM_URL,
            json={"message": "주식 투자 추천해 주세요"},
            headers=headers,
        )

    assert resp.status_code == 200
    events = _parse_sse_events(resp.text)
    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) >= 1
    assert error_events[0]["code"] == "OUT_OF_SCOPE"


# ---------------------------------------------------------------------------
# current_step 분류 (로드맵 보유 사용자)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_current_step(client: AsyncClient) -> None:
    """현재 단계 질문 → current_step → ContextBuilder + LLM."""
    headers = await _login_headers(client)

    async def _mock_stream(*args, **kwargs):
        yield 'data: {"type":"meta","session_id":"test-id","intent":"current_step","step_id":1,"step_title":"영업 인허가 신청"}\n\n'
        yield 'data: {"type":"token","token":"영업신고는"}\n\n'
        yield 'data: {"type":"token","token":" 관할 구청에"}\n\n'
        yield 'data: {"type":"done"}\n\n'

    with patch(
        "app.features.chat.application.chat_service.ChatService.stream",
        side_effect=_mock_stream,
    ):
        resp = await client.post(
            _STREAM_URL,
            json={"message": "현재 단계에서 뭘 해야 하나요"},
            headers=headers,
        )

    assert resp.status_code == 200
    events = _parse_sse_events(resp.text)
    meta = next(e for e in events if e["type"] == "meta")
    assert meta["intent"] == "current_step"
    assert meta["step_title"] is not None

    tokens = [e for e in events if e["type"] == "token"]
    assert len(tokens) >= 1


# ---------------------------------------------------------------------------
# legal_general + RAG 폴백 warning
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_legal_with_warning(client: AsyncClient) -> None:
    """법률 질문 + RAG 미사용 → warning 이벤트 + LLM 폴백."""
    headers = await _login_headers(client)

    async def _mock_stream(*args, **kwargs):
        yield 'data: {"type":"meta","session_id":"test-id","intent":"legal_general","step_id":null,"step_title":null}\n\n'
        yield 'data: {"type":"warning","message":"법령 검색 서비스를 사용할 수 없어 일반 AI가 답변합니다."}\n\n'
        yield 'data: {"type":"token","token":"인허가 절차는"}\n\n'
        yield 'data: {"type":"done"}\n\n'

    with patch(
        "app.features.chat.application.chat_service.ChatService.stream",
        side_effect=_mock_stream,
    ):
        resp = await client.post(
            _STREAM_URL,
            json={"message": "영업 허가 절차가 궁금해요"},
            headers=headers,
        )

    assert resp.status_code == 200
    events = _parse_sse_events(resp.text)
    warnings = [e for e in events if e["type"] == "warning"]
    assert len(warnings) >= 1


# ---------------------------------------------------------------------------
# 세션 연속성 (session_id 전달)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stream_with_session_id(client: AsyncClient) -> None:
    """기존 session_id 전달 시 해당 세션에 메시지 추가."""
    headers = await _login_headers(client)

    async def _mock_stream(*args, **kwargs):
        yield 'data: {"type":"meta","session_id":"existing-session","intent":"general","step_id":null,"step_title":null}\n\n'
        yield 'data: {"type":"token","token":"답변"}\n\n'
        yield 'data: {"type":"done"}\n\n'

    with patch(
        "app.features.chat.application.chat_service.ChatService.stream",
        side_effect=_mock_stream,
    ):
        resp = await client.post(
            _STREAM_URL,
            json={
                "message": "추가 질문입니다",
                "session_id": "00000000-0000-0000-0000-000000000001",
            },
            headers=headers,
        )

    assert resp.status_code == 200
    events = _parse_sse_events(resp.text)
    assert any(e["type"] == "meta" for e in events)
