"""AI 코치 채팅 통합 테스트.

E2E 플로우, 컨텍스트 격리, 에러 시나리오를 검증한다.
LLM 호출은 mock으로 대체하여 OPENAI_API_KEY 없이 실행 가능.
SQLite 테스트 DB 사용 (동시 쓰기 불가 → 순차 검증).
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessageChunk

from app.core import db
from app.models.roadmap import Roadmap, RoadmapStep, RoadmapStepAction, RoadmapStepDetail
from app.models.roadmap_chat import RoadmapChatThread
from app.models.team import Team, TeamMember
from app.models.user import User
from app.repositories.roadmap_chat_repository import RoadmapChatRepository
from sqlmodel import select


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


async def _create_full_roadmap(*, team_id, user_id, num_steps=3):
    """여러 단계를 가진 로드맵 생성. (roadmap_id, [(step_id, status)]) 반환."""
    async with db.async_session() as session:
        roadmap = Roadmap(
            team_id=team_id,
            title="E2E 통합 테스트 로드맵",
            business_type="카페",
            location="서울특별시 강남구",
            created_by=user_id,
            updated_by=user_id,
        )
        session.add(roadmap)
        await session.flush()

        steps = []
        statuses = ["COMPLETED", "IN_PROGRESS"] + ["PENDING"] * (num_steps - 2)
        for i in range(num_steps):
            step = RoadmapStep(
                roadmap_id=roadmap.id,
                step_order=i + 1,
                title=f"단계 {i + 1}",
                status=statuses[i] if i < len(statuses) else "PENDING",
            )
            session.add(step)
            await session.flush()

            detail = RoadmapStepDetail(
                roadmap_step_id=step.id,
                phase=f"Phase {i + 1}",
                objective=f"목표 {i + 1}",
                estimated_days=7 * (i + 1),
                risk_notes=[f"리스크 {i + 1}"],
            )
            session.add(detail)

            legal = RoadmapStepAction(
                roadmap_step_id=step.id,
                action_type="LEGAL_BASIS",
                title=f"법령 {i + 1}",
                description=f"법령 설명 {i + 1}",
                source_url=f"/api/v1/actionkits/items/{100 + i}",
                metadata_json={"actionkit_item_id": 100 + i},
            )
            session.add(legal)

            steps.append((step.id, step.status))

        await session.commit()
        await session.refresh(roadmap)
        return str(roadmap.id), steps


async def _create_thread_with_messages(
    *, roadmap_id, step_id, user_id, message_count=2
):
    """Repository를 통해 스레드 + 메시지 생성. thread_id 반환."""
    rid = UUID(roadmap_id) if isinstance(roadmap_id, str) else roadmap_id
    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        thread = await repo.get_or_create_thread(
            roadmap_id=rid, step_id=step_id, user_id=user_id
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


# ---------------------------------------------------------------------------
# E2E 플로우: 컨텍스트 격리 (단계별 독립 스레드)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_context_isolation_between_steps(client: AsyncClient):
    """서로 다른 단계는 독립된 스레드를 가짐 (컨텍스트 격리)."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, steps = await _create_full_roadmap(
        team_id=team_id, user_id=user_id, num_steps=3
    )
    headers = await _login_headers(client)

    # step 0 (COMPLETED)과 step 1 (IN_PROGRESS) 각각 스레드 생성
    tid_0 = await _create_thread_with_messages(
        roadmap_id=roadmap_id,
        step_id=steps[0][0],
        user_id=user_id,
        message_count=2,
    )
    tid_1 = await _create_thread_with_messages(
        roadmap_id=roadmap_id,
        step_id=steps[1][0],
        user_id=user_id,
        message_count=4,
    )

    # 각 단계 스레드 조회 — 독립적
    resp_0 = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{steps[0][0]}/chat/threads",
        headers=headers,
    )
    resp_1 = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{steps[1][0]}/chat/threads",
        headers=headers,
    )
    assert resp_0.status_code == 200
    assert resp_1.status_code == 200

    threads_0 = resp_0.json()
    threads_1 = resp_1.json()
    assert len(threads_0) == 1
    assert len(threads_1) == 1
    assert threads_0[0]["thread_id"] != threads_1[0]["thread_id"]

    # 메시지 수도 독립적
    assert threads_0[0]["message_count"] == 2
    assert threads_1[0]["message_count"] == 4


@pytest.mark.asyncio
async def test_e2e_history_persistence_and_retrieval(client: AsyncClient):
    """채팅 이력이 DB에 저장되고 API로 복원됨."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, steps = await _create_full_roadmap(
        team_id=team_id, user_id=user_id, num_steps=2
    )
    headers = await _login_headers(client)
    step_id = steps[1][0]  # IN_PROGRESS

    # 6개 메시지 생성
    thread_id = await _create_thread_with_messages(
        roadmap_id=roadmap_id,
        step_id=step_id,
        user_id=user_id,
        message_count=6,
    )

    # 전체 메시지 조회
    resp = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages",
        headers=headers,
    )
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 6
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

    # 페이징 조회 (limit=2)
    resp2 = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages",
        params={"limit": 2},
        headers=headers,
    )
    assert len(resp2.json()) == 2

    # offset 조회 (최근 2개 건너뛰고 나머지)
    resp3 = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages",
        params={"offset": 2, "limit": 10},
        headers=headers,
    )
    assert len(resp3.json()) == 4


@pytest.mark.asyncio
async def test_e2e_thread_per_roadmap_step_user_uniqueness(client: AsyncClient):
    """동일 (roadmap, step, user) 조합은 항상 같은 스레드 (멱등성)."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, steps = await _create_full_roadmap(
        team_id=team_id, user_id=user_id, num_steps=2
    )
    step_id = steps[1][0]
    rid = UUID(roadmap_id)

    # 같은 인자로 두 번 생성
    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        t1 = await repo.get_or_create_thread(
            roadmap_id=rid, step_id=step_id, user_id=user_id
        )
        t2 = await repo.get_or_create_thread(
            roadmap_id=rid, step_id=step_id, user_id=user_id
        )
        assert t1.id == t2.id
        await session.commit()

    # API로도 확인 — 스레드 1개만 존재
    headers = await _login_headers(client)
    resp = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads",
        headers=headers,
    )
    assert len(resp.json()) == 1


# ---------------------------------------------------------------------------
# SSE 스트리밍 E2E (LLM mock)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_e2e_stream_with_mock_llm_saves_messages(client: AsyncClient):
    """Mock LLM으로 SSE 스트리밍 → DB에 user/assistant 메시지 저장 확인."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, steps = await _create_full_roadmap(
        team_id=team_id, user_id=user_id, num_steps=2
    )
    headers = await _login_headers(client)
    step_id = steps[1][0]  # IN_PROGRESS

    # Mock: ChatOpenAI.astream → AI 토큰 yield
    async def mock_astream(self, messages, **kwargs):
        for token in ["안녕", "하세요", "!"]:
            yield AIMessageChunk(content=token)

    with patch(
        "langchain_openai.ChatOpenAI.astream",
        mock_astream,
    ):
        resp = await client.post(
            f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/stream",
            json={"message": "영업신고 방법 알려주세요"},
            headers=headers,
        )

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    # SSE 본문 확인 — token 이벤트 존재
    body = resp.text
    assert "token" in body

    # DB에 스레드+메시지 저장 확인
    thread_resp = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads",
        headers=headers,
    )
    threads = thread_resp.json()
    assert len(threads) >= 1
    thread_id = threads[0]["thread_id"]
    assert threads[0]["message_count"] >= 2  # user + assistant

    # 메시지 내용 확인
    msg_resp = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages",
        headers=headers,
    )
    messages = msg_resp.json()
    assert any(m["role"] == "user" for m in messages)
    assert any(m["role"] == "assistant" for m in messages)

    # assistant 응답 내용
    assistant_msg = next(m for m in messages if m["role"] == "assistant")
    assert "안녕하세요!" == assistant_msg["content"]


# ---------------------------------------------------------------------------
# 에러 시나리오
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_error_expired_token_all_endpoints(client: AsyncClient):
    """만료/잘못된 토큰으로 모든 채팅 엔드포인트 401."""
    bad_headers = {
        "Authorization": "Bearer invalid-expired-token",
        "X-Team-Id": "00000000-0000-0000-0000-000000000000",
    }
    fake_id = "00000000-0000-0000-0000-000000000000"

    r1 = await client.post(
        f"/api/v1/roadmaps/{fake_id}/steps/1/chat/stream",
        json={"message": "테스트"},
        headers=bad_headers,
    )
    assert r1.status_code == 401

    r2 = await client.get(
        f"/api/v1/roadmaps/{fake_id}/steps/1/chat/threads",
        headers=bad_headers,
    )
    assert r2.status_code == 401

    r3 = await client.get(
        f"/api/v1/roadmaps/{fake_id}/steps/1/chat/threads/{fake_id}/messages",
        headers=bad_headers,
    )
    assert r3.status_code == 401


@pytest.mark.asyncio
async def test_error_pending_step_blocks_stream_allows_read(client: AsyncClient):
    """PENDING 단계: stream → 400, threads/messages 조회 → 200."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, steps = await _create_full_roadmap(
        team_id=team_id, user_id=user_id, num_steps=3
    )
    headers = await _login_headers(client)
    pending_step_id = steps[2][0]

    # stream 차단
    resp = await client.post(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{pending_step_id}/chat/stream",
        json={"message": "PENDING 단계 테스트"},
        headers=headers,
    )
    assert resp.status_code == 400

    # threads 조회 — 빈 리스트지만 200
    resp2 = await client.get(
        f"/api/v1/roadmaps/{roadmap_id}/steps/{pending_step_id}/chat/threads",
        headers=headers,
    )
    assert resp2.status_code == 200
    assert resp2.json() == []


@pytest.mark.asyncio
async def test_error_nonexistent_roadmap_all_endpoints(client: AsyncClient):
    """존재하지 않는 로드맵 → 모든 엔드포인트 404."""
    headers = await _login_headers(client)
    fake_id = "00000000-0000-0000-0000-ffffffffffff"

    r1 = await client.post(
        f"/api/v1/roadmaps/{fake_id}/steps/99999/chat/stream",
        json={"message": "테스트"},
        headers=headers,
    )
    assert r1.status_code == 404

    r2 = await client.get(
        f"/api/v1/roadmaps/{fake_id}/steps/99999/chat/threads",
        headers=headers,
    )
    assert r2.status_code == 404

    r3 = await client.get(
        f"/api/v1/roadmaps/{fake_id}/steps/99999/chat/threads/{fake_id}/messages",
        headers=headers,
    )
    assert r3.status_code == 404


@pytest.mark.asyncio
async def test_error_step_not_belonging_to_roadmap(client: AsyncClient):
    """다른 로드맵의 step_id로 접근 시 404."""
    user_id, team_id = await _get_test_user_and_team()

    roadmap_id_1, steps_1 = await _create_full_roadmap(
        team_id=team_id, user_id=user_id, num_steps=2
    )
    roadmap_id_2, steps_2 = await _create_full_roadmap(
        team_id=team_id, user_id=user_id, num_steps=2
    )
    headers = await _login_headers(client)

    # roadmap_1 + step from roadmap_2 → 불일치
    resp = await client.post(
        f"/api/v1/roadmaps/{roadmap_id_1}/steps/{steps_2[1][0]}/chat/stream",
        json={"message": "cross-roadmap 테스트"},
        headers=headers,
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Repository 통합: message_count 증가 + 페이지네이션 정렬
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_repository_message_count_auto_increment():
    """메시지 추가 시 스레드 message_count 자동 증가."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, steps = await _create_full_roadmap(
        team_id=team_id, user_id=user_id, num_steps=1
    )
    rid = UUID(roadmap_id)
    step_id = steps[0][0]

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        thread = await repo.get_or_create_thread(
            roadmap_id=rid, step_id=step_id, user_id=user_id
        )
        assert thread.message_count == 0

        await repo.add_message(
            thread_id=thread.id, role="user", content="질문"
        )
        await repo.add_message(
            thread_id=thread.id, role="assistant", content="답변"
        )
        await session.commit()

        count = await repo.count_messages(thread.id)
        assert count == 2

        refreshed = await repo.get_thread(thread.id)
        assert refreshed.message_count == 2


@pytest.mark.asyncio
async def test_repository_get_recent_messages_chronological_order():
    """get_recent_messages는 시간순(오래된 것 먼저) 정렬."""
    user_id, team_id = await _get_test_user_and_team()
    roadmap_id, steps = await _create_full_roadmap(
        team_id=team_id, user_id=user_id, num_steps=1
    )
    rid = UUID(roadmap_id)
    step_id = steps[0][0]

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        thread = await repo.get_or_create_thread(
            roadmap_id=rid, step_id=step_id, user_id=user_id
        )
        for i in range(5):
            await repo.add_message(
                thread_id=thread.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"메시지 {i}",
            )
        await session.commit()

        # 최근 3개
        recent = await repo.get_recent_messages(thread.id, limit=3)
        assert len(recent) == 3
        # 시간순: 오래된 것이 먼저 (id 오름차순)
        assert recent[0].id < recent[1].id < recent[2].id
        # 가장 최근 3개 (메시지 2, 3, 4)
        assert recent[0].content == "메시지 2"
        assert recent[2].content == "메시지 4"
