from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.db import get_session
from app.features.ops.application.files import OpsFilesService
from app.models.user import AuthenticatedUser

router = APIRouter(prefix="/files")


# ── Schemas ──────────────────────────────────────────


class OpsFileResponse(BaseModel):
    id: int
    owner_type: str
    owner_id: int
    category: str
    object_key: str
    original_filename: str | None
    mime_type: str | None
    size_bytes: int | None
    kind: str | None
    uploaded_at: str | None
    public_url: str


class OpsFileListResponse(BaseModel):
    data: list[OpsFileResponse]
    total: int
    page: int
    page_size: int


class OpsFileStatsGroupItem(BaseModel):
    owner_type: str | None = None
    mime_group: str | None = None
    count: int
    bytes: int


class OpsFileStatsResponse(BaseModel):
    total_files: int
    total_bytes: int
    by_owner_type: list[dict]
    by_mime_group: list[dict]


class OpsFileBatchDeleteRequest(BaseModel):
    ids: list[int]


class OpsFileBatchDeleteResponse(BaseModel):
    deleted: int
    failed: int


# ── Endpoints ────────────────────────────────────────


@router.get(
    "/",
    response_model=OpsFileListResponse,
    summary="파일 목록 조회",
)
async def list_files(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", pattern="^(created_at|uploaded_at|size_bytes|original_filename)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    owner_type: Optional[str] = Query(None),
    mime_group: Optional[str] = Query(None, pattern="^(image|document|other)$"),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = OpsFilesService(session)
    return await service.list_files(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        owner_type=owner_type,
        mime_group=mime_group,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )


@router.get(
    "/stats",
    response_model=OpsFileStatsResponse,
    summary="파일 사용량 통계",
)
async def get_file_stats(
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = OpsFilesService(session)
    return await service.get_stats()


@router.delete(
    "/batch",
    response_model=OpsFileBatchDeleteResponse,
    summary="파일 일괄 삭제",
)
async def delete_files_batch(
    body: OpsFileBatchDeleteRequest,
    session: AsyncSession = Depends(get_session),
    admin: AuthenticatedUser = Depends(deps.get_current_user),
) -> dict:
    service = OpsFilesService(session)
    result = await service.delete_files(body.ids, admin_id=admin.id)
    await session.commit()
    return result


@router.delete(
    "/{file_id}",
    summary="파일 단건 삭제",
    status_code=status.HTTP_200_OK,
)
async def delete_file(
    file_id: int,
    session: AsyncSession = Depends(get_session),
    admin: AuthenticatedUser = Depends(deps.get_current_user),
) -> dict:
    service = OpsFilesService(session)
    ok = await service.delete_file(file_id, admin_id=admin.id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없거나 삭제에 실패했습니다.",
        )
    await session.commit()
    return {"ok": True}
