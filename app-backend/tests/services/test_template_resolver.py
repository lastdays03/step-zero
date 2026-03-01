"""Unit tests for TemplateResolver."""

import pytest
from sqlmodel import select

from app.core import db
from app.features.roadmaps.application.template_resolver import TemplateResolver
from app.models.roadmap_template import (
    RoadmapTemplate,
    RoadmapTemplateAction,
    RoadmapTemplateStep,
)
from app.models.user import User


async def _get_test_user_id() -> int:
    async with db.async_session() as session:
        user = (
            await session.execute(
                select(User).where(User.email == "test@example.com")
            )
        ).scalar_one()
        return user.id


async def _create_approved_template(
    session, *, business_type: str, startup_method: str | None = None, user_id: int
) -> RoadmapTemplate:
    template = RoadmapTemplate(
        business_type=business_type,
        startup_method=startup_method,
        title=f"{business_type} 템플릿",
        status="APPROVED",
        version=1,
        created_by=user_id,
        approved_by=user_id,
    )
    session.add(template)
    await session.flush()

    step = RoadmapTemplateStep(
        template_id=template.id,
        step_order=1,
        phase="준비",
        title="사전 준비",
        objective="기초 준비",
        estimated_days=5,
        risk_notes=["주의사항"],
    )
    session.add(step)
    await session.flush()

    action = RoadmapTemplateAction(
        template_step_id=step.id,
        action_type="CHECKLIST",
        title="사업자등록",
        description="",
        sort_order=0,
        metadata_json={},
    )
    session.add(action)
    await session.commit()
    await session.refresh(template)
    return template


@pytest.mark.asyncio
async def test_resolve_exact_match():
    user_id = await _get_test_user_id()
    async with db.async_session() as session:
        await _create_approved_template(
            session,
            business_type="일반음식점",
            startup_method="신규",
            user_id=user_id,
        )

    async with db.async_session() as session:
        result = await TemplateResolver.resolve(
            session, business_type="일반음식점", startup_method="신규"
        )
        assert result is not None
        assert result.business_type == "일반음식점"
        assert result.startup_method == "신규"


@pytest.mark.asyncio
async def test_resolve_common_fallback():
    user_id = await _get_test_user_id()
    async with db.async_session() as session:
        await _create_approved_template(
            session,
            business_type="미용업",
            startup_method=None,
            user_id=user_id,
        )

    async with db.async_session() as session:
        result = await TemplateResolver.resolve(
            session, business_type="미용업", startup_method="프랜차이즈"
        )
        assert result is not None
        assert result.business_type == "미용업"
        assert result.startup_method is None


@pytest.mark.asyncio
async def test_resolve_no_match():
    async with db.async_session() as session:
        result = await TemplateResolver.resolve(
            session, business_type="우주산업"
        )
        assert result is None


@pytest.mark.asyncio
async def test_template_to_steps_payload():
    user_id = await _get_test_user_id()
    async with db.async_session() as session:
        template = await _create_approved_template(
            session,
            business_type="학원업",
            user_id=user_id,
        )

    async with db.async_session() as session:
        tmpl = (
            await session.execute(
                select(RoadmapTemplate).where(RoadmapTemplate.id == template.id)
            )
        ).scalar_one()
        payload = await TemplateResolver.template_to_steps_payload(session, tmpl)

    assert len(payload) >= 1
    step = payload[0]
    assert step["phase"] == "준비"
    assert step["mapping_source"] == "template"
    assert len(step["checklist"]) >= 1


@pytest.mark.asyncio
async def test_should_create_auto_draft_no_existing():
    async with db.async_session() as session:
        result = await TemplateResolver.should_create_auto_draft(
            session, business_type="건설업_테스트_없는업종"
        )
        assert result is True


@pytest.mark.asyncio
async def test_should_create_auto_draft_existing():
    user_id = await _get_test_user_id()
    async with db.async_session() as session:
        template = RoadmapTemplate(
            business_type="통신판매업_중복테스트",
            title="테스트",
            status="DRAFT",
            version=1,
            created_by=user_id,
        )
        session.add(template)
        await session.commit()

    async with db.async_session() as session:
        result = await TemplateResolver.should_create_auto_draft(
            session, business_type="통신판매업_중복테스트"
        )
        assert result is False
