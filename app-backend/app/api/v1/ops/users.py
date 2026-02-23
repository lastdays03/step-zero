from typing import Any
from fastapi import APIRouter, Depends, Query, HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.db import get_session
from app.api.deps import AuthenticatedUser, get_current_user
from app.features.ops.application.users import (
    OpsUserRead, 
    DisciplineHistoryRead,
    list_users, 
    update_user_status, 
    bulk_update_user_status,
    get_user_discipline_history
)

router = APIRouter(prefix="/users")


class UserStatusUpdateRequest(BaseModel):
    status: str
    reason: str


class BulkStatusUpdateRequest(BaseModel):
    user_ids: list[int]
    status: str
    reason: str


@router.get(
    "",
    response_model=list[OpsUserRead],
    summary="운영 사용자 목록 조회",
    description="사용자 목록을 조회합니다. 이메일/이름 검색 및 상태 필터링을 지원합니다.",
    response_description="운영 사용자 목록을 반환합니다.",
)
async def list_ops_users(
    search: str | None = Query(default=None, description="이메일 또는 이름 검색어"),
    status: str | None = Query(default=None, description="계정 상태 (active, suspended 등)"),
    offset: int = Query(default=0, ge=0, description="조회 시작 오프셋"),
    limit: int = Query(default=50, ge=1, le=200, description="조회 개수"),
    session: AsyncSession = Depends(get_session),
) -> list[OpsUserRead]:
    return await list_users(session, search=search, status=status, offset=offset, limit=limit)


@router.patch(
    "/bulk-status",
    summary="사용자 일괄 상태 변경",
    description="여러 명의 사용자 상태를 한꺼번에 변경합니다.",
)
async def bulk_update_ops_users_status(
    request: BulkStatusUpdateRequest,
    current_admin: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    count = await bulk_update_user_status(
        session,
        admin_id=current_admin.id,
        user_ids=request.user_ids,
        status=request.status,
        reason=request.reason,
    )
    return {"updated_count": count}


@router.patch(
    "/{user_id}/status",
    response_model=OpsUserRead,
    summary="사용자 상태 변경",
    description="운영자가 사용자의 계정 상태(활성/정지 등)를 변경합니다.",
)
async def update_ops_user_status(
    user_id: int,
    request: UserStatusUpdateRequest,
    current_admin: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OpsUserRead:
    user = await update_user_status(
        session,
        admin_id=current_admin.id,
        user_id=user_id,
        status=request.status,
        reason=request.reason,
    )
    
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
        
    return OpsUserRead.model_validate(user, from_attributes=True)


@router.get(
    "/{user_id}/history",
    response_model=list[DisciplineHistoryRead],
    summary="사용자 징계 이력 조회",
    description="특정 사용자의 과거 징계 및 상태 변경 기록을 조회합니다.",
)
async def list_ops_user_history(
    user_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[DisciplineHistoryRead]:
    return await get_user_discipline_history(session, user_id=user_id)
