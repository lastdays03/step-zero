from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any

from pydantic import model_validator
from sqlmodel import Field, Relationship, SQLModel

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
        # data could be dict or User ORM object
        if hasattr(data, "profile") and data.profile:
            obj_dict: dict[str, Any] = {k: getattr(data, k) for k in data.__class__.__table__.columns.keys()} if hasattr(data, "__table__") else dict(data)
            
            is_public = getattr(data.profile, "is_public", True)
            if is_public:
                if getattr(data.profile, "nickname", None):
                    obj_dict["username"] = data.profile.nickname
                if getattr(data.profile, "profile_img", None):
                    obj_dict["profile_img"] = data.profile.profile_img
            else:
                obj_dict["username"] = "익명"
                obj_dict["profile_img"] = "default.png"
                
            return obj_dict
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
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GrowthClubPost(GrowthClubPostBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    report_count: int = Field(default=0)
    is_blinded: bool = Field(default=False)
    
    # Relationships
    author: "User" = Relationship()
    comments: list["GrowthClubComment"] = Relationship(
        back_populates="post", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    likes: list[GrowthClubPostLike] = Relationship(sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    attachments: list["GrowthClubPostAttachment"] = Relationship(
        back_populates="post",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class GrowthClubPostAttachment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="growthclubpost.id", index=True)
    kind: str = Field(default="file", index=True)  # image | file
    object_key: str
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    post: GrowthClubPost = Relationship(back_populates="attachments")


class GrowthClubCommentBase(SQLModel):
    content: str
    post_id: int = Field(foreign_key="growthclubpost.id")
    parent_id: Optional[int] = Field(default=None, foreign_key="growthclubcomment.id")

class GrowthClubComment(GrowthClubCommentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
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
    report_count: int
    likes_count: int = 0
    is_liked: bool = False
