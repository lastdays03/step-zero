from typing import List

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import desc, select

from app.core.db import get_session
from app.core.exceptions import AnnouncementNotFoundError
from app.features.ops.application.announcements.service import AnnouncementItem
from app.models.announcement import Announcement

router = APIRouter()


@router.get(
    "",
    response_model=List[AnnouncementItem],
    summary="공지사항 목록 조회",
    description="게시 중인 모든 공지사항을 최신순으로 조회합니다.",
)
async def list_published_announcements(
    session: AsyncSession = Depends(get_session),
) -> List[AnnouncementItem]:
    query = (
        select(Announcement)
        .where(Announcement.status == "published")
        .order_by(desc(Announcement.published_at), desc(Announcement.id))
    )
    result = await session.execute(query)
    rows = result.scalars().all()
    return [AnnouncementItem.model_validate(row, from_attributes=True) for row in rows]


@router.get(
    "/{announcement_id}",
    response_model=AnnouncementItem,
    summary="공지사항 상세 조회",
    description="특정 공지사항의 상세 내용을 조회합니다.",
)
async def get_published_announcement(
    announcement_id: int = Path(..., description="조회할 공지 ID"),
    session: AsyncSession = Depends(get_session),
) -> AnnouncementItem:
    row = await session.get(Announcement, announcement_id)
    if not row or row.status != "published":
        raise AnnouncementNotFoundError()

    return AnnouncementItem.model_validate(row, from_attributes=True)
