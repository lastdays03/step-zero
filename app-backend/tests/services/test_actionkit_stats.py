import pytest
from datetime import datetime, timedelta, timezone

from app.core import db
from app.features.ops.application.actionkit.stats_service import ActionKitStatsService
from app.models.actionkit_event import ActionKitEvent


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@pytest.fixture
async def seed_events():
    """Seed actionkit events for testing."""
    now = _utcnow()
    events = [
        # Current period downloads
        ActionKitEvent(event_type="download", item_id=1, user_id=1, created_at=now - timedelta(days=5)),
        ActionKitEvent(event_type="download", item_id=1, user_id=1, created_at=now - timedelta(days=10)),
        ActionKitEvent(event_type="download", item_id=2, user_id=2, created_at=now - timedelta(days=3)),
        ActionKitEvent(event_type="bulk_download", item_id=1, user_id=1, created_at=now - timedelta(days=2)),
        # Current period views
        ActionKitEvent(event_type="view", item_id=1, user_id=1, created_at=now - timedelta(days=5)),
        ActionKitEvent(event_type="view", item_id=2, user_id=2, created_at=now - timedelta(days=3)),
        ActionKitEvent(event_type="detail_view", item_id=3, user_id=1, created_at=now - timedelta(days=1)),
        # Previous period downloads (for delta)
        ActionKitEvent(event_type="download", item_id=1, user_id=1, created_at=now - timedelta(days=35)),
        ActionKitEvent(event_type="download", item_id=2, user_id=2, created_at=now - timedelta(days=40)),
        # Searches
        ActionKitEvent(event_type="search", search_query="근로계약서", user_id=1, created_at=now - timedelta(days=2)),
        ActionKitEvent(event_type="search", search_query="근로계약서", user_id=2, created_at=now - timedelta(days=3)),
        ActionKitEvent(event_type="search", search_query="투자계약", user_id=1, created_at=now - timedelta(days=5)),
        # Bookmarks
        ActionKitEvent(event_type="bookmark", item_id=1, user_id=1, created_at=now - timedelta(days=1)),
        # Unauthenticated view
        ActionKitEvent(event_type="view", item_id=1, user_id=None, created_at=now - timedelta(days=1)),
    ]
    async with db.async_session() as session:
        for event in events:
            session.add(event)
        await session.commit()
    yield
    # Cleanup
    async with db.async_session() as session:
        from sqlalchemy import delete
        await session.execute(delete(ActionKitEvent))
        await session.commit()


@pytest.mark.asyncio
async def test_empty_stats():
    """Empty table returns safe defaults."""
    async with db.async_session() as session:
        from sqlalchemy import delete
        await session.execute(delete(ActionKitEvent))
        await session.commit()

    async with db.async_session() as session:
        service = ActionKitStatsService(session)
        stats = await service.get_stats(30)

    assert stats["kpi"]["downloads"] == 0
    assert stats["kpi"]["active_users"] == 0
    assert stats["kpi"]["per_user"] == 0.0
    assert stats["kpi"]["downloads_delta"] is None
    assert stats["popular_items"] == []
    assert stats["search_keywords"] == []
    assert stats["insight"] is None


@pytest.mark.asyncio
async def test_kpi_with_data(seed_events):
    """KPI aggregation should return correct counts."""
    async with db.async_session() as session:
        service = ActionKitStatsService(session)
        stats = await service.get_stats(30)

    kpi = stats["kpi"]
    # view(3) + download(3) + bulk_download(1) = 7
    assert kpi["downloads"] == 7
    assert kpi["active_users"] == 2  # user_id 1 and 2
    assert kpi["per_user"] > 0


@pytest.mark.asyncio
async def test_delta_calculation(seed_events):
    """Delta should compare current vs previous period."""
    async with db.async_session() as session:
        service = ActionKitStatsService(session)
        stats = await service.get_stats(30)

    kpi = stats["kpi"]
    # Current: 7 (view+download+bulk), Previous: 2 (download only) → delta = (7-2)/2 = 2.5
    assert kpi["downloads_delta"] == 2.5


@pytest.mark.asyncio
async def test_popular_items(seed_events):
    """Popular items should be ranked by download count."""
    async with db.async_session() as session:
        service = ActionKitStatsService(session)
        stats = await service.get_stats(30)

    popular = stats["popular_items"]
    assert len(popular) >= 1
    # Item 1 has most accesses (2 view + 2 download + 1 bulk = 5)
    assert popular[0]["item_id"] == 1
    assert popular[0]["count"] == 5


@pytest.mark.asyncio
async def test_search_keywords(seed_events):
    """Search keywords should be ranked by count."""
    async with db.async_session() as session:
        service = ActionKitStatsService(session)
        stats = await service.get_stats(30)

    keywords = stats["search_keywords"]
    assert len(keywords) >= 2
    # "근로계약서" has 2 searches, "투자계약" has 1
    assert keywords[0]["keyword"] == "근로계약서"
    assert keywords[0]["count"] == 2


@pytest.mark.asyncio
async def test_insight_generation(seed_events):
    """Insight should be generated when data exists."""
    async with db.async_session() as session:
        service = ActionKitStatsService(session)
        stats = await service.get_stats(30)

    # Should have insight with search keyword mention
    insight = stats["insight"]
    assert insight is not None
    assert "근로계약서" in insight


@pytest.mark.asyncio
async def test_range_filtering(seed_events):
    """7-day range should return fewer results than 30-day."""
    async with db.async_session() as session:
        service = ActionKitStatsService(session)
        stats_7 = await service.get_stats(7)
        stats_30 = await service.get_stats(30)

    assert stats_7["kpi"]["downloads"] <= stats_30["kpi"]["downloads"]
