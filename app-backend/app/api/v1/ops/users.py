from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.db import get_session
from app.core.exceptions import UserNotFoundError
from app.features.ops.application.audit_logs import (
    AuditAction,
    AuditTargetType,
    record_admin_audit_log,
)
from app.features.ops.application.users import (
    BulkStatusUpdateRequest,
    DisciplineHistoryRead,
    OpsUserRead,
    UserStatusUpdateRequest,
    bulk_update_user_status,
    get_user_discipline_history,
    list_users,
    update_user_status,
)
from app.models.user import AuthenticatedUser

router = APIRouter(prefix="/users")


@router.get(
    "",
    response_model=list[OpsUserRead],
    summary="운영 사용자 목록 조회",
    description="사용자 목록을 조회합니다. 이메일/이름 검색 및 상태 필터링을 지원합니다.",
    response_description="운영 사용자 목록을 반환합니다.",
)
async def list_ops_users(
    search: str | None = Query(default=None, description="이메일 또는 이름 검색어"),
    status: str | None = Query(
        default=None, description="계정 상태 (active, suspended 등)"
    ),
    offset: int = Query(default=0, ge=0, description="조회 시작 오프셋"),
    limit: int = Query(default=50, ge=1, le=200, description="조회 개수"),
    session: AsyncSession = Depends(get_session),
) -> list[OpsUserRead]:
    return await list_users(
        session, search=search, status=status, offset=offset, limit=limit
    )


@router.patch(
    "/bulk-status",
    summary="사용자 일괄 상태 변경",
    description="여러 명의 사용자 상태를 한꺼번에 변경하고 감사로그를 남깁니다.",
)
async def bulk_update_ops_users_status(
    request: BulkStatusUpdateRequest,
    current_admin: AuthenticatedUser = Depends(deps.get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    count = await bulk_update_user_status(
        session,
        admin_id=current_admin.id,
        user_ids=request.user_ids,
        status=request.status,
        reason=request.reason,
        duration_days=request.duration_days,
    )

    await record_admin_audit_log(
        session,
        admin_id=current_admin.id,
        action=AuditAction.USER_BULK_STATUS_UPDATED,
        target_type=AuditTargetType.USER,
        target_id=None,
        reason=request.reason,
        meta={
            "user_ids": request.user_ids,
            "status": request.status,
            "duration_days": request.duration_days,
            "updated_count": count,
        },
    )
    await session.commit()

    return {"updated_count": count}


@router.patch(
    "/{user_id}/status",
    response_model=OpsUserRead,
    summary="사용자 상태 변경",
    description="운영자가 사용자의 계정 상태(활성/정지 등)를 변경하고 감사로그를 남깁니다.",
)
async def update_ops_user_status(
    user_id: int,
    request: UserStatusUpdateRequest,
    current_admin: AuthenticatedUser = Depends(deps.get_current_user),
    session: AsyncSession = Depends(get_session),
) -> OpsUserRead:
    result = await update_user_status(
        session,
        admin_id=current_admin.id,
        user_id=user_id,
        status=request.status,
        reason=request.reason,
        duration_days=request.duration_days,
    )

    if not result:
        raise UserNotFoundError()

    user, prev_status = result

    await record_admin_audit_log(
        session,
        admin_id=current_admin.id,
        action=AuditAction.USER_STATUS_UPDATED,
        target_type=AuditTargetType.USER,
        target_id=str(user.id),
        reason=request.reason,
        meta={
            "prev_status": prev_status,
            "new_status": user.status,
            "duration_days": request.duration_days,
        },
    )
    await session.commit()

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
