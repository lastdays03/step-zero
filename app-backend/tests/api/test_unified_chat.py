"""통합 챗봇 SSE 스트리밍 API 테스트.

POST /api/v1/rag/chat/stream — 글로벌 + 코치 모드 통합 SSE 엔드포인트.
- 인증/유효성 검증 (mock 불필요)
- 일반 모드 SSE 스트리밍 (ChatService.stream mock)
- 코치 모드 SSE 스트리밍 (RoadmapChatService.stream mock)
"""

import json
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core import db, security
from app.models.roadmap import Roadmap, RoadmapStep, RoadmapStepDetail
from app.models.team import Team, TeamMember
from app.models.user import User
from sqlmodel import select


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _login_headers(client: AsyncClient) -> dict[str, str]:
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    return {
        "Authorization": f"Bearer {login_data['access_token']}",
        "X-Team-Id": login_data["current_team_id"],
    }


async def _get_test_user_and_team():
    """테스트 유저 ID와 팀 ID를 반환."""
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
            title="통합 챗봇 테스트",
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
            risk_notes=["지역별 처리 기간 상이"],
        )
        session.add(detail)
        await session.commit()
        await session.refresh(roadmap)
        await session.refresh(step)
        return str(roadmap.id), step.id


# ---------------------------------------------------------------------------
# Validation 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unified_chat_stream_requires_auth(client: AsyncClient):
    """인증 없이 접근 시 401 반환."""
    response = await client.post(
        "/api/v1/rag/chat/stream",
        json={"message": "테스트"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unified_chat_stream_roadmap_id_only_returns_422(
    client: AsyncClient,
):
    """roadmap_id만 제공하고 step_id 누락 시 422."""
    headers = await _login_headers(client)
    response = await client.post(
        "/api/v1/rag/chat/stream",
        json={
            "message": "테스트",
            "roadmap_id": "00000000-0000-0000-0000-000000000000",
        },
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unified_chat_stream_step_id_only_returns_422(
    client: AsyncClient,
):
    """step_id만 제공하고 roadmap_id 누락 시 422."""
    headers = await _login_headers(client)
    response = await client.post(
        "/api/v1/rag/chat/stream",
        json={
            "message": "테스트",
            "step_id": 1,
        },
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unified_chat_stream_empty_message_returns_422(
    client: AsyncClient,
):
    """빈 메시지 시 422."""
    headers = await _login_headers(client)
    response = await client.post(
        "/api/v1/rag/chat/stream",
        json={"message": ""},
        headers=headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_unified_chat_stream_message_too_long_returns_422(
    client: AsyncClient,
):
    """2000자 초과 메시지 시 422."""
    headers = await _login_headers(client)
    response = await client.post(
        "/api/v1/rag/chat/stream",
        json={"message": "가" * 2001},
        headers=headers,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 일반 모드 SSE 스트리밍
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.requires_openai
async def test_unified_chat_stream_general_mode(client: AsyncClient):
    """일반 모드: mock ChatService.stream → SSE 응답 검증."""
    headers = await _login_headers(client)

    with patch(
        "app.features.rag.application.chat_service.ChatService.stream"
    ) as mock_stream:

        async def fake_stream(message):
            yield f'data: {json.dumps({"type": "token", "token": "안녕"}, ensure_ascii=False)}\n\n'
            yield f'data: {json.dumps({"type": "token", "token": "하세요"}, ensure_ascii=False)}\n\n'
            yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'

        mock_stream.return_value = fake_stream("test")

        response = await client.post(
            "/api/v1/rag/chat/stream",
            json={"message": "카페 마케팅 전략 알려주세요"},
            headers=headers,
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "안녕" in body
    assert "done" in body


# ---------------------------------------------------------------------------
# 코치 모드 SSE 스트리밍
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.requires_openai
async def test_unified_chat_stream_coach_mode(client: AsyncClient):
    """코치 모드: roadmap_id + step_id → mock RoadmapChatService.stream → SSE 응답."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id, user_id=user_id
    )
    headers = await _login_headers(client)

    with patch(
        "app.features.roadmaps.application.roadmap_chat_service"
        ".RoadmapChatService.stream"
    ) as mock_stream:

        async def fake_stream(**kwargs):
            yield f'data: {json.dumps({"type": "token", "token": "영업신고는"}, ensure_ascii=False)}\n\n'
            yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'

        mock_stream.return_value = fake_stream()

        response = await client.post(
            "/api/v1/rag/chat/stream",
            json={
                "message": "영업신고 어떻게 하나요?",
                "roadmap_id": roadmap_id,
                "step_id": step_id,
            },
            headers=headers,
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "영업신고는" in body
    assert "done" in body


@pytest.mark.asyncio
@pytest.mark.requires_openai
async def test_unified_chat_stream_coach_mode_roadmap_not_found(
    client: AsyncClient,
):
    """코치 모드: 존재하지 않는 로드맵 → SSE error 이벤트."""
    headers = await _login_headers(client)
    response = await client.post(
        "/api/v1/rag/chat/stream",
        json={
            "message": "테스트",
            "roadmap_id": "00000000-0000-0000-0000-000000000000",
            "step_id": 99999,
        },
        headers=headers,
    )
    # SSE 스트리밍이므로 HTTP 200으로 시작, 본문에 error 이벤트 포함
    assert response.status_code == 200
    body = response.text
    assert "NOT_FOUND" in body
