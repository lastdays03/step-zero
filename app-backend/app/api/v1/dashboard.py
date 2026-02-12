
from typing import Any
from fastapi import APIRouter, Depends
from app.api import deps

router = APIRouter()

@router.get("", response_model=Any)
async def get_dashboard_stats(
    current_user: Any = Depends(deps.get_current_user)
) -> Any:
    """
    Get dashboard statistics and roadmap summary.
    """
    # Mock Data matching the design
    return {
        "user_name": "Alex",  # Or current_user['username']
        "current_phase": {
            "title": "Business Registration",
            "progress": 20,
            "status": "IN_PROGRESS"
        },
        "roadmap": [
            {"title": "Idea Validation", "status": "COMPLETED", "date": "Jan 12"},
            {"title": "Sign Lease", "status": "COMPLETED", "date": "Jan 24"},
            {"title": "Tax Registration", "status": "CURRENT", "date": "Current Task"},
            {"title": "Bank Account", "status": "LOCKED", "date": "Estimated Feb 10"}
        ],
        "stats": {
            "days_left": 3,
            "tasks_completed": 8,
            "total_tasks": 12
        },
        "growth_club": {
            "founders_online": 12
        }
    }
