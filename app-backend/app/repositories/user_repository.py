from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_google_user(self, email: str, full_name: str, hashed_password: str) -> User:
        is_superuser = email == "dojyu1928@gmail.com"
        user = User(
            email=email, 
            full_name=full_name, 
            hashed_password=hashed_password,
            is_superuser=is_superuser
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_latest_discipline_reason(self, user_id: int) -> str | None:
        from app.models.user_discipline_history import UserDisciplineHistory
        result = await self.session.execute(
            select(UserDisciplineHistory.reason)
            .where(UserDisciplineHistory.user_id == user_id)
            .order_by(UserDisciplineHistory.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
