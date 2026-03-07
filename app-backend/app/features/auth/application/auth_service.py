import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy import desc
from sqlmodel import select
from starlette.concurrency import run_in_threadpool

from app.core import security
from app.core.config import get_settings
from app.core.security import utc_now
from app.models.team import Team
from app.models.user import User
from app.models.user_discipline_history import UserDisciplineHistory
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


@dataclass
class AuthResult:
    access_token: str
    refresh_token: str
    token_type: str
    user: User
    current_team: Team
    teams: list[Team]
    refresh_token_id: UUID | None = None


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

        # Handle inactivity recovery and update last login
        await self._handle_user_login_metadata(user)

        if user.status != "active":
            await self._raise_suspension_error(user)

        return await self._build_auth_result(user)

    async def login_with_google(
        self, google_client_id: str, token: str
    ) -> AuthResult | None:
        # Wrap blocking Google library call in a threadpool
        idinfo = await run_in_threadpool(
            id_token.verify_oauth2_token, token, requests.Request(), google_client_id
        )
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

        # Handle inactivity recovery and update last login
        await self._handle_user_login_metadata(user)

        if user.status != "active":
            await self._raise_suspension_error(user)

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
        if result.refresh_token_id is None:
            logger.error("Refresh token rotation created no persisted token for user %s", user.id)
            return None

        await self.refresh_token_repo.mark_replaced(stored.id, result.refresh_token_id)

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
            revoked_token = result.scalars().first()
            if revoked_token and revoked_token.revoked:
                # Reuse detected — revoke all tokens for this user
                await self.refresh_token_repo.revoke_all_for_user(revoked_token.user_id)
                return True
        return False

    def _get_kst_now(self) -> datetime:
        """KST(UTC+9) 기준 현재 시각 반환"""
        return datetime.now(timezone(timedelta(hours=9)))

    async def _handle_user_login_metadata(self, user: User) -> None:
        """Update last_login_at and recover suspended users if applicable."""
        now = utc_now()
        user.last_login_at = now

        # Normalize suspended_until to naive UTC for comparison
        suspended_until = user.suspended_until
        if suspended_until and suspended_until.tzinfo is not None:
            suspended_until = suspended_until.astimezone(timezone.utc).replace(
                tzinfo=None
            )

        # Check for suspension recovery: if suspended_until has expired, restore
        if user.status.startswith("suspended") and suspended_until:
            if suspended_until <= now:
                user.status = "active"
                user.is_active = True
                user.suspended_until = None

        # suspended_inactive users are restored on login
        if user.status == "suspended_inactive":
            user.status = "active"
            user.is_active = True

        self.user_repo.session.add(user)
        await self.user_repo.session.commit()
        await self.user_repo.session.refresh(user)

    async def _raise_suspension_error(self, user: User) -> None:
        """정지/차단된 유저에 대해 403 에러 발생 및 사유 전달"""
        reason = user.audit_log_reason
        try:
            latest_reason = await self.user_repo.get_latest_discipline_reason(user.id)
            if latest_reason:
                reason = latest_reason
        except Exception as e:
            logger.warning(
                f"Failed to fetch latest discipline reason for user {user.id}: {e}"
            )

        if not reason:
            reason = "운영 정책 위반으로 인해 계정이 제한되었습니다."

        suspended_until_str = "영구"
        expiry_iso = None
        if user.suspended_until:
            kst_tz = timezone(timedelta(hours=9))
            kst_time = user.suspended_until.replace(tzinfo=timezone.utc).astimezone(
                kst_tz
            )
            suspended_until_str = kst_time.strftime("%Y.%m.%d")
            expiry_iso = user.suspended_until.replace(tzinfo=timezone.utc).isoformat()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ACCOUNT_RESTRICTED",
                "status": user.status,
                "reason": reason,
                "suspended_until": suspended_until_str,
                "expiry_iso": expiry_iso,
            },
        )

    async def _build_auth_result(self, user: User) -> AuthResult:
        teams = await self.team_repo.list_for_user(user.id)
        if not teams:
            default_team = await self.team_repo.create_default_team_for_user(
                user.id, user.email
            )
            teams = [default_team]
        current_team = teams[0]

        access_token = security.create_access_token(subject=str(user.id))
        raw_refresh_token = security.create_refresh_token()

        # Store refresh token in DB and enforce per-user limit
        settings = get_settings()
        token_hash = security.hash_refresh_token(raw_refresh_token)
        stored_refresh_token = await self.refresh_token_repo.create(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=utc_now() + settings.refresh_token_ttl,
        )
        await self.refresh_token_repo.evict_oldest_for_user(user.id, max_active=5)

        return AuthResult(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            user=user,
            current_team=current_team,
            teams=teams,
            refresh_token_id=stored_refresh_token.id,
        )
