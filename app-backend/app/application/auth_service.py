from dataclasses import dataclass

from google.auth.transport import requests
from google.oauth2 import id_token

from app.core import security
from app.models.team import Team
from app.models.user import User
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository


@dataclass
class AuthResult:
    access_token: str
    token_type: str
    user: User
    current_team: Team
    teams: list[Team]


class AuthService:
    def __init__(self, user_repo: UserRepository, team_repo: TeamRepository):
        self.user_repo = user_repo
        self.team_repo = team_repo

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
                hashed_password=security.get_password_hash("SOCIAL_AUTH_GOOGLE"),
            )
        return await self._build_auth_result(user)

    async def _build_auth_result(self, user: User) -> AuthResult:
        teams = await self.team_repo.list_for_user(user.id)
        if not teams:
            default_team = await self.team_repo.create_default_team_for_user(user.id, user.email)
            teams = [default_team]
        current_team = teams[0]

        access_token = security.create_access_token(subject=str(user.id))
        return AuthResult(
            access_token=access_token,
            token_type="bearer",
            user=user,
            current_team=current_team,
            teams=teams,
        )
