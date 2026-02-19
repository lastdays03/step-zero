import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.core import db
from app.models.roadmap import RoadmapStepAction


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


@pytest.mark.asyncio
async def test_update_roadmap_step_status_and_auto_advance(client: AsyncClient):
    headers = await _login_headers(client)
    create_response = await client.post(
        "/api/v1/roadmaps",
        json={
            "business_type": "카페",
            "location": "서울특별시 강남구",
            "description": "테스트 로드맵",
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    roadmap_data = create_response.json()
    first_step_id = roadmap_data["steps"][0]["id"]
    second_step_id = roadmap_data["steps"][1]["id"]

    start_response = await client.patch(
        f"/api/v1/roadmaps/tasks/{first_step_id}",
        json={"status": "IN_PROGRESS"},
        headers=headers,
    )
    assert start_response.status_code == 200
    assert start_response.json()["status"] == "IN_PROGRESS"

    complete_response = await client.patch(
        f"/api/v1/roadmaps/tasks/{first_step_id}",
        json={"status": "COMPLETED"},
        headers=headers,
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["status"] == "COMPLETED"

    detail_response = await client.get(
        f"/api/v1/roadmaps/{roadmap_data['roadmap_id']}/detail",
        headers=headers,
    )
    assert detail_response.status_code == 200
    detail_data = detail_response.json()
    second_step = next(step for step in detail_data["steps"] if step["id"] == second_step_id)
    assert second_step["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_update_roadmap_step_status_blocks_out_of_order_completion(client: AsyncClient):
    headers = await _login_headers(client)
    create_response = await client.post(
        "/api/v1/roadmaps",
        json={
            "business_type": "카페",
            "location": "서울특별시 강남구",
            "description": "테스트 로드맵",
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    roadmap_data = create_response.json()
    second_step_id = roadmap_data["steps"][1]["id"]

    out_of_order = await client.patch(
        f"/api/v1/roadmaps/tasks/{second_step_id}",
        json={"status": "COMPLETED"},
        headers=headers,
    )
    assert out_of_order.status_code == 400
    assert out_of_order.json()["detail"] == "Previous steps must be completed first"


@pytest.mark.asyncio
async def test_get_latest_roadmap_detail(client: AsyncClient):
    headers = await _login_headers(client)
    create_response = await client.post(
        "/api/v1/roadmaps",
        json={
            "business_type": "카페",
            "location": "서울특별시 강남구",
            "description": "최신 조회 테스트",
        },
        headers=headers,
    )
    assert create_response.status_code == 200

    latest_response = await client.get("/api/v1/roadmaps/latest/detail", headers=headers)
    assert latest_response.status_code == 200
    data = latest_response.json()
    assert "roadmap_id" in data
    assert isinstance(data["steps"], list)


@pytest.mark.asyncio
async def test_update_roadmap_step_action_completion(client: AsyncClient):
    headers = await _login_headers(client)
    create_response = await client.post(
        "/api/v1/roadmaps",
        json={
            "business_type": "카페",
            "location": "서울특별시 강남구",
            "description": "action completion test",
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    roadmap_data = create_response.json()
    step_id = roadmap_data["steps"][0]["id"]

    async with db.async_session() as session:
        action = RoadmapStepAction(
            roadmap_step_id=step_id,
            action_type="CHECKLIST",
            title="사업자등록 신청서 준비",
            description="필수 입력값 확인",
            metadata_json={},
        )
        session.add(action)
        await session.commit()
        await session.refresh(action)
        action_id = action.id

    response = await client.patch(
        f"/api/v1/roadmaps/tasks/{step_id}/actions/{action_id}",
        json={"completed": True},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["metadata_json"]["completed"] is True


@pytest.mark.asyncio
async def test_action_completion_auto_completes_step_and_advances_next(client: AsyncClient):
    headers = await _login_headers(client)
    create_response = await client.post(
        "/api/v1/roadmaps",
        json={
            "business_type": "카페",
            "location": "서울특별시 강남구",
            "description": "auto complete test",
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    roadmap_data = create_response.json()
    first_step_id = roadmap_data["steps"][0]["id"]
    second_step_id = roadmap_data["steps"][1]["id"]

    async with db.async_session() as session:
        session.add_all(
            [
                RoadmapStepAction(
                    roadmap_step_id=first_step_id,
                    action_type="CHECKLIST",
                    title="체크 1",
                    description="",
                    metadata_json={},
                ),
                RoadmapStepAction(
                    roadmap_step_id=first_step_id,
                    action_type="CHECKLIST",
                    title="체크 2",
                    description="",
                    metadata_json={},
                ),
            ]
        )
        await session.commit()

        actions = (
            await session.execute(
                select(RoadmapStepAction)
                .where(RoadmapStepAction.roadmap_step_id == first_step_id)
                .order_by(RoadmapStepAction.id.asc())
            )
        ).scalars().all()
        action_ids = [action.id for action in actions]

    for action_id in action_ids:
        toggle = await client.patch(
            f"/api/v1/roadmaps/tasks/{first_step_id}/actions/{action_id}",
            json={"completed": True},
            headers=headers,
        )
        assert toggle.status_code == 200

    detail_response = await client.get(
        f"/api/v1/roadmaps/{roadmap_data['roadmap_id']}/detail",
        headers=headers,
    )
    assert detail_response.status_code == 200
    steps = detail_response.json()["steps"]
    first_step = next(item for item in steps if item["id"] == first_step_id)
    second_step = next(item for item in steps if item["id"] == second_step_id)
    assert first_step["status"] == "COMPLETED"
    assert second_step["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_action_completion_requires_document_actions_too(client: AsyncClient):
    headers = await _login_headers(client)
    create_response = await client.post(
        "/api/v1/roadmaps",
        json={
            "business_type": "카페",
            "location": "서울특별시 강남구",
            "description": "document requirement test",
        },
        headers=headers,
    )
    assert create_response.status_code == 200
    roadmap_data = create_response.json()
    first_step_id = roadmap_data["steps"][0]["id"]
    second_step_id = roadmap_data["steps"][1]["id"]

    async with db.async_session() as session:
        checklist = RoadmapStepAction(
            roadmap_step_id=first_step_id,
            action_type="CHECKLIST",
            title="체크 1",
            description="",
            metadata_json={},
        )
        document = RoadmapStepAction(
            roadmap_step_id=first_step_id,
            action_type="DOCUMENT",
            title="필수 서류 1",
            description="",
            metadata_json={},
        )
        session.add_all([checklist, document])
        await session.commit()
        await session.refresh(checklist)
        await session.refresh(document)
        checklist_id = checklist.id
        document_id = document.id

    checklist_toggle = await client.patch(
        f"/api/v1/roadmaps/tasks/{first_step_id}/actions/{checklist_id}",
        json={"completed": True},
        headers=headers,
    )
    assert checklist_toggle.status_code == 200

    detail_after_checklist = await client.get(
        f"/api/v1/roadmaps/{roadmap_data['roadmap_id']}/detail",
        headers=headers,
    )
    assert detail_after_checklist.status_code == 200
    steps_after_checklist = detail_after_checklist.json()["steps"]
    first_step_after_checklist = next(item for item in steps_after_checklist if item["id"] == first_step_id)
    second_step_after_checklist = next(item for item in steps_after_checklist if item["id"] == second_step_id)
    assert first_step_after_checklist["status"] != "COMPLETED"
    assert second_step_after_checklist["status"] != "IN_PROGRESS"

    document_toggle = await client.patch(
        f"/api/v1/roadmaps/tasks/{first_step_id}/actions/{document_id}",
        json={"completed": True},
        headers=headers,
    )
    assert document_toggle.status_code == 200

    detail_after_document = await client.get(
        f"/api/v1/roadmaps/{roadmap_data['roadmap_id']}/detail",
        headers=headers,
    )
    assert detail_after_document.status_code == 200
    steps_after_document = detail_after_document.json()["steps"]
    first_step_after_document = next(item for item in steps_after_document if item["id"] == first_step_id)
    second_step_after_document = next(item for item in steps_after_document if item["id"] == second_step_id)
    assert first_step_after_document["status"] == "COMPLETED"
    assert second_step_after_document["status"] == "IN_PROGRESS"
