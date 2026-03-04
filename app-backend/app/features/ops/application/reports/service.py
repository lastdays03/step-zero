from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_club import GrowthClubPost
from app.models.roadmap import Roadmap
from app.models.roadmap_chat import RoadmapChatThread
from app.models.team import Team
from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class OpsReportsService:
    def __init__(self, session: AsyncSession):
        self._session = session

    # ── public ──────────────────────────────────────────

    async def get_summary(self, range_days: int = 7) -> dict:
        now = _utcnow()
        since = _shift(now, -range_days)
        prev_since = _shift(now, -range_days * 2)
        prev_until = since

        # 현재 기간 지표
        active_users = await self._count_active_users(since)
        new_signups = await self._count_new_signups(since)
        roadmaps_generated = await self._count_roadmaps(since)
        chat_sessions = await self._count_chat_sessions(since)
        community_posts = await self._count_community_posts(since)

        # 이전 기간 지표 (delta 계산용)
        prev_active = await self._count_active_users(prev_since, prev_until)
        prev_signups = await self._count_new_signups(prev_since, prev_until)
        prev_roadmaps = await self._count_roadmaps(prev_since, prev_until)

        # 총계
        total_users = await self._count_total_users()
        total_teams = await self._count_total_teams()
        total_roadmaps = await self._count_total_roadmaps()

        # 비율
        dau_mau_ratio = await self._calc_dau_mau_ratio()
        signup_to_roadmap_rate = await self._calc_signup_to_roadmap_rate(since)

        return {
            "active_users": active_users,
            "new_signups": new_signups,
            "roadmaps_generated": roadmaps_generated,
            "chat_sessions": chat_sessions,
            "community_posts": community_posts,
            "dau_mau_ratio": dau_mau_ratio,
            "signup_to_roadmap_rate": signup_to_roadmap_rate,
            "total_users": total_users,
            "total_teams": total_teams,
            "total_roadmaps": total_roadmaps,
            "active_users_delta": _delta(active_users, prev_active),
            "new_signups_delta": _delta(new_signups, prev_signups),
            "roadmaps_generated_delta": _delta(roadmaps_generated, prev_roadmaps),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "range": f"{range_days}d",
        }

    # ── private queries ─────────────────────────────────

    async def _count_active_users(
        self, since: datetime, until: datetime | None = None
    ) -> int:
        stmt = select(func.count()).select_from(User).where(
            User.last_login_at.isnot(None),
            User.last_login_at >= since,
            User.is_active.is_(True),
            User.is_suspended.is_(False),
        )
        if until:
            stmt = stmt.where(User.last_login_at < until)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _count_new_signups(
        self, since: datetime, until: datetime | None = None
    ) -> int:
        stmt = select(func.count()).select_from(User).where(User.created_at >= since)
        if until:
            stmt = stmt.where(User.created_at < until)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _count_roadmaps(
        self, since: datetime, until: datetime | None = None
    ) -> int:
        stmt = select(func.count()).select_from(Roadmap).where(
            Roadmap.created_at >= since,
            Roadmap.deleted_at.is_(None),
        )
        if until:
            stmt = stmt.where(Roadmap.created_at < until)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _count_chat_sessions(
        self, since: datetime, until: datetime | None = None
    ) -> int:
        stmt = select(func.count()).select_from(RoadmapChatThread).where(
            RoadmapChatThread.created_at >= since,
            RoadmapChatThread.is_deleted.is_(False),
        )
        if until:
            stmt = stmt.where(RoadmapChatThread.created_at < until)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _count_community_posts(
        self, since: datetime, until: datetime | None = None
    ) -> int:
        stmt = select(func.count()).select_from(GrowthClubPost).where(
            GrowthClubPost.created_at >= since,
        )
        if until:
            stmt = stmt.where(GrowthClubPost.created_at < until)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _count_total_users(self) -> int:
        stmt = select(func.count()).select_from(User).where(User.is_active.is_(True))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _count_total_teams(self) -> int:
        stmt = select(func.count()).select_from(Team).where(Team.deleted_at.is_(None))
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _count_total_roadmaps(self) -> int:
        stmt = select(func.count()).select_from(Roadmap).where(
            Roadmap.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def _calc_dau_mau_ratio(self) -> float:
        now = _utcnow()
        dau_7d = await self._count_active_users(_shift(now, -7))
        mau_30d = await self._count_active_users(_shift(now, -30))
        if mau_30d == 0:
            return 0.0
        return round(dau_7d / mau_30d, 3)

    async def _calc_signup_to_roadmap_rate(self, since: datetime) -> float:
        new_signups = await self._count_new_signups(since)
        if new_signups == 0:
            return 0.0
        stmt = (
            select(func.count(func.distinct(Roadmap.created_by)))
            .select_from(Roadmap)
            .join(User, Roadmap.created_by == User.id)
            .where(
                User.created_at >= since,
                Roadmap.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        converted = result.scalar_one()
        return round(converted / new_signups, 3)


# ── helpers ─────────────────────────────────────────────


def _shift(dt: datetime, days: int) -> datetime:
    from datetime import timedelta

    return dt + timedelta(days=days)


def _delta(current: int, previous: int) -> float | None:
    if previous == 0:
        return None
    return round((current - previous) / previous, 3)
