from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class Roadmap(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    team_id: UUID = Field(foreign_key="team.id", index=True)
    title: str
    business_type: str
    location: str
    description: str = ""
    startup_type: str | None = None
    open_timeline: str | None = None
    budget_range: str | None = None
    additional_notes: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    deleted_at: datetime | None = None
    created_by: Optional[int] = Field(default=None, foreign_key="user.id")
    updated_by: Optional[int] = Field(default=None, foreign_key="user.id")


class RoadmapStep(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roadmap_id: UUID = Field(foreign_key="roadmap.id", index=True)
    step_order: int = Field(index=True)
    title: str
    status: str = "PENDING"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class RoadmapGenerationJob(SQLModel, table=True):
    __tablename__ = "roadmap_generation_jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    team_id: UUID = Field(foreign_key="team.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    status: str = Field(default="QUEUED", index=True)
    progress: int = Field(default=0)
    stage: str = Field(default="QUEUED")
    input_payload: dict = Field(default_factory=dict, sa_column=sa.Column(sa.JSON, nullable=False))
    error_code: str | None = None
    error_message: str | None = None
    roadmap_id: UUID | None = Field(default=None, foreign_key="roadmap.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RoadmapStepDetail(SQLModel, table=True):
    __tablename__ = "roadmap_step_details"

    id: Optional[int] = Field(default=None, primary_key=True)
    roadmap_step_id: int = Field(foreign_key="roadmapstep.id", index=True, unique=True)
    phase: str = Field(default="기본")
    objective: str = Field(default="")
    estimated_days: int = Field(default=0)
    risk_notes: list[str] = Field(default_factory=list, sa_column=sa.Column(sa.JSON, nullable=False))
    generation_mode: str = Field(default="RAG")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class RoadmapStepAction(SQLModel, table=True):
    __tablename__ = "roadmap_step_actions"

    id: Optional[int] = Field(default=None, primary_key=True)
    roadmap_step_id: int = Field(foreign_key="roadmapstep.id", index=True)
    action_type: str = Field(index=True)  # CHECKLIST | LEGAL_BASIS | DOCUMENT
    title: str
    description: str = Field(default="")
    source_url: str | None = None
    metadata_json: dict = Field(default_factory=dict, sa_column=sa.Column(sa.JSON, nullable=False))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
