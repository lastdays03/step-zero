import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from google.auth.transport import requests
from google.oauth2 import id_token

from app.core import security
from app.core.config import get_settings
from app.models.team import Team
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository


@dataclass
class AuthResult:
    access_token: str
    refresh_token: str
    token_type: str
    user: User
    current_team: Team
    teams: list[Team]


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        team_repo: TeamRepository,
        refresh_token_repo: RefreshTokenRepository,
    ):
        self.user_repo = user_repo
        self.team_repo = team_repo
        self.refresh_token_repo = refresh_token_repo

    async def login_with_password(self, email: str, password: str) -> AuthResult | None:
        user = await self.user_repo.get_by_email(email)
        if not user or not security.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return await self._build_auth_result(user)

    async def login_with_google(self, google_client_id: str, token: str) -> AuthResult | None:
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), google_client_id)
        email = idinfo.get("email")
        if not email:
            return None
        user = await self.user_repo.get_by_email(email)
        if not user:
            user = await self.user_repo.create_google_user(
                email=email,
                full_name=idinfo.get("name") or email.split("@")[0],
                hashed_password=security.get_password_hash(secrets.token_hex(32)),
            )
        return await self._build_auth_result(user)

    async def refresh_access_token(self, raw_refresh_token: str) -> AuthResult | None:
        token_hash = security.hash_refresh_token(raw_refresh_token)
        stored = await self.refresh_token_repo.get_by_hash(token_hash)
        if not stored:
            return None

        if self.refresh_token_repo.is_expired(stored):
            await self.refresh_token_repo.revoke(stored.id)
            return None

        # Token rotation: revoke old, issue new
        user = await self.user_repo.get_by_id(stored.user_id)
        if not user or not user.is_active:
            await self.refresh_token_repo.revoke_all_for_user(stored.user_id)
            return None

        result = await self._build_auth_result(user)

        # Mark old token as replaced by the new one
        settings = get_settings()
        new_token_hash = security.hash_refresh_token(result.refresh_token)
        new_stored = await self.refresh_token_repo.create(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=datetime.utcnow()
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        await self.refresh_token_repo.mark_replaced(stored.id, new_stored.id)

        return result

    async def detect_refresh_token_reuse(self, raw_refresh_token: str) -> bool:
        """Check if a revoked token is being reused (possible theft)."""
        token_hash = security.hash_refresh_token(raw_refresh_token)
        stored = await self.refresh_token_repo.get_by_hash(token_hash)
        # If get_by_hash returns None (revoked=True excluded), check if it was revoked
        if stored is None:
            from sqlmodel import select
            from app.models.refresh_token import RefreshToken

            result = await self.refresh_token_repo.session.execute(
                select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            )
            revoked_token = result.scalar_one_or_none()
            if revoked_token and revoked_token.revoked:
                # Reuse detected — revoke all tokens for this user
                await self.refresh_token_repo.revoke_all_for_user(revoked_token.user_id)
                return True
        return False

    async def _build_auth_result(self, user: User) -> AuthResult:
        teams = await self.team_repo.list_for_user(user.id)
        if not teams:
            default_team = await self.team_repo.create_default_team_for_user(user.id, user.email)
            teams = [default_team]
        current_team = teams[0]

        access_token = security.create_access_token(subject=str(user.id))
        raw_refresh_token = security.create_refresh_token()

        # Store refresh token in DB
        settings = get_settings()
        token_hash = security.hash_refresh_token(raw_refresh_token)
        await self.refresh_token_repo.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow()
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        return AuthResult(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            user=user,
            current_team=current_team,
            teams=teams,
        )
