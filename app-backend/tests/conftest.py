import os
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./tests/test.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.core import db, security
from app.core.rate_limit import limiter
from app.main import app

# Disable rate limiting in tests
limiter.enabled = False
from app.models.team import Team, TeamMember
from app.models.user import User

TEST_DB_PATH = Path(__file__).parent / "test.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    future=True,
)
test_async_session = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

db.engine = test_engine
db.async_session = test_async_session


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
async def seed_test_user() -> AsyncGenerator[None, None]:
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    async with db.engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with db.async_session() as session:
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email="test@example.com",
                full_name="Test User",
                hashed_password=security.get_password_hash("password123"),
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        team_result = await session.execute(
            select(Team)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == user.id)
            .order_by(TeamMember.id.asc())
        )
        existing_team = team_result.scalar_one_or_none()
        if not existing_team:
            team = Team(name="Test Team", created_by=user.id, updated_by=user.id)
            session.add(team)
            await session.flush()
            session.add(TeamMember(team_id=team.id, user_id=user.id, role="owner"))
            await session.commit()
        else:
            await session.commit()
    yield

    await db.engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
