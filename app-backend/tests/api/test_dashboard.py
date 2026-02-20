
import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.core import db
from app.models.roadmap import RoadmapStep, RoadmapStepDetail


async def _login_headers(client: AsyncClient) -> dict[str, str]:
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_dashboard_stats(client: AsyncClient):
    # Given: Authenticated user (Mocked via dependency override or header injection)
    # For now, we assume public or simple mock. 
    # But usually dashboard requires auth. 
    # Let's try calling it. If 401, we need to inject token.
    # The plan says "GET /api/v1/dashboard".
    
    # We can use a token from login if needed, or mock the `current_user` dependency.
    # Since I don't have dependency injection override setup in conftest yet, 
    # I might skip auth check for this specific endpoint in MVP or mock it.
    # But clean architecture says use `Depends(get_current_user)`.
    
    # Let's assume the endpoint is protecting. 
    # I'll get a token first (using the implemented /login).
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # When: GET /api/v1/dashboard
    response = await client.get("/api/v1/dashboard", headers=headers)

    # Then: Expect failure initially (404)
    # Goal: 200 OK with correct schema
    assert response.status_code == 200
    data = response.json()
    
    # Check structure matches design requirements
    assert "user_name" in data
    assert "current_phase" in data
    assert "title" in data["current_phase"]
    assert "roadmap" in data
    assert isinstance(data["roadmap"], list)
    assert "stats" in data
    assert "growth_club" in data


@pytest.mark.asyncio
async def test_dashboard_current_phase_uses_step_detail_phase(client: AsyncClient):
    headers = await _login_headers(client)
    create_response = await client.post(
        "/api/v1/roadmaps",
        json={
            "business_type": "카페",
            "location": "서울특별시 강남구",
            "description": "phase sync test",
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    created = create_response.json()
    detail_response = await client.get(
        f"/api/v1/roadmaps/{created['roadmap_id']}/detail",
        headers=headers,
    )
    assert detail_response.status_code == 200
    first_step_id = detail_response.json()["steps"][0]["id"]

    async with db.async_session() as session:
        session.add(
            RoadmapStepDetail(
                roadmap_step_id=first_step_id,
                phase="법인 설립 준비",
                objective="phase title sync",
                estimated_days=2,
                risk_notes=[],
                generation_mode="TEST",
            )
        )
        await session.commit()

    dashboard_response = await client.get("/api/v1/dashboard", headers=headers)
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["current_phase"]["title"] == "법인 설립 준비"


@pytest.mark.asyncio
async def test_dashboard_roadmap_items_are_phase_summary(client: AsyncClient):
    headers = await _login_headers(client)
    create_response = await client.post(
        "/api/v1/roadmaps",
        json={
            "business_type": "카페",
            "location": "서울특별시 강남구",
            "description": "phase summary test",
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    created = create_response.json()
    detail_response = await client.get(
        f"/api/v1/roadmaps/{created['roadmap_id']}/detail",
        headers=headers,
    )
    assert detail_response.status_code == 200
    steps = detail_response.json()["steps"]
    first_step_id = steps[0]["id"]
    second_step_id = steps[1]["id"]
    third_step_id = steps[2]["id"]

    async with db.async_session() as session:
        session.add_all(
            [
                RoadmapStepDetail(
                    roadmap_step_id=first_step_id,
                    phase="Phase 1",
                    objective="phase 1",
                    estimated_days=2,
                    risk_notes=[],
                    generation_mode="TEST",
                ),
                RoadmapStepDetail(
                    roadmap_step_id=second_step_id,
                    phase="Phase 2",
                    objective="phase 2",
                    estimated_days=2,
                    risk_notes=[],
                    generation_mode="TEST",
                ),
                RoadmapStepDetail(
                    roadmap_step_id=third_step_id,
                    phase="Phase 3",
                    objective="phase 3",
                    estimated_days=2,
                    risk_notes=[],
                    generation_mode="TEST",
                ),
            ]
        )
        stmt = select(RoadmapStep).where(RoadmapStep.id == first_step_id)
        first_step = (await session.execute(stmt)).scalar_one()
        first_step.status = "COMPLETED"
        await session.commit()

    dashboard_response = await client.get("/api/v1/dashboard", headers=headers)
    assert dashboard_response.status_code == 200
    roadmap_items = dashboard_response.json()["roadmap"]
    assert [item["title"] for item in roadmap_items] == ["Phase 1", "Phase 2", "Phase 3"]
    assert [item["status"] for item in roadmap_items] == ["completed", "current", "locked"]
