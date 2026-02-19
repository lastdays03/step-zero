from datetime import datetime

from fastapi import APIRouter

router = APIRouter(prefix="/reports")


@router.get("/summary")
async def get_ops_summary() -> dict[str, str | int]:
    # TODO: Replace with real metrics aggregation.
    return {
        "active_users_7d": 0,
        "new_signups_7d": 0,
        "roadmaps_generated_7d": 0,
        "generated_at": datetime.utcnow().isoformat(),
    }
