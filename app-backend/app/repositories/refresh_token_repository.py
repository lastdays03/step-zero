from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, user_id: int, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, token_id: UUID) -> None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.id == token_id)
        )
        token = result.scalar_one_or_none()
        if token:
            token.revoked = True
            self.session.add(token)
            await self.session.commit()

    async def mark_replaced(self, token_id: UUID, replaced_by: UUID) -> None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.id == token_id)
        )
        token = result.scalar_one_or_none()
        if token:
            token.revoked = True
            token.replaced_by = replaced_by
            self.session.add(token)
            await self.session.commit()

    async def revoke_all_for_user(self, user_id: int) -> None:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoked = True
            self.session.add(token)
        await self.session.commit()

    def is_expired(self, token: RefreshToken) -> bool:
        expires = token.expires_at
        now = datetime.now(timezone.utc)
        # Handle timezone-naive datetimes (e.g. from SQLite)
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires < now
