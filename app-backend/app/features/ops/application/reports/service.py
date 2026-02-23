from datetime import datetime, timezone
from typing import TypedDict


class OpsSummary(TypedDict):
    active_users_7d: int
    new_signups_7d: int
    roadmaps_generated_7d: int
    generated_at: str


def get_summary() -> OpsSummary:
    # TODO: Replace with real metrics aggregation.
    return {
        "active_users_7d": 0,
        "new_signups_7d": 0,
        "roadmaps_generated_7d": 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
