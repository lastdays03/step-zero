from typing import Any

from google.auth.exceptions import GoogleAuthError
from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import RefreshTokenRequest, TeamRead, TokenWithTeams
from app.core import config, security
from app.core.db import get_session
from app.features.auth.application.auth_service import AuthService
from app.models.user import User, UserRead
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository

router = APIRouter()
settings = config.get_settings()


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(description="Google OAuth ID Token")


def _auth_service(session: AsyncSession) -> AuthService:
    return AuthService(
        user_repo=UserRepository(session),
        team_repo=TeamRepository(session),
        refresh_token_repo=RefreshTokenRepository(session),
    )


def _serialize_auth_result(result: Any) -> TokenWithTeams:
    return TokenWithTeams(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
        token_type=result.token_type,
        user=UserRead.model_validate(result.user),
        current_team_id=result.current_team.id,
        teams=[TeamRead(id=team.id, name=team.name) for team in result.teams],
    )


def _is_backend_unavailable_error(error: Exception) -> bool:
    return isinstance(error, (SQLAlchemyError, ConnectionError, OSError, PermissionError))


async def _login_social_mock_user(provider: str, session: AsyncSession) -> dict[str, Any]:
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
    if result:
        return _serialize_auth_result(result).model_dump(mode="json")

    # fallback for seeded mock user with hashed secret
    token = security.create_access_token(subject=str(user.id))
    raw_refresh = security.create_refresh_token()
    team_repo = TeamRepository(session)
    teams = await team_repo.list_for_user(user.id)
    if not teams:
        default_team = await team_repo.create_default_team_for_user(user.id, user.email)
        teams = [default_team]
    current_team = teams[0]

    # Store refresh token for fallback path
    from datetime import datetime, timedelta

    refresh_repo = RefreshTokenRepository(session)
    await refresh_repo.create(
        user_id=user.id,
        token_hash=security.hash_refresh_token(raw_refresh),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return {
        "access_token": token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
        "user": UserRead.model_validate(user).model_dump(mode="json"),
        "current_team_id": current_team.id,
        "teams": [TeamRead(id=team.id, name=team.name).model_dump(mode="json") for team in teams],
    }


@router.post(
    "/login",
    response_model=TokenWithTeams,
    summary="이메일 로그인",
    description="이메일/비밀번호로 로그인하고 팀 컨텍스트가 포함된 액세스 토큰을 발급합니다.",
    response_description="액세스 토큰과 사용자/팀 정보를 반환합니다.",
)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = _auth_service(session)
    try:
        result = await service.login_with_password(form_data.username, form_data.password)
    except Exception as error:
        if _is_backend_unavailable_error(error):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication backend unavailable",
            )
        raise
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return _serialize_auth_result(result)


@router.post(
    "/login/google",
    response_model=TokenWithTeams,
    summary="Google 로그인",
    description="Google ID Token을 검증해 로그인합니다.",
    response_description="액세스 토큰과 사용자/팀 정보를 반환합니다.",
)
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
    except GoogleAuthError:
        if settings.ENABLE_SOCIAL_MOCK:
            return await _login_social_mock_user("google", session)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google authentication service unavailable",
        )
    except HTTPException:
        raise
    except Exception as error:
        if _is_backend_unavailable_error(error):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication backend unavailable",
            )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")
    return _serialize_auth_result(result)


@router.post(
    "/login/social/{provider}",
    response_model=TokenWithTeams,
    summary="소셜 로그인(mock)",
    description="개발 환경에서 mock 소셜 계정으로 로그인합니다.",
    response_description="액세스 토큰과 사용자/팀 정보를 반환합니다.",
)
async def login_social(
    provider: str = Path(description="소셜 로그인 제공자 (`google` 또는 `kakao`)"),
    session: AsyncSession = Depends(get_session),
) -> Any:
    if not settings.ENABLE_SOCIAL_MOCK:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    if provider not in ["google", "kakao"]:
        raise HTTPException(status_code=400, detail="Unsupported provider")

    try:
        return await _login_social_mock_user(provider, session)
    except Exception as error:
        if _is_backend_unavailable_error(error):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication backend unavailable",
            )
        raise


@router.post(
    "/refresh",
    response_model=TokenWithTeams,
    summary="토큰 갱신",
    description="리프레시 토큰으로 새 액세스 토큰과 리프레시 토큰을 발급합니다.",
    response_description="새 액세스 토큰과 리프레시 토큰을 반환합니다.",
)
async def refresh_token(
    body: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
) -> Any:
    service = _auth_service(session)

    # Check for token reuse (possible theft)
    reuse_detected = await service.detect_refresh_token_reuse(body.refresh_token)
    if reuse_detected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected. All sessions revoked.",
        )

    result = await service.refresh_access_token(body.refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return _serialize_auth_result(result)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="로그아웃",
    description="리프레시 토큰을 폐기합니다.",
)
async def logout(
    body: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
) -> None:
    token_hash = security.hash_refresh_token(body.refresh_token)
    refresh_repo = RefreshTokenRepository(session)
    stored = await refresh_repo.get_by_hash(token_hash)
    if stored:
        await refresh_repo.revoke(stored.id)
