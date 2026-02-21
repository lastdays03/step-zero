from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.growth_club import GrowthClubComment, GrowthClubCommentRead, GrowthClubPost
from app.models.user import AuthenticatedUser, User

router = APIRouter()


class CommentCreate(BaseModel):
    content: str
    post_id: int
    parent_id: Optional[int] = None


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
    session: AsyncSession = Depends(get_session)
):
    post = await session.get(GrowthClubPost, comment_in.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comment = GrowthClubComment(
        content=comment_in.content,
        post_id=comment_in.post_id,
        parent_id=comment_in.parent_id,
        author_id=current_user.id
    )
    session.add(comment)
    await session.flush()
    comment_id = comment.id
    await session.commit()

    # Refresh with author relationship to satisfy response model
    query = (
        select(GrowthClubComment)
        .where(GrowthClubComment.id == comment_id)
        .options(selectinload(GrowthClubComment.author).selectinload(User.profile))
    )
    result = await session.execute(query)
    return result.scalar_one()


@router.delete(
    "/{comment_id}",
    summary="댓글 삭제",
    description="댓글 작성자 또는 운영자가 댓글을 삭제합니다.",
    response_description="삭제 결과를 반환합니다.",
)
async def delete_comment(
    comment_id: int = Path(..., description="삭제할 댓글 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    comment = await session.get(GrowthClubComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 대댓글 먼저 삭제 (ForeignKey constraint error 방지)
    replies_query = select(GrowthClubComment).where(GrowthClubComment.parent_id == comment_id)
    replies_result = await session.execute(replies_query)
    replies = replies_result.scalars().all()
    for reply in replies:
        await session.delete(reply)

    await session.delete(comment)
    await session.commit()
    return {"status": "success"}
