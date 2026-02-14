from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth_service import AuthService
from app.core import config
from app.core.db import get_session
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.api.v2.schemas import TeamRead, TokenWithTeams
from app.models.user import UserRead

router = APIRouter()
settings = config.get_settings()


class GoogleLoginRequest(BaseModel):
    id_token: str


def _serialize_auth_result(result: Any) -> TokenWithTeams:
    return TokenWithTeams(
        access_token=result.access_token,
        token_type=result.token_type,
        user=UserRead.model_validate(result.user),
        current_team_id=result.current_team.id,
        teams=[TeamRead(id=team.id, name=team.name) for team in result.teams],
    )


@router.post("/login", response_model=TokenWithTeams)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = AuthService(
        user_repo=UserRepository(session),
        team_repo=TeamRepository(session),
    )
    result = await service.login_with_password(form_data.username, form_data.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return _serialize_auth_result(result)


@router.post("/login/google", response_model=TokenWithTeams)
async def login_google(
    request_data: GoogleLoginRequest,
    session: AsyncSession = Depends(get_session),
) -> Any:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is not configured",
        )
    service = AuthService(
        user_repo=UserRepository(session),
        team_repo=TeamRepository(session),
    )
    try:
        result = await service.login_with_google(settings.GOOGLE_CLIENT_ID, request_data.id_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")
    return _serialize_auth_result(result)
