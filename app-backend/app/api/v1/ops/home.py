from fastapi import APIRouter

from app.features.ops.application.home import get_overview

router = APIRouter()


@router.get(
    "/overview",
    summary="운영 홈 메뉴 구조 조회",
    description="운영 콘솔 홈에서 사용하는 메뉴 구조를 조회합니다.",
    response_description="운영 메뉴 구조를 반환합니다.",
)
async def get_ops_overview() -> dict[str, list[dict[str, str]]]:
    return get_overview()
