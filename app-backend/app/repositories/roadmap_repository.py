from uuid import UUID
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap import Roadmap, RoadmapStep, RoadmapStepAction, RoadmapStepDetail


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

    async def get_step_for_team(self, step_id: int, team_id: UUID) -> RoadmapStep | None:
        stmt = (
            select(RoadmapStep)
            .join(Roadmap, Roadmap.id == RoadmapStep.roadmap_id)
            .where(
                RoadmapStep.id == step_id,
                Roadmap.team_id == team_id,
                Roadmap.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_step_action_for_team(
        self,
        *,
        step_id: int,
        action_id: int,
        team_id: UUID,
    ) -> RoadmapStepAction | None:
        stmt = (
            select(RoadmapStepAction)
            .join(RoadmapStep, RoadmapStep.id == RoadmapStepAction.roadmap_step_id)
            .join(Roadmap, Roadmap.id == RoadmapStep.roadmap_id)
            .where(
                RoadmapStep.id == step_id,
                RoadmapStepAction.id == action_id,
                Roadmap.team_id == team_id,
                Roadmap.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

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

    async def create_steps_with_details(
        self,
        *,
        roadmap_id: UUID,
        steps_payload: list[dict],
        generation_mode: str = "RAG",
    ) -> list[RoadmapStep]:
        created_steps: list[RoadmapStep] = []
        for idx, payload in enumerate(steps_payload, start=1):
            step = RoadmapStep(
                roadmap_id=roadmap_id,
                step_order=idx,
                title=payload.get("title", f"Step {idx}"),
                status=payload.get("status", "PENDING"),
            )
            self.session.add(step)
            await self.session.flush()

            detail = RoadmapStepDetail(
                roadmap_step_id=step.id,
                phase=payload.get("phase", "기본"),
                objective=payload.get("objective", ""),
                estimated_days=int(payload.get("estimated_days") or 0),
                risk_notes=payload.get("risk_notes", []),
                generation_mode=generation_mode,
            )
            self.session.add(detail)

            for item in payload.get("checklist", []):
                action = RoadmapStepAction(
                    roadmap_step_id=step.id,
                    action_type="CHECKLIST",
                    title=str(item),
                    description="",
                    metadata_json={},
                )
                self.session.add(action)

            for item in payload.get("legal_basis", []):
                action = RoadmapStepAction(
                    roadmap_step_id=step.id,
                    action_type="LEGAL_BASIS",
                    title=str(item.get("title", "근거")),
                    description=str(item.get("snippet", "")),
                    source_url=item.get("source_url"),
                    metadata_json=item,
                )
                self.session.add(action)

            for item in payload.get("documents", []):
                action = RoadmapStepAction(
                    roadmap_step_id=step.id,
                    action_type="DOCUMENT",
                    title=str(item.get("name", "서류")),
                    description=str(item.get("type", "")),
                    source_url=item.get("source_url"),
                    metadata_json=item,
                )
                self.session.add(action)

            created_steps.append(step)
        return created_steps

    async def list_step_details(self, roadmap_step_ids: list[int]) -> list[RoadmapStepDetail]:
        if not roadmap_step_ids:
            return []
        stmt = select(RoadmapStepDetail).where(RoadmapStepDetail.roadmap_step_id.in_(roadmap_step_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_step_actions(self, roadmap_step_ids: list[int]) -> list[RoadmapStepAction]:
        if not roadmap_step_ids:
            return []
        stmt = (
            select(RoadmapStepAction)
            .where(RoadmapStepAction.roadmap_step_id.in_(roadmap_step_ids))
            .order_by(RoadmapStepAction.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self.session.commit()
