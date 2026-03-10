from typing import List

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel
from sqlalchemy import delete, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.deps import get_current_user
from app.core.db import get_session
from app.core.exceptions import (
    BusinessRuleError,
    CommentNotFoundError,
    PostNotFoundError,
    UserNotFoundError,
)
from app.features.ops.application.audit_logs.service import save_audit_log
from app.features.ops.application.growth_club import get_queue_summary
from app.models.file import File
from app.models.growth_club import (
    GrowthClubAttachmentRead,
    GrowthClubComment,
    GrowthClubCommentRead,
    GrowthClubCommentReport,
    GrowthClubPost,
    GrowthClubPostRead,
    GrowthClubPostReport,
)
from app.models.notification import Notification
from app.models.user import AuthenticatedUser, User

router = APIRouter(prefix="/growth-club")


@router.get(
    "/queue-summary",
    summary="커뮤니티 모더레이션 큐 요약 조회",
    description="신고 게시글/댓글 처리 대기 건수 요약을 조회합니다.",
    response_description="모더레이션 큐 요약을 반환합니다.",
)
async def get_growth_club_queue_summary(
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    return await get_queue_summary(session)


@router.get(
    "/posts/blinded",
    summary="블라인드 게시글 목록 조회",
    description="운영자에 의해 또는 자동 신고로 블라인드 처리된 게시글 목록을 조회합니다.",
    response_model=List[GrowthClubPostRead],
)
async def list_blinded_posts(session: AsyncSession = Depends(get_session)):
    from app.models.growth_club import GrowthClubPostReport

    query = (
        select(
            GrowthClubPost,
            func.count(GrowthClubPostReport.id).label("report_count_val"),
            func.mode()
            .within_group(GrowthClubPostReport.reason)
            .label("most_common_reason"),
        )
        .outerjoin(GrowthClubPostReport)
        .where(GrowthClubPost.is_blinded == True)
        .group_by(GrowthClubPost.id)
        .order_by(desc("report_count_val"))
        .options(
            selectinload(GrowthClubPost.author).selectinload(User.profile),
            selectinload(GrowthClubPost.comments)
            .selectinload(GrowthClubComment.author)
            .selectinload(User.profile),
        )
    )
    result = await session.execute(query)

    rows = result.all()
    post_ids = [post.id for post, _, _ in rows]

    # Load attachments from unified File table
    attachments_map: dict[int, list[GrowthClubAttachmentRead]] = {}
    if post_ids:
        file_stmt = select(File).where(
            File.owner_type == "growth_club_post",
            File.owner_id.in_(post_ids),
        )
        file_result = await session.execute(file_stmt)
        for f in file_result.scalars().all():
            att = GrowthClubAttachmentRead(
                id=f.id,
                kind=f.kind or "file",
                object_key=f.object_key,
                original_filename=f.original_filename,
                mime_type=f.mime_type,
                size_bytes=f.size_bytes,
                created_at=f.created_at,
            )
            attachments_map.setdefault(f.owner_id, []).append(att)

    read_posts = []
    for post, report_count, report_reason in rows:
        post_read = GrowthClubPostRead.model_validate(
            post, update={"attachments": []}
        )
        post_read.report_count = report_count
        post_read.report_reason = report_reason
        post_read.attachments = attachments_map.get(post.id, [])
        post_read.comments = []
        post_read.likes_count = 0
        post_read.is_liked = False
        read_posts.append(post_read)

    return read_posts


@router.post(
    "/posts/{post_id}/unblind",
    summary="게시글 블라인드 해제",
    description="블라인드 처리된 게시글을 다시 활성화하여 모든 사용자에게 보이게 합니다.",
)
async def unblind_post(
    post_id: int = Path(..., description="블라인드 해제할 게시글 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(GrowthClubPost, post_id)
    if not post:
        raise PostNotFoundError()

    post.is_blinded = False
    post.report_count = 0  # 블라인드 해제 시 신고 횟수도 초기화

    # 신고 기록 삭제
    await session.execute(
        delete(GrowthClubPostReport).where(GrowthClubPostReport.post_id == post_id)
    )

    # 작성자 정보 조회
    author = await session.get(User, post.author_id)
    target_author = author.email if author else None

    # 기존 블라인드 감사 로그가 있는지 확인하고, 있으면 업데이트
    from app.core.security import utc_now
    from app.models.audit_log import AuditLog

    old_log_query = await session.execute(
        select(AuditLog)
        .where(
            AuditLog.target_type == "post",
            AuditLog.target_id == str(post_id),
            AuditLog.action == "growth_club.post.blind",
        )
        .order_by(desc(AuditLog.created_at))
    )
    old_log = old_log_query.scalars().first()

    if old_log:
        old_log.action = "growth_club.post.unblind"
        old_log.user_id = current_user.id
        old_log.details = f"게시글 '{post.title[:20]}...' 블라인드 해제"
        old_log.created_at = utc_now()
    else:
        # 감사 로그 기록
        await save_audit_log(
            session=session,
            user_id=current_user.id,
            action="growth_club.post.unblind",
            target_type="post",
            target_id=str(post_id),
            target_author=target_author,
            details=f"게시글 '{post.title[:20]}...' 블라인드 해제",
        )

    session.add(post)
    await session.commit()

    return {"status": "success", "message": "Post unblinded successfully"}


@router.get(
    "/comments/blinded",
    summary="블라인드 댓글 목록 조회",
    description="신고로 인해 블라인드 처리된 댓글 목록을 조회합니다.",
    response_model=List[GrowthClubCommentRead],
)
async def list_blinded_comments(session: AsyncSession = Depends(get_session)):
    from app.models.growth_club import GrowthClubCommentReport

    query = (
        select(
            GrowthClubComment,
            func.count(GrowthClubCommentReport.id).label("report_count_val"),
            func.mode()
            .within_group(GrowthClubCommentReport.reason)
            .label("most_common_reason"),
        )
        .outerjoin(GrowthClubCommentReport)
        .where(GrowthClubComment.is_blinded == True)
        .group_by(GrowthClubComment.id)
        .order_by(desc("report_count_val"))
        .options(
            selectinload(GrowthClubComment.author).selectinload(User.profile),
        )
    )
    result = await session.execute(query)

    read_comments = []
    for comment, report_count, report_reason in result.all():
        comment_read = GrowthClubCommentRead.model_validate(comment)
        comment_read.report_count = report_count
        comment_read.report_reason = report_reason
        read_comments.append(comment_read)

    return read_comments


@router.post(
    "/comments/{comment_id}/unblind",
    summary="댓글 블라인드 해제",
    description="블라인드 처리된 댓글을 다시 활성화합니다.",
)
async def unblind_comment(
    comment_id: int = Path(..., description="블라인드 해제할 댓글 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    comment = await session.get(GrowthClubComment, comment_id)
    if not comment:
        raise CommentNotFoundError()

    comment.is_blinded = False
    comment.report_count = 0

    # 신고 기록 삭제
    await session.execute(
        delete(GrowthClubCommentReport).where(
            GrowthClubCommentReport.comment_id == comment_id
        )
    )

    # 작성자 정보 조회
    author = await session.get(User, comment.author_id)
    target_author = author.email if author else None

    # 기존 블라인드 감사 로그가 있는지 확인하고, 있으면 업데이트
    from app.core.security import utc_now  # noqa: F811
    from app.models.audit_log import AuditLog  # noqa: F811

    old_log_query = await session.execute(
        select(AuditLog)
        .where(
            AuditLog.target_type == "comment",
            AuditLog.target_id == str(comment_id),
            AuditLog.action == "growth_club.comment.blind",
        )
        .order_by(desc(AuditLog.created_at))
    )
    old_log = old_log_query.scalars().first()

    if old_log:
        old_log.action = "growth_club.comment.unblind"
        old_log.user_id = current_user.id
        old_log.details = f"댓글 '{comment.content[:20]}...' 블라인드 해제"
        old_log.created_at = utc_now()
    else:
        # 감사 로그 기록
        await save_audit_log(
            session=session,
            user_id=current_user.id,
            action="growth_club.comment.unblind",
            target_type="comment",
            target_id=str(comment_id),
            target_author=target_author,
            details=f"댓글 '{comment.content[:20]}...' 블라인드 해제",
        )

    session.add(comment)
    await session.commit()

    return {"status": "success", "message": "Comment unblinded successfully"}


class SuspendRequest(BaseModel):
    reason: str
    target_type: str  # "POST" or "COMMENT"
    target_id: int


@router.post(
    "/users/{user_id}/suspend",
    summary="작성자 정지",
    description="작성자를 정지하여 그로스 클럽 활동을 제한합니다.",
)
async def suspend_user(
    suspend_data: SuspendRequest,
    user_id: int = Path(..., description="정지할 사용자 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if not user:
        raise UserNotFoundError()

    from datetime import datetime, timezone

    now_utc = datetime.now(timezone.utc)
    user.is_suspended = True
    user.suspended_at = now_utc.replace(tzinfo=None)  # DB는 naive UTC로 저장
    user.suspension_reason = suspend_data.reason
    session.add(user)

    # 알림 생성
    target_label = "게시글" if suspend_data.target_type == "POST" else "댓글"
    message = f"사용자의 {target_label}이 부적절함에 따라 관리자에 의해 그로스 클럽의 이용이 불가합니다. 사유: {suspend_data.reason}"

    notification = Notification(
        user_id=user_id,
        content=message,
        type="notice",
        link="/growth-club",
    )
    session.add(notification)

    # 감사 로그 기록
    from app.features.ops.application.audit_logs.service import save_audit_log

    await save_audit_log(
        session=session,
        user_id=current_user.id,
        action="ops.user.suspend",
        target_type="user",
        target_id=str(user_id),
        target_author=user.email,
        details=f"사용자 '{user.email}' 이용 정지 처리 (사유: {suspend_data.reason})",
    )

    await session.commit()

    # SSE push for suspension notification
    from app.services.notification_pubsub import publish_notification
    await publish_notification(user_id, {"type": "new_notification"})

    # Z suffix를 붙여 프론트엔드가 UTC로 올바르게 파싱하도록 함
    suspended_at_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return {
        "status": "success",
        "message": "User suspended successfully",
        "suspended_at": suspended_at_iso,
    }


@router.post(
    "/users/{user_id}/unsuspend",
    summary="작성자 정지 해제",
    description="정지된 작성자를 원래 상태로 복구합니다.",
)
async def unsuspend_user(
    user_id: int = Path(..., description="정지 해제할 사용자 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if not user:
        raise UserNotFoundError()

    user.is_suspended = False
    user.suspended_at = None
    session.add(user)

    # 감사 로그 기록
    from app.features.ops.application.audit_logs.service import save_audit_log

    await save_audit_log(
        session=session,
        user_id=current_user.id,
        action="ops.user.unsuspend",
        target_type="user",
        target_id=str(user_id),
        target_author=user.email,
        details=f"사용자 '{user.email}' 이용 정지 해제",
    )

    await session.commit()
    return {"status": "success", "message": "User unsuspended successfully"}


@router.delete(
    "/posts/{post_id}",
    summary="블라인드 게시글 영구 삭제",
    description="블라인드 처리된 게시글을 영구적으로 삭제합니다.",
)
async def delete_blinded_post(
    post_id: int = Path(..., description="삭제할 게시글 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    post = await session.get(GrowthClubPost, post_id)
    if not post:
        raise PostNotFoundError()
    if not post.is_blinded:
        raise BusinessRuleError("블라인드 처리된 게시글만 삭제할 수 있습니다.")

    # 작성자 정보
    author = await session.get(User, post.author_id)

    # 감사 로그 저장 (삭제 전)
    await save_audit_log(
        session=session,
        user_id=current_user.id,
        action="growth_club.post.delete",
        target_type="post",
        target_id=str(post_id),
        target_author=author.email if author else None,
        details=f"게시글 '{post.title[:20]}...' 운영자에 의해 영구 삭제",
    )

    await session.delete(post)
    await session.commit()
    return {"status": "success", "message": "Post permanently deleted"}


@router.delete(
    "/comments/{comment_id}",
    summary="블라인드 댓글 영구 삭제",
    description="블라인드 처리된 댓글을 영구적으로 삭제합니다.",
)
async def delete_blinded_comment(
    comment_id: int = Path(..., description="삭제할 댓글 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    comment = await session.get(GrowthClubComment, comment_id)
    if not comment:
        raise CommentNotFoundError()
    if not comment.is_blinded:
        raise BusinessRuleError("블라인드 처리된 댓글만 삭제할 수 있습니다.")

    # 작성자 정보
    author = await session.get(User, comment.author_id)

    # 감사 로그 저장 (삭제 전)
    await save_audit_log(
        session=session,
        user_id=current_user.id,
        action="growth_club.comment.delete",
        target_type="comment",
        target_id=str(comment_id),
        target_author=author.email if author else None,
        details=f"댓글 '{comment.content[:20]}...' 운영자에 의해 영구 삭제",
    )

    await session.delete(comment)
    await session.commit()
    return {"status": "success", "message": "Comment permanently deleted"}
