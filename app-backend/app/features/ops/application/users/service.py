from datetime import datetime, timedelta

from app.core.security import utc_now

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import or_, select

from app.models.user import User
from app.models.user_discipline_history import UserDisciplineHistory

from .schemas import DisciplineHistoryRead, OpsUserRead


def _apply_status_update(user: User, status: str, duration_days: int | None) -> None:
    """Helper to apply status and suspension logic to a user model."""
    user.status = status
    if status.startswith("suspended"):
        user.is_active = False
        if (
            duration_days is not None
            and duration_days > 0
            and status != "suspended_permanent"
        ):
            user.suspended_until = utc_now() + timedelta(
                days=float(duration_days)
            )
        else:
            user.suspended_until = None
    else:
        user.is_active = True
        user.suspended_until = None


async def list_users(
    session: AsyncSession,
    *,
    search: str | None = None,
    status: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[OpsUserRead]:
    from sqlalchemy import nulls_last

    statement = select(User).order_by(
        nulls_last(User.last_login_at.desc()), User.created_at.desc()
    )

    if search:
        statement = statement.where(
            or_(
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
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
    return [
        DisciplineHistoryRead.model_validate(h, from_attributes=True) for h in histories
    ]


async def update_user_status(
    session: AsyncSession,
    *,
    admin_id: int,
    user_id: int,
    status: str,
    reason: str,
    duration_days: int | None = None,
) -> tuple[User, str] | None:
    """Update a single user's status.

    Returns ``(updated_user, prev_status)`` or ``None`` if the user was not
    found.
    """
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        return None

    prev_status = user.status
    _apply_status_update(user, status, duration_days)
    session.add(user)

    history = UserDisciplineHistory(
        user_id=user_id,
        admin_id=admin_id,
        prev_status=prev_status,
        new_status=status,
        reason=reason,
        suspended_until=user.suspended_until,
    )
    session.add(history)

    await session.commit()
    await session.refresh(user)
    return user, prev_status


async def bulk_update_user_status(
    session: AsyncSession,
    *,
    admin_id: int,
    user_ids: list[int],
    status: str,
    reason: str,
    duration_days: int | None = None,
) -> int:
    statement = select(User).where(User.id.in_(user_ids))
    result = await session.execute(statement)
    users = result.scalars().all()

    if not users:
        return 0

    for user in users:
        prev_status = user.status
        _apply_status_update(user, status, duration_days)
        session.add(user)

        history = UserDisciplineHistory(
            user_id=user.id,
            admin_id=admin_id,
            prev_status=prev_status,
            new_status=status,
            reason=reason,
            suspended_until=user.suspended_until,
        )
        session.add(history)

    await session.commit()
    return len(users)
