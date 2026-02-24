from typing import List
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import func, desc, delete

from app.core.db import get_session
from app.models.growth_club import GrowthClubPost, GrowthClubPostRead, GrowthClubComment, GrowthClubCommentRead, GrowthClubPostReport, GrowthClubCommentReport
from app.features.ops.application.growth_club import get_queue_summary
from app.features.ops.application.audit_logs.service import save_audit_log
from app.api.deps import get_current_user
from app.models.user import AuthenticatedUser, User

router = APIRouter(prefix="/growth-club")


@router.get(
    "/queue-summary",
    summary="커뮤니티 모더레이션 큐 요약 조회",
    description="신고 게시글/댓글 처리 대기 건수 요약을 조회합니다.",
    response_description="모더레이션 큐 요약을 반환합니다.",
)
async def get_growth_club_queue_summary() -> dict[str, int]:
    return get_queue_summary()


@router.get(
    "/posts/blinded",
    summary="블라인드 게시글 목록 조회",
    description="운영자에 의해 또는 자동 신고로 블라인드 처리된 게시글 목록을 조회합니다.",
    response_model=List[GrowthClubPostRead],
)
async def list_blinded_posts(
    session: AsyncSession = Depends(get_session)
):
    from app.models.growth_club import GrowthClubPostReport
    
    query = (
        select(
            GrowthClubPost,
            func.count(GrowthClubPostReport.id).label("report_count_val"),
            func.mode().within_group(GrowthClubPostReport.reason).label("most_common_reason")
        )
        .outerjoin(GrowthClubPostReport)
        .where(GrowthClubPost.is_blinded == True)
        .group_by(GrowthClubPost.id)
        .order_by(desc("report_count_val"))
        .options(
            selectinload(GrowthClubPost.author).selectinload(User.profile),
            selectinload(GrowthClubPost.attachments),
            selectinload(GrowthClubPost.comments).selectinload(GrowthClubComment.author).selectinload(User.profile),
        )
    )
    result = await session.execute(query)
    
    read_posts = []
    for post, report_count, report_reason in result.all():
        post_read = GrowthClubPostRead.model_validate(post)
        post_read.report_count = report_count
        post_read.report_reason = report_reason
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
    session: AsyncSession = Depends(get_session)
):
    post = await session.get(GrowthClubPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.is_blinded = False
    post.report_count = 0  # 블라인드 해제 시 신고 횟수도 초기화
    
    # 신고 기록 삭제
    await session.execute(delete(GrowthClubPostReport).where(GrowthClubPostReport.post_id == post_id))
    
    # 감사 로그 기록
    await save_audit_log(
        session=session,
        user_id=current_user.id,
        action="growth_club.post.unblind",
        target_type="post",
        target_id=str(post_id),
        details=f"게시글 '{post.title}' 블라인드 해제"
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
async def list_blinded_comments(
    session: AsyncSession = Depends(get_session)
):
    from app.models.growth_club import GrowthClubCommentReport
    
    query = (
        select(
            GrowthClubComment,
            func.count(GrowthClubCommentReport.id).label("report_count_val"),
            func.mode().within_group(GrowthClubCommentReport.reason).label("most_common_reason")
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
    session: AsyncSession = Depends(get_session)
):
    comment = await session.get(GrowthClubComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment.is_blinded = False
    comment.report_count = 0
    
    # 신고 기록 삭제
    await session.execute(delete(GrowthClubCommentReport).where(GrowthClubCommentReport.comment_id == comment_id))
    
    # 감사 로그 기록
    await save_audit_log(
        session=session,
        user_id=current_user.id,
        action="growth_club.comment.unblind",
        target_type="comment",
        target_id=str(comment_id),
        details=f"댓글 '{comment.content[:20]}...' 블라인드 해제"
    )
    
    session.add(comment)
    await session.commit()
    
    return {"status": "success", "message": "Comment unblinded successfully"}
