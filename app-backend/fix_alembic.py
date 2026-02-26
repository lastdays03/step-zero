import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import get_settings

async def main():
    try:
        settings = get_settings()
        engine = create_async_engine(str(settings.DATABASE_URL))
        async with engine.begin() as conn:
            await conn.execute(text("UPDATE alembic_version SET version_num = '006_notification';"))
        print("Successfully updated alembic_version")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
