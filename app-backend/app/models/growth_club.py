from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Optional

from pydantic import model_validator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class AuthorRead(SQLModel):
    id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    nickname: Optional[str] = None
    profile_img: Optional[str] = None
    is_public: bool = True
    neighborhood: Optional[str] = None
    industry: Optional[str] = None
    is_suspended: bool = False
    suspended_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def from_user(cls, data: Any) -> Any:
        # data could be a User ORM object or a dict
        if isinstance(data, dict):
            profile = data.get("profile")
            if profile:
                data["nickname"] = profile.get("nickname")
                data["profile_img"] = profile.get("profile_img")
                data["industry"] = profile.get("category")
                data["neighborhood"] = profile.get("region")
            return data

        # If it's an object (User ORM)
        if hasattr(data, "profile") and data.profile:
            p = data.profile
            return {
                "id": getattr(data, "id", None),
                "full_name": getattr(data, "full_name", None),
                "email": getattr(data, "email", None),
                "username": getattr(data, "username", None),
                "nickname": getattr(p, "nickname", None),
                "profile_img": getattr(p, "profile_img", None),
                "is_public": getattr(p, "is_public", True),
                "industry": getattr(p, "category", None),
                "neighborhood": getattr(p, "region", None),
                "is_suspended": getattr(data, "is_suspended", False),
                "suspended_at": getattr(data, "suspended_at", None),
            }
        return data

    @model_validator(mode="after")
    def set_display_name(self) -> "AuthorRead":
        # Prioritize nickname if available
        if self.nickname:
            self.username = self.nickname
        elif not self.username:
            if self.full_name:
                self.username = self.full_name
            elif self.email and isinstance(self.email, str):
                parts = self.email.split("@")
                if parts:
                    self.username = parts[0]

            if not self.username:
                self.username = f"User_{self.id}"

        # Ensure profile_img has a default if None
        if not self.profile_img:
            self.profile_img = "default.png"

        return self

    def mask_privacy(self, current_user_id: Optional[int]) -> "AuthorRead":
        """
        내 프로필이 비공개(is_public=False)인 경우, 타인에게는 익명으로 표시함.
        작성자 본인에게는 항상 실제 정보가 보임.
        """
        if not self.is_public and self.id != current_user_id:
            self.nickname = "익명"
            self.username = "익명"
            self.full_name = "익명"
            self.email = None
            self.profile_img = "default.png"
            self.industry = None
            self.neighborhood = None
        return self


class GrowthClubPostBase(SQLModel):
    title: str
    content: str
    category: str
    neighborhood: Optional[str] = None
    industry: Optional[str] = None


class GrowthClubPostTagLink(SQLModel, table=True):
    post_id: int = Field(foreign_key="growthclubpost.id", primary_key=True)
    tag_id: int = Field(foreign_key="growthclubtag.id", primary_key=True)


class GrowthClubTag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    posts: list["GrowthClubPost"] = Relationship(
        back_populates="tags",
        link_model=GrowthClubPostTagLink,
    )


class GrowthClubPostLike(SQLModel, table=True):
    post_id: int = Field(foreign_key="growthclubpost.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


class GrowthClubPost(GrowthClubPostBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    report_count: int = Field(default=0)
    is_blinded: bool = Field(default=False)

    # Relationships
    author: "User" = Relationship()
    comments: list["GrowthClubComment"] = Relationship(
        back_populates="post", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    likes: list[GrowthClubPostLike] = Relationship(
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    attachments: list["GrowthClubPostAttachment"] = Relationship(
        back_populates="post",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    tags: list[GrowthClubTag] = Relationship(
        back_populates="posts",
        link_model=GrowthClubPostTagLink,
    )


class GrowthClubPostAttachment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="growthclubpost.id", index=True)
    kind: str = Field(default="file", index=True)  # image | file
    object_key: str
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    post: GrowthClubPost = Relationship(back_populates="attachments")


class GrowthClubCommentBase(SQLModel):
    content: str
    post_id: int = Field(foreign_key="growthclubpost.id", ondelete="CASCADE")
    parent_id: Optional[int] = Field(
        default=None, foreign_key="growthclubcomment.id", ondelete="CASCADE"
    )


class GrowthClubComment(GrowthClubCommentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    report_count: int = Field(default=0)
    is_blinded: bool = Field(default=False)

    post: GrowthClubPost = Relationship(back_populates="comments")
    author: "User" = Relationship()


class GrowthClubPostReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(
        foreign_key="growthclubpost.id", index=True, ondelete="CASCADE"
    )
    reporter_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    reason: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


class GrowthClubCommentReport(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    comment_id: int = Field(
        foreign_key="growthclubcomment.id", index=True, ondelete="CASCADE"
    )
    reporter_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    reason: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


class GrowthClubCommentRead(GrowthClubCommentBase):
    id: int
    author_id: int
    created_at: datetime
    author: AuthorRead
    report_count: int = 0
    report_reason: Optional[str] = None


class GrowthClubAttachmentRead(SQLModel):
    id: int
    kind: str
    object_key: str
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at: datetime


class GrowthClubPostRead(GrowthClubPostBase):
    id: int
    author_id: int
    created_at: datetime
    author: AuthorRead
    comments: list[GrowthClubCommentRead] = Field(default_factory=list)
    attachments: list[GrowthClubAttachmentRead] = Field(default_factory=list)
    report_count: int
    report_reason: Optional[str] = None
    likes_count: int = 0
    is_liked: bool = False
