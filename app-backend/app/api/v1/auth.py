from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth_service import AuthService
from app.core import config, security
from app.core.db import get_session
from app.models.user import TokenWithUser, User, UserRead
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository

router = APIRouter()
settings = config.get_settings()


class GoogleLoginRequest(BaseModel):
    id_token: str


def _auth_service(session: AsyncSession) -> AuthService:
    return AuthService(
        user_repo=UserRepository(session),
        team_repo=TeamRepository(session),
    )


@router.post("/login", response_model=TokenWithUser)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = _auth_service(session)
    result = await service.login_with_password(form_data.username, form_data.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return {
        "access_token": result.access_token,
        "token_type": result.token_type,
        "user": UserRead.model_validate(result.user),
    }


@router.post("/login/google", response_model=TokenWithUser)
async def login_google(
    request_data: GoogleLoginRequest,
    session: AsyncSession = Depends(get_session),
) -> Any:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is not configured",
        )
    service = _auth_service(session)
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
    return {
        "access_token": result.access_token,
        "token_type": result.token_type,
        "user": UserRead.model_validate(result.user),
    }


@router.post("/login/social/{provider}", response_model=TokenWithUser)
async def login_social(
    provider: str,
    session: AsyncSession = Depends(get_session),
) -> Any:
    if not settings.ENABLE_SOCIAL_MOCK:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    if provider not in ["google", "kakao"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    user_repo = UserRepository(session)
    user = await user_repo.get_by_email(f"social_{provider}_user@example.com")
    if not user:
        user = User(
            email=f"social_{provider}_user@example.com",
            full_name=f"{provider.capitalize()} User",
            hashed_password=security.get_password_hash("SOCIAL_AUTH_MOCK"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    service = _auth_service(session)
    result = await service.login_with_password(user.email, "SOCIAL_AUTH_MOCK")
    if not result:
        # fallback for seeded mock user with hashed secret
        token = security.create_access_token(subject=str(user.id))
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": UserRead.model_validate(user),
        }
    return {
        "access_token": result.access_token,
        "token_type": result.token_type,
        "user": UserRead.model_validate(result.user),
    }
