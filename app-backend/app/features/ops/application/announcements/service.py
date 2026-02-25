from datetime import datetime
from typing import Literal

from pydantic import BaseModel
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.announcement import Announcement


AnnouncementStatus = Literal["draft", "published", "archived"]


class AnnouncementItem(BaseModel):
    id: int
    title: str
    content: str
    status: AnnouncementStatus
    created_by: int
    updated_by: int
    created_at: datetime
    published_at: datetime | None = None
    updated_at: datetime


class AnnouncementList(BaseModel):
    items: list[AnnouncementItem]


class AnnouncementCreate(BaseModel):
    title: str
    content: str


class AnnouncementUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


async def list_announcements(session: AsyncSession) -> AnnouncementList:
    rows = (
        await session.execute(
            select(Announcement).order_by(Announcement.created_at.desc(), Announcement.id.desc())
        )
    ).scalars().all()
    return AnnouncementList(items=[AnnouncementItem.model_validate(row, from_attributes=True) for row in rows])


async def create_announcement(
    session: AsyncSession,
    *,
    title: str,
    content: str,
    actor_id: int,
) -> Announcement:
    row = Announcement(
        title=title,
        content=content,
        status="draft",
        created_by=actor_id,
        updated_by=actor_id,
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row


async def update_announcement(
    session: AsyncSession,
    *,
    announcement_id: int,
    title: str | None,
    content: str | None,
    actor_id: int,
) -> Announcement | None:
    row = (await session.execute(select(Announcement).where(Announcement.id == announcement_id))).scalar_one_or_none()
    if not row:
        return None

    if title is not None:
        row.title = title
    if content is not None:
        row.content = content
    row.updated_by = actor_id
    row.updated_at = datetime.utcnow()
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row


async def update_announcement_status(
    session: AsyncSession,
    *,
    announcement_id: int,
    status: AnnouncementStatus,
    actor_id: int,
) -> Announcement | None:
    row = (await session.execute(select(Announcement).where(Announcement.id == announcement_id))).scalar_one_or_none()
    if not row:
        return None

    old_status = row.status
    row.status = status
    if status == "published" and row.published_at is None:
        row.published_at = datetime.utcnow()
    row.updated_by = actor_id
    row.updated_at = datetime.utcnow()
    session.add(row)
    await session.flush()
    await session.refresh(row)

    # Trigger notifications when status changes to 'published'
    if status == "published" and old_status != "published":
        from app.models.notification import Notification
        from app.models.user import User

        # Fetch all active users
        user_query = select(User.id).where(User.status == "active")
        user_result = await session.execute(user_query)
        user_ids = user_result.scalars().all()

        # Create notifications for all active users
        notifications = [
            Notification(
                user_id=uid,
                content=f"[공지] {row.title}",
                type="notice",
                link=f"/announcements/{row.id}"
            )
            for uid in user_ids
        ]
        session.add_all(notifications)
        await session.flush()

    # Delete notifications when status changes to 'archived'
    if status == "archived" and old_status != "archived":
        from app.models.notification import Notification

        # Delete all notifications linked to this announcement
        delete_query = (
            sa.delete(Notification)
            .where(Notification.link == f"/announcements/{row.id}")
        )
        await session.execute(delete_query)
        await session.flush()

    return row
