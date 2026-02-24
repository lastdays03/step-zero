from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.notification import Notification, NotificationRead
from app.models.user import AuthenticatedUser

router = APIRouter()

@router.get(
    "",
    response_model=List[NotificationRead],
    summary="알림 목록 조회",
    description="현재 사용자의 알림 목록을 최신순으로 조회합니다.",
)
async def list_notifications(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    result = await session.execute(query)
    notifications = list(result.scalars().all())
    return notifications


@router.put(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="알림 읽음 처리",
)
async def mark_notification_read(
    notification_id: int = Path(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    notification = await session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    notification.is_read = True
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return notification


@router.put(
    "/read-all",
    summary="모든 알림 읽음 처리",
)
async def mark_all_notifications_read(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    query = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    result = await session.execute(query)
    notifications = result.scalars().all()
    
    for notification in notifications:
        notification.is_read = True
        session.add(notification)
        
    await session.commit()
    return {"status": "success"}
