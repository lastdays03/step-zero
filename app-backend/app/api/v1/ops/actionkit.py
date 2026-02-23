from fastapi import APIRouter

from app.features.ops.application.actionkit import get_summary

router = APIRouter(prefix="/actionkit")


@router.get(
    "/summary",
    summary="액션키트 운영 요약 조회",
    description="액션키트 운영 화면에서 사용하는 기본 요약을 조회합니다.",
    response_description="액션키트 운영 요약을 반환합니다.",
)
async def get_actionkit_summary() -> dict[str, int]:
    return get_summary()
