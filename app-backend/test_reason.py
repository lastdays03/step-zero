import asyncio
import sys
import os

sys.path.append('/app')

from app.core.db import get_session
from app.models.user import User
from sqlmodel import select
from datetime import datetime, timedelta, timezone

async def test_suspension():
    async for session in get_session():
        # 1. Create or Find test user
        email = "suspended_reason_test@example.com"
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            from app.core import security
            user = User(
                email=email,
                full_name="Suspended Test User",
                hashed_password=security.get_password_hash("testpass123"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # 2. Set suspension and REASON
        user.status = "suspended"
        user.suspended_until = datetime.now(timezone(timedelta(hours=9))) + timedelta(days=7)
        user.audit_log_reason = "테스트용 정지 사유입니다: 운영 정책 제5조 위반"
        session.add(user)
        await session.commit()
        print(f"User {email} suspended with reason: {user.audit_log_reason}")

if __name__ == "__main__":
    asyncio.run(test_suspension())
