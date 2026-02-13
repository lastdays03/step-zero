
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests

from app.core import security
from app.core import config
from app.models.user import User, TokenWithUser, UserRead
from app.core.db import get_session
from app.core.logging import get_logger

router = APIRouter()
settings = config.get_settings()
logger = get_logger("api.auth")

class GoogleLoginRequest(BaseModel):
    id_token: str

@router.post("/login", response_model=TokenWithUser)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    result = await session.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserRead.model_validate(user),
    }

@router.post("/login/google", response_model=TokenWithUser)
async def login_google(
    request_data: GoogleLoginRequest,
    session: AsyncSession = Depends(get_session)
) -> Any:
    """
    Verify Google ID token and return access token
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google login is not configured",
        )

    try:
        idinfo = id_token.verify_oauth2_token(
            request_data.id_token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
        email = idinfo.get("email")
        name = idinfo.get("name")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not retrieve email from Google token",
            )

        # User handling: check DB and create if not exists
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                email=email,
                full_name=name or email.split("@")[0],
                hashed_password=security.get_password_hash("SOCIAL_AUTH_GOOGLE"),
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

        # Create internal JWT
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            subject=email, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserRead.model_validate(user),
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Google login failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )

@router.post("/login/social/{provider}", response_model=TokenWithUser)
async def login_social(
    provider: str,
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Mock Social Login for Google/Kakao (Legacy/Fallback)
    """
    if not settings.ENABLE_SOCIAL_MOCK:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    if provider not in ["google", "kakao"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    email = f"social_{provider}_user@example.com"
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            email=email,
            full_name=f"{provider.capitalize()} User",
            hashed_password=security.get_password_hash("SOCIAL_AUTH_MOCK"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=email, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserRead.model_validate(user),
    }
