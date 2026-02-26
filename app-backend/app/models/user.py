
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.models.profile import UserProfile

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    is_suspended: bool = Field(default=False, index=True)
    suspended_at: Optional[datetime] = Field(default=None)
    suspension_reason: Optional[str] = Field(default=None)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    profile: "UserProfile" = Relationship(
        sa_relationship_kwargs={"backref": "user", "uselist": False}
    )

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class Token(SQLModel):
    access_token: str
    token_type: str

class UserRead(UserBase):
    id: int
    is_suspended: bool = False
    suspended_at: Optional[datetime] = None
    suspension_reason: Optional[str] = None

class TokenWithUser(Token):
    user: UserRead


class AuthenticatedUser(SQLModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_superuser: bool = False
    is_suspended: bool = False
    suspended_at: Optional[datetime] = None
    suspension_reason: Optional[str] = None
