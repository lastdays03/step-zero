from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Announcement(SQLModel, table=True):
    __tablename__ = "announcements"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    status: str = Field(default="draft", index=True)  # draft | published | archived
    created_by: int = Field(foreign_key="user.id", index=True)
    updated_by: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    published_at: Optional[datetime] = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
