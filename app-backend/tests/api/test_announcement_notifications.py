import pytest
from httpx import AsyncClient
from sqlmodel import desc, select

from app.core import db
from app.features.ops.application.announcements.service import (
    create_announcement,
    update_announcement_status,
)
from app.models.announcement import Announcement
from app.models.notification import Notification
from app.models.user import User


async def _get_admin_user(session):
    result = await session.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one()
    user.is_superuser = True
    user.is_active = True
    session.add(user)
    await session.commit()
    return user


@pytest.mark.asyncio
async def test_announcement_notification_trigger(client: AsyncClient):
    """공지사항 게시 시 모든 사용자에게 알림이 생성되는지 확인합니다."""
    async with db.async_session() as session:
        admin = await _get_admin_user(session)

        # 1. 공지사항 초안 생성
        announcement = await create_announcement(
            session, title="테스트 공지", content="테스트 내용", actor_id=admin.id
        )
        await session.commit()

        # 2. 상태를 'published'로 변경 -> 알림 트리거됨
        await update_announcement_status(
            session,
            announcement_id=announcement.id,
            status="published",
            actor_id=admin.id,
        )
        await session.commit()

        # 3. 알림 생성 확인
        notif_query = select(Notification).where(
            Notification.link == f"/announcements/{announcement.id}"
        )
        result = await session.execute(notif_query)
        notifications = result.scalars().all()

        assert len(notifications) >= 1
        assert notifications[0].content == f"[공지] 테스트 공지"
        assert notifications[0].type == "announcement"


@pytest.mark.asyncio
async def test_duplicate_publication_no_duplicate_notifications(client: AsyncClient):
    """이미 게시된 공지의 상태를 다시 'published'로 변경해도 알림이 중복 생성되지 않아야 합니다."""
    async with db.async_session() as session:
        admin = await _get_admin_user(session)

        # 1. 공지사항 생성 및 게시
        announcement = await create_announcement(
            session, title="중복 테스트", content="내용", actor_id=admin.id
        )
        await update_announcement_status(
            session,
            announcement_id=announcement.id,
            status="published",
            actor_id=admin.id,
        )
        await session.commit()

        # 알림 개수 확인
        result = await session.execute(
            select(Notification).where(
                Notification.link == f"/announcements/{announcement.id}"
            )
        )
        initial_count = len(result.scalars().all())

        # 2. 다시 'published'로 변경 (상태 유지)
        await update_announcement_status(
            session,
            announcement_id=announcement.id,
            status="published",
            actor_id=admin.id,
        )
        await session.commit()

        # 알림 개수 변화 없는지 확인
        result = await session.execute(
            select(Notification).where(
                Notification.link == f"/announcements/{announcement.id}"
            )
        )
        final_count = len(result.scalars().all())

        assert initial_count == final_count


@pytest.mark.asyncio
async def test_announcement_notification_deletion_on_archive(client: AsyncClient):
    """공지사항을 'archived' 상태로 변경하면 관련 알림이 삭제되는지 확인합니다."""
    async with db.async_session() as session:
        admin = await _get_admin_user(session)

        # 1. 공지사항 생성 및 게시
        announcement = await create_announcement(
            session, title="삭제 테스트", content="내용", actor_id=admin.id
        )
        await update_announcement_status(
            session,
            announcement_id=announcement.id,
            status="published",
            actor_id=admin.id,
        )
        await session.commit()

        # 알림 생성 확인
        result = await session.execute(
            select(Notification).where(
                Notification.link == f"/announcements/{announcement.id}"
            )
        )
        assert len(result.scalars().all()) >= 1

        # 2. 'archived'로 변경
        await update_announcement_status(
            session,
            announcement_id=announcement.id,
            status="archived",
            actor_id=admin.id,
        )
        await session.commit()

        # 알림 삭제 확인
        result = await session.execute(
            select(Notification).where(
                Notification.link == f"/announcements/{announcement.id}"
            )
        )
        assert len(result.scalars().all()) == 0
