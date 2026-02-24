from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    action: str = Field(index=True)  # ex: "growth_club.post.unblind"
    target_type: str = Field(index=True)  # ex: "post", "comment"
    target_id: str = Field(index=True)
    details: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now())

    user: "User" = Relationship()

class AuditLogRead(SQLModel):
    id: int
    user_id: int
    actor_name: str
    action: str
    target_type: str
    target_id: str
    details: Optional[str]
    created_at: datetime
