from datetime import datetime

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.user import User


class OpsUserRead(BaseModel):
    id: int
    email: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime


async def list_users(
    session: AsyncSession,
    *,
    offset: int = 0,
    limit: int = 50,
) -> list[OpsUserRead]:
    result = await session.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    )
    users = result.scalars().all()
    return [OpsUserRead.model_validate(user, from_attributes=True) for user in users]
