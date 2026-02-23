from fastapi import APIRouter

from app.features.ops.application.growth_club import get_queue_summary

router = APIRouter(prefix="/growth-club")


@router.get(
    "/queue-summary",
    summary="커뮤니티 모더레이션 큐 요약 조회",
    description="신고 게시글/댓글 처리 대기 건수 요약을 조회합니다.",
    response_description="모더레이션 큐 요약을 반환합니다.",
)
async def get_growth_club_queue_summary() -> dict[str, int]:
    return get_queue_summary()
