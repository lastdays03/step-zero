from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/reports")


@router.get(
    "/summary",
    summary="운영 리포트 요약 조회",
    description="운영 콘솔 카드에서 사용하는 핵심 지표 요약을 조회합니다.",
    response_description="최근 7일 기준 운영 지표 요약을 반환합니다.",
)
async def get_ops_summary() -> dict[str, str | int]:
    # TODO: Replace with real metrics aggregation.
    return {
        "active_users_7d": 0,
        "new_signups_7d": 0,
        "roadmaps_generated_7d": 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
