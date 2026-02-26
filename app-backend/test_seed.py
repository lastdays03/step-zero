import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.announcement import Announcement
from app.models.notification import Notification

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:changethis123!@localhost:5432/stepzero_db")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create an announcement
        a = Announcement(
            title="테스트 공지사항 1",
            content="안녕하세요! 이것은 테스트 공지사항입니다.",
            status="published",
            created_by=1,
            updated_by=1
        )
        session.add(a)
        await session.commit()
        await session.refresh(a)
        
        # Create 6 notifications for user 1 to test the "View More" toggle
        for i in range(6):
            n = Notification(
                user_id=1,
                content=f"알림 {i+1}",
                type="announcement",
                link=f"/announcements/{a.id}" if i == 0 else None
            )
            session.add(n)
        
        await session.commit()
        print("Successfully seeded announcements and notifications!")

if __name__ == "__main__":
    asyncio.run(main())
