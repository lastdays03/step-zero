import asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings
from app.core import security
from app.models.user import User

async def setup_restricted_user():
    settings = get_settings()
    engine = create_async_engine(str(settings.DATABASE_URL))
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == 'restricted@test.com'))
        user = result.scalar_one_or_none()
        
        pw_hash = security.get_password_hash("test1234!")
        kst = timezone(timedelta(hours=9))
        expiry_kst = datetime.now(kst) + timedelta(days=7)
        # Store naive UTC in DB
        expiry_utc = expiry_kst.astimezone(timezone.utc).replace(tzinfo=None)
        
        reason = "테스트 차단 사유입니다."
        
        if not user:
            user = User(
                email='restricted@test.com',
                full_name='Restricted User',
                hashed_password=pw_hash,
                status='suspended',
                is_active=True,
                is_superuser=False,
                suspended_until=expiry_utc,
                audit_log_reason=reason
            )
            session.add(user)
        else:
            user.status = 'suspended'
            user.suspended_until = expiry_utc
            user.audit_log_reason = reason
            user.hashed_password = pw_hash
            session.add(user)
            
        await session.commit()
        print("Test user is ready in DB.")

async def test_login():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            data={"username": "restricted@test.com", "password": "test1234!"}
        )
        print(f"Status Code: {response.status_code}")
        print("Response Body:")
        print(response.json())

async def main():
    await setup_restricted_user()
    await test_login()

if __name__ == "__main__":
    asyncio.run(main())
