import asyncio
import sys
import os

# Add app-backend to sys.path
sys.path.append('/app')

from app.core.db import get_session
from app.models.user import User
from app.models.user_discipline_history import UserDisciplineHistory
from sqlmodel import select
from datetime import datetime, timedelta, timezone
from app.core import security

async def verify():
    async for session in get_session():
        email = 'restricted@test.com'
        password = 'password123'
        
        # 1. Ensure user exists
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                email=email, 
                hashed_password=security.get_password_hash(password),
                full_name="Restricted User"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        # 2. Apply 1 day suspension (UTC naive for DB stability)
        now_utc = datetime.utcnow()
        user.status = "suspended_1d"
        user.is_active = False
        user.suspended_until = now_utc + timedelta(days=1)
        user.audit_log_reason = "부적절한 게시글 작성 (1일 정지)"
        session.add(user)
        
        # 3. Add discipline history (legacy sync)
        history = UserDisciplineHistory(
            user_id=user.id,
            admin_id=1, 
            prev_status="active",
            new_status="suspended_1d",
            reason=user.audit_log_reason,
            suspended_until=user.suspended_until
        )
        session.add(history)
        await session.commit()
        print(f"--- [SETUP] User {email} restricted until {user.suspended_until} ---")
        
        # Try login via AuthService
        from app.features.auth.application.auth_service import AuthService
        from app.repositories.user_repository import UserRepository
        from app.repositories.team_repository import TeamRepository
        from app.repositories.refresh_token_repository import RefreshTokenRepository
        from fastapi import HTTPException
        
        service = AuthService(
            user_repo=UserRepository(session),
            team_repo=TeamRepository(session),
            refresh_token_repo=RefreshTokenRepository(session)
        )
        
        print(f"--- [TEST] Attempting login for {email} ---")
        try:
            await service.login_with_password(email, password)
            print("ERROR: Login succeeded for restricted user!")
        except HTTPException as e:
            print(f"SUCCESS: Login blocked as expected. Status: {e.status_code}")
            print(f"DETAIL: {e.detail}")
        
        # 4. Test Auto-recovery
        print(f"--- [TEST] Attempting auto-recovery (mocking past expiration) ---")
        user.suspended_until = now_utc - timedelta(hours=1)
        session.add(user)
        await session.commit()
        
        try:
            result = await service.login_with_password(email, password)
            if result:
                print(f"SUCCESS: Auto-recovery worked. User status: {user.status}")
            else:
                print("ERROR: Login failed after recovery path.")
        except HTTPException as e:
            print(f"ERROR: Login still blocked! {e.detail}")
            
        break

if __name__ == "__main__":
    asyncio.run(verify())
