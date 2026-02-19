from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.v1.schemas import RoadmapResponse
from app.core.db import get_session
from app.models.team import Team
from app.repositories.roadmap_repository import RoadmapRepository

router = APIRouter()


@router.get("/{roadmap_id}", response_model=RoadmapResponse)
async def get_roadmap(
    roadmap_id: UUID,
    current_team: Team = Depends(deps.get_current_team),
    session: AsyncSession = Depends(get_session),
) -> Any:
    repo = RoadmapRepository(session)
    roadmap = await repo.get_by_id_for_team(roadmap_id, current_team.id)
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
    steps = await repo.list_steps(roadmap.id)
    return {
        "roadmap_id": roadmap.id,
        "title": roadmap.title,
        "steps": [{"id": step.id, "title": step.title, "status": step.status} for step in steps],
    }
