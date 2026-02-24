from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.models.audit_log import AuditLog, AuditLogRead

async def save_audit_log(
    session: AsyncSession,
    user_id: int,
    action: str,
    target_type: str,
    target_id: str,
    details: Optional[str] = None
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    session.add(log)
    # Note: We don't commit here, usually called within another transaction

async def list_audit_logs(session: AsyncSession) -> list[AuditLogRead]:
    query = (
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .order_by(AuditLog.created_at.desc())
        .limit(100)
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
            details=log.details,
            created_at=log.created_at
        )
        for log in logs
    ]
