
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api import deps
from app.core.db import get_session
from app.models.roadmap import Roadmap, RoadmapStep
from app.models.user import AuthenticatedUser

router = APIRouter()


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
    roadmap: List[RoadmapItem]
    stats: DashboardStats
    growth_club: GrowthClub


@router.get("", response_model=DashboardResponse)
async def get_dashboard_stats(
    current_user: AuthenticatedUser | None = Depends(deps.get_optional_current_user),
    session: AsyncSession = Depends(get_session),
) -> DashboardResponse:
    """
    Get dashboard statistics and roadmap summary.
    If no user is logged in, return guest data.
    """
    if not current_user:
        # Guest Data
        return DashboardResponse(
            user_name="Guest",
            current_phase=CurrentPhase(
                title="로드맵을 생성해 보세요",
                progress=0,
                status="GUEST",
            ),
            roadmap=[
                RoadmapItem(title="Step 1: 아이디어 검증", status="LOCKED", date="-"),
                RoadmapItem(title="Step 2: 법인 설립", status="LOCKED", date="-"),
                RoadmapItem(title="Step 3: 비즈니스 계좌", status="LOCKED", date="-"),
            ],
            stats=DashboardStats(days_left=0, tasks_completed=0, total_tasks=0),
            growth_club=GrowthClub(founders_online=1250),
        )

    roadmap_result = await session.execute(
        select(Roadmap)
        .where(Roadmap.user_id == current_user.id)
        .order_by(Roadmap.created_at.desc())
        .limit(1)
    )
    latest_roadmap = roadmap_result.scalar_one_or_none()
    if not latest_roadmap:
        return DashboardResponse(
            user_name=current_user.full_name or current_user.email.split("@")[0],
            current_phase=CurrentPhase(
                title="로드맵을 생성해 보세요",
                progress=0,
                status="READY",
            ),
            roadmap=[],
            stats=DashboardStats(days_left=0, tasks_completed=0, total_tasks=0),
            growth_club=GrowthClub(founders_online=12),
        )

    step_result = await session.execute(
        select(RoadmapStep)
        .where(RoadmapStep.roadmap_id == latest_roadmap.id)
        .order_by(RoadmapStep.step_order.asc())
    )
    steps = list(step_result.scalars().all())

    total_tasks = len(steps)
    tasks_completed = len([step for step in steps if step.status == "COMPLETED"])
    progress = int((tasks_completed / total_tasks) * 100) if total_tasks else 0
    current_step = next((step for step in steps if step.status != "COMPLETED"), None)
    phase_title = current_step.title if current_step else "모든 단계 완료"
    phase_status = "IN_PROGRESS" if current_step else "COMPLETED"

    roadmap_items = [
        RoadmapItem(
            title=step.title,
            status=step.status,
            date=latest_roadmap.created_at.strftime("%b %d")
            if step.status == "COMPLETED"
            else "-",
        )
        for step in steps
    ]

    days_left = max(0, 30 - (datetime.utcnow() - latest_roadmap.created_at).days)

    return DashboardResponse(
        user_name=current_user.full_name or current_user.email.split("@")[0],
        current_phase=CurrentPhase(
            title=phase_title,
            progress=progress,
            status=phase_status,
        ),
        roadmap=roadmap_items,
        stats=DashboardStats(
            days_left=days_left,
            tasks_completed=tasks_completed,
            total_tasks=total_tasks,
        ),
        growth_club=GrowthClub(founders_online=12),
    )
