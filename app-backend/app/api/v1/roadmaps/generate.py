from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.db import get_session
from app.features.roadmaps.application.roadmap_service import RoadmapService
from app.models.user import AuthenticatedUser
from app.repositories.roadmap_repository import RoadmapRepository

router = APIRouter()


class GenerationRequest(BaseModel):
    business_type: str
    location: str
    description: str


class RoadmapStepResponse(BaseModel):
    id: int
    title: str
    status: str


class GenerationResponse(BaseModel):
    roadmap_id: UUID
    title: str
    steps: list[RoadmapStepResponse]


@router.post("", response_model=GenerationResponse)
async def generate_roadmap(
    request: GenerationRequest,
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    team = await deps.get_current_team(current_user=current_user, session=session)
    if not team:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No team context")
    service = RoadmapService(roadmap_repo=RoadmapRepository(session))
    result = await service.create_roadmap(
        team_id=team.id,
        user_id=current_user.id,
        business_type=request.business_type,
        location=request.location,
        description=request.description,
    )
    return result.__dict__
