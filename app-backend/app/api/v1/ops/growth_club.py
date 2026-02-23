from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api import deps
from app.core.db import get_session
from app.features.ops.application.audit_logs import record_admin_audit_log
from app.features.ops.application.growth_club import get_queue_summary
from app.models.growth_club import GrowthClubPost
from app.models.user import AuthenticatedUser

router = APIRouter(prefix="/growth-club")


@router.get(
    "/queue-summary",
    summary="커뮤니티 모더레이션 큐 요약 조회",
    description="신고 게시글/댓글 처리 대기 건수 요약을 조회합니다.",
    response_description="모더레이션 큐 요약을 반환합니다.",
)
async def get_growth_club_queue_summary() -> dict[str, int]:
    return get_queue_summary()


class OpsGrowthClubModerateRequest(BaseModel):
    action: str  # blind | unblind | delete
    reason: str | None = None


@router.patch(
    "/posts/{post_id}/moderate",
    summary="운영 그로스클럽 게시글 조치",
    description="게시글 블라인드/해제/삭제 조치를 수행하고 감사로그를 남깁니다.",
    response_description="조치 결과를 반환합니다.",
)
async def moderate_growth_club_post(
    payload: OpsGrowthClubModerateRequest,
    post_id: int = Path(description="조치할 게시글 ID"),
    session: AsyncSession = Depends(get_session),
    admin_user: AuthenticatedUser = Depends(deps.get_current_user),
) -> dict[str, object]:
    action = payload.action.strip().lower()
    if action not in {"blind", "unblind", "delete"}:
        raise HTTPException(status_code=400, detail="Unsupported action")

    stmt = select(GrowthClubPost).where(GrowthClubPost.id == post_id)
    post = (await session.execute(stmt)).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    before = {"is_blinded": bool(post.is_blinded), "report_count": int(post.report_count)}

    if action == "blind":
        if post.is_blinded:
            return {"status": "no_change", "post_id": post.id, "is_blinded": True}
        post.is_blinded = True
        after = {"is_blinded": True}
        action_code = "growth_club.post.blinded"
    elif action == "unblind":
        if not post.is_blinded:
            return {"status": "no_change", "post_id": post.id, "is_blinded": False}
        post.is_blinded = False
        after = {"is_blinded": False}
        action_code = "growth_club.post.unblinded"
    else:
        await session.delete(post)
        after = {"deleted": True}
        action_code = "growth_club.post.deleted"

    await record_admin_audit_log(
        session,
        admin_id=admin_user.id,
        action=action_code,
        target_type="growth_club_post",
        target_id=str(post_id),
        reason=payload.reason,
        meta={"before": before, "after": after},
    )
    await session.commit()

    result: dict[str, object] = {"status": "success", "post_id": post_id, "action": action}
    result.update(after)
    return result
