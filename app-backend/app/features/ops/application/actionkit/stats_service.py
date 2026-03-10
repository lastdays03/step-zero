from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.actionkit_event import ActionKitEvent


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _delta(current: int, previous: int) -> float | None:
    if previous == 0:
        return None
    return round((current - previous) / previous, 3)


class ActionKitStatsService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_stats(self, range_days: int = 30) -> dict:
        now = _utcnow()
        since = now - timedelta(days=range_days)
        prev_since = now - timedelta(days=range_days * 2)
        prev_until = since

        kpi = await self._get_kpi(since, prev_since, prev_until)
        popular_items = await self._get_popular_items(since, range_days)
        search_keywords = await self._get_search_keywords(since)
        insight = self._generate_insight(kpi, popular_items, search_keywords)

        return {
            "kpi": kpi,
            "popular_items": popular_items,
            "search_keywords": search_keywords,
            "insight": insight,
            "range_days": range_days,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _get_kpi(
        self,
        since: datetime,
        prev_since: datetime,
        prev_until: datetime,
    ) -> dict:
        # 파일 접근 = 인라인 뷰 + 다운로드 + 일괄 다운로드 (서버에서 파일 제공)
        file_access_types = ["view", "download", "bulk_download"]

        # 현재 기간
        downloads = await self._count_events(file_access_types, since)
        active_users = await self._count_distinct_users(since)

        # 이전 기간
        prev_downloads = await self._count_events(
            file_access_types, prev_since, prev_until
        )
        prev_active = await self._count_distinct_users(prev_since, prev_until)

        # 인당 이용 건수
        per_user = round(downloads / active_users, 1) if active_users > 0 else 0.0
        prev_per_user = (
            round(prev_downloads / prev_active, 1) if prev_active > 0 else 0.0
        )

        return {
            "downloads": downloads,
            "downloads_delta": _delta(downloads, prev_downloads),
            "active_users": active_users,
            "active_users_delta": _delta(active_users, prev_active),
            "per_user": per_user,
            "per_user_delta": (
                _delta(int(per_user * 10), int(prev_per_user * 10))
                if prev_per_user > 0
                else None
            ),
        }

    async def _get_popular_items(
        self, since: datetime, range_days: int
    ) -> list[dict]:
        prev_since = since - timedelta(days=range_days)

        stmt = (
            select(
                ActionKitEvent.item_id,
                func.count().label("count"),
            )
            .where(
                ActionKitEvent.event_type.in_(["view", "download", "bulk_download"]),
                ActionKitEvent.created_at >= since,
                ActionKitEvent.item_id.isnot(None),
            )
            .group_by(ActionKitEvent.item_id)
            .order_by(func.count().desc())
            .limit(5)
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        items = []
        for row in rows:
            item_id, count = row
            prev_count = await self._count_item_downloads(
                item_id, prev_since, since
            )
            trend = _delta(count, prev_count)
            items.append({
                "item_id": item_id,
                "count": count,
                "trend": trend,
            })
        return items

    async def _get_search_keywords(self, since: datetime) -> list[dict]:
        stmt = (
            select(
                ActionKitEvent.search_query,
                func.count().label("count"),
            )
            .where(
                ActionKitEvent.event_type == "search",
                ActionKitEvent.created_at >= since,
                ActionKitEvent.search_query.isnot(None),
                ActionKitEvent.search_query != "",
            )
            .group_by(ActionKitEvent.search_query)
            .order_by(func.count().desc())
            .limit(10)
        )
        result = await self._session.execute(stmt)
        return [{"keyword": row[0], "count": row[1]} for row in result.all()]

    def _generate_insight(
        self,
        kpi: dict,
        popular_items: list[dict],
        search_keywords: list[dict],
    ) -> str | None:
        parts = []

        # 급성장 아이템
        trending = [
            item
            for item in popular_items
            if item.get("trend") is not None and item["trend"] > 0.1
        ]
        if trending:
            top = trending[0]
            pct = int(top["trend"] * 100)
            parts.append(
                f"아이템 #{top['item_id']}의 이용 건수가 전기 대비 {pct}% 증가했습니다."
            )

        # 인기 검색어
        if search_keywords:
            top_kw = search_keywords[0]["keyword"]
            parts.append(f"가장 많이 검색된 키워드는 '{top_kw}'입니다.")

        # KPI 요약
        if kpi.get("downloads_delta") is not None and kpi["downloads_delta"] > 0:
            pct = int(kpi["downloads_delta"] * 100)
            parts.append(f"전체 이용 건수가 전기 대비 {pct}% 증가했습니다.")

        return " ".join(parts) if parts else None

    # ── private helpers ──

    async def _count_events(
        self,
        event_types: list[str],
        since: datetime,
        until: datetime | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(ActionKitEvent)
            .where(
                ActionKitEvent.event_type.in_(event_types),
                ActionKitEvent.created_at >= since,
            )
        )
        if until:
            stmt = stmt.where(ActionKitEvent.created_at < until)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _count_distinct_users(
        self, since: datetime, until: datetime | None = None
    ) -> int:
        stmt = (
            select(func.count(func.distinct(ActionKitEvent.user_id)))
            .select_from(ActionKitEvent)
            .where(
                ActionKitEvent.created_at >= since,
                ActionKitEvent.user_id.isnot(None),
            )
        )
        if until:
            stmt = stmt.where(ActionKitEvent.created_at < until)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _count_item_downloads(
        self, item_id: int, since: datetime, until: datetime
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(ActionKitEvent)
            .where(
                ActionKitEvent.event_type.in_(["view", "download", "bulk_download"]),
                ActionKitEvent.item_id == item_id,
                ActionKitEvent.created_at >= since,
                ActionKitEvent.created_at < until,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
