from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel



class UserDisciplineHistory(SQLModel, table=True):
    __tablename__ = "user_discipline_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    admin_id: int = Field(foreign_key="user.id")
    prev_status: str
    new_status: str
    reason: str
    suspended_until: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
