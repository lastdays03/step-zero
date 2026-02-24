import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

class NotificationBase(SQLModel):
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="CASCADE")
    actor_id: Optional[int] = Field(default=None, foreign_key="user.id", ondelete="SET NULL")
    action_type: str  # e.g., "LIKE", "COMMENT", "REPLY"
    target_id: Optional[int] = None # ID of the post or comment
    target_type: Optional[str] = None # "POST" or "COMMENT" 
    message: str
    is_read: bool = Field(default=False)

class Notification(NotificationBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class NotificationRead(NotificationBase):
    id: int
    created_at: datetime.datetime
