from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import func

from app.models.admin_audit_log import AdminAuditLog


class AuditLogItem(BaseModel):
    id: int
    admin_id: int
    action: str
    target_type: str
    target_id: str | None
    reason: str | None
    meta: dict[str, Any]
    created_at: datetime


class AuditLogList(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    size: int


async def record_admin_audit_log(
    session: AsyncSession,
    *,
    admin_id: int,
    action: str,
    target_type: str,
    target_id: str | None = None,
    reason: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AdminAuditLog:
    row = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        meta_json=meta or {},
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row


async def list_audit_logs(
    session: AsyncSession,
    *,
    actor: int | None = None,
    action: str | None = None,
    target_type: str | None = None,
    from_at: datetime | None = None,
    to_at: datetime | None = None,
    page: int = 1,
    size: int = 20,
) -> AuditLogList:
    filters = []
    if actor is not None:
        filters.append(AdminAuditLog.admin_id == actor)
    if action:
        filters.append(AdminAuditLog.action == action)
    if target_type:
        filters.append(AdminAuditLog.target_type == target_type)
    if from_at:
        filters.append(AdminAuditLog.created_at >= from_at)
    if to_at:
        filters.append(AdminAuditLog.created_at <= to_at)

    total_stmt = select(func.count()).select_from(AdminAuditLog)
    if filters:
        total_stmt = total_stmt.where(*filters)
    total = int((await session.execute(total_stmt)).scalar_one())

    offset = (page - 1) * size
    data_stmt = (
        select(AdminAuditLog)
        .where(*filters) if filters else select(AdminAuditLog)
    )
    data_stmt = (
        data_stmt
        .order_by(AdminAuditLog.created_at.desc(), AdminAuditLog.id.desc())
        .offset(offset)
        .limit(size)
    )
    rows = (await session.execute(data_stmt)).scalars().all()

    items = [
        AuditLogItem(
            id=row.id or 0,
            admin_id=row.admin_id,
            action=row.action,
            target_type=row.target_type,
            target_id=row.target_id,
            reason=row.reason,
            meta=row.meta_json,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return AuditLogList(items=items, total=total, page=page, size=size)
