from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api import deps
from app.core.db import get_session
from app.features.ops.application.audit_logs import record_admin_audit_log
from app.features.ops.application.actionkit import get_summary
from app.models.actionkit import ActionKitItem
from app.models.user import AuthenticatedUser

router = APIRouter(prefix="/actionkit")


@router.get(
    "/summary",
    summary="액션키트 운영 요약 조회",
    description="액션키트 운영 화면에서 사용하는 기본 요약을 조회합니다.",
    response_description="액션키트 운영 요약을 반환합니다.",
)
async def get_actionkit_summary() -> dict[str, int]:
    return get_summary()


class OpsActionKitItemStatusUpdateRequest(BaseModel):
    is_active: bool
    reason: str | None = None


@router.patch(
    "/items/{item_id}/status",
    summary="운영 액션키트 아이템 상태 변경",
    description="액션키트 아이템 활성/비활성 상태를 변경하고 감사로그를 남깁니다.",
    response_description="변경 결과를 반환합니다.",
)
async def update_actionkit_item_status(
    payload: OpsActionKitItemStatusUpdateRequest,
    item_id: int = Path(description="상태를 변경할 아이템 ID"),
    session: AsyncSession = Depends(get_session),
    admin_user: AuthenticatedUser = Depends(deps.get_current_user),
) -> dict[str, object]:
    stmt = select(ActionKitItem).where(ActionKitItem.id == item_id)
    item = (await session.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="ActionKit item not found")

    before_is_active = bool(item.is_active)
    after_is_active = bool(payload.is_active)
    if before_is_active == after_is_active:
        return {"status": "no_change", "item_id": item.id, "is_active": before_is_active}

    item.is_active = after_is_active
    item.updated_at = datetime.now(timezone.utc)
    session.add(item)

    await record_admin_audit_log(
        session,
        admin_id=admin_user.id,
        action="actionkit.item.status.updated",
        target_type="actionkit_item",
        target_id=str(item.id),
        reason=payload.reason,
        meta={"before": {"is_active": before_is_active}, "after": {"is_active": after_is_active}},
    )
    await session.commit()

    return {"status": "success", "item_id": item.id, "is_active": item.is_active}
