from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class RoadmapTemplate(SQLModel, table=True):
    __tablename__ = "roadmap_templates"
    __table_args__ = (
        Index(
            "ix_roadmap_templates_btype_smethod_status",
            "business_type",
            "startup_method",
            "status",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    business_type: str = Field(index=True)
    startup_method: str | None = Field(default=None, index=True)
    title: str
    status: str = Field(default="DRAFT", index=True)
    version: int = Field(default=1)
    source_roadmap_id: UUID | None = Field(
        default=None, foreign_key="roadmap.id", ondelete="SET NULL"
    )
    created_by: int = Field(foreign_key="user.id")
    approved_by: Optional[int] = Field(default=None, foreign_key="user.id")
    approved_at: datetime | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


class RoadmapTemplateStep(SQLModel, table=True):
    __tablename__ = "roadmap_template_steps"

    id: Optional[int] = Field(default=None, primary_key=True)
    template_id: int = Field(
        foreign_key="roadmap_templates.id", index=True, ondelete="CASCADE"
    )
    step_order: int
    phase: str
    title: str
    objective: str = Field(default="")
    estimated_days: int = Field(default=0)
    risk_notes: list[str] = Field(
        default_factory=list, sa_column=sa.Column(sa.JSON, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


class RoadmapTemplateAction(SQLModel, table=True):
    __tablename__ = "roadmap_template_actions"

    id: Optional[int] = Field(default=None, primary_key=True)
    template_step_id: int = Field(
        foreign_key="roadmap_template_steps.id", index=True, ondelete="CASCADE"
    )
    action_type: str = Field(index=True)  # CHECKLIST | LEGAL_BASIS | DOCUMENT
    title: str
    description: str = Field(default="")
    source_url: str | None = None
    actionkit_item_id: Optional[int] = Field(
        default=None, foreign_key="actionkit_items.id", ondelete="SET NULL"
    )
    actionkit_file_id: Optional[int] = Field(
        default=None, foreign_key="actionkit_files.id", ondelete="SET NULL"
    )
    sort_order: int = Field(default=0)
    metadata_json: dict = Field(
        default_factory=dict, sa_column=sa.Column(sa.JSON, nullable=False)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
