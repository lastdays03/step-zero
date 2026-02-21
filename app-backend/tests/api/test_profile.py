import pytest
from httpx import AsyncClient


async def _login_headers(client: AsyncClient) -> dict[str, str]:
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_profile_me_get_and_update(client: AsyncClient):
    headers = await _login_headers(client)

    get_response = await client.get("/api/v1/profile/me", headers=headers)
    assert get_response.status_code == 200
    profile = get_response.json()
    assert profile["user_id"] > 0
    assert "completeness_rate" in profile

    update_payload = {
        "full_name": "Updated Test User",
        "category": "카페",
        "region": "서울 마포구",
        "philosophy": "좋은 커피와 경험",
        "experiences": ["바리스타 3년"],
    }
    update_response = await client.put("/api/v1/profile/me", json=update_payload, headers=headers)
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["full_name"] == "Updated Test User"
    assert updated["category"] == "카페"
    assert updated["region"] == "서울 마포구"
    assert updated["philosophy"] == "좋은 커피와 경험"
    assert updated["experiences"] == ["바리스타 3년"]

