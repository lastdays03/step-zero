from dataclasses import dataclass
from uuid import UUID

from app.repositories.roadmap_repository import RoadmapRepository


@dataclass
class RoadmapCreationResult:
    roadmap_id: UUID
    title: str
    steps: list[dict]


def build_default_steps(business_type: str, location: str) -> list[str]:
    return [
        f"{business_type} 시장 조사",
        f"{location} 입지 및 규제 확인",
        "사업자 등록 및 인허가 준비",
    ]


class RoadmapService:
    def __init__(self, roadmap_repo: RoadmapRepository):
        self.roadmap_repo = roadmap_repo

    async def create_roadmap(
        self,
        *,
        team_id: UUID,
        user_id: int,
        business_type: str,
        location: str,
        description: str,
        startup_type: str | None = None,
        open_timeline: str | None = None,
        budget_range: str | None = None,
        additional_notes: str = "",
    ) -> RoadmapCreationResult:
        title = f"{business_type} 창업 로드맵"
        roadmap = await self.roadmap_repo.create_roadmap(
            team_id=team_id,
            title=title,
            business_type=business_type,
            location=location,
            description=description,
            startup_type=startup_type,
            open_timeline=open_timeline,
            budget_range=budget_range,
            additional_notes=additional_notes,
            created_by=user_id,
        )
        steps = await self.roadmap_repo.create_steps(
            roadmap_id=roadmap.id,
            step_titles=build_default_steps(business_type, location),
        )
        await self.roadmap_repo.commit()
        return RoadmapCreationResult(
            roadmap_id=roadmap.id,
            title=title,
            steps=[{"id": step.id, "title": step.title, "status": step.status} for step in steps],
        )
