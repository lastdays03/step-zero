from uuid import UUID
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap import Roadmap, RoadmapStep


class RoadmapRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_latest_for_team(self, team_id: UUID) -> Roadmap | None:
        stmt = (
            select(Roadmap)
            .where(Roadmap.team_id == team_id, Roadmap.deleted_at.is_(None))
            .order_by(Roadmap.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_team(self, roadmap_id: UUID, team_id: UUID) -> Roadmap | None:
        stmt = select(Roadmap).where(
            Roadmap.id == roadmap_id,
            Roadmap.team_id == team_id,
            Roadmap.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_steps(self, roadmap_id: UUID) -> list[RoadmapStep]:
        step_stmt = (
            select(RoadmapStep)
            .where(RoadmapStep.roadmap_id == roadmap_id)
            .order_by(RoadmapStep.step_order.asc())
        )
        step_result = await self.session.execute(step_stmt)
        return list(step_result.scalars().all())

    async def create_roadmap(
        self,
        *,
        team_id: UUID,
        title: str,
        business_type: str,
        location: str,
        description: str,
        created_by: int,
    ) -> Roadmap:
        roadmap = Roadmap(
            team_id=team_id,
            title=title,
            business_type=business_type,
            location=location,
            description=description,
            created_by=created_by,
            updated_by=created_by,
        )
        self.session.add(roadmap)
        await self.session.flush()
        return roadmap

    async def create_steps(self, roadmap_id: UUID, step_titles: list[str]) -> list[RoadmapStep]:
        steps: list[RoadmapStep] = []
        for idx, step_title in enumerate(step_titles, start=1):
            step = RoadmapStep(
                roadmap_id=roadmap_id,
                step_order=idx,
                title=step_title,
                status="PENDING",
            )
            self.session.add(step)
            await self.session.flush()
            steps.append(step)
        return steps

    async def commit(self) -> None:
        await self.session.commit()
