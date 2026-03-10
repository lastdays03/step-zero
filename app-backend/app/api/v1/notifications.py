import asyncio
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, or_, select

from app.api.deps import get_current_user
from app.core.db import get_session
from app.core.exceptions import NotificationNotFoundError
from app.models.announcement import Announcement
from app.models.notification import Notification, NotificationRead
from app.models.user import AuthenticatedUser
from app.services.notification_pubsub import subscribe_notifications

router = APIRouter()


@router.get(
    "/stream",
    summary="알림 SSE 스트림",
    description="Server-Sent Events로 실시간 알림을 수신합니다.",
    response_description="text/event-stream SSE 응답",
)
async def notification_stream(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> StreamingResponse:
    async def _event_generator():
        # Send initial heartbeat
        yield "data: {\"type\": \"connected\"}\n\n"
        try:
            async for message in subscribe_notifications(current_user.id):
                yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            return

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("", response_model=List[NotificationRead])
async def list_notifications(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """현재 사용자의 알림 목록을 최신순으로 조회합니다.
    7일 이내의 알림만 노출하며, 삭제된 알림은 제외합니다.
    공지사항의 경우 'published' 상태인 것만 노출합니다.
    """
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
    query = (
        select(Notification)
        .outerjoin(Announcement, Notification.resource_id == Announcement.id)
        .where(Notification.user_id == current_user.id)
        .where(Notification.is_deleted == False)
        .where(Notification.created_at >= cutoff)
        .where(
            or_(Notification.type != "announcement", Announcement.status == "published")
        )
        .order_by(desc(Notification.created_at))
        .limit(100)
    )
    result = await session.execute(query)
    return result.scalars().all()


@router.post("/read-all")
async def mark_all_as_read(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """현재 사용자의 모든 알림을 읽음 처리합니다."""
    query = select(Notification).where(
        Notification.user_id == current_user.id, Notification.is_read == False
    )
    result = await session.execute(query)
    unread_notifications = result.scalars().all()

    for notification in unread_notifications:
        notification.is_read = True
        session.add(notification)

    await session.commit()
    return {"status": "success"}


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """특정 알림을 읽음 처리합니다."""
    notification = await session.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise NotificationNotFoundError()

    notification.is_read = True
    session.add(notification)
    await session.commit()
    return {"status": "success"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """특정 알림을 삭제(숨김) 처리합니다."""
    notification = await session.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise NotificationNotFoundError()

    notification.is_deleted = True
    session.add(notification)
    await session.commit()
    return {"status": "success"}
