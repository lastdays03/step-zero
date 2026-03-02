import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings


def utc_now() -> datetime:
    """Return current UTC time as a naive datetime (no tzinfo).

    All DB columns use TIMESTAMP WITHOUT TIME ZONE with an implicit
    UTC convention.  This helper replaces the deprecated
    ``datetime.utcnow()`` without breaking DB compatibility.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    now = datetime.now(timezone.utc)
    to_encode = {
        "exp": expire,
        "iat": now,
        "iss": settings.PROJECT_NAME,
        "sub": str(subject),
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
