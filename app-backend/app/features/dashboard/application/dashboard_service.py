from datetime import datetime
from dataclasses import dataclass
from uuid import UUID

from app.repositories.roadmap_repository import RoadmapRepository


@dataclass
class DashboardResult:
    user_name: str
    current_phase: dict
    roadmap: list[dict]
    stats: dict
    growth_club: dict


class DashboardService:
    def __init__(self, roadmap_repo: RoadmapRepository):
        self.roadmap_repo = roadmap_repo

    async def get_dashboard(self, *, team_id: UUID, user_name: str, is_guest: bool) -> DashboardResult:
        if is_guest:
            return DashboardResult(
                user_name="Guest",
                current_phase={"title": "로드맵을 생성해 보세요", "progress": 0, "status": "GUEST"},
                roadmap=[
                    {"title": "Step 1: 아이디어 검증", "status": "LOCKED", "date": "-"},
                    {"title": "Step 2: 법인 설립", "status": "LOCKED", "date": "-"},
                    {"title": "Step 3: 비즈니스 계좌", "status": "LOCKED", "date": "-"},
                ],
                stats={"days_left": 0, "tasks_completed": 0, "total_tasks": 0},
                growth_club={"founders_online": 1250},
            )

        latest_roadmap = await self.roadmap_repo.get_latest_for_team(team_id)
        if not latest_roadmap:
            return DashboardResult(
                user_name=user_name,
                current_phase={"title": "로드맵을 생성해 보세요", "progress": 0, "status": "READY"},
                roadmap=[],
                stats={"days_left": 0, "tasks_completed": 0, "total_tasks": 0},
                growth_club={"founders_online": 12},
            )

        steps = await self.roadmap_repo.list_steps(latest_roadmap.id)
        total_tasks = len(steps)
        tasks_completed = len([step for step in steps if step.status == "COMPLETED"])
        progress = int((tasks_completed / total_tasks) * 100) if total_tasks else 0
        current_step = next((step for step in steps if step.status != "COMPLETED"), None)
        phase_title = current_step.title if current_step else "모든 단계 완료"
        phase_status = "IN_PROGRESS" if current_step else "COMPLETED"
        roadmap_items = [
            {
                "title": step.title,
                "status": step.status,
                "date": latest_roadmap.created_at.strftime("%b %d") if step.status == "COMPLETED" else "-",
            }
            for step in steps
        ]
        days_left = max(0, 30 - (datetime.utcnow() - latest_roadmap.created_at).days)

        return DashboardResult(
            user_name=user_name,
            current_phase={"title": phase_title, "progress": progress, "status": phase_status},
            roadmap=roadmap_items,
            stats={"days_left": days_left, "tasks_completed": tasks_completed, "total_tasks": total_tasks},
            growth_club={"founders_online": 12},
        )
