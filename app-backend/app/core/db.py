from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models import (  # noqa: F401
    actionkit,
    admin_audit_log,
    announcement,
    growth_club,
    notification,
    profile,
    refresh_token,
    roadmap,
    team,
    user,
    user_discipline_history,
)

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=settings.SQL_ECHO, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
