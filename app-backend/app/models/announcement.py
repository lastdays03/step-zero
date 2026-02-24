from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel, Column, Text
import sqlalchemy as sa

ops_announcement_meta = sa.MetaData()

class OpsAnnouncement(SQLModel, table=True):
    __tablename__ = "ops_announcement"
    metadata = ops_announcement_meta
    __table_args__ = {"extend_existing": True}

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    content: str = Field(sa_column=Column(Text))
    status: str = Field(default="draft", index=True) # draft, published, archived
    published_at: Optional[datetime] = Field(default=None, index=True)
    admin_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
