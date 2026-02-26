from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, Any

from pydantic import model_validator, field_validator
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import inspect

if TYPE_CHECKING:
    from app.models.user import User


class AuthorRead(SQLModel):
    id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    neighborhood: Optional[str] = None
    industry: Optional[str] = None
    profile_img: Optional[str] = "default.png"

    @model_validator(mode="before")
    @classmethod
    def extract_profile_data(cls, data: Any) -> Any:
        # If it's an ORM object, we want to extract profile data without losing other fields
        if hasattr(data, "_sa_instance_state"):
            try:
                state = inspect(data)
                # Ensure profile is loaded
                if state and "profile" not in state.unloaded:
                    profile = getattr(data, "profile", None)
                    if profile:
                        # Find existing values or use profile values
                        is_public = getattr(profile, "is_public", True)
                        
                        # We don't return a dict here to avoid losing data.
                        # Instead, we rely on the fact that Pydantic will call getattr(data, "username") etc.
                        # But "username" is not an ORM column on User.
                        # So we might need to return a dict or use a property.
                        
                        # Option: return a proxy-like dict or a full dict
                        obj_dict = {k: getattr(data, k) for k in data.__class__.__table__.columns.keys()}
                        
                        if is_public:
                            obj_dict["username"] = getattr(profile, "nickname", None)
                            obj_dict["profile_img"] = getattr(profile, "profile_img", "default.png")
                            obj_dict["neighborhood"] = getattr(profile, "region", None)
                            obj_dict["industry"] = getattr(profile, "category", None)
                        else:
                            obj_dict["username"] = "익명"
                            obj_dict["profile_img"] = "default.png"
                            obj_dict["neighborhood"] = None
                            obj_dict["industry"] = None
                        
                        # Add email if available (it should be a column)
                        if "email" not in obj_dict:
                            obj_dict["email"] = getattr(data, "email", None)
                        if "full_name" not in obj_dict:
                            obj_dict["full_name"] = getattr(data, "full_name", None)
                            
                        return obj_dict
            except Exception:
                pass
        return data

    @model_validator(mode="after")
    def set_username(self) -> "AuthorRead":
        if not self.username:
            if self.full_name:
                self.username = self.full_name
            elif self.email is not None and isinstance(self.email, str):
                self.username = self.email.split("@")[0]
            else:
                self.username = f"User_{self.id}"
        return self


class GrowthClubPostBase(SQLModel):
    title: str
    content: str
    category: str
    neighborhood: Optional[str] = None
    industry: Optional[str] = None

class GrowthClubPostLike(SQLModel, table=True):
    post_id: int = Field(foreign_key="growthclubpost.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class GrowthClubPostReport(SQLModel, table=True):
    post_id: int = Field(foreign_key="growthclubpost.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GrowthClubPostTagLink(SQLModel, table=True):
    post_id: Optional[int] = Field(
        default=None, foreign_key="growthclubpost.id", primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="growthclubtag.id", primary_key=True
    )

class GrowthClubTag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    posts: list["GrowthClubPost"] = Relationship(
        back_populates="tags", link_model=GrowthClubPostTagLink
    )

class GrowthClubPost(GrowthClubPostBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    report_count: int = Field(default=0)
    is_blinded: bool = Field(default=False)

    # Relationships
    author: "User" = Relationship()
    comments: list["GrowthClubComment"] = Relationship(
        back_populates="post",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    likes: list[GrowthClubPostLike] = Relationship(sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    reports: list["GrowthClubPostReport"] = Relationship(sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    attachments: list["GrowthClubPostAttachment"] = Relationship(
        back_populates="post",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    tags: list[GrowthClubTag] = Relationship(
        back_populates="posts", link_model=GrowthClubPostTagLink
    )


class GrowthClubPostAttachment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="growthclubpost.id", index=True)
    kind: str = Field(default="file", index=True)  # image | file
    object_key: str
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    post: GrowthClubPost = Relationship(back_populates="attachments")


class GrowthClubCommentBase(SQLModel):
    content: str
    post_id: int = Field(foreign_key="growthclubpost.id")
    parent_id: Optional[int] = Field(default=None, foreign_key="growthclubcomment.id")

class GrowthClubComment(GrowthClubCommentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    report_count: int = Field(default=0)
    is_blinded: bool = Field(default=False)

    post: GrowthClubPost = Relationship(back_populates="comments")
    author: "User" = Relationship()
    
    parent: Optional["GrowthClubComment"] = Relationship(
        back_populates="replies",
        sa_relationship_kwargs={"remote_side": "GrowthClubComment.id"}
    )
    replies: list["GrowthClubComment"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class GrowthClubCommentRead(GrowthClubCommentBase):
    id: int
    author_id: int
    created_at: datetime
    author: AuthorRead


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
    tags: list[str] = Field(default_factory=list)
    report_count: int
    likes_count: int = 0
    is_liked: bool = False
    is_reported: bool = False

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: Any) -> list[str]:
        if isinstance(v, list) and len(v) > 0:
            # If it's a list of GrowthClubTag objects, extract names
            if hasattr(v[0], "name"):
                return [tag.name for tag in v]
        return v
