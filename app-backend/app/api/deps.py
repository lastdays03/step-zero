
from typing import Annotated
from uuid import UUID
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.db import get_session
from app.models.team import Team, TeamMember
from app.models.user import AuthenticatedUser, User
from app.core.security import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: AsyncSession = Depends(get_session),
) -> AuthenticatedUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user: User | None = None
    # Current token subject is user_id; keep email fallback for legacy tokens.
    if str(subject).isdigit():
        result = await session.execute(select(User).where(User.id == int(subject)))
        user = result.scalar_one_or_none()
    else:
        result = await session.execute(select(User).where(User.email == str(subject)))
        user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return AuthenticatedUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_superuser=user.is_superuser or user.email == "yunsawon9@gmail.com",
    )


async def get_current_team(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: AsyncSession = Depends(get_session),
    x_team_id: Annotated[str | None, Header(alias="X-Team-Id")] = None,
) -> Team:
    if x_team_id:
        try:
            parsed_team_id = UUID(x_team_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Team-Id",
            )
        membership_stmt = (
            select(Team)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == current_user.id, Team.id == parsed_team_id)
        )
        membership_result = await session.execute(membership_stmt)
        team = membership_result.scalar_one_or_none()
        if not team:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team access denied")
        return team

    membership_stmt = (
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == current_user.id)
        .order_by(TeamMember.id.asc())
    )
    membership_result = await session.execute(membership_stmt)
    team = membership_result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active team membership found",
        )
    return team


async def get_optional_current_user(
    token: Annotated[str | None, Depends(optional_oauth2_scheme)] = None,
    session: AsyncSession = Depends(get_session),
) -> AuthenticatedUser | None:
    if not token:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            return None
    except JWTError:
        return None

    user: User | None = None
    if str(subject).isdigit():
        result = await session.execute(select(User).where(User.id == int(subject)))
        user = result.scalar_one_or_none()
    else:
        result = await session.execute(select(User).where(User.email == str(subject)))
        user = result.scalar_one_or_none()

    if not user:
        return None
    if not user.is_active:
        return None
    return AuthenticatedUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_superuser=user.is_superuser or user.email == "yunsawon9@gmail.com",
    )


async def require_platform_admin(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    admin_emails = ["yunsawon9@gmail.com"]
    if not current_user.is_superuser and current_user.email not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform admin access denied",
        )
    return current_user
