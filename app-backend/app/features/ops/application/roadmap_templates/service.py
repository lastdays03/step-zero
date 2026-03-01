from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.roadmap import Roadmap, RoadmapStep, RoadmapStepAction, RoadmapStepDetail
from app.models.roadmap_template import (
    RoadmapTemplate,
    RoadmapTemplateAction,
    RoadmapTemplateStep,
)

# Valid status transitions
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "DRAFT": {"REVIEW"},
    "REVIEW": {"DRAFT", "APPROVED"},
    "APPROVED": {"ARCHIVED"},
    "ARCHIVED": set(),
}

# Statuses that allow editing
_EDITABLE_STATUSES = {"DRAFT", "REVIEW"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TemplateSummary(TypedDict):
    total: int
    draft: int
    review: int
    approved: int
    archived: int


async def get_template_summary(session: AsyncSession) -> TemplateSummary:
    result = await session.execute(select(RoadmapTemplate))
    templates = list(result.scalars().all())
    return {
        "total": len(templates),
        "draft": sum(1 for t in templates if t.status == "DRAFT"),
        "review": sum(1 for t in templates if t.status == "REVIEW"),
        "approved": sum(1 for t in templates if t.status == "APPROVED"),
        "archived": sum(1 for t in templates if t.status == "ARCHIVED"),
    }


async def list_templates(
    session: AsyncSession,
    *,
    status: str | None = None,
    business_type: str | None = None,
) -> list[RoadmapTemplate]:
    stmt = select(RoadmapTemplate)
    if status:
        stmt = stmt.where(RoadmapTemplate.status == status)
    if business_type:
        stmt = stmt.where(RoadmapTemplate.business_type == business_type)
    stmt = stmt.order_by(RoadmapTemplate.updated_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_template_detail(
    session: AsyncSession, template_id: int
) -> RoadmapTemplate | None:
    stmt = select(RoadmapTemplate).where(RoadmapTemplate.id == template_id)
    result = await session.execute(stmt)
    template = result.scalar_one_or_none()
    if not template:
        return None

    # Load steps
    step_stmt = (
        select(RoadmapTemplateStep)
        .where(RoadmapTemplateStep.template_id == template_id)
        .order_by(RoadmapTemplateStep.step_order)
    )
    step_result = await session.execute(step_stmt)
    steps = list(step_result.scalars().all())

    # Load actions for all steps
    step_ids = [s.id for s in steps]
    actions_by_step: dict[int, list[RoadmapTemplateAction]] = {}
    if step_ids:
        action_stmt = (
            select(RoadmapTemplateAction)
            .where(RoadmapTemplateAction.template_step_id.in_(step_ids))
            .order_by(RoadmapTemplateAction.sort_order)
        )
        action_result = await session.execute(action_stmt)
        for action in action_result.scalars().all():
            actions_by_step.setdefault(action.template_step_id, []).append(action)

    # Attach as transient attributes for serialization
    template._steps = steps  # type: ignore[attr-defined]
    for step in steps:
        step._actions = actions_by_step.get(step.id, [])  # type: ignore[attr-defined]

    return template


async def create_template_from_roadmap(
    session: AsyncSession,
    *,
    roadmap_id: UUID,
    user_id: int,
) -> RoadmapTemplate:
    # 1. Load roadmap
    stmt = select(Roadmap).where(Roadmap.id == roadmap_id)
    roadmap = (await session.execute(stmt)).scalar_one_or_none()
    if not roadmap:
        raise ValueError(f"Roadmap {roadmap_id} not found")

    # 2. Load steps
    step_stmt = (
        select(RoadmapStep)
        .where(RoadmapStep.roadmap_id == roadmap_id)
        .order_by(RoadmapStep.step_order)
    )
    steps = list((await session.execute(step_stmt)).scalars().all())

    step_ids = [s.id for s in steps]

    # 3. Load details
    details_by_step: dict[int, RoadmapStepDetail] = {}
    if step_ids:
        detail_stmt = select(RoadmapStepDetail).where(
            RoadmapStepDetail.roadmap_step_id.in_(step_ids)
        )
        for detail in (await session.execute(detail_stmt)).scalars().all():
            details_by_step[detail.roadmap_step_id] = detail

    # 4. Load actions
    actions_by_step: dict[int, list[RoadmapStepAction]] = {}
    if step_ids:
        action_stmt = (
            select(RoadmapStepAction)
            .where(RoadmapStepAction.roadmap_step_id.in_(step_ids))
            .order_by(RoadmapStepAction.id)
        )
        for action in (await session.execute(action_stmt)).scalars().all():
            actions_by_step.setdefault(action.roadmap_step_id, []).append(action)

    # 5. Create template
    template = RoadmapTemplate(
        business_type=roadmap.business_type,
        startup_method=roadmap.startup_method,
        title=f"{roadmap.business_type} 로드맵 템플릿",
        status="DRAFT",
        version=1,
        source_roadmap_id=roadmap.id,
        created_by=user_id,
    )
    session.add(template)
    await session.flush()

    # 6. Copy steps + actions
    for step in steps:
        detail = details_by_step.get(step.id)
        t_step = RoadmapTemplateStep(
            template_id=template.id,
            step_order=step.step_order,
            phase=detail.phase if detail else "기본",
            title=step.title,
            objective=detail.objective if detail else "",
            estimated_days=detail.estimated_days if detail else 0,
            risk_notes=detail.risk_notes if detail else [],
        )
        session.add(t_step)
        await session.flush()

        for idx, action in enumerate(actions_by_step.get(step.id, [])):
            t_action = RoadmapTemplateAction(
                template_step_id=t_step.id,
                action_type=action.action_type,
                title=action.title,
                description=action.description,
                source_url=action.source_url,
                actionkit_item_id=action.metadata_json.get("actionkit_item_id"),
                actionkit_file_id=action.metadata_json.get("actionkit_file_id"),
                sort_order=idx,
                metadata_json=action.metadata_json,
            )
            session.add(t_action)

    await session.commit()
    await session.refresh(template)
    return template


async def update_template(
    session: AsyncSession,
    template_id: int,
    data: dict[str, Any],
) -> RoadmapTemplate | None:
    template = (
        await session.execute(
            select(RoadmapTemplate).where(RoadmapTemplate.id == template_id)
        )
    ).scalar_one_or_none()
    if not template:
        return None
    if template.status not in _EDITABLE_STATUSES:
        raise ValueError(f"Cannot edit template in {template.status} status")

    for key, value in data.items():
        if hasattr(template, key) and key not in ("id", "created_at", "created_by"):
            setattr(template, key, value)
    template.updated_at = _utcnow()
    await session.commit()
    await session.refresh(template)
    return template


async def update_template_status(
    session: AsyncSession,
    template_id: int,
    *,
    new_status: str,
    admin_id: int,
    reason: str | None = None,
) -> RoadmapTemplate | None:
    from app.features.ops.application.audit_logs import (
        AuditAction,
        AuditTargetType,
        record_admin_audit_log,
    )

    template = (
        await session.execute(
            select(RoadmapTemplate).where(RoadmapTemplate.id == template_id)
        )
    ).scalar_one_or_none()
    if not template:
        return None

    valid_next = _VALID_TRANSITIONS.get(template.status, set())
    if new_status not in valid_next:
        raise ValueError(
            f"Invalid transition: {template.status} → {new_status}"
        )

    old_status = template.status
    template.status = new_status
    template.updated_at = _utcnow()

    if new_status == "APPROVED":
        template.approved_by = admin_id
        template.approved_at = _utcnow()

    # Select appropriate audit action
    if new_status == "APPROVED":
        audit_action = AuditAction.TEMPLATE_APPROVED
    elif new_status == "ARCHIVED":
        audit_action = AuditAction.TEMPLATE_ARCHIVED
    else:
        audit_action = AuditAction.TEMPLATE_STATUS_CHANGED

    await record_admin_audit_log(
        session,
        admin_id=admin_id,
        action=audit_action,
        target_type=AuditTargetType.ROADMAP_TEMPLATE,
        target_id=str(template.id),
        reason=reason,
        meta={"before": {"status": old_status}, "after": {"status": new_status}},
    )

    await session.commit()
    await session.refresh(template)
    return template


async def create_template_action(
    session: AsyncSession,
    step_id: int,
    data: dict[str, Any],
) -> RoadmapTemplateAction | None:
    step = (
        await session.execute(
            select(RoadmapTemplateStep).where(RoadmapTemplateStep.id == step_id)
        )
    ).scalar_one_or_none()
    if not step:
        return None

    # Check template is editable
    template = (
        await session.execute(
            select(RoadmapTemplate).where(RoadmapTemplate.id == step.template_id)
        )
    ).scalar_one_or_none()
    if not template or template.status not in _EDITABLE_STATUSES:
        raise ValueError("Cannot add actions to non-editable template")

    action = RoadmapTemplateAction(
        template_step_id=step_id,
        action_type=data.get("action_type", "CHECKLIST"),
        title=data.get("title", ""),
        description=data.get("description", ""),
        source_url=data.get("source_url"),
        actionkit_item_id=data.get("actionkit_item_id"),
        actionkit_file_id=data.get("actionkit_file_id"),
        sort_order=data.get("sort_order", 0),
        metadata_json=data.get("metadata_json", {}),
    )
    session.add(action)
    await session.commit()
    await session.refresh(action)
    return action


async def update_template_action(
    session: AsyncSession,
    action_id: int,
    data: dict[str, Any],
) -> RoadmapTemplateAction | None:
    action = (
        await session.execute(
            select(RoadmapTemplateAction).where(RoadmapTemplateAction.id == action_id)
        )
    ).scalar_one_or_none()
    if not action:
        return None

    # Check template is editable via step → template
    step = (
        await session.execute(
            select(RoadmapTemplateStep).where(
                RoadmapTemplateStep.id == action.template_step_id
            )
        )
    ).scalar_one_or_none()
    if step:
        template = (
            await session.execute(
                select(RoadmapTemplate).where(RoadmapTemplate.id == step.template_id)
            )
        ).scalar_one_or_none()
        if template and template.status not in _EDITABLE_STATUSES:
            raise ValueError("Cannot edit actions of non-editable template")

    for key, value in data.items():
        if hasattr(action, key) and key not in ("id", "created_at", "template_step_id"):
            setattr(action, key, value)
    await session.commit()
    await session.refresh(action)
    return action


async def delete_template_action(
    session: AsyncSession, action_id: int
) -> bool:
    action = (
        await session.execute(
            select(RoadmapTemplateAction).where(RoadmapTemplateAction.id == action_id)
        )
    ).scalar_one_or_none()
    if not action:
        return False
    await session.delete(action)
    await session.commit()
    return True


async def delete_template(
    session: AsyncSession, template_id: int
) -> bool:
    template = (
        await session.execute(
            select(RoadmapTemplate).where(RoadmapTemplate.id == template_id)
        )
    ).scalar_one_or_none()
    if not template:
        return False
    if template.status not in _EDITABLE_STATUSES:
        raise ValueError(f"Cannot delete template in {template.status} status")
    await session.delete(template)
    await session.commit()
    return True
