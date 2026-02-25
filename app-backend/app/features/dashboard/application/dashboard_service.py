from datetime import datetime, timezone
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

    async def get_dashboard(
        self, *, team_id: UUID, user_name: str, is_guest: bool, roadmap_id: UUID | None = None,
    ) -> DashboardResult:
        if is_guest:
            return DashboardResult(
                user_name="Guest",
                current_phase={"title": "로드맵을 생성해 보세요", "progress": 0, "status": "GUEST"},
                roadmap=[
                    {"title": "Step 1: 아이디어 검증", "status": "locked", "date": "-"},
                    {"title": "Step 2: 법인 설립", "status": "locked", "date": "-"},
                    {"title": "Step 3: 비즈니스 계좌", "status": "locked", "date": "-"},
                ],
                stats={"days_left": 0, "tasks_completed": 0, "total_tasks": 0},
                growth_club={"founders_online": 1250},
            )

        if roadmap_id:
            latest_roadmap = await self.roadmap_repo.get_by_id_for_team(roadmap_id, team_id)
        else:
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

        step_ids = [step.id for step in steps if step.id is not None]
        detail_map = {}
        if step_ids:
            details = await self.roadmap_repo.list_step_details(step_ids)
            detail_map = {detail.roadmap_step_id: detail for detail in details}

        if current_step and current_step.id is not None:
            current_detail = detail_map.get(current_step.id)
            if current_detail and current_detail.phase:
                phase_title = current_detail.phase
        phase_status = "IN_PROGRESS" if current_step else "COMPLETED"

        phase_order: list[str] = []
        phase_stats: dict[str, dict[str, int]] = {}
        for step in steps:
            phase_name = step.title
            if step.id is not None:
                detail = detail_map.get(step.id)
                if detail and detail.phase:
                    phase_name = detail.phase
            if phase_name not in phase_stats:
                phase_order.append(phase_name)
                phase_stats[phase_name] = {"total": 0, "completed": 0}
            phase_stats[phase_name]["total"] += 1
            if step.status == "COMPLETED":
                phase_stats[phase_name]["completed"] += 1

        current_phase_idx = next(
            (
                idx
                for idx, phase_name in enumerate(phase_order)
                if phase_stats[phase_name]["completed"] < phase_stats[phase_name]["total"]
            ),
            None,
        )
        roadmap_items = []
        for idx, phase_name in enumerate(phase_order):
            stat = phase_stats[phase_name]
            if stat["completed"] == stat["total"]:
                status = "completed"
                date = latest_roadmap.created_at.strftime("%b %d")
            elif current_phase_idx is not None and idx == current_phase_idx:
                status = "current"
                date = "-"
            else:
                status = "locked"
                date = "-"
            roadmap_items.append({"title": phase_name, "status": status, "date": date})

        created_at = latest_roadmap.created_at.replace(tzinfo=timezone.utc) if latest_roadmap.created_at.tzinfo is None else latest_roadmap.created_at
        days_left = max(0, 30 - (datetime.now(timezone.utc) - created_at).days)

        return DashboardResult(
            user_name=user_name,
            current_phase={"title": phase_title, "progress": progress, "status": phase_status},
            roadmap=roadmap_items,
            stats={"days_left": days_left, "tasks_completed": tasks_completed, "total_tasks": total_tasks},
            growth_club={"founders_online": 12},
        )
