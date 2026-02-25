
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from app.models.profile import UserProfile

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
    audit_log_reason: Optional[str] = Field(default=None)
    last_login_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    profile: Optional["UserProfile"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"uselist": False}
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

class TokenWithUser(Token):
    user: UserRead


class AuthenticatedUser(SQLModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_superuser: bool = False
