from fastapi import APIRouter

from app.features.ops.application.reports import get_summary

router = APIRouter(prefix="/reports")


@router.get(
    "/summary",
    summary="운영 리포트 요약 조회",
    description="운영 콘솔 카드에서 사용하는 핵심 지표 요약을 조회합니다.",
    response_description="최근 7일 기준 운영 지표 요약을 반환합니다.",
)
async def get_ops_summary() -> dict[str, str | int]:
    return get_summary()
