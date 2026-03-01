from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ── Response schemas ──


class RoadmapTemplateActionResponse(BaseModel):
    id: int
    template_step_id: int
    action_type: str
    title: str
    description: str
    source_url: str | None
    actionkit_item_id: int | None
    actionkit_file_id: int | None
    sort_order: int
    metadata_json: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoadmapTemplateStepResponse(BaseModel):
    id: int
    template_id: int
    step_order: int
    phase: str
    title: str
    objective: str
    estimated_days: int
    risk_notes: list[str]
    created_at: datetime
    actions: list[RoadmapTemplateActionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class RoadmapTemplateResponse(BaseModel):
    id: int
    business_type: str
    startup_method: str | None
    title: str
    status: str
    version: int
    source_roadmap_id: UUID | None
    created_by: int
    approved_by: int | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoadmapTemplateDetailResponse(RoadmapTemplateResponse):
    steps: list[RoadmapTemplateStepResponse] = []


class RoadmapTemplateSummaryResponse(BaseModel):
    total: int
    draft: int
    review: int
    approved: int
    archived: int


# ── Request schemas ──


class RoadmapTemplateCreateFromRoadmapRequest(BaseModel):
    roadmap_id: UUID


class RoadmapTemplateUpdateRequest(BaseModel):
    title: str | None = None
    business_type: str | None = None
    startup_method: str | None = None


class RoadmapTemplateStatusUpdateRequest(BaseModel):
    new_status: str
    reason: str | None = None


class RoadmapTemplateActionCreateRequest(BaseModel):
    action_type: str = "CHECKLIST"
    title: str
    description: str = ""
    source_url: str | None = None
    actionkit_item_id: int | None = None
    actionkit_file_id: int | None = None
    sort_order: int = 0
    metadata_json: dict = {}


class RoadmapTemplateActionUpdateRequest(BaseModel):
    action_type: str | None = None
    title: str | None = None
    description: str | None = None
    source_url: str | None = None
    actionkit_item_id: int | None = None
    actionkit_file_id: int | None = None
    sort_order: int | None = None
    metadata_json: dict | None = None
