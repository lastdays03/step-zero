
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_generate_roadmap_mock(client: AsyncClient):
    # Given: Business Idea Payload
    payload = {
        "business_type": "Cafe",
        "location": "Seoul",
        "description": "A cozy space for developers"
    }

    # When: POST /api/v1/generate
    # Note: Authentication might be required, but for MVP/Mock we might skip or use test token
    # Let's assume it requires Auth like dashboard
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post("/api/v1/generate", json=payload, headers=headers)

    # Then: Expect 200 OK and Mock Data
    assert response.status_code == 200
    data = response.json()
    assert "roadmap_id" in data
    assert "steps" in data
    assert len(data["steps"]) > 0
    assert data["title"] == "Mock Roadmap for Cafe"
