from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api import deps
from app.core.db import get_session
from app.features.ops.application.audit_logs import record_admin_audit_log
from app.features.ops.application.users import OpsUserRead, list_users
from app.models.user import AuthenticatedUser, User

router = APIRouter(prefix="/users")


class OpsUserStatusUpdateRequest(BaseModel):
    is_active: bool
    reason: str | None = None


@router.get(
    "",
    response_model=list[OpsUserRead],
    summary="운영 사용자 목록 조회",
    description="최근 생성된 사용자 목록(최대 50건)을 운영자 화면용으로 조회합니다.",
    response_description="운영 사용자 목록을 반환합니다.",
)
async def list_ops_users(
    offset: int = Query(default=0, ge=0, description="조회 시작 오프셋"),
    limit: int = Query(default=50, ge=1, le=200, description="조회 개수"),
    session: AsyncSession = Depends(get_session),
) -> list[OpsUserRead]:
    return await list_users(session, offset=offset, limit=limit)


@router.patch(
    "/{user_id}/status",
    summary="운영 사용자 상태 변경",
    description="사용자 활성/비활성 상태를 변경하고 감사로그를 남깁니다.",
    response_description="변경 결과와 최신 상태를 반환합니다.",
)
async def update_ops_user_status(
    payload: OpsUserStatusUpdateRequest,
    user_id: int = Path(description="상태를 변경할 사용자 ID"),
    session: AsyncSession = Depends(get_session),
    admin_user: AuthenticatedUser = Depends(deps.get_current_user),
) -> dict[str, object]:
    stmt = select(User).where(User.id == user_id)
    user = (await session.execute(stmt)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    before_is_active = bool(user.is_active)
    after_is_active = bool(payload.is_active)
    if before_is_active == after_is_active:
        return {
            "status": "no_change",
            "user_id": user.id,
            "is_active": before_is_active,
        }

    user.is_active = after_is_active
    user.updated_at = datetime.now(timezone.utc)
    session.add(user)

    await record_admin_audit_log(
        session,
        admin_id=admin_user.id,
        action="user.status.updated",
        target_type="user",
        target_id=str(user.id),
        reason=payload.reason,
        meta={
            "before": {"is_active": before_is_active},
            "after": {"is_active": after_is_active},
        },
    )
    await session.commit()

    return {
        "status": "success",
        "user_id": user.id,
        "is_active": user.is_active,
    }
