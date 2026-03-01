import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_v1_create_roadmap(client: AsyncClient):
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    headers = {
        "Authorization": f"Bearer {login_data['access_token']}",
        "X-Team-Id": login_data["current_team_id"],
    }
    payload = {
        "business_type": "Cafe",
        "location": "Seoul",
        "description": "A cozy space for developers",
    }

    create_response = await client.post(
        "/api/v1/roadmaps", json=payload, headers=headers
    )
    assert create_response.status_code == 200
    data = create_response.json()
    assert "roadmap_id" in data
    assert data["title"] == "Cafe 창업 로드맵"
    assert len(data["steps"]) == 3
