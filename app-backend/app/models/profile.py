from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import JSON, Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class UserProfileBase(SQLModel):
    nickname: Optional[str] = None
    profile_img: Optional[str] = "default.png"
    is_public: bool = Field(default=True)
    category: Optional[str] = None
    region: Optional[str] = None
    philosophy: Optional[str] = None
    experiences: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    awards: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    certificates: List[str] = Field(default_factory=list, sa_column=Column(JSON))


class UserProfile(UserProfileBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    user: Optional["User"] = Relationship(back_populates="profile")


class UserProfileUpdate(UserProfileBase):
    full_name: Optional[str] = None


class UserProfileRead(UserProfileBase):
    id: int
    user_id: int
    updated_at: str
    completeness_rate: int
    full_name: Optional[str] = None
    email: Optional[str] = None
