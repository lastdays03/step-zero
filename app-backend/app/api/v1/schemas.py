from uuid import UUID

from pydantic import BaseModel

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
    description: str


class RoadmapStepResponse(BaseModel):
    id: int
    title: str
    status: str


class RoadmapResponse(BaseModel):
    roadmap_id: UUID
    title: str
    steps: list[RoadmapStepResponse]


class RagQueryRequest(BaseModel):
    question: str


class RagQueryResponse(BaseModel):
    answer: str
