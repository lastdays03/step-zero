from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.models.audit_log import AuditLogRead
from app.features.ops.application.audit_logs.service import list_audit_logs

router = APIRouter(prefix="/audit-logs")


@router.get(
    "",
    summary="운영 감사로그 목록 조회",
    description="운영자 조치 이력 목록을 조회합니다.",
    response_model=List[AuditLogRead],
)
async def get_audit_logs(
    session: AsyncSession = Depends(get_session)
) -> List[AuditLogRead]:
    return await list_audit_logs(session)
