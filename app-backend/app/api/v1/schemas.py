from uuid import UUID

from pydantic import BaseModel, Field

from app.models.user import UserRead


class TeamRead(BaseModel):
    id: UUID
    name: str


class TokenWithTeams(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserRead
    current_team_id: UUID
    teams: list[TeamRead]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


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


class RoadmapSummaryItem(BaseModel):
    roadmap_id: UUID
    title: str
    business_type: str
    location: str
    created_at: str
    progress: int
    total_steps: int
    completed_steps: int


class RoadmapListResponse(BaseModel):
    items: list[RoadmapSummaryItem]
    total: int


class RoadmapUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class RoadmapCreateRequest(BaseModel):
    business_type: str
    location: str
    description: str = ""
    startup_type: str | None = None
    startup_method: str | None = None
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
    source_count: int | None = None
    has_fallback: bool | None = None
    mapping_source: str | None = None
    actions: list[RoadmapStepActionResponse]


class RoadmapDetailStepResponse(BaseModel):
    id: int
    title: str
    status: str
    completed_at: str | None = None
    detail: RoadmapStepDetailResponse | None = None


class RoadmapDetailResponse(BaseModel):
    roadmap_id: UUID
    title: str
    created_at: str
    steps: list[RoadmapDetailStepResponse]


class RoadmapJobCreateRequest(BaseModel):
    business_type: str
    location: str
    description: str = ""
    startup_type: str | None = None
    startup_method: str | None = None
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


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    source: str


# ─── AI 코치 채팅 (Phase 4) ───


class StepChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    thread_id: UUID | None = None


class ThreadSummary(BaseModel):
    thread_id: UUID
    message_count: int
    created_at: str
    updated_at: str


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: list[dict] | None = None
    created_at: str
