
import asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import engine
from app.models.user import User

async def run():
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).where(User.email == 'dojyu1928@gmail.com'))
        user = result.scalar_one_or_none()
        if user:
            user.is_superuser = True
            session.add(user)
            await session.commit()
            print('Admin privilege granted to dojyu1928@gmail.com')
        else:
            print('User dojyu1928@gmail.com not found. Admin privilege will be granted upon registration via code.')

if __name__ == "__main__":
    asyncio.run(run())
