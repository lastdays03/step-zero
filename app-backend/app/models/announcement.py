from datetime import datetime, timezone
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
