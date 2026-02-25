from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.models.announcement import Announcement
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/announcements", tags=["announcements"])

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    published_at: datetime | None

@router.get(
    "",
    response_model=List[AnnouncementResponse],
    summary="Get public announcements",
    description="Retrieve a list of published announcements.",
)
async def get_public_announcements(
    session: AsyncSession = Depends(get_session),
) -> List[AnnouncementResponse]:
    # only return published
    stmt = (
        select(Announcement)
        .where(Announcement.status == "published")
        .order_by(Announcement.published_at.desc())
        .limit(20)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()
    
    return [
        AnnouncementResponse(
            id=r.id,
            title=r.title,
            content=r.content,
            published_at=r.published_at,
        ) for r in rows
    ]

@router.get(
    "/{announcement_id}",
    response_model=AnnouncementResponse,
    summary="Get an announcement by ID",
)
async def get_public_announcement(
    announcement_id: int = Path(...),
    session: AsyncSession = Depends(get_session),
) -> AnnouncementResponse:
    stmt = select(Announcement).where(
        Announcement.id == announcement_id,
        Announcement.status == "published"
    )
    result = await session.execute(stmt)
    announcement = result.scalar_one_or_none()
    
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
        
    return AnnouncementResponse(
        id=announcement.id,
        title=announcement.title,
        content=announcement.content,
        published_at=announcement.published_at,
    )
