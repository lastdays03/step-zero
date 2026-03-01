import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# Import all models to ensure they are in metadata
from app.models import *


async def check_schema():
    db_url = "sqlite+aiosqlite:///./diag_test.db"
    if os.path.exists("./diag_test.db"):
        os.remove("./diag_test.db")

    print(f"Connecting to {db_url}...")
    engine = create_async_engine(db_url)

    try:
        async with engine.begin() as conn:
            print("Attempting to create all tables...")
            await conn.run_sync(SQLModel.metadata.create_all)
            print("Successfully created all tables!")
    except Exception as e:
        print(f"Error during schema creation: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await engine.dispose()
        if os.path.exists("./diag_test.db"):
            os.remove("./diag_test.db")


if __name__ == "__main__":
    asyncio.run(check_schema())
