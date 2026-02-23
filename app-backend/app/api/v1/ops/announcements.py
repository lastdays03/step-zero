from fastapi import APIRouter

from app.features.ops.application.announcements import list_announcements

router = APIRouter(prefix="/announcements")


@router.get(
    "",
    summary="운영 공지 목록 조회",
    description="운영 공지 작성/수정/게시 관리를 위한 목록을 조회합니다.",
    response_description="운영 공지 목록을 반환합니다.",
)
async def get_announcements() -> dict[str, list[dict[str, str]]]:
    return list_announcements()
