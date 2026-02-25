import asyncio
import sys
import os

sys.path.append('/app')

from app.core.db import get_session
from sqlalchemy import text

async def check():
    async for session in get_session():
        try:
            result = await session.execute(text("SELECT 1 FROM user_discipline_history LIMIT 1"))
            print("SUCCESS: user_discipline_history table exists")
        except Exception as e:
            print(f"FAILURE: {e}")
        break

if __name__ == "__main__":
    asyncio.run(check())
