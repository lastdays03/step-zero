from fastapi import APIRouter

from app.features.ops.application.audit_logs import list_audit_logs

router = APIRouter(prefix="/audit-logs")


@router.get(
    "",
    summary="운영 감사로그 목록 조회",
    description="운영자 조치 이력 목록을 조회합니다.",
    response_description="운영 감사로그 목록을 반환합니다.",
)
async def get_audit_logs() -> dict[str, list[dict[str, str]]]:
    return list_audit_logs()
