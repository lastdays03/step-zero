from typing import TypedDict


class ActionKitOpsSummary(TypedDict):
    total_items: int
    pending_reviews: int


def get_summary() -> ActionKitOpsSummary:
    # TODO: connect to actionkit ops repository
    return {"total_items": 0, "pending_reviews": 0}
