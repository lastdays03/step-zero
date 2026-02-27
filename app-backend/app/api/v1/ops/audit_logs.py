from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select
from datetime import datetime

from app.core.db import get_session
from app.models.audit_log import AuditLog, AuditLogRead
from app.models.admin_audit_log import AdminAuditLog
from app.models.user import User
from app.features.ops.application.audit_logs.service import list_ops_audit_logs, list_audit_logs, AuditLogList

router = APIRouter(prefix="/audit-logs")


@router.get(
    "",
    summary="운영 감사로그 목록 조회",
    description="운영자 조치 이력 목록을 조회합니다. 필터, 페이지네이션, 검색 지원.",
)
async def get_audit_logs(
    action: Optional[str] = Query(None, description="액션 타입 필터"),
    target_type: Optional[str] = Query(None, description="대상 타입 필터"),
    keyword: Optional[str] = Query(None, description="세부 내용, 대상자 검색"),
    date_from: Optional[datetime] = Query(None, alias="from", description="시작 날짜 (ISO)"),
    date_to: Optional[datetime] = Query(None, alias="to", description="종료 날짜 (ISO)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=500, description="페이지 사이즈"),
    limit: Optional[int] = Query(None, ge=1, le=500, description="최대 조회 건수 (page/size 대신 사용)"),
    offset: Optional[int] = Query(None, ge=0, description="오프셋 (page/size 대신 사용)"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    # page/size 기반 AdminAuditLog 조회
    admin_result: AuditLogList = await list_audit_logs(
        session,
        actor=None,
        action=action,
        target_type=target_type,
        from_at=date_from,
        to_at=date_to,
        page=page,
        size=size,
    )

    # AuditLog (운영 감사로그) 조회
    effective_limit = limit or size
    effective_offset = offset if offset is not None else (page - 1) * size
    ops_rows: list[AuditLog] = await list_ops_audit_logs(
        session,
        action=action,
        target_type=target_type,
        keyword=keyword,
        date_from=date_from,
        date_to=date_to,
        limit=effective_limit,
        offset=effective_offset,
    )

    # 두 소스를 통합하여 반환
    items: list[dict[str, Any]] = []

    # AdminAuditLog 항목 변환
    for item in admin_result.items:
        items.append({
            "id": item.id,
            "admin_id": item.admin_id,
            "action": item.action,
            "target_type": item.target_type,
            "target_id": item.target_id,
            "reason": item.reason,
            "meta": item.meta,
            "created_at": item.created_at.isoformat(),
        })

    # AuditLog 항목 변환
    for row in ops_rows:
        items.append({
            "id": row.id or 0,
            "admin_id": row.user_id,
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "reason": row.details,
            "meta": {"target_author": row.target_author} if row.target_author else {},
            "created_at": row.created_at.isoformat() if row.created_at else None,
        })

    # 시간순 정렬 (최신 우선)
    items.sort(key=lambda x: x.get("created_at", "") or "", reverse=True)

    return {
        "items": items,
        "total": admin_result.total + len(ops_rows),
        "page": page,
        "size": size,
    }
