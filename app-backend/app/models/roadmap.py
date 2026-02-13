from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Roadmap(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str
    business_type: str
    location: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RoadmapStep(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roadmap_id: UUID = Field(foreign_key="roadmap.id", index=True)
    step_order: int = Field(index=True)
    title: str
    status: str = "PENDING"
    created_at: datetime = Field(default_factory=datetime.utcnow)
