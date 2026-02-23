from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class AdminAuditLog(SQLModel, table=True):
    __tablename__ = "admin_audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    admin_id: int = Field(foreign_key="user.id", index=True)
    action: str = Field(index=True)
    target_type: str = Field(index=True)
    target_id: Optional[str] = Field(default=None)
    reason: Optional[str] = Field(default=None)
    meta_json: dict = Field(
        default_factory=dict,
        sa_column=sa.Column("meta", sa.JSON, nullable=False),
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)
