from typing import TypedDict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.growth_club import GrowthClubComment, GrowthClubPost


class GrowthClubQueueSummary(TypedDict):
    pending_posts: int
    pending_comments: int


async def get_queue_summary(session: AsyncSession) -> GrowthClubQueueSummary:
    post_stmt = select(func.count()).where(
        GrowthClubPost.report_count > 0,
        GrowthClubPost.is_blinded.is_(False),
    )
    comment_stmt = select(func.count()).where(
        GrowthClubComment.report_count > 0,
        GrowthClubComment.is_blinded.is_(False),
    )

    post_result = await session.execute(post_stmt)
    comment_result = await session.execute(comment_stmt)

    return {
        "pending_posts": post_result.scalar_one(),
        "pending_comments": comment_result.scalar_one(),
    }
