from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.core.security import utc_now

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

    async def evict_oldest_for_user(
        self, user_id: int, max_active: int = 5
    ) -> None:
        """Keep at most *max_active* active tokens per user (FIFO eviction)."""
        result = await self.session.execute(
            select(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,  # noqa: E712
            )
            .order_by(RefreshToken.created_at.asc())
        )
        active_tokens = list(result.scalars().all())
        if len(active_tokens) <= max_active:
            return
        to_revoke = active_tokens[: len(active_tokens) - max_active]
        for token in to_revoke:
            token.revoked = True
            self.session.add(token)
        await self.session.commit()

    async def delete_expired_and_revoked(self, older_than_days: int = 30) -> int:
        """Delete tokens that are expired or revoked and older than the given days."""
        cutoff = utc_now() - timedelta(days=older_than_days)
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.created_at < cutoff,
                (RefreshToken.revoked == True) | (RefreshToken.expires_at < utc_now()),  # noqa: E712
            )
        )
        tokens = result.scalars().all()
        count = len(tokens)
        for token in tokens:
            await self.session.delete(token)
        if count:
            await self.session.commit()
        return count

    def is_expired(self, token: RefreshToken) -> bool:
        expires = token.expires_at
        now = utc_now()
        # Normalize to naive UTC for comparison
        if expires.tzinfo is not None:
            expires = expires.replace(tzinfo=None)
        return expires < now
