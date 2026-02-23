from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.notification import Notification, NotificationRead
from app.models.user import AuthenticatedUser

router = APIRouter()

@router.get("", response_model=List[NotificationRead])
async def list_notifications(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """현재 사용자의 알림 목록을 최신순으로 조회합니다."""
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(desc(Notification.created_at))
        .limit(50)
    )
    result = await session.execute(query)
    return result.scalars().all()

@router.post("/read-all")
async def mark_all_as_read(
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """현재 사용자의 모든 알림을 읽음 처리합니다."""
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read == False)
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
    session: AsyncSession = Depends(get_session)
):
    """특정 알림을 읽음 처리합니다."""
    notification = await session.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    session.add(notification)
    await session.commit()
    return {"status": "success"}
