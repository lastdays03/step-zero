
from datetime import datetime
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.core.db import get_session
from app.models.roadmap import Roadmap, RoadmapStep as RoadmapStepModel
from app.models.user import AuthenticatedUser

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
    steps: List[RoadmapStepResponse]


def build_default_steps(business_type: str, location: str) -> list[str]:
    return [
        f"{business_type} 시장 조사",
        f"{location} 입지 및 규제 확인",
        "사업자 등록 및 인허가 준비",
    ]

@router.post("", response_model=GenerationResponse)
async def generate_roadmap(
    request: GenerationRequest,
    current_user: AuthenticatedUser = Depends(deps.get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Any:
    """
    Generate and persist roadmap based on user input.
    """
    title = f"{request.business_type} 창업 로드맵"
    now = datetime.utcnow()
    roadmap = Roadmap(
        user_id=current_user.id,
        title=title,
        business_type=request.business_type,
        location=request.location,
        description=request.description,
        created_at=now,
        updated_at=now,
    )
    session.add(roadmap)
    await session.flush()

    created_steps: list[RoadmapStepModel] = []
    for idx, step_title in enumerate(
        build_default_steps(request.business_type, request.location), start=1
    ):
        step = RoadmapStepModel(
            roadmap_id=roadmap.id,
            step_order=idx,
            title=step_title,
            status="PENDING",
        )
        session.add(step)
        await session.flush()
        created_steps.append(step)

    await session.commit()

    return {
        "roadmap_id": roadmap.id,
        "title": title,
        "steps": [
            {"id": step.id, "title": step.title, "status": step.status}
            for step in created_steps
        ],
    }
