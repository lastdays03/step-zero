import os
import shutil
import time
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.deps import get_current_user, get_optional_current_user
from app.core.config import get_settings
from app.core.db import get_session
from app.models.growth_club import (
    GrowthClubComment,
    GrowthClubPost,
    GrowthClubPostLike,
    GrowthClubPostRead,
)
from app.models.user import AuthenticatedUser

router = APIRouter()

UPLOAD_DIR = get_settings().STORAGE_ROOT_PATH / "growth-club"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("", response_model=list[GrowthClubPostRead])
async def list_posts(
    category: str = "all",
    search: Optional[str] = None,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_session)
):

    """게시글 목록 조회 (검색 및 카테고리 필터링 포함)"""
    query = (
        select(GrowthClubPost)
        .where(GrowthClubPost.is_blinded.is_(False))
        .options(
            selectinload(GrowthClubPost.author),
            selectinload(GrowthClubPost.comments).selectinload(GrowthClubComment.author),
            selectinload(GrowthClubPost.likes)
        )
    )

    if category != "all":
        query = query.where(GrowthClubPost.category == category)
    if search:
        query = query.where(
            (GrowthClubPost.title.contains(search))
            | (GrowthClubPost.content.contains(search))
        )
    
    query = query.order_by(GrowthClubPost.created_at.desc())
    result = await session.execute(query)
    posts = result.scalars().all()
    
    # 가공하여 반환
    read_posts: list[GrowthClubPostRead] = []
    for post in posts:
        post_read = GrowthClubPostRead.model_validate(post)
        post_read.likes_count = len(post.likes)
        if current_user:
            post_read.is_liked = any(like.user_id == current_user.id for like in post.likes)
        read_posts.append(post_read)
        
    return read_posts

@router.post("", response_model=GrowthClubPostRead)
async def create_post(
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form("free"),
    image: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """새 게시글 작성"""
    image_url: Optional[str] = None
    if image:
        file_extension = os.path.splitext(image.filename or "")[1]
        file_name = f"{int(time.time())}_img{file_extension}"
        file_path = UPLOAD_DIR / file_name
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = f"growth-club/{file_name}"

    other_file_url: Optional[str] = None
    if file:
        file_extension = os.path.splitext(file.filename or "")[1]
        file_name = f"{int(time.time())}_file{file_extension}"
        file_path = UPLOAD_DIR / file_name
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        other_file_url = f"growth-club/{file_name}"

    db_post = GrowthClubPost(
        title=title,
        content=content,
        category=category,
        author_id=current_user.id,
        neighborhood=getattr(current_user, 'neighborhood', '미지정'),
        industry=getattr(current_user, 'industry', '기타'),
        image_path=image_url,
        file_path=other_file_url
    )
    session.add(db_post)
    await session.flush()
    post_id = db_post.id
    await session.commit()

    
    # Refresh with relationships to satisfy response model.
    query = (
        select(GrowthClubPost)
        .where(GrowthClubPost.id == post_id)
        .options(
            selectinload(GrowthClubPost.author),
            selectinload(GrowthClubPost.comments),
            selectinload(GrowthClubPost.likes)
        )
    )
    result = await session.execute(query)
    post = result.scalar_one()
    
    post_read = GrowthClubPostRead.model_validate(post)
    post_read.likes_count = len(post.likes)
    post_read.is_liked = any(like.user_id == current_user.id for like in post.likes)
    return post_read

@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """게시글 삭제 (작성자 본인만 가능)"""
    from app.core.logging import get_logger

    logger = get_logger("app.api.growth_club.posts")

    db_post = await session.get(GrowthClubPost, post_id)
    if not db_post:
        logger.warning(f"Delete attempt for non-existent post: {post_id}")
        raise HTTPException(status_code=404, detail="Post not found")

    if db_post.author_id != current_user.id and not current_user.is_superuser:
        logger.warning(f"Unauthorized delete attempt: post_id={post_id}, user_id={current_user.id}")
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")

    logger.info(f"Deleting post: {post_id} by user: {current_user.id}")
    await session.delete(db_post)
    await session.commit()
    return {"status": "success", "message": "Post deleted successfully"}

@router.post("/{post_id}/report")
async def report_post(
    post_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """게시글 신고 (5회 이상 신고 시 자동 블라인드)"""
    db_post = await session.get(GrowthClubPost, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    # 신고 횟수 증가
    db_post.report_count += 1

    # 5회 이상 신고 시 블라인드 처리
    if db_post.report_count >= 5:
        db_post.is_blinded = True
        message = "게시글이 누적 신고로 인해 블라인드 처리되었습니다."
    else:
        message = "게시글이 신고되었습니다."

    session.add(db_post)
    await session.commit()

    return {
        "status": "success",
        "message": message,
        "report_count": db_post.report_count,
        "is_blinded": db_post.is_blinded
    }


@router.post("/{post_id}/like")
async def toggle_like_post(
    post_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """게시글 좋아요 토글"""
    db_post = await session.get(GrowthClubPost, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    query = select(GrowthClubPostLike).where(
        GrowthClubPostLike.post_id == post_id,
        GrowthClubPostLike.user_id == current_user.id
    )
    result = await session.execute(query)
    like = result.scalar_one_or_none()

    if like:
        await session.delete(like)
        liked = False
    else:
        new_like = GrowthClubPostLike(post_id=post_id, user_id=current_user.id)
        session.add(new_like)
        liked = True

    await session.commit()

    # 최신 좋아요 수 조회
    count_query = select(func.count()).select_from(GrowthClubPostLike).where(GrowthClubPostLike.post_id == post_id)
    count_result = await session.execute(count_query)
    likes_count = count_result.scalar() or 0
    
    return {
        "status": "success",
        "liked": liked,
        "likes_count": likes_count
    }
