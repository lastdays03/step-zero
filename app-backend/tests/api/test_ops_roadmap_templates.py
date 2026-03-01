import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.core import db
from app.models.roadmap import Roadmap
from app.models.roadmap_template import RoadmapTemplate
from app.models.team import Team, TeamMember
from app.models.user import User


async def _get_admin_token(client: AsyncClient) -> str:
    async with db.async_session() as session:
        user = (
            await session.execute(select(User).where(User.email == "test@example.com"))
        ).scalar_one()
        user.is_superuser = True
        user.is_active = True
        session.add(user)
        await session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def _get_normal_token(client: AsyncClient) -> str:
    async with db.async_session() as session:
        user = (
            await session.execute(select(User).where(User.email == "test@example.com"))
        ).scalar_one()
        user.is_superuser = False
        user.is_active = True
        session.add(user)
        await session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def _ensure_roadmap(session) -> Roadmap:
    """Create a fresh test roadmap with steps."""
    user = (
        await session.execute(select(User).where(User.email == "test@example.com"))
    ).scalar_one()
    team = (
        await session.execute(
            select(Team)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == user.id)
        )
    ).scalar_one()

    from app.models.roadmap import RoadmapStep, RoadmapStepDetail, RoadmapStepAction

    roadmap = Roadmap(
        team_id=team.id,
        title="테스트 로드맵",
        business_type="휴게음식점",
        location="서울시 강남구",
        description="테스트용",
        created_by=user.id,
    )
    session.add(roadmap)
    await session.flush()

    step = RoadmapStep(
        roadmap_id=roadmap.id, step_order=1, title="준비 단계", status="PENDING"
    )
    session.add(step)
    await session.flush()

    detail = RoadmapStepDetail(
        roadmap_step_id=step.id,
        phase="준비",
        objective="사업 준비",
        estimated_days=7,
        risk_notes=["위험1"],
    )
    session.add(detail)

    action = RoadmapStepAction(
        roadmap_step_id=step.id,
        action_type="CHECKLIST",
        title="사업자등록",
        description="",
        metadata_json={"mapping_source": "test"},
    )
    session.add(action)
    await session.commit()
    await session.refresh(roadmap)
    return roadmap


async def _create_template_directly(session, user_id: int) -> RoadmapTemplate:
    """Create a template directly in DB for testing."""
    template = RoadmapTemplate(
        business_type="휴게음식점",
        title="테스트 템플릿",
        status="DRAFT",
        version=1,
        created_by=user_id,
    )
    session.add(template)
    await session.commit()
    await session.refresh(template)
    return template


@pytest.mark.asyncio
async def test_template_summary(client: AsyncClient):
    token = await _get_admin_token(client)
    response = await client.get(
        "/api/v1/ops/roadmap-templates/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "draft" in data
    assert "approved" in data


@pytest.mark.asyncio
async def test_template_list(client: AsyncClient):
    token = await _get_admin_token(client)
    response = await client.get(
        "/api/v1/ops/roadmap-templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_template_from_roadmap(client: AsyncClient):
    token = await _get_admin_token(client)

    async with db.async_session() as session:
        roadmap = await _ensure_roadmap(session)
        roadmap_id = str(roadmap.id)

    response = await client.post(
        "/api/v1/ops/roadmap-templates/from-roadmap",
        json={"roadmap_id": roadmap_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "DRAFT"
    assert data["business_type"] == "휴게음식점"


@pytest.mark.asyncio
async def test_template_detail(client: AsyncClient):
    token = await _get_admin_token(client)

    # Get first template
    list_response = await client.get(
        "/api/v1/ops/roadmap-templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    templates = list_response.json()
    if not templates:
        pytest.skip("No templates to test detail view")

    template_id = templates[0]["id"]
    response = await client.get(
        f"/api/v1/ops/roadmap-templates/{template_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "steps" in data


@pytest.mark.asyncio
async def test_update_template_meta(client: AsyncClient):
    token = await _get_admin_token(client)

    list_response = await client.get(
        "/api/v1/ops/roadmap-templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    templates = list_response.json()
    draft = next((t for t in templates if t["status"] == "DRAFT"), None)
    if not draft:
        pytest.skip("No DRAFT template available")

    response = await client.patch(
        f"/api/v1/ops/roadmap-templates/{draft['id']}",
        json={"title": "수정된 제목"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "수정된 제목"


@pytest.mark.asyncio
async def test_template_status_transition_draft_to_review(client: AsyncClient):
    token = await _get_admin_token(client)

    async with db.async_session() as session:
        user = (
            await session.execute(
                select(User).where(User.email == "test@example.com")
            )
        ).scalar_one()
        template = await _create_template_directly(session, user.id)
        tid = template.id

    response = await client.patch(
        f"/api/v1/ops/roadmap-templates/{tid}/status",
        json={"new_status": "REVIEW", "reason": "검토 요청"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "REVIEW"


@pytest.mark.asyncio
async def test_template_invalid_status_transition(client: AsyncClient):
    token = await _get_admin_token(client)

    async with db.async_session() as session:
        user = (
            await session.execute(
                select(User).where(User.email == "test@example.com")
            )
        ).scalar_one()
        template = await _create_template_directly(session, user.id)
        tid = template.id

    # DRAFT -> APPROVED is invalid (must go through REVIEW)
    response = await client.patch(
        f"/api/v1/ops/roadmap-templates/{tid}/status",
        json={"new_status": "APPROVED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_template(client: AsyncClient):
    token = await _get_admin_token(client)

    async with db.async_session() as session:
        user = (
            await session.execute(
                select(User).where(User.email == "test@example.com")
            )
        ).scalar_one()
        template = await _create_template_directly(session, user.id)
        tid = template.id

    response = await client.delete(
        f"/api/v1/ops/roadmap-templates/{tid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.asyncio
async def test_non_admin_access_denied(client: AsyncClient):
    token = await _get_normal_token(client)
    response = await client.get(
        "/api/v1/ops/roadmap-templates/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
