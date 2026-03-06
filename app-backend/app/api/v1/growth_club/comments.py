from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.deps import get_current_user
from app.core.db import get_session
from app.services.notification_pubsub import publish_notification
from app.models.growth_club import (
    GrowthClubComment,
    GrowthClubCommentRead,
    GrowthClubCommentReport,
    GrowthClubPost,
)
from app.models.notification import Notification
from app.models.user import AuthenticatedUser, User

router = APIRouter()


class CommentCreate(BaseModel):
    content: str
    post_id: int
    parent_id: Optional[int] = None


class ReportRequest(BaseModel):
    reason: str = Field(..., description="신고 사유")


@router.post(
    "",
    response_model=GrowthClubCommentRead,
    summary="댓글 생성",
    description="게시글에 댓글(또는 대댓글)을 생성합니다.",
    response_description="생성된 댓글 정보를 반환합니다.",
)
async def create_comment(
    comment_in: CommentCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if current_user.is_suspended:
        raise HTTPException(
            status_code=403, detail="이용이 정지된 사용자입니다. 접근이 제한됩니다."
        )
    post = await session.get(GrowthClubPost, comment_in.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = GrowthClubComment(
        content=comment_in.content,
        post_id=comment_in.post_id,
        parent_id=comment_in.parent_id,
        author_id=current_user.id,
    )
    session.add(comment)

    # Notify post author if not the same user
    if post.author_id != current_user.id:
        notification = Notification(
            user_id=post.author_id,
            content=f"{current_user.full_name or current_user.email}님이 당신의 게시물에 댓글을 달았습니다.",
            type="comment",
            link=f"/growth-club/{post.id}",
            resource_id=post.id,
        )
        session.add(notification)

    # Notify parent comment author if it's a reply
    if comment_in.parent_id:
        parent_comment = await session.get(GrowthClubComment, comment_in.parent_id)
        if parent_comment and parent_comment.author_id != current_user.id:
            # Avoid duplicate if post author is the same as parent comment author
            if parent_comment.author_id != post.author_id:
                reply_notification = Notification(
                    user_id=parent_comment.author_id,
                    content=f"{current_user.full_name or current_user.email}님이 당신의 댓글에 답글을 달았습니다.",
                    type="reply",
                    link=f"/growth-club/{post.id}",
                    resource_id=post.id,
                )
                session.add(reply_notification)

    # Collect notification user IDs for SSE push
    _sse_targets: list[int] = []
    if post.author_id != current_user.id:
        _sse_targets.append(post.author_id)
    if comment_in.parent_id:
        parent_comment_obj = await session.get(GrowthClubComment, comment_in.parent_id)
        if (
            parent_comment_obj
            and parent_comment_obj.author_id != current_user.id
            and parent_comment_obj.author_id != post.author_id
        ):
            _sse_targets.append(parent_comment_obj.author_id)

    await session.flush()
    comment_id = comment.id
    await session.commit()

    # Publish SSE events (fire-and-forget)
    for uid in _sse_targets:
        await publish_notification(uid, {"type": "new_notification"})

    # Refresh with author relationship to satisfy response model
    query = (
        select(GrowthClubComment)
        .where(GrowthClubComment.id == comment_id)
        .options(selectinload(GrowthClubComment.author).selectinload(User.profile))
    )
    result = await session.execute(query)
    comment = result.scalar_one()
    read_comment = GrowthClubCommentRead.model_validate(comment)
    read_comment.author.mask_privacy(current_user.id)
    return read_comment


@router.delete(
    "/{comment_id}",
    summary="댓글 삭제",
    description="댓글 작성자 또는 운영자가 댓글을 삭제합니다.",
    response_description="삭제 결과를 반환합니다.",
)
async def delete_comment(
    comment_id: int = Path(description="삭제할 댓글 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    comment = await session.get(GrowthClubComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    await session.delete(comment)
    await session.commit()
    return {"status": "success"}


@router.post(
    "/{comment_id}/report",
    summary="댓글 신고",
    description="댓글을 신고합니다. 1회 이상 신고 시 자동 블라인드 처리됩니다.",
    response_description="신고 결과와 블라인드 상태를 반환합니다.",
)
async def report_comment(
    report_data: ReportRequest,
    comment_id: int = Path(description="신고할 댓글 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """댓글 신고 (1회 이상 신고 시 자동 블라인드)"""
    comment = await session.get(GrowthClubComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id == current_user.id:
        raise HTTPException(status_code=400, detail="자신의 댓글은 신고할 수 없습니다.")

    # 기존 신고 여부 확인
    existing_report_query = select(GrowthClubCommentReport).where(
        GrowthClubCommentReport.comment_id == comment_id,
        GrowthClubCommentReport.reporter_id == current_user.id,
    )
    existing_report_result = await session.execute(existing_report_query)
    if existing_report_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 신고한 댓글입니다.")

    # 신고 기록 생성
    new_report = GrowthClubCommentReport(
        comment_id=comment_id, reporter_id=current_user.id, reason=report_data.reason
    )
    session.add(new_report)

    # 신고 횟수 증가
    comment.report_count += 1

    # 1회 이상 신고 시 자동 블라인드 처리
    if comment.report_count >= 1:
        comment.is_blinded = True
        message = "댓글이 누적 신고로 인해 블라인드 처리되었습니다."

        # 블라인드 처리 시 감사 로그 기록
        author = await session.get(User, comment.author_id)
        from app.features.ops.application.audit_logs.service import save_audit_log

        await save_audit_log(
            session=session,
            user_id=current_user.id,
            action="growth_club.comment.blind",
            target_type="comment",
            target_id=str(comment_id),
            target_author=author.email if author else None,
            details=f"댓글 '{comment.content[:20]}...' 누적 신고로 블라인드 처리 (자동)",
        )
    else:
        message = "댓글이 신고되었습니다."

    session.add(comment)
    await session.commit()

    return {
        "status": "success",
        "message": message,
        "report_count": comment.report_count,
        "is_blinded": comment.is_blinded,
    }
