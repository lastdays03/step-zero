from typing import TypedDict


class GrowthClubQueueSummary(TypedDict):
    pending_posts: int
    pending_comments: int


def get_queue_summary() -> GrowthClubQueueSummary:
    # TODO: connect to moderation queue repository
    return {"pending_posts": 0, "pending_comments": 0}
