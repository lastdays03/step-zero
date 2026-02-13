
import pytest
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator

from sqlmodel import select

from app.main import app
from app.core import db, security
from app.models.user import User

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session", autouse=True)
async def seed_test_user() -> AsyncGenerator[None, None]:
    await db.init_db()
    async with db.async_session() as session:
        result = await session.execute(select(User).where(User.email == "test@example.com"))
        existing_user = result.scalar_one_or_none()
        if not existing_user:
            session.add(
                User(
                    email="test@example.com",
                    full_name="Test User",
                    hashed_password=security.get_password_hash("password123"),
                )
            )
            await session.commit()
    yield

@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
