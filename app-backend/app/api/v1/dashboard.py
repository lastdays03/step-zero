
from typing import Any
from fastapi import APIRouter, Depends
from app.api import deps

router = APIRouter()

@router.get("", response_model=Any)
async def get_dashboard_stats(
    current_user: Any = Depends(deps.get_optional_current_user)
) -> Any:
    """
    Get dashboard statistics and roadmap summary.
    If no user is logged in, return guest data.
    """
    if not current_user:
        # Guest Data
        return {
            "user_name": "Guest",
            "current_phase": {
                "title": "로드맵을 생성해 보세요",
                "progress": 0,
                "status": "GUEST"
            },
            "roadmap": [
                {"title": "Step 1: 아이디어 검증", "status": "LOCKED", "date": "-"},
                {"title": "Step 2: 법인 설립", "status": "LOCKED", "date": "-"},
                {"title": "Step 3: 비즈니스 계좌", "status": "LOCKED", "date": "-"}
            ],
            "stats": {
                "days_left": 0,
                "tasks_completed": 0,
                "total_tasks": 0
            },
            "growth_club": {
                "founders_online": 1250 # Static Social Proof for guests
            }
        }

    # Authenticated Member Data (Mock)
    return {
        "user_name": "Alex",
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
