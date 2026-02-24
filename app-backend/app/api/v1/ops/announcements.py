from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api import deps
from app.features.ops.application.announcements.service import AnnouncementService
from app.features.ops.application.announcements.schemas import (
    OpsAnnouncementCreate,
    OpsAnnouncementUpdate,
    OpsAnnouncementList,
    OpsAnnouncementRead
)
from app.models.user import AuthenticatedUser

router = APIRouter(prefix="/announcements")

@router.get(
    "",
    summary="운영 공지 목록 조회",
    response_model=OpsAnnouncementList,
)
async def get_announcements(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    session: AsyncSession = Depends(deps.get_session)
):
    service = AnnouncementService(session)
    return await service.list_announcements(skip=skip, limit=limit, status=status)

@router.post(
    "",
    summary="운영 공지 작성",
    response_model=OpsAnnouncementRead,
)
async def create_announcement(
    data: OpsAnnouncementCreate,
    current_admin: AuthenticatedUser = Depends(deps.require_platform_admin),
    session: AsyncSession = Depends(deps.get_session)
):
    service = AnnouncementService(session)
    return await service.create_announcement(admin_id=current_admin.id, data=data)

@router.patch(
    "/{announcement_id}",
    summary="운영 공지 수정 및 상태 변경",
    response_model=OpsAnnouncementRead,
)
async def update_announcement(
    announcement_id: int,
    data: OpsAnnouncementUpdate,
    current_admin: AuthenticatedUser = Depends(deps.require_platform_admin),
    session: AsyncSession = Depends(deps.get_session)
):
    service = AnnouncementService(session)
    try:
        return await service.update_announcement(
            admin_id=current_admin.id, 
            announcement_id=announcement_id, 
            data=data
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete(
    "/{announcement_id}",
    summary="운영 공지 삭제",
)
async def delete_announcement(
    announcement_id: int,
    current_admin: AuthenticatedUser = Depends(deps.require_platform_admin),
    session: AsyncSession = Depends(deps.get_session)
):
    service = AnnouncementService(session)
    try:
        await service.delete_announcement(
            admin_id=current_admin.id, 
            announcement_id=announcement_id
        )
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
