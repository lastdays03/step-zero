from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.audit_log import AuditLog, AuditLogRead


async def save_audit_log(
    session: AsyncSession,
    user_id: int,
    action: str,
    target_type: str,
    target_id: str,
    target_author: Optional[str] = None,
    details: Optional[str] = None,
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_author=target_author,
        details=details,
    )
    session.add(log)
    # Note: We don't commit here, usually called within another transaction


async def list_audit_logs(
    session: AsyncSession,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    keyword: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLogRead]:
    conditions = []

    if action:
        conditions.append(AuditLog.action == action)
    if target_type:
        conditions.append(AuditLog.target_type == target_type)
    if keyword:
        kw = f"%{keyword}%"
        from sqlalchemy import or_
        conditions.append(
            or_(
                AuditLog.target_author.ilike(kw),
                AuditLog.details.ilike(kw),
                AuditLog.target_id.ilike(kw),
            )
        )
    if date_from:
        conditions.append(AuditLog.created_at >= date_from)
    if date_to:
        conditions.append(AuditLog.created_at <= date_to)

    query = (
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .where(and_(*conditions) if conditions else True)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(query)
    logs = result.scalars().all()

    return [
        AuditLogRead(
            id=log.id,
            user_id=log.user_id,
            actor_name=log.user.full_name or log.user.email,
            action=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            target_author=log.target_author,
            details=log.details,
            created_at=log.created_at,
        )
        for log in logs
    ]
