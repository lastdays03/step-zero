"""RoadmapChatRepository CRUD 테스트."""

from uuid import uuid4

import pytest
from sqlmodel import select

from app.core import db
from app.models.roadmap import Roadmap, RoadmapStep
from app.models.roadmap_chat import RoadmapChatMessage, RoadmapChatThread
from app.models.user import User
from app.repositories.roadmap_chat_repository import RoadmapChatRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_test_user_and_roadmap() -> tuple[int, "UUID", int]:
    """테스트 유저, 로드맵(UUID), 스텝 ID를 반환."""
    async with db.async_session() as session:
        user = (
            await session.execute(
                select(User).where(User.email == "test@example.com")
            )
        ).scalar_one()

        roadmap = Roadmap(
            team_id=uuid4(),
            title="채팅 테스트 로드맵",
            business_type="카페",
            location="서울특별시",
        )
        session.add(roadmap)
        await session.flush()

        step = RoadmapStep(
            roadmap_id=roadmap.id,
            step_order=1,
            title="1단계",
            status="IN_PROGRESS",
        )
        session.add(step)
        await session.commit()
        await session.refresh(roadmap)
        await session.refresh(step)

        return user.id, roadmap.id, step.id


# ---------------------------------------------------------------------------
# get_or_create_thread
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_or_create_thread_creates_new():
    """스레드가 없으면 새로 생성한다."""
    user_id, roadmap_id, step_id = await _get_test_user_and_roadmap()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        thread = await repo.get_or_create_thread(
            roadmap_id=roadmap_id,
            step_id=step_id,
            user_id=user_id,
        )
        await session.commit()

    assert thread is not None
    assert thread.roadmap_id == roadmap_id
    assert thread.step_id == step_id
    assert thread.user_id == user_id
    assert thread.message_count == 0


@pytest.mark.asyncio
async def test_get_or_create_thread_returns_existing():
    """동일 (roadmap, step, user) 조합이면 기존 스레드를 반환한다."""
    user_id, roadmap_id, step_id = await _get_test_user_and_roadmap()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        thread1 = await repo.get_or_create_thread(
            roadmap_id=roadmap_id,
            step_id=step_id,
            user_id=user_id,
        )
        await session.commit()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        thread2 = await repo.get_or_create_thread(
            roadmap_id=roadmap_id,
            step_id=step_id,
            user_id=user_id,
        )
        await session.commit()

    assert thread1.id == thread2.id


# ---------------------------------------------------------------------------
# get_thread
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_thread_found():
    """존재하는 스레드 ID로 조회 시 반환한다."""
    user_id, roadmap_id, step_id = await _get_test_user_and_roadmap()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        created = await repo.get_or_create_thread(
            roadmap_id=roadmap_id,
            step_id=step_id,
            user_id=user_id,
        )
        await session.commit()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        found = await repo.get_thread(created.id)

    assert found is not None
    assert found.id == created.id


@pytest.mark.asyncio
async def test_get_thread_not_found():
    """존재하지 않는 ID로 조회 시 None을 반환한다."""
    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        result = await repo.get_thread(uuid4())

    assert result is None


# ---------------------------------------------------------------------------
# add_message + get_recent_messages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_message_and_get_recent():
    """메시지 추가 후 최근 메시지 조회 확인."""
    user_id, roadmap_id, step_id = await _get_test_user_and_roadmap()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        thread = await repo.get_or_create_thread(
            roadmap_id=roadmap_id,
            step_id=step_id,
            user_id=user_id,
        )

        msg1 = await repo.add_message(
            thread_id=thread.id,
            role="user",
            content="영업신고 어떻게 해요?",
        )
        msg2 = await repo.add_message(
            thread_id=thread.id,
            role="assistant",
            content="영업신고는 관할 구청에 신청합니다.",
            sources_json={"sources": [{"type": "legal_basis", "title": "식품위생법"}]},
            token_count=25,
        )
        await session.commit()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        messages = await repo.get_recent_messages(thread.id, limit=10)

    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert messages[1].sources_json is not None
    assert messages[1].token_count == 25


@pytest.mark.asyncio
async def test_add_message_increments_thread_count():
    """메시지 추가 시 스레드 message_count가 증가한다."""
    user_id, roadmap_id, step_id = await _get_test_user_and_roadmap()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        thread = await repo.get_or_create_thread(
            roadmap_id=roadmap_id,
            step_id=step_id,
            user_id=user_id,
        )
        await repo.add_message(
            thread_id=thread.id, role="user", content="질문 1"
        )
        await repo.add_message(
            thread_id=thread.id, role="assistant", content="답변 1"
        )
        await session.commit()
        await session.refresh(thread)

    assert thread.message_count == 2


# ---------------------------------------------------------------------------
# get_recent_messages — limit 동작
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_recent_messages_respects_limit():
    """limit 파라미터가 메시지 수를 제한한다."""
    user_id, roadmap_id, step_id = await _get_test_user_and_roadmap()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        thread = await repo.get_or_create_thread(
            roadmap_id=roadmap_id,
            step_id=step_id,
            user_id=user_id,
        )
        for i in range(5):
            await repo.add_message(
                thread_id=thread.id, role="user", content=f"메시지 {i}"
            )
        await session.commit()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        messages = await repo.get_recent_messages(thread.id, limit=3)

    assert len(messages) == 3
    # 가장 최근 3개가 시간순 정렬로 반환
    assert messages[0].content == "메시지 2"
    assert messages[2].content == "메시지 4"


# ---------------------------------------------------------------------------
# count_messages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_messages():
    """스레드 내 메시지 수를 정확히 반환한다."""
    user_id, roadmap_id, step_id = await _get_test_user_and_roadmap()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        thread = await repo.get_or_create_thread(
            roadmap_id=roadmap_id,
            step_id=step_id,
            user_id=user_id,
        )
        for i in range(3):
            await repo.add_message(
                thread_id=thread.id, role="user", content=f"msg {i}"
            )
        await session.commit()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        count = await repo.count_messages(thread.id)

    assert count == 3


# ---------------------------------------------------------------------------
# list_threads
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_threads():
    """특정 로드맵 단계의 스레드 목록을 반환한다."""
    user_id, roadmap_id, step_id = await _get_test_user_and_roadmap()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        await repo.get_or_create_thread(
            roadmap_id=roadmap_id,
            step_id=step_id,
            user_id=user_id,
        )
        await session.commit()

    async with db.async_session() as session:
        repo = RoadmapChatRepository(session)
        threads = await repo.list_threads(roadmap_id, step_id)

    assert len(threads) >= 1
    assert all(t.roadmap_id == roadmap_id for t in threads)
    assert all(t.step_id == step_id for t in threads)
