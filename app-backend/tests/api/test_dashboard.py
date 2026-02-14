
import pytest
from httpx import AsyncClient

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
