import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.core import db
from app.models.actionkit_event import ActionKitEvent
from app.models.user import User


async def _get_user_token(client: AsyncClient) -> str:
    async with db.async_session() as session:
        user = (
            await session.execute(select(User).where(User.email == "test@example.com"))
        ).scalar_one()
        user.is_active = True
        session.add(user)
        await session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_track_search_event(client: AsyncClient):
    """POST /track with search event type should record event."""
    token = await _get_user_token(client)
    response = await client.post(
        "/api/v1/actionkits/track",
        json={"event_type": "search", "search_query": "근로계약서"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    async with db.async_session() as session:
        result = await session.execute(
            select(ActionKitEvent).where(
                ActionKitEvent.event_type == "search",
                ActionKitEvent.search_query == "근로계약서",
            )
        )
        event = result.scalar_one_or_none()
        assert event is not None
        assert event.user_id is not None


@pytest.mark.asyncio
async def test_track_download_event(client: AsyncClient):
    """POST /track with download event type should record event."""
    token = await _get_user_token(client)
    response = await client.post(
        "/api/v1/actionkits/track",
        json={"event_type": "download", "item_id": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_track_event_unauthenticated(client: AsyncClient):
    """POST /track without auth should record event with user_id=None."""
    response = await client.post(
        "/api/v1/actionkits/track",
        json={"event_type": "search", "search_query": "비밀유지"},
    )
    assert response.status_code == 204

    async with db.async_session() as session:
        result = await session.execute(
            select(ActionKitEvent).where(
                ActionKitEvent.search_query == "비밀유지",
            )
        )
        event = result.scalar_one_or_none()
        assert event is not None
        assert event.user_id is None


@pytest.mark.asyncio
async def test_track_invalid_event_type(client: AsyncClient):
    """POST /track with invalid event type should return 422."""
    response = await client.post(
        "/api/v1/actionkits/track",
        json={"event_type": "invalid_type"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_track_bookmark_event(client: AsyncClient):
    """POST /track with bookmark event type should record event."""
    token = await _get_user_token(client)
    response = await client.post(
        "/api/v1/actionkits/track",
        json={"event_type": "bookmark", "item_id": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_track_bulk_download_event(client: AsyncClient):
    """POST /track with bulk_download event type should record event."""
    response = await client.post(
        "/api/v1/actionkits/track",
        json={"event_type": "bulk_download", "item_id": 3},
    )
    assert response.status_code == 204
