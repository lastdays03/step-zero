from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.features.ops.application.audit_logs import AuditLogList, list_audit_logs


router = APIRouter(prefix="/audit-logs")


@router.get(
    "",
    summary="운영 감사로그 목록 조회",
    description="운영자 조치 이력 목록을 조회합니다.",
    response_description="운영 감사로그 목록을 반환합니다.",
)
async def get_audit_logs(
    actor: int | None = Query(default=None, description="운영자 ID"),
    action: str | None = Query(default=None, description="액션 코드"),
    target_type: str | None = Query(default=None, description="대상 타입"),
    from_at: datetime | None = Query(default=None, alias="from", description="시작 시각(ISO8601)"),
    to_at: datetime | None = Query(default=None, alias="to", description="종료 시각(ISO8601)"),
    page: int = Query(default=1, ge=1, description="페이지 번호(1-base)"),
    size: int = Query(default=20, ge=1, le=200, description="페이지 크기"),
    session: AsyncSession = Depends(get_session),
) -> AuditLogList:
    return await list_audit_logs(
        session,
        actor=actor,
        action=action,
        target_type=target_type,
        from_at=from_at,
        to_at=to_at,
        page=page,
        size=size,
    )
