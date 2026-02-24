
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    status: str = Field(default="active", index=True)
    report_count: int = Field(default=0, index=True)
    suspended_until: Optional[datetime] = Field(default=None, index=True)
    last_login_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class Token(SQLModel):
    access_token: str
    token_type: str

class UserRead(UserBase):
    id: int

class TokenWithUser(Token):
    user: UserRead


class AuthenticatedUser(SQLModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_superuser: bool = False
