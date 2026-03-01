from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.admin_audit_log import AdminAuditLog
from app.models.audit_log import AuditLog

from .constants import ALLOWED_AUDIT_ACTIONS, ALLOWED_AUDIT_TARGET_TYPES


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


SENSITIVE_META_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "id_token",
    "api_key",
    "authorization",
    "cookie",
    "session",
    "client_secret",
    "credential",
    "credentials",
}


def _mask_meta_value(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, nested_value in value.items():
            key_lower = key.lower()
            if key_lower in SENSITIVE_META_KEYS or any(
                sensitive in key_lower for sensitive in SENSITIVE_META_KEYS
            ):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = _mask_meta_value(nested_value)
        return sanitized
    if isinstance(value, list):
        return [_mask_meta_value(item) for item in value]
    return value


def _normalize_to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


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
    if action not in ALLOWED_AUDIT_ACTIONS:
        raise ValueError(f"Unsupported audit action: {action}")
    if target_type not in ALLOWED_AUDIT_TARGET_TYPES:
        raise ValueError(f"Unsupported audit target_type: {target_type}")

    sanitized_meta = _mask_meta_value(meta or {})
    row = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        meta_json=sanitized_meta,
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
    normalized_from = _normalize_to_utc(from_at)
    normalized_to = _normalize_to_utc(to_at)

    filters = []
    if actor is not None:
        filters.append(AdminAuditLog.admin_id == actor)
    if action:
        filters.append(AdminAuditLog.action == action)
    if target_type:
        filters.append(AdminAuditLog.target_type == target_type)
    if normalized_from:
        filters.append(AdminAuditLog.created_at >= normalized_from)
    if normalized_to:
        filters.append(AdminAuditLog.created_at <= normalized_to)

    total_stmt = select(func.count()).select_from(AdminAuditLog)
    if filters:
        total_stmt = total_stmt.where(*filters)
    total = int((await session.execute(total_stmt)).scalar_one())

    offset = (page - 1) * size
    data_stmt = (
        select(AdminAuditLog).where(*filters) if filters else select(AdminAuditLog)
    )
    data_stmt = (
        data_stmt.order_by(AdminAuditLog.created_at.desc(), AdminAuditLog.id.desc())
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


async def list_ops_audit_logs(
    session: AsyncSession,
    *,
    action: str | None = None,
    target_type: str | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """AuditLog 테이블에서 운영 감사로그를 조회합니다."""
    normalized_from = _normalize_to_utc(date_from)
    normalized_to = _normalize_to_utc(date_to)

    stmt = select(AuditLog)
    filters = []
    if action:
        filters.append(AuditLog.action == action)
    if target_type:
        filters.append(AuditLog.target_type == target_type)
    if normalized_from:
        filters.append(AuditLog.created_at >= normalized_from)
    if normalized_to:
        filters.append(AuditLog.created_at <= normalized_to)
    if keyword:
        filters.append(
            AuditLog.details.ilike(f"%{keyword}%")
            | AuditLog.target_author.ilike(f"%{keyword}%")
        )
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)


async def save_audit_log(
    session: AsyncSession,
    *,
    user_id: int,
    action: str,
    target_type: str,
    target_id: str | None = None,
    target_author: str | None = None,
    details: str | None = None,
) -> AuditLog:
    """Save an operational audit log entry (AuditLog table)."""
    row = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id or "",
        target_author=target_author,
        details=details,
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row
