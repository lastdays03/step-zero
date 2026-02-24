from datetime import datetime, timedelta, timezone

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, or_

from app.models.user import User
from app.models.user_discipline_history import UserDisciplineHistory


class OpsUserRead(BaseModel):
    id: int
    email: str
    full_name: str | None
    status: str
    report_count: int
    last_login_at: datetime | None
    is_active: bool
    is_superuser: bool
    created_at: datetime


class DisciplineHistoryRead(BaseModel):
    id: int
    user_id: int
    admin_id: int
    prev_status: str
    new_status: str
    reason: str
    created_at: datetime


async def list_users(
    session: AsyncSession,
    *,
    search: str | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[OpsUserRead]:
    from sqlalchemy import nulls_last
    statement = select(User).order_by(nulls_last(User.last_login_at.desc()), User.created_at.desc())
    
    if search:
        # 이메일 또는 이름 검색 (대소문자 무시)
        statement = statement.where(
            or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    if status:
        statement = statement.where(User.status == status)

    result = await session.execute(statement.offset(offset).limit(limit))
    users = result.scalars().all()
    return [OpsUserRead.model_validate(user, from_attributes=True) for user in users]


async def get_user_discipline_history(
    session: AsyncSession,
    user_id: int,
) -> list[DisciplineHistoryRead]:
    statement = (
        select(UserDisciplineHistory)
        .where(UserDisciplineHistory.user_id == user_id)
        .order_by(UserDisciplineHistory.created_at.desc())
    )
    result = await session.execute(statement)
    histories = result.scalars().all()
    return [DisciplineHistoryRead.model_validate(h, from_attributes=True) for h in histories]


async def update_user_status(
    session: AsyncSession,
    *,
    admin_id: int,
    user_id: int,
    status: str,
    reason: str,
    duration_days: int | None = None,
) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
        
    prev_status = user.status
    user.status = status
    # 'suspended' 계열이면 is_active = False 처리 (필요에 따라 정책 조정 가능)
    if status.startswith("suspended"):
        user.is_active = False
        if duration_days is not None and duration_days > 0 and status != "suspended_permanent":
            user.suspended_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=float(duration_days))
        else:
            user.suspended_until = None
    else:
        user.is_active = True
        user.suspended_until = None
        
    session.add(user)
    
    # 징계 이력 저장
    history = UserDisciplineHistory(
        user_id=user_id,
        admin_id=admin_id,
        prev_status=prev_status,
        new_status=status,
        reason=reason,
        suspended_until=user.suspended_until,
    )
    session.add(history)
    
    # ---------------------------------------------------------
    # TODO: [감사로그 구현 게이트] 
    # record_admin_audit_log 유틸리티가 완성되면 아래 자리에 꽂을 것.
    # 예: await record_admin_audit_log(
    #     session=session,
    #     admin_id=admin_id,
    #     action="UPDATE_USER_STATUS",
    #     target_type="USER",
    #     target_id=str(user_id),
    #     reason=reason,
    #     meta={"new_status": status, "prev_status": prev_status}
    # )
    # ---------------------------------------------------------
    
    await session.commit()
    await session.refresh(user)
    return user


async def bulk_update_user_status(
    session: AsyncSession,
    *,
    admin_id: int,
    user_ids: list[int],
    status: str,
    reason: str,
    duration_days: int | None = None,
) -> int:
    # 대상 사용자들 조회
    statement = select(User).where(User.id.in_(user_ids))
    result = await session.execute(statement)
    users = result.scalars().all()
    
    if not users:
        return 0
        
    for user in users:
        prev_status = user.status
        user.status = status
        if status.startswith("suspended"):
            user.is_active = False
            if duration_days is not None and duration_days > 0 and status != "suspended_permanent":
                user.suspended_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=float(duration_days))
            else:
                user.suspended_until = None
        else:
            user.is_active = True
            user.suspended_until = None
        
        session.add(user)
        
        # 각 사용자별 징계 이력 저장
        history = UserDisciplineHistory(
            user_id=user.id,
            admin_id=admin_id,
            prev_status=prev_status,
            new_status=status,
            reason=reason,
        )
        session.add(history)
        
    # ---------------------------------------------------------
    # TODO: [감사로그 구현 게이트] 
    # record_admin_audit_log 유틸리티가 완성되면 아래 자리에 꽂을 것.
    # 예: await record_admin_audit_log(
    #     session=session,
    #     admin_id=admin_id,
    #     action="BULK_UPDATE_USER_STATUS",
    #     target_type="USER",
    #     target_id="bulk",
    #     reason=reason,
    #     meta={"user_ids": user_ids, "new_status": status}
    # )
    # ---------------------------------------------------------
    
    await session.commit()
    return len(users)
