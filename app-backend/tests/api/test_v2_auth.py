import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_v2_login_returns_team_context(client: AsyncClient):
    response = await client.post(
        "/api/v2/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"
    assert "current_team_id" in data
    assert isinstance(data["teams"], list)
    assert len(data["teams"]) >= 1
