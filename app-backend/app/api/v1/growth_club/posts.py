from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.deps import get_current_user, get_optional_current_user
from app.core.config import get_settings
from app.core.db import get_session
from app.features.growth_club.application.post_service import GrowthClubPostService
from app.models.growth_club import (
    GrowthClubComment,
    GrowthClubPost,
    GrowthClubPostLike,
    GrowthClubPostRead,
)
from app.models.user import AuthenticatedUser

router = APIRouter()
settings = get_settings()

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
FILE_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".hwp",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".txt",
}


def _extract_extension(filename: Optional[str]) -> str:
    return Path(filename or "").suffix.lower()


async def _validate_and_read_uploads(
    *,
    kind: Literal["image", "file"],
    uploads: list[UploadFile],
    running_total_bytes: int,
) -> tuple[list[tuple[UploadFile, bytes]], int]:
    if kind == "image":
        max_count = settings.GROWTH_CLUB_MAX_IMAGE_COUNT
        max_bytes = settings.GROWTH_CLUB_MAX_IMAGE_MB * 1024 * 1024
        allowed_extensions = IMAGE_EXTENSIONS
        label = "이미지"
    else:
        max_count = settings.GROWTH_CLUB_MAX_FILE_COUNT
        max_bytes = settings.GROWTH_CLUB_MAX_FILE_MB * 1024 * 1024
        allowed_extensions = FILE_EXTENSIONS
        label = "파일"

    if len(uploads) > max_count:
        raise HTTPException(
            status_code=400,
            detail=f"{label}는 최대 {max_count}개까지 첨부할 수 있습니다.",
        )

    prepared: list[tuple[UploadFile, bytes]] = []
    total_bytes = running_total_bytes
    max_total_bytes = settings.GROWTH_CLUB_MAX_TOTAL_MB * 1024 * 1024

    for upload in uploads:
        extension = _extract_extension(upload.filename)
        if extension not in allowed_extensions:
            allowed = ", ".join(sorted(allowed_extensions))
            raise HTTPException(
                status_code=400,
                detail=f"허용되지 않은 {label} 확장자입니다: {extension or '(none)'} (허용: {allowed})",
            )

        data = await upload.read()
        size_bytes = len(data)
        if size_bytes > max_bytes:
            max_mb = settings.GROWTH_CLUB_MAX_IMAGE_MB if kind == "image" else settings.GROWTH_CLUB_MAX_FILE_MB
            raise HTTPException(
                status_code=413,
                detail=f"{label} 한 개의 최대 크기는 {max_mb}MB 입니다.",
            )

        if kind == "image":
            content_type = (upload.content_type or "").lower()
            if content_type and not content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="이미지 MIME 타입이 올바르지 않습니다.")

        total_bytes += size_bytes
        if total_bytes > max_total_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"첨부 파일 총 용량은 {settings.GROWTH_CLUB_MAX_TOTAL_MB}MB를 초과할 수 없습니다.",
            )
        prepared.append((upload, data))

    return prepared, total_bytes


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
            selectinload(GrowthClubPost.likes),
            selectinload(GrowthClubPost.attachments),
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
    images: list[UploadFile] = File(default=[]),
    files: list[UploadFile] = File(default=[]),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """새 게시글 작성"""
    image_uploads = [u for u in images if u is not None]
    file_uploads = [u for u in files if u is not None]
    prepared_images, total_bytes = await _validate_and_read_uploads(
        kind="image",
        uploads=image_uploads,
        running_total_bytes=0,
    )
    prepared_files, _ = await _validate_and_read_uploads(
        kind="file",
        uploads=file_uploads,
        running_total_bytes=total_bytes,
    )

    service = GrowthClubPostService(session)
    post_id = await service.create_post(
        current_user=current_user,
        title=title,
        content=content,
        category=category,
        prepared_images=prepared_images,
        prepared_files=prepared_files,
    )

    
    # Refresh with relationships to satisfy response model.
    query = (
        select(GrowthClubPost)
        .where(GrowthClubPost.id == post_id)
        .options(
            selectinload(GrowthClubPost.author),
            selectinload(GrowthClubPost.comments),
            selectinload(GrowthClubPost.likes),
            selectinload(GrowthClubPost.attachments),
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

    service = GrowthClubPostService(session)
    logger.info(f"Deleting post: {post_id} by user: {current_user.id}")
    try:
        await service.delete_post(post_id=post_id, current_user=current_user)
    except HTTPException as exc:
        if exc.status_code == 404:
            logger.warning(f"Delete attempt for non-existent post: {post_id}")
        elif exc.status_code == 403:
            logger.warning(f"Unauthorized delete attempt: post_id={post_id}, user_id={current_user.id}")
        raise
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
