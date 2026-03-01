from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.user import User


class NotificationBase(SQLModel):
    user_id: int = Field(foreign_key="user.id", index=True)
    content: str
    type: str  # 'like', 'comment', 'reply'
    link: Optional[str] = None
    is_read: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    resource_id: Optional[int] = Field(default=None, index=True)


class Notification(NotificationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: User = Relationship()


class NotificationRead(NotificationBase):
    id: int
    created_at: datetime
