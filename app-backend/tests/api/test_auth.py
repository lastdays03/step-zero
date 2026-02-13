
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # Given: Valid user credentials (mocked later)
    login_data = {
        "username": "test@example.com",
        "password": "password123"
    }
    
    # When: POST /api/v1/auth/login
    response = await client.post(
        "/api/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Then: Expect failure initially (404 Not Found as endpoint doesn't exist)
    # The goal is to reach 200 OK after implementation
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"
