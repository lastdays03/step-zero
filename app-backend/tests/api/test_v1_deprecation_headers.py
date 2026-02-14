import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_v1_endpoints_include_deprecation_headers(client: AsyncClient):
    response = await client.get("/api/v1/dashboard")

    assert response.status_code == 200
    assert response.headers.get("Deprecation") == "true"
    assert response.headers.get("Sunset") == "Tue, 30 Jun 2026 00:00:00 GMT"
    assert response.headers.get("Link") == '</api/v2/dashboard>; rel="successor-version"'
    assert "Deprecated API v1" in response.headers.get("Warning", "")


@pytest.mark.asyncio
async def test_v1_generate_has_roadmaps_successor_link(client: AsyncClient):
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]
    response = await client.post(
        "/api/v1/generate",
        json={"business_type": "Cafe", "location": "Seoul", "description": "test"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.headers.get("Link") == '</api/v2/roadmaps>; rel="successor-version"'
