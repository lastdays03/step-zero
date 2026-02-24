from datetime import datetime, timezone
from typing import Optional, Any
from sqlmodel import Field, SQLModel, Column, JSON

class OpsAuditLog(SQLModel, table=True):
    __tablename__ = "ops_audit_log"
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    admin_id: int = Field(foreign_key="user.id", index=True)
    action: str = Field(index=True) # e.g., ANNOUNCEMENT_CREATED
    target_type: str = Field(index=True) # e.g., announcement
    target_id: Optional[str] = Field(default=None, index=True)
    description: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON), sa_column_kwargs={"name": "metadata"})
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
