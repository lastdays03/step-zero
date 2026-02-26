from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.db import get_session
from app.models.audit_log import AuditLogRead
from app.features.ops.application.audit_logs.service import list_audit_logs

router = APIRouter(prefix="/audit-logs")


@router.get(
    "",
    summary="운영 감사로그 목록 조회",
    description="운영자 조치 이력 목록을 조회합니다. 필터, 페이지네이션, 검색 지원.",
    response_model=List[AuditLogRead],
)
async def get_audit_logs(
    action: Optional[str] = Query(None, description="액션 타입 필터 (e.g. ops.user.suspend)"),
    target_type: Optional[str] = Query(None, description="대상 타입 필터 (post, comment, user)"),
    keyword: Optional[str] = Query(None, description="세부 내용, 대상자 검색"),
    date_from: Optional[datetime] = Query(None, description="시작 날짜 (ISO)"),
    date_to: Optional[datetime] = Query(None, description="종료 날짜 (ISO)"),
    limit: int = Query(100, ge=1, le=500, description="최대 조회 건수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    session: AsyncSession = Depends(get_session),
) -> List[AuditLogRead]:
    return await list_audit_logs(
        session,
        action=action,
        target_type=target_type,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
