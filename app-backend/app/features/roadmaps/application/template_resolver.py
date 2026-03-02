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
        startup_type: str | None = None,
    ) -> RoadmapTemplate | None:
        """Match an APPROVED template by business_type + startup_method + startup_type.

        Priority:
        1. Exact match: business_type + startup_method + startup_type
        2. Partial A: business_type + startup_method (startup_type=NULL)
        3. Partial B: business_type + startup_type (startup_method=NULL)
        4. Common fallback: business_type only (startup_method=NULL, startup_type=NULL)
        5. None -> use existing pipeline
        """
        base = (
            select(RoadmapTemplate)
            .where(
                RoadmapTemplate.business_type == business_type,
                RoadmapTemplate.status == "APPROVED",
            )
            .order_by(RoadmapTemplate.version.desc())
            .limit(1)
        )

        # 1. Exact match: all 3 fields
        if startup_method and startup_type:
            stmt = base.where(
                RoadmapTemplate.startup_method == startup_method,
                RoadmapTemplate.startup_type == startup_type,
            )
            template = (await session.execute(stmt)).scalar_one_or_none()
            if template:
                logger.info(
                    "Template resolved: exact 3-tier id=%d btype=%s smethod=%s stype=%s",
                    template.id, business_type, startup_method, startup_type,
                )
                return template

        # 2. Partial A: business_type + startup_method (startup_type=NULL)
        if startup_method:
            stmt = base.where(
                RoadmapTemplate.startup_method == startup_method,
                RoadmapTemplate.startup_type.is_(None),
            )
            template = (await session.execute(stmt)).scalar_one_or_none()
            if template:
                logger.info(
                    "Template resolved: partial-smethod id=%d btype=%s smethod=%s",
                    template.id, business_type, startup_method,
                )
                return template

        # 3. Partial B: business_type + startup_type (startup_method=NULL)
        if startup_type:
            stmt = base.where(
                RoadmapTemplate.startup_method.is_(None),
                RoadmapTemplate.startup_type == startup_type,
            )
            template = (await session.execute(stmt)).scalar_one_or_none()
            if template:
                logger.info(
                    "Template resolved: partial-stype id=%d btype=%s stype=%s",
                    template.id, business_type, startup_type,
                )
                return template

        # 4. Common fallback: business_type only (others NULL)
        stmt = base.where(
            RoadmapTemplate.startup_method.is_(None),
            RoadmapTemplate.startup_type.is_(None),
        )
        template = (await session.execute(stmt)).scalar_one_or_none()
        if template:
            logger.info(
                "Template resolved: common fallback id=%d btype=%s",
                template.id, business_type,
            )
            return template

        logger.info(
            "No approved template for btype=%s smethod=%s stype=%s",
            business_type, startup_method, startup_type,
        )
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
        startup_method: str | None = None,
        startup_type: str | None = None,
    ) -> bool:
        """Check if auto-DRAFT creation should proceed.

        Returns True if no active (DRAFT/REVIEW/APPROVED) template exists
        for this combination. ARCHIVED-only counts as "no active template".
        """
        stmt = (
            select(RoadmapTemplate.id)
            .where(
                RoadmapTemplate.business_type == business_type,
                RoadmapTemplate.status.in_(["DRAFT", "REVIEW", "APPROVED"]),
            )
        )
        if startup_method:
            stmt = stmt.where(RoadmapTemplate.startup_method == startup_method)
        if startup_type:
            stmt = stmt.where(RoadmapTemplate.startup_type == startup_type)
        stmt = stmt.limit(1)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is None
