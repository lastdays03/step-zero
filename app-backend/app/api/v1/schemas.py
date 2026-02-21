from uuid import UUID

from pydantic import BaseModel, Field

from app.models.user import UserRead


class TeamRead(BaseModel):
    id: UUID
    name: str


class TokenWithTeams(BaseModel):
    access_token: str
    token_type: str
    user: UserRead
    current_team_id: UUID
    teams: list[TeamRead]


class CurrentPhase(BaseModel):
    title: str
    progress: int
    status: str


class RoadmapItem(BaseModel):
    title: str
    status: str
    date: str


class DashboardStats(BaseModel):
    days_left: int
    tasks_completed: int
    total_tasks: int


class GrowthClub(BaseModel):
    founders_online: int


class DashboardResponse(BaseModel):
    user_name: str
    current_phase: CurrentPhase
    roadmap: list[RoadmapItem]
    stats: DashboardStats
    growth_club: GrowthClub


class RoadmapCreateRequest(BaseModel):
    business_type: str
    location: str
    description: str = ""
    startup_type: str | None = None
    open_timeline: str | None = None
    budget_range: str | None = None
    additional_notes: str = ""
    goal_horizon_days: int = 30
    experience_level: str = "BEGINNER"


class RoadmapStepResponse(BaseModel):
    id: int
    title: str
    status: str


class RoadmapStepStatusUpdateRequest(BaseModel):
    status: str


class RoadmapStepActionUpdateRequest(BaseModel):
    completed: bool


class RoadmapResponse(BaseModel):
    roadmap_id: UUID
    title: str
    steps: list[RoadmapStepResponse]


class RoadmapStepActionResponse(BaseModel):
    id: int
    action_type: str
    title: str
    description: str
    source_url: str | None = None
    metadata_json: dict = Field(default_factory=dict)


class RoadmapStepDetailResponse(BaseModel):
    id: int
    phase: str
    objective: str
    estimated_days: int
    risk_notes: list[str]
    generation_mode: str
    actions: list[RoadmapStepActionResponse]


class RoadmapDetailStepResponse(BaseModel):
    id: int
    title: str
    status: str
    detail: RoadmapStepDetailResponse | None = None


class RoadmapDetailResponse(BaseModel):
    roadmap_id: UUID
    title: str
    steps: list[RoadmapDetailStepResponse]


class RoadmapJobCreateRequest(BaseModel):
    business_type: str
    location: str
    description: str = ""
    startup_type: str | None = None
    open_timeline: str | None = None
    budget_range: str | None = None
    additional_notes: str = ""
    goal_horizon_days: int = 30
    experience_level: str = "BEGINNER"


class RoadmapInputValidateRequest(BaseModel):
    business_type: str
    location: str
    description: str = ""


class RoadmapInputValidateResponse(BaseModel):
    valid: bool
    normalized_business_type: str | None = None
    normalized_location: str | None = None
    reason: str | None = None
    confidence: float = 0.0


class RoadmapJobResponse(BaseModel):
    job_id: UUID
    status: str
    stage: str
    progress: int
    roadmap_id: UUID | None = None
    error_code: str | None = None
    error_message: str | None = None


class RoadmapJobResultResponse(BaseModel):
    job_id: UUID
    status: str
    roadmap_id: UUID | None = None


class RagQueryRequest(BaseModel):
    question: str


class RagQueryResponse(BaseModel):
    answer: str
