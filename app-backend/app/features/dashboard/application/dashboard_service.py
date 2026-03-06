from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_club import GrowthClubPost
from app.models.user import User
from app.repositories.roadmap_repository import RoadmapRepository


@dataclass
class CurrentPhaseResult:
    title: str
    progress: int
    status: str


@dataclass
class DashboardStatsResult:
    days_left: int
    tasks_completed: int
    total_tasks: int


@dataclass
class RecentPostResult:
    id: int
    title: str
    author_name: str
    created_at: str
    comment_count: int


@dataclass
class GrowthClubResult:
    founders_online: int
    recent_posts: list[RecentPostResult] = field(default_factory=list)


@dataclass
class RoadmapItemResult:
    title: str
    status: str
    date: str


@dataclass
class DashboardResult:
    user_name: str
    current_phase: CurrentPhaseResult
    roadmap: list[RoadmapItemResult]
    stats: DashboardStatsResult
    growth_club: GrowthClubResult
    roadmap_id: str | None = None


class DashboardService:
    def __init__(
        self,
        roadmap_repo: RoadmapRepository,
        session: AsyncSession | None = None,
    ):
        self.roadmap_repo = roadmap_repo
        self.session = session

    async def _get_growth_club(self) -> GrowthClubResult:
        try:
            return await self._query_growth_club()
        except Exception:
            return GrowthClubResult(founders_online=0)

    async def _query_growth_club(self) -> GrowthClubResult:
        if self.session is None:
            return GrowthClubResult(founders_online=0)

        seven_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
            days=7
        )

        # Active founders: distinct authors in last 7 days
        count_stmt = sa.select(
            sa.func.count(sa.distinct(GrowthClubPost.author_id))
        ).where(GrowthClubPost.created_at >= seven_days_ago)
        count_result = await self.session.execute(count_stmt)
        founders_online = count_result.scalar_one() or 0

        # Recent 3 posts with comment count
        try:
            from app.models.growth_club import GrowthClubComment

            comment_count_sub = (
                sa.select(
                    GrowthClubComment.post_id,
                    sa.func.count().label("cnt"),
                )
                .group_by(GrowthClubComment.post_id)
                .subquery()
            )

            posts_stmt = (
                sa.select(
                    GrowthClubPost.id,
                    GrowthClubPost.title,
                    GrowthClubPost.created_at,
                    User.full_name,
                    User.email,
                    sa.func.coalesce(comment_count_sub.c.cnt, 0).label(
                        "comment_count"
                    ),
                )
                .join(User, User.id == GrowthClubPost.author_id)
                .outerjoin(
                    comment_count_sub,
                    comment_count_sub.c.post_id == GrowthClubPost.id,
                )
                .order_by(GrowthClubPost.created_at.desc())
                .limit(3)
            )
            posts_result = await self.session.execute(posts_stmt)
            rows = posts_result.all()
        except Exception:
            rows = []

        recent_posts: list[RecentPostResult] = []
        for row in rows:
            author_name = row.full_name or (row.email.split("@")[0] if row.email else "Unknown")
            recent_posts.append(
                RecentPostResult(
                    id=row.id,
                    title=row.title,
                    author_name=author_name,
                    created_at=row.created_at.isoformat() if row.created_at else "",
                    comment_count=row.comment_count,
                )
            )

        return GrowthClubResult(
            founders_online=founders_online,
            recent_posts=recent_posts,
        )

    async def get_dashboard(
        self,
        *,
        team_id: UUID,
        user_name: str,
        is_guest: bool,
        roadmap_id: UUID | None = None,
    ) -> DashboardResult:
        growth_club = await self._get_growth_club()

        if is_guest:
            return DashboardResult(
                user_name="Guest",
                current_phase=CurrentPhaseResult(
                    title="로드맵을 생성해 보세요",
                    progress=0,
                    status="GUEST",
                ),
                roadmap=[
                    RoadmapItemResult(title="Step 1: 아이디어 검증", status="locked", date="-"),
                    RoadmapItemResult(title="Step 2: 법인 설립", status="locked", date="-"),
                    RoadmapItemResult(title="Step 3: 비즈니스 계좌", status="locked", date="-"),
                ],
                stats=DashboardStatsResult(days_left=0, tasks_completed=0, total_tasks=0),
                growth_club=growth_club,
            )

        if roadmap_id:
            latest_roadmap = await self.roadmap_repo.get_by_id_for_team(
                roadmap_id, team_id
            )
        else:
            latest_roadmap = await self.roadmap_repo.get_latest_for_team(team_id)
        if not latest_roadmap:
            return DashboardResult(
                user_name=user_name,
                current_phase=CurrentPhaseResult(
                    title="로드맵을 생성해 보세요",
                    progress=0,
                    status="READY",
                ),
                roadmap=[],
                stats=DashboardStatsResult(days_left=0, tasks_completed=0, total_tasks=0),
                growth_club=growth_club,
            )

        steps = await self.roadmap_repo.list_steps(latest_roadmap.id)
        total_tasks = len(steps)
        tasks_completed = len([step for step in steps if step.status == "COMPLETED"])
        progress = int((tasks_completed / total_tasks) * 100) if total_tasks else 0
        current_step = next(
            (step for step in steps if step.status != "COMPLETED"), None
        )
        phase_title = current_step.title if current_step else "모든 단계 완료"

        step_ids = [step.id for step in steps if step.id is not None]
        detail_map = {}
        if step_ids:
            details = await self.roadmap_repo.list_step_details(step_ids)
            detail_map = {detail.roadmap_step_id: detail for detail in details}

        if current_step and current_step.id is not None:
            current_detail = detail_map.get(current_step.id)
            if current_detail and current_detail.phase:
                phase_title = current_detail.phase
        phase_status = "IN_PROGRESS" if current_step else "COMPLETED"

        phase_order: list[str] = []
        phase_stats: dict[str, dict[str, int]] = {}
        for step in steps:
            phase_name = step.title
            if step.id is not None:
                detail = detail_map.get(step.id)
                if detail and detail.phase:
                    phase_name = detail.phase
            if phase_name not in phase_stats:
                phase_order.append(phase_name)
                phase_stats[phase_name] = {"total": 0, "completed": 0}
            phase_stats[phase_name]["total"] += 1
            if step.status == "COMPLETED":
                phase_stats[phase_name]["completed"] += 1

        current_phase_idx = next(
            (
                idx
                for idx, phase_name in enumerate(phase_order)
                if phase_stats[phase_name]["completed"]
                < phase_stats[phase_name]["total"]
            ),
            None,
        )
        roadmap_items = []
        for idx, phase_name in enumerate(phase_order):
            stat = phase_stats[phase_name]
            if stat["completed"] == stat["total"]:
                status = "completed"
                date = latest_roadmap.created_at.strftime("%b %d")
            elif current_phase_idx is not None and idx == current_phase_idx:
                status = "current"
                date = "-"
            else:
                status = "locked"
                date = "-"
            roadmap_items.append(RoadmapItemResult(title=phase_name, status=status, date=date))

        created_at = (
            latest_roadmap.created_at.replace(tzinfo=timezone.utc)
            if latest_roadmap.created_at.tzinfo is None
            else latest_roadmap.created_at
        )
        horizon = getattr(latest_roadmap, "goal_horizon_days", 30) or 30
        days_left = max(0, horizon - (datetime.now(timezone.utc) - created_at).days)

        return DashboardResult(
            user_name=user_name,
            current_phase=CurrentPhaseResult(
                title=phase_title,
                progress=progress,
                status=phase_status,
            ),
            roadmap=roadmap_items,
            stats=DashboardStatsResult(
                days_left=days_left,
                tasks_completed=tasks_completed,
                total_tasks=total_tasks,
            ),
            growth_club=growth_club,
            roadmap_id=str(latest_roadmap.id),
        )
