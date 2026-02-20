from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models.growth_club import GrowthClubComment, GrowthClubCommentRead, GrowthClubPost
from app.models.user import AuthenticatedUser

router = APIRouter()


class CommentCreate(BaseModel):
    content: str
    post_id: int
    parent_id: Optional[int] = None


@router.post("", response_model=GrowthClubCommentRead)
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
        .options(selectinload(GrowthClubComment.author))
    )
    result = await session.execute(query)
    return result.scalar_one()


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    comment = await session.get(GrowthClubComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    await session.delete(comment)
    await session.commit()
    return {"status": "success"}
