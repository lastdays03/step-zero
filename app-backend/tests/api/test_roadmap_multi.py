import pytest
from httpx import AsyncClient

from app.core import db
from app.models.roadmap import Roadmap


async def _login_headers(client: AsyncClient) -> dict[str, str]:
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    return {
        "Authorization": f"Bearer {login_data['access_token']}",
        "X-Team-Id": login_data["current_team_id"],
    }


async def _create_roadmap(
    client: AsyncClient,
    headers: dict[str, str],
    description: str = "테스트 로드맵",
) -> dict:
    response = await client.post(
        "/api/v1/roadmaps",
        json={
            "business_type": "카페",
            "location": "서울특별시 강남구",
            "description": description,
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_list_roadmaps_empty(client: AsyncClient):
    headers = await _login_headers(client)

    # soft-delete all existing roadmaps to start clean
    list_resp = await client.get("/api/v1/roadmaps", headers=headers)
    assert list_resp.status_code == 200
    for item in list_resp.json()["items"]:
        await client.delete(f"/api/v1/roadmaps/{item['roadmap_id']}", headers=headers)

    response = await client.get("/api/v1/roadmaps", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_roadmaps_multiple(client: AsyncClient):
    headers = await _login_headers(client)

    # clean up first
    list_resp = await client.get("/api/v1/roadmaps", headers=headers)
    for item in list_resp.json()["items"]:
        await client.delete(f"/api/v1/roadmaps/{item['roadmap_id']}", headers=headers)

    r1 = await _create_roadmap(client, headers, description="첫 번째")
    r2 = await _create_roadmap(client, headers, description="두 번째")
    r3 = await _create_roadmap(client, headers, description="세 번째")

    response = await client.get("/api/v1/roadmaps", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3

    # 최신순 정렬 확인 (세 번째가 첫 번째)
    assert data["items"][0]["roadmap_id"] == r3["roadmap_id"]
    assert data["items"][1]["roadmap_id"] == r2["roadmap_id"]
    assert data["items"][2]["roadmap_id"] == r1["roadmap_id"]

    # summary fields 확인
    first_item = data["items"][0]
    assert "title" in first_item
    assert "business_type" in first_item
    assert "location" in first_item
    assert "created_at" in first_item
    assert "progress" in first_item
    assert "total_steps" in first_item
    assert "completed_steps" in first_item


@pytest.mark.asyncio
async def test_list_roadmaps_excludes_deleted(client: AsyncClient):
    headers = await _login_headers(client)

    # clean up
    list_resp = await client.get("/api/v1/roadmaps", headers=headers)
    for item in list_resp.json()["items"]:
        await client.delete(f"/api/v1/roadmaps/{item['roadmap_id']}", headers=headers)

    r1 = await _create_roadmap(client, headers, description="유지")
    r2 = await _create_roadmap(client, headers, description="삭제 대상")

    delete_resp = await client.delete(
        f"/api/v1/roadmaps/{r2['roadmap_id']}", headers=headers
    )
    assert delete_resp.status_code == 204

    response = await client.get("/api/v1/roadmaps", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    ids = [item["roadmap_id"] for item in data["items"]]
    assert r1["roadmap_id"] in ids
    assert r2["roadmap_id"] not in ids


@pytest.mark.asyncio
async def test_list_roadmaps_pagination(client: AsyncClient):
    headers = await _login_headers(client)

    # clean up
    list_resp = await client.get("/api/v1/roadmaps", headers=headers)
    for item in list_resp.json()["items"]:
        await client.delete(f"/api/v1/roadmaps/{item['roadmap_id']}", headers=headers)

    for i in range(3):
        await _create_roadmap(client, headers, description=f"페이징 {i}")

    page1 = await client.get("/api/v1/roadmaps?offset=0&limit=2", headers=headers)
    assert page1.status_code == 200
    data1 = page1.json()
    assert len(data1["items"]) == 2
    assert data1["total"] == 3

    page2 = await client.get("/api/v1/roadmaps?offset=2&limit=2", headers=headers)
    assert page2.status_code == 200
    data2 = page2.json()
    assert len(data2["items"]) == 1
    assert data2["total"] == 3


@pytest.mark.asyncio
async def test_delete_roadmap_success(client: AsyncClient):
    headers = await _login_headers(client)
    roadmap = await _create_roadmap(client, headers, description="삭제 테스트")

    delete_resp = await client.delete(
        f"/api/v1/roadmaps/{roadmap['roadmap_id']}", headers=headers
    )
    assert delete_resp.status_code == 204

    # 목록에서 사라짐 확인
    list_resp = await client.get("/api/v1/roadmaps", headers=headers)
    ids = [item["roadmap_id"] for item in list_resp.json()["items"]]
    assert roadmap["roadmap_id"] not in ids


@pytest.mark.asyncio
async def test_delete_roadmap_not_found(client: AsyncClient):
    headers = await _login_headers(client)
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.delete(f"/api/v1/roadmaps/{fake_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_title_success(client: AsyncClient):
    headers = await _login_headers(client)
    roadmap = await _create_roadmap(client, headers, description="제목 수정 테스트")

    response = await client.patch(
        f"/api/v1/roadmaps/{roadmap['roadmap_id']}",
        json={"title": "새로운 제목"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "새로운 제목"
    assert data["roadmap_id"] == roadmap["roadmap_id"]


@pytest.mark.asyncio
async def test_update_title_not_found(client: AsyncClient):
    headers = await _login_headers(client)
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await client.patch(
        f"/api/v1/roadmaps/{fake_id}",
        json={"title": "존재하지 않는 로드맵"},
        headers=headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_title_empty(client: AsyncClient):
    headers = await _login_headers(client)
    roadmap = await _create_roadmap(client, headers, description="빈 제목 테스트")

    response = await client.patch(
        f"/api/v1/roadmaps/{roadmap['roadmap_id']}",
        json={"title": ""},
        headers=headers,
    )
    assert response.status_code == 422
