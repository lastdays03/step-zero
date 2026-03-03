"""AI 코치 채팅 SSE 라우터 API 테스트.

SSE 스트리밍 엔드포인트는 LLM 호출이 필요하므로 @pytest.mark.requires_openai.
인증/권한/스레드 조회 등 non-LLM 테스트는 바로 실행 가능.
mock LLM 테스트는 unittest.mock으로 LLM을 대체하여 OPENAI_API_KEY 없이 실행.
"""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.core import db, security
from app.models.roadmap import Roadmap, RoadmapStep, RoadmapStepAction, RoadmapStepDetail
from app.models.roadmap_chat import RoadmapChatMessage, RoadmapChatThread
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
    *,
    team_id,
    user_id,
    step_status="IN_PROGRESS",
    with_actions=True,
):
    """테스트용 로드맵 + 단계 + 액션 생성. (roadmap_id, step_id) 반환."""
    async with db.async_session() as session:
        roadmap = Roadmap(
            team_id=team_id,
            title="AI 코치 채팅 테스트",
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

        if with_actions:
            legal = RoadmapStepAction(
                roadmap_step_id=step.id,
                action_type="LEGAL_BASIS",
                title="식품위생법",
                description="영업신고 근거",
                source_url="/api/v1/actionkits/items/42",
                metadata_json={"actionkit_item_id": 42},
            )
            session.add(legal)

            doc = RoadmapStepAction(
                roadmap_step_id=step.id,
                action_type="DOCUMENT",
                title="영업신고서",
                description="신청 서류",
                source_url="/api/v1/actionkits/items/43",
                metadata_json={},
            )
            session.add(doc)

        await session.commit()
        await session.refresh(roadmap)
        await session.refresh(step)
        return str(roadmap.id), step.id


async def _create_thread_with_messages(
    *,
    roadmap_id,
    step_id,
    user_id,
    message_count=2,
):
    """테스트용 스레드 + 메시지 생성. thread_id 반환."""
    from uuid import UUID

    from app.repositories.roadmap_chat_repository import RoadmapChatRepository

    # SQLite 테스트에서는 UUID 객체가 필요
    rid = UUID(roadmap_id) if isinstance(roadmap_id, str) else roadmap_id

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        thread = await repo.get_or_create_thread(
            roadmap_id=rid,
            step_id=step_id,
            user_id=user_id,
        )
        for i in range(message_count):
            role = "user" if i % 2 == 0 else "assistant"
            await repo.add_message(
                thread_id=thread.id,
                role=role,
                content=f"테스트 메시지 {i}",
            )
        await session.commit()
        return str(thread.id)


async def _create_second_user_and_team():
    """두 번째 테스트 유저 + 별도 팀 생성. (user_id, team_id) 반환."""
    async with db.async_session() as session:
        result = await session.execute(
            select(User).where(User.email == "other@example.com")
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email="other@example.com",
                full_name="Other User",
                hashed_password=security.get_password_hash("password123"),
            )
            session.add(user)
            await session.flush()

            team = Team(
                name="Other Team", created_by=user.id, updated_by=user.id
            )
            session.add(team)
            await session.flush()
            session.add(
                TeamMember(team_id=team.id, user_id=user.id, role="owner")
            )
            await session.commit()
            await session.refresh(user)
            await session.refresh(team)
            return user.id, team.id

        team_result = await session.execute(
            select(Team)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == user.id)
        )
        team = team_result.scalar_one()
        return user.id, team.id


async def _login_headers_for(client: AsyncClient, email: str) -> dict[str, str]:
    """지정 이메일로 로그인하여 인증 헤더 반환."""
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    return {
        "Authorization": f"Bearer {login_data['access_token']}",
        "X-Team-Id": login_data["current_team_id"],
    }


# ---------------------------------------------------------------------------
# SSE 스트리밍 채팅 — 인증/권한 검증
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_step_chat_stream_requires_auth(client: AsyncClient):
    """인증 없이 접근 시 401 반환."""
    response = await client.post(
        "/api/v1/roadmaps/00000000-0000-0000-0000-000000000000/steps/1/chat/stream",
        json={"message": "테스트"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_step_chat_stream_roadmap_not_found(client: AsyncClient):
    """존재하지 않는 로드맵 ID로 접근 시 404 반환."""
    headers = await _login_headers(client)
    response = await client.post(
        "/api/v1/roadmaps/00000000-0000-0000-0000-000000000000/steps/1/chat/stream",
        json={"message": "테스트"},
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_step_chat_stream_validates_step_status(client: AsyncClient):
    """PENDING 상태 단계에서 채팅 시도 시 400 반환."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
        step_status="PENDING",
    )

    headers = await _login_headers(client)
    response = await client.post(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/stream",
        json={"message": "테스트"},
        headers=headers,
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_step_chat_stream_validates_message_length(client: AsyncClient):
    """빈 메시지 또는 2000자 초과 시 422 반환."""
    headers = await _login_headers(client)

    # 빈 메시지
    response = await client.post(
        "/api/v1/roadmaps/00000000-0000-0000-0000-000000000000/steps/1/chat/stream",
        json={"message": ""},
        headers=headers,
    )
    assert response.status_code == 422

    # 2001자 초과
    response = await client.post(
        "/api/v1/roadmaps/00000000-0000-0000-0000-000000000000/steps/1/chat/stream",
        json={"message": "가" * 2001},
        headers=headers,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# SSE 스트리밍 채팅 — LLM 필요 테스트
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
async def test_step_chat_stream_returns_sse(client: AsyncClient):
    """POST /roadmaps/{id}/steps/{id}/chat/stream → SSE 응답 (실제 LLM)."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
        step_status="IN_PROGRESS",
    )
    headers = await _login_headers(client)

    response = await client.post(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/stream",
        json={"message": "영업신고 어떻게 하나요?"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")


@pytest.mark.asyncio
@pytest.mark.requires_openai
async def test_step_chat_stream_returns_sse_with_mock_llm(client: AsyncClient):
    """Mock LLM으로 SSE 스트리밍 정상 동작 검증 (서비스 초기화에 OPENAI_API_KEY 필요)."""
    from langchain_core.messages import AIMessageChunk

    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
        step_status="IN_PROGRESS",
    )
    headers = await _login_headers(client)

    # Mock LLM astream: 토큰 3개를 yield
    async def mock_astream(messages):
        for token in ["안녕", "하세요", "!"]:
            yield AIMessageChunk(content=token)

    with patch(
        "app.features.roadmaps.application.roadmap_chat_service.RoadmapChatService.stream"
    ) as mock_stream:
        # stream 제너레이터를 직접 mock하여 SSE 이벤트 반환
        async def fake_stream(**kwargs):
            yield f'data: {json.dumps({"type": "token", "token": "안녕"}, ensure_ascii=False)}\n\n'
            yield f'data: {json.dumps({"type": "token", "token": "하세요"}, ensure_ascii=False)}\n\n'
            yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'

        mock_stream.return_value = fake_stream()

        response = await client.post(
            f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/stream",
            json={"message": "영업신고 어떻게 하나요?"},
            headers=headers,
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    body = response.text
    assert "token" in body


# ---------------------------------------------------------------------------
# SSE 스트리밍 채팅 — 다른 팀 접근 차단
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_step_chat_stream_other_team_roadmap_returns_404(client: AsyncClient):
    """다른 팀의 로드맵에 접근 시 404 반환 (팀 스코프 검증)."""
    # 첫 번째 유저의 로드맵 생성
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
        step_status="IN_PROGRESS",
    )

    # 두 번째 유저로 로그인 (다른 팀)
    await _create_second_user_and_team()
    other_headers = await _login_headers_for(client, "other@example.com")

    response = await client.post(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/stream",
        json={"message": "테스트"},
        headers=other_headers,
    )
    # 다른 팀이므로 로드맵을 찾을 수 없음
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_threads_other_team_roadmap_returns_404(client: AsyncClient):
    """다른 팀의 로드맵 스레드 목록 조회 시 404 반환."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
    )

    await _create_second_user_and_team()
    other_headers = await _login_headers_for(client, "other@example.com")

    response = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads",
        headers=other_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_messages_other_team_roadmap_returns_404(client: AsyncClient):
    """다른 팀의 로드맵 메시지 조회 시 404 반환."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
    )
    thread_id = await _create_thread_with_messages(
        roadmap_id=roadmap_id,
        step_id=step_id,
        user_id=user_id,
    )

    await _create_second_user_and_team()
    other_headers = await _login_headers_for(client, "other@example.com")

    response = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages",
        headers=other_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 대화 스레드 목록 조회
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_chat_threads(client: AsyncClient):
    """GET /roadmaps/{id}/steps/{id}/chat/threads → 스레드 목록."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
    )

    # 스레드 생성
    await _create_thread_with_messages(
        roadmap_id=roadmap_id,
        step_id=step_id,
        user_id=user_id,
    )

    headers = await _login_headers(client)
    response = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads",
        headers=headers,
    )
    assert response.status_code == 200
    threads = response.json()
    assert isinstance(threads, list)
    assert len(threads) >= 1
    assert "thread_id" in threads[0]
    assert "message_count" in threads[0]


@pytest.mark.asyncio
async def test_list_chat_threads_empty(client: AsyncClient):
    """스레드가 없으면 빈 리스트 반환."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
    )

    headers = await _login_headers(client)
    response = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_chat_threads_requires_auth(client: AsyncClient):
    """인증 없이 스레드 목록 접근 시 401."""
    response = await client.get(
        "/api/v1/roadmaps/00000000-0000-0000-0000-000000000000/steps/1/chat/threads",
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 스레드 메시지 조회
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_thread_messages(client: AsyncClient):
    """GET /roadmaps/{id}/steps/{id}/chat/threads/{tid}/messages → 메시지 목록."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
    )
    thread_id = await _create_thread_with_messages(
        roadmap_id=roadmap_id,
        step_id=step_id,
        user_id=user_id,
        message_count=4,
    )

    headers = await _login_headers(client)
    response = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages",
        headers=headers,
    )
    assert response.status_code == 200
    messages = response.json()
    assert isinstance(messages, list)
    assert len(messages) == 4
    assert "role" in messages[0]
    assert "content" in messages[0]


@pytest.mark.asyncio
async def test_get_thread_messages_not_found(client: AsyncClient):
    """존재하지 않는 스레드 ID로 메시지 조회 시 404."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
    )

    headers = await _login_headers(client)
    response = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads/00000000-0000-0000-0000-000000000000/messages",
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_thread_messages_requires_auth(client: AsyncClient):
    """인증 없이 메시지 조회 시 401."""
    response = await client.get(
        "/api/v1/roadmaps/00000000-0000-0000-0000-000000000000/steps/1/chat/threads/00000000-0000-0000-0000-000000000000/messages",
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 메시지 페이징 (offset/limit)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_thread_messages_with_limit(client: AsyncClient):
    """limit 파라미터로 반환 메시지 수 제한."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
    )
    thread_id = await _create_thread_with_messages(
        roadmap_id=roadmap_id,
        step_id=step_id,
        user_id=user_id,
        message_count=6,
    )

    headers = await _login_headers(client)
    response = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages",
        params={"limit": 3},
        headers=headers,
    )
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 3


@pytest.mark.asyncio
async def test_get_thread_messages_with_offset(client: AsyncClient):
    """offset 파라미터로 오래된 메시지 로드 (역방향 페이지네이션)."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
    )
    thread_id = await _create_thread_with_messages(
        roadmap_id=roadmap_id,
        step_id=step_id,
        user_id=user_id,
        message_count=6,
    )

    headers = await _login_headers(client)

    # 전체 조회 (기본 limit=20)
    all_response = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages",
        headers=headers,
    )
    all_messages = all_response.json()
    assert len(all_messages) == 6

    # offset=3으로 최근 3개 건너뛰고 나머지 조회
    offset_response = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages",
        params={"offset": 3, "limit": 10},
        headers=headers,
    )
    offset_messages = offset_response.json()
    assert len(offset_messages) == 3


@pytest.mark.asyncio
async def test_get_thread_messages_offset_beyond_total(client: AsyncClient):
    """offset이 전체 메시지 수를 초과하면 빈 리스트 반환."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, step_id = await _create_roadmap_with_step(
        team_id=team_id,
        user_id=user_id,
    )
    thread_id = await _create_thread_with_messages(
        roadmap_id=roadmap_id,
        step_id=step_id,
        user_id=user_id,
        message_count=2,
    )

    headers = await _login_headers(client)
    response = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages",
        params={"offset": 100},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_thread_messages_invalid_limit(client: AsyncClient):
    """limit=0 또는 limit>100 시 422 반환."""
    headers = await _login_headers(client)

    # limit=0 (최소 1 필요)
    response = await client.get(
        "/api/v1/roadmaps/00000000-0000-0000-0000-000000000000/steps/1/chat/threads/00000000-0000-0000-0000-000000000000/messages",
        params={"limit": 0},
        headers=headers,
    )
    assert response.status_code == 422

    # limit=101 (최대 100)
    response = await client.get(
        "/api/v1/roadmaps/00000000-0000-0000-0000-000000000000/steps/1/chat/threads/00000000-0000-0000-0000-000000000000/messages",
        params={"limit": 101},
        headers=headers,
    )
    assert response.status_code == 422
