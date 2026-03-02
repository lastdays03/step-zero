from datetime import datetime

from app.core.security import utc_now
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.roadmap import (
    Roadmap,
    RoadmapStep,
    RoadmapStepAction,
    RoadmapStepDetail,
)


class RoadmapRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _resolve_document_source_url(item: dict) -> str | None:
        # Prefer item_id-based URL for consistent linking
        item_id = item.get("actionkit_item_id")
        if item_id:
            return f"/api/v1/actionkits/items/{item_id}"
        for key in ("source_url", "download_url", "template_url", "file_url"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return None

    async def get_latest_for_team(self, team_id: UUID) -> Roadmap | None:
        stmt = (
            select(Roadmap)
            .where(Roadmap.team_id == team_id, Roadmap.deleted_at.is_(None))
            .order_by(Roadmap.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_team(
        self, roadmap_id: UUID, team_id: UUID
    ) -> Roadmap | None:
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

    async def get_step_for_team(
        self, step_id: int, team_id: UUID
    ) -> RoadmapStep | None:
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
        startup_type: str | None = None,
        startup_method: str | None = None,
        open_timeline: str | None = None,
        budget_range: str | None = None,
        additional_notes: str = "",
    ) -> Roadmap:
        roadmap = Roadmap(
            team_id=team_id,
            title=title,
            business_type=business_type,
            location=location,
            description=description,
            startup_type=startup_type,
            startup_method=startup_method,
            open_timeline=open_timeline,
            budget_range=budget_range,
            additional_notes=additional_notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self.session.add(roadmap)
        await self.session.flush()
        return roadmap

    async def create_steps(
        self, roadmap_id: UUID, step_titles: list[str]
    ) -> list[RoadmapStep]:
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

    @staticmethod
    def _build_actionkit_metadata(item: dict, action_type: str) -> dict:
        """Build metadata_json with ActionKit traceability fields.

        Adds ``actionkit_item_id``, ``actionkit_file_id``,
        ``actionkit_highlight_id``, ``actionkit_domain``,
        ``actionkit_category``, and ``mapping_source`` when present.
        Backward-compatible: old data without these fields is unaffected.
        """
        metadata = dict(item)

        # Ensure mapping_source is present (default to llm_generated)
        if "mapping_source" not in metadata:
            metadata["mapping_source"] = "llm_generated"

        # For LEGAL_BASIS: extract actionkit_item_id
        if action_type == "LEGAL_BASIS":
            for key in ("actionkit_item_id", "actionkit_domain", "actionkit_category"):
                if key in item:
                    metadata[key] = item[key]

        # For DOCUMENT: extract actionkit_item_id and actionkit_file_id
        elif action_type == "DOCUMENT":
            for key in ("actionkit_item_id", "actionkit_file_id"):
                if key in item:
                    metadata[key] = item[key]

        # For CHECKLIST: extract actionkit_item_id and actionkit_highlight_id
        elif action_type == "CHECKLIST":
            for key in ("actionkit_item_id", "actionkit_highlight_id"):
                if key in item:
                    metadata[key] = item[key]

        return metadata

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
                source_count=payload.get("source_count"),
                has_fallback=payload.get("has_fallback"),
                mapping_source=payload.get("mapping_source"),
            )
            self.session.add(detail)

            # Determine step-level mapping_source for checklist items
            step_mapping_source = payload.get("mapping_source", "llm_generated")

            for item in payload.get("checklist", []):
                if isinstance(item, str):
                    checklist_metadata = {
                        "mapping_source": step_mapping_source,
                    }
                    # Propagate actionkit_items from step payload if available
                    actionkit_items = payload.get("actionkit_items", [])
                    if actionkit_items:
                        checklist_metadata["actionkit_item_ids"] = actionkit_items
                    action = RoadmapStepAction(
                        roadmap_step_id=step.id,
                        action_type="CHECKLIST",
                        title=str(item),
                        description="",
                        metadata_json=checklist_metadata,
                    )
                else:
                    # dict-style checklist item (future extension)
                    action = RoadmapStepAction(
                        roadmap_step_id=step.id,
                        action_type="CHECKLIST",
                        title=str(item.get("title", item)),
                        description=str(item.get("description", "")),
                        metadata_json=self._build_actionkit_metadata(item, "CHECKLIST"),
                    )
                self.session.add(action)

            for item in payload.get("legal_basis", []):
                metadata_json = self._build_actionkit_metadata(item, "LEGAL_BASIS")
                action = RoadmapStepAction(
                    roadmap_step_id=step.id,
                    action_type="LEGAL_BASIS",
                    title=str(item.get("title", "근거")),
                    description=str(item.get("snippet", "")),
                    source_url=item.get("source_url"),
                    metadata_json=metadata_json,
                )
                self.session.add(action)

            for item in payload.get("documents", []):
                source_url = self._resolve_document_source_url(item)
                metadata_json = self._build_actionkit_metadata(item, "DOCUMENT")
                action = RoadmapStepAction(
                    roadmap_step_id=step.id,
                    action_type="DOCUMENT",
                    title=str(item.get("name", "서류")),
                    description=str(item.get("type", "")),
                    source_url=source_url,
                    metadata_json=metadata_json,
                )
                self.session.add(action)

            created_steps.append(step)
        return created_steps

    async def list_step_details(
        self, roadmap_step_ids: list[int]
    ) -> list[RoadmapStepDetail]:
        if not roadmap_step_ids:
            return []
        stmt = select(RoadmapStepDetail).where(
            RoadmapStepDetail.roadmap_step_id.in_(roadmap_step_ids)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_step_actions(
        self, roadmap_step_ids: list[int]
    ) -> list[RoadmapStepAction]:
        if not roadmap_step_ids:
            return []
        stmt = (
            select(RoadmapStepAction)
            .where(RoadmapStepAction.roadmap_step_id.in_(roadmap_step_ids))
            .order_by(RoadmapStepAction.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_team(
        self, team_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[Roadmap], int]:
        count_stmt = (
            select(func.count())
            .select_from(Roadmap)
            .where(Roadmap.team_id == team_id, Roadmap.deleted_at.is_(None))
        )
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            select(Roadmap)
            .where(Roadmap.team_id == team_id, Roadmap.deleted_at.is_(None))
            .order_by(Roadmap.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def soft_delete(self, roadmap_id: UUID, team_id: UUID) -> bool:
        roadmap = await self.get_by_id_for_team(roadmap_id, team_id)
        if not roadmap:
            return False
        roadmap.deleted_at = utc_now()
        self.session.add(roadmap)
        await self.session.flush()
        return True

    async def update_title(
        self, roadmap_id: UUID, team_id: UUID, new_title: str
    ) -> Roadmap | None:
        roadmap = await self.get_by_id_for_team(roadmap_id, team_id)
        if not roadmap:
            return None
        roadmap.title = new_title
        roadmap.updated_at = utc_now()
        self.session.add(roadmap)
        await self.session.flush()
        return roadmap

    async def commit(self) -> None:
        await self.session.commit()
