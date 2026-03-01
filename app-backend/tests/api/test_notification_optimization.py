from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.api.v1.notifications import delete_notification, list_notifications
from app.core import db
from app.features.ops.application.announcements.service import (
    create_announcement,
    update_announcement_status,
)
from app.models.notification import Notification
from app.models.user import User

from .test_announcement_notifications import _get_admin_user


@pytest.mark.asyncio
async def test_notification_age_filtering(client: AsyncClient):
    """7일이 지난 알림은 조회되지 않는지 확인합니다."""
    async with db.async_session() as session:
        admin = await _get_admin_user(session)

        # 1. 오래된 알림 생성 (8일 전)
        old_time = datetime.utcnow() - timedelta(days=8)
        old_notif = Notification(
            user_id=admin.id, content="오래된 알림", type="notice", created_at=old_time
        )

        # 2. 최신 알림 생성
        new_notif = Notification(
            user_id=admin.id,
            content="최신 알림",
            type="notice",
            created_at=datetime.utcnow(),
        )

        session.add(old_notif)
        session.add(new_notif)
        await session.commit()
        await session.refresh(admin)  # Refresh admin to ensure it's still bound

        # 3. 목록 조회 logic 확인 (API router 함수 직접 호출)
        result = await list_notifications(current_user=admin, session=session)

        contents = [n.content for n in result]
        assert "최신 알림" in contents
        assert "오래된 알림" not in contents


@pytest.mark.asyncio
async def test_notification_individual_deletion(client: AsyncClient):
    """알림 개별 삭제가 정상 작동하는지 확인합니다."""
    async with db.async_session() as session:
        admin = await _get_admin_user(session)

        notif = Notification(user_id=admin.id, content="삭제할 알림", type="notice")
        session.add(notif)
        await session.commit()
        await session.refresh(notif)
        await session.refresh(admin)

        # 삭제 전 확인
        exists = await session.get(Notification, notif.id)
        assert exists is not None

        # 4. 삭제 호출
        await delete_notification(
            notification_id=notif.id, current_user=admin, session=session
        )

        # 삭제 후 확인 (soft-delete이므로 is_deleted=True 확인)
        async with db.async_session() as session2:
            deleted = await session2.get(Notification, notif.id)
            assert deleted is not None
            assert deleted.is_deleted is True
