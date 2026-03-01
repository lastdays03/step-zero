from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.roadmap_template import (
    RoadmapTemplate,
    RoadmapTemplateAction,
    RoadmapTemplateStep,
)

logger = get_logger(__name__)


class TemplateResolver:
    """Resolve APPROVED templates and convert to steps payload."""

    @staticmethod
    async def resolve(
        session: AsyncSession,
        *,
        business_type: str,
        startup_method: str | None = None,
    ) -> RoadmapTemplate | None:
        """Match an APPROVED template by business_type (+ startup_method).

        Priority:
        1. Exact match: business_type + startup_method (APPROVED)
        2. Common fallback: business_type + startup_method=NULL (APPROVED)
        3. None -> use existing pipeline
        """
        # 1. Exact match with startup_method
        if startup_method:
            stmt = (
                select(RoadmapTemplate)
                .where(
                    RoadmapTemplate.business_type == business_type,
                    RoadmapTemplate.startup_method == startup_method,
                    RoadmapTemplate.status == "APPROVED",
                )
                .order_by(RoadmapTemplate.version.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            template = result.scalar_one_or_none()
            if template:
                logger.info(
                    "Template resolved: exact match id=%d btype=%s smethod=%s",
                    template.id,
                    business_type,
                    startup_method,
                )
                return template

        # 2. Common fallback (startup_method is NULL)
        stmt = (
            select(RoadmapTemplate)
            .where(
                RoadmapTemplate.business_type == business_type,
                RoadmapTemplate.startup_method.is_(None),
                RoadmapTemplate.status == "APPROVED",
            )
            .order_by(RoadmapTemplate.version.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        template = result.scalar_one_or_none()
        if template:
            logger.info(
                "Template resolved: common fallback id=%d btype=%s",
                template.id,
                business_type,
            )
            return template

        # 3. No match
        logger.info("No approved template for btype=%s smethod=%s", business_type, startup_method)
        return None

    @staticmethod
    async def template_to_steps_payload(
        session: AsyncSession,
        template: RoadmapTemplate,
    ) -> list[dict]:
        """Convert RoadmapTemplate → steps_payload compatible with
        RoadmapRepository.create_steps_with_details().
        """
        # Load steps
        step_stmt = (
            select(RoadmapTemplateStep)
            .where(RoadmapTemplateStep.template_id == template.id)
            .order_by(RoadmapTemplateStep.step_order)
        )
        steps = list((await session.execute(step_stmt)).scalars().all())

        # Load actions
        step_ids = [s.id for s in steps]
        actions_by_step: dict[int, list[RoadmapTemplateAction]] = {}
        if step_ids:
            action_stmt = (
                select(RoadmapTemplateAction)
                .where(RoadmapTemplateAction.template_step_id.in_(step_ids))
                .order_by(RoadmapTemplateAction.sort_order)
            )
            for action in (await session.execute(action_stmt)).scalars().all():
                actions_by_step.setdefault(action.template_step_id, []).append(action)

        results: list[dict] = []
        for step in steps:
            actions = actions_by_step.get(step.id, [])

            checklist = []
            legal_basis = []
            documents = []

            for action in actions:
                if action.action_type == "CHECKLIST":
                    checklist.append({
                        "title": action.title,
                        "description": action.description,
                        "actionkit_item_id": action.actionkit_item_id,
                        "mapping_source": "template",
                    })
                elif action.action_type == "LEGAL_BASIS":
                    legal_basis.append({
                        "title": action.title,
                        "snippet": action.description,
                        "source_url": action.source_url,
                        "actionkit_item_id": action.actionkit_item_id,
                        "mapping_source": "template",
                    })
                elif action.action_type == "DOCUMENT":
                    documents.append({
                        "name": action.title,
                        "type": action.description or "FORM",
                        "source_url": action.source_url,
                        "actionkit_item_id": action.actionkit_item_id,
                        "actionkit_file_id": action.actionkit_file_id,
                        "mapping_source": "template",
                    })

            results.append({
                "phase": step.phase,
                "title": step.title,
                "objective": step.objective,
                "estimated_days": step.estimated_days,
                "risk_notes": step.risk_notes,
                "checklist": checklist or ["필수 요건 확인"],
                "legal_basis": legal_basis,
                "documents": documents,
                "mapping_source": "template",
            })

        return results

    @staticmethod
    async def should_create_auto_draft(
        session: AsyncSession,
        *,
        business_type: str,
    ) -> bool:
        """Check if auto-DRAFT creation should proceed.

        Returns True only if no template (any status) exists for this business_type.
        """
        stmt = (
            select(RoadmapTemplate.id)
            .where(RoadmapTemplate.business_type == business_type)
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is None
