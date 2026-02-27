import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import sys

engine = create_async_engine("postgresql+asyncpg://stepzero_admin:stepzero_password@localhost:5432/stepzero_db")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def main():
    async with async_session() as session:
        result = await session.execute(text("SELECT id, post_id, reason FROM growthclubpostreport"))
        reports = result.fetchall()
        print(f"Reports: {reports}")
        
        result2 = await session.execute(text("SELECT id, report_count, is_blinded FROM growthclubpost WHERE id = 1"))
        post = result2.fetchone()
        print(f"Post 1: {post}")
        
asyncio.run(main())
