from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.models.user import User

router = APIRouter(prefix="/users")


class OpsUserRead(BaseModel):
    id: int
    email: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime


@router.get("", response_model=list[OpsUserRead])
async def list_ops_users(
    session: AsyncSession = Depends(get_session),
) -> list[OpsUserRead]:
    result = await session.execute(
        select(User).order_by(User.created_at.desc()).limit(50)
    )
    users = result.scalars().all()
    return [OpsUserRead.model_validate(user, from_attributes=True) for user in users]
