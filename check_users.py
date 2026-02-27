import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.db import engine
from app.models.user import User

async def check():
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f'ID: {u.id}, Email: {u.email}, Active: {u.is_active}, Suspended: {u.is_suspended}')

if __name__ == "__main__":
    asyncio.run(check())
