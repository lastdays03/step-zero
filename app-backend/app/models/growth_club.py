from datetime import datetime
from typing import TYPE_CHECKING, Optional

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
    image_path: Optional[str] = None
    file_path: Optional[str] = None

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


class GrowthClubCommentRead(GrowthClubCommentBase):
    id: int
    author_id: int
    created_at: datetime
    author: AuthorRead


class GrowthClubPostRead(GrowthClubPostBase):
    id: int
    author_id: int
    created_at: datetime
    author: AuthorRead
    comments: list[GrowthClubCommentRead] = Field(default_factory=list)
    report_count: int
    likes_count: int = 0
    is_liked: bool = False
