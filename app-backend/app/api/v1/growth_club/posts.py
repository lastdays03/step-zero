import pathlib
from typing import Literal, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import and_, exists, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.api.deps import get_current_user, get_optional_current_user
from app.core.config import get_settings
from app.core.db import get_session
from app.features.growth_club.application.post_service import GrowthClubPostService
from app.models.growth_club import (
    GrowthClubAttachmentRead,
    GrowthClubComment,
    GrowthClubPost,
    GrowthClubPostLike,
    GrowthClubPostRead,
    GrowthClubPostReport,
)
from app.models.notification import Notification
from app.models.user import AuthenticatedUser, User
from app.repositories.file_repository import FileRepository

router = APIRouter()
settings = get_settings()


class ReportRequest(BaseModel):
    reason: str = Field(..., description="신고 사유")


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
    return pathlib.Path(filename or "").suffix.lower()


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
            max_mb = (
                settings.GROWTH_CLUB_MAX_IMAGE_MB
                if kind == "image"
                else settings.GROWTH_CLUB_MAX_FILE_MB
            )
            raise HTTPException(
                status_code=413,
                detail=f"{label} 한 개의 최대 크기는 {max_mb}MB 입니다.",
            )

        if kind == "image":
            content_type = (upload.content_type or "").lower()
            if content_type and not content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400, detail="이미지 MIME 타입이 올바르지 않습니다."
                )

        total_bytes += size_bytes
        if total_bytes > max_total_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"첨부 파일 총 용량은 {settings.GROWTH_CLUB_MAX_TOTAL_MB}MB를 초과할 수 없습니다.",
            )
        prepared.append((upload, data))

    return prepared, total_bytes


@router.get(
    "",
    response_model=list[GrowthClubPostRead],
    summary="게시글 목록 조회",
    description="카테고리/검색어 조건으로 그로스클럽 게시글 목록을 조회합니다.",
    response_description="게시글 목록을 최신순으로 반환합니다.",
)
async def list_posts(
    category: str = Query(default="all", description="카테고리 필터 (`all`이면 전체)"),
    search_type: str = Query(
        default="all", description="검색 기준 (all, title, content)"
    ),
    search: Optional[str] = Query(default=None, description="검색어"),
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_current_user),
    session: AsyncSession = Depends(get_session),
):
    """게시글 목록 조회 (검색 및 카테고리 필터링 포함)"""
    likes_count_subquery = (
        select(func.count())
        .select_from(GrowthClubPostLike)
        .where(GrowthClubPostLike.post_id == GrowthClubPost.id)
        .correlate(GrowthClubPost)
        .scalar_subquery()
    )

    is_liked_subquery = None
    if current_user:
        is_liked_subquery = exists(
            select(1).where(
                and_(
                    GrowthClubPostLike.post_id == GrowthClubPost.id,
                    GrowthClubPostLike.user_id == current_user.id,
                )
            )
        ).correlate(GrowthClubPost)

    if is_liked_subquery is not None:
        query = (
            select(
                GrowthClubPost,
                likes_count_subquery.label("likes_count"),
                is_liked_subquery.label("is_liked"),
            )
            .where(GrowthClubPost.is_blinded.is_(False))
            .options(
                selectinload(GrowthClubPost.author).selectinload(User.profile),
                selectinload(GrowthClubPost.comments)
                .selectinload(GrowthClubComment.author)
                .selectinload(User.profile),
            )
        )
    else:
        query = (
            select(
                GrowthClubPost,
                likes_count_subquery.label("likes_count"),
            )
            .where(GrowthClubPost.is_blinded.is_(False))
            .options(
                selectinload(GrowthClubPost.author).selectinload(User.profile),
                selectinload(GrowthClubPost.comments)
                .selectinload(GrowthClubComment.author)
                .selectinload(User.profile),
            )
        )

    if category != "all" and category != "hot":
        query = query.where(GrowthClubPost.category == category)
    if search:
        if search_type == "title":
            query = query.where(GrowthClubPost.title.contains(search))
        elif search_type == "content":
            query = query.where(GrowthClubPost.content.contains(search))
        else:
            query = query.where(
                (GrowthClubPost.title.contains(search))
                | (GrowthClubPost.content.contains(search))
            )

    if category == "hot":
        query = query.order_by(
            likes_count_subquery.desc(), GrowthClubPost.created_at.desc()
        )
    else:
        query = query.order_by(GrowthClubPost.created_at.desc())

    result = await session.execute(query)

    # 가공하여 반환
    read_posts: list[GrowthClubPostRead] = []
    rows = result.all()
    post_ids = [row[0].id for row in rows if row[0].id is not None]

    # File 기반 attachments 일괄 조회
    file_repo = FileRepository(session)
    attachments_map: dict[int, list[GrowthClubAttachmentRead]] = {}
    if post_ids:
        from app.models.file import File as FileModel
        from sqlmodel import select as sm_select

        att_stmt = (
            sm_select(FileModel)
            .where(
                FileModel.owner_type == "growth_club_post",
                FileModel.owner_id.in_(post_ids),
            )
            .order_by(FileModel.created_at.asc())
        )
        att_result = await session.execute(att_stmt)
        for f in att_result.scalars().all():
            attachments_map.setdefault(f.owner_id, []).append(
                GrowthClubAttachmentRead(
                    id=f.id,  # type: ignore[arg-type]
                    kind=f.kind or ("image" if f.category == "image" else "file"),
                    object_key=f.object_key,
                    original_filename=f.original_filename,
                    mime_type=f.mime_type,
                    size_bytes=f.size_bytes,
                    created_at=f.created_at,
                )
            )

    for row in rows:
        post = row[0]
        likes_count = row[1] if len(row) > 1 else 0
        is_liked = bool(row[2]) if current_user and len(row) > 2 else False

        post_read = GrowthClubPostRead.model_validate(
            post, update={"attachments": []}
        )
        post_read.likes_count = int(likes_count or 0)
        post_read.is_liked = is_liked
        post_read.attachments = attachments_map.get(post.id, [])

        # Filter blinded comments and apply privacy masking
        user_id = current_user.id if current_user else None
        post_read.author.mask_privacy(user_id)

        # Only show non-blinded comments
        post_read.comments = [
            c for c in post_read.comments if not getattr(c, "is_blinded", False)
        ]

        for comment in post_read.comments:
            comment.author.mask_privacy(user_id)

        read_posts.append(post_read)

    return read_posts


@router.post(
    "",
    response_model=GrowthClubPostRead,
    summary="게시글 생성",
    description="제목/내용/카테고리와 첨부파일로 새 게시글을 생성합니다.",
    response_description="생성된 게시글 상세를 반환합니다.",
)
async def create_post(
    title: str = Form(..., description="게시글 제목"),
    content: str = Form(..., description="게시글 본문"),
    category: str = Form("free", description="게시글 카테고리"),
    images: list[UploadFile] = File(default=[], description="첨부 이미지 목록"),
    files: list[UploadFile] = File(default=[], description="첨부 문서 파일 목록"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """새 게시글 작성"""
    if current_user.is_suspended:
        raise HTTPException(
            status_code=403, detail="이용이 정지된 사용자입니다. 접근이 제한됩니다."
        )
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
    # 새로 생성된 글이므로 likes는 항상 0건 — selectinload 불필요
    query = (
        select(GrowthClubPost)
        .where(GrowthClubPost.id == post_id)
        .options(
            selectinload(GrowthClubPost.author).selectinload(User.profile),
            selectinload(GrowthClubPost.comments)
            .selectinload(GrowthClubComment.author)
            .selectinload(User.profile),
        )
    )
    result = await session.execute(query)
    post = result.scalar_one()

    post_read = GrowthClubPostRead.model_validate(
        post, update={"attachments": []}
    )
    post_read.author.mask_privacy(current_user.id)
    post_read.likes_count = 0
    post_read.is_liked = False

    # File 기반 attachments 조회
    file_repo = FileRepository(session)
    file_records = await file_repo.get_by_owner(
        owner_type="growth_club_post", owner_id=post_id
    )
    post_read.attachments = [
        GrowthClubAttachmentRead(
            id=f.id,  # type: ignore[arg-type]
            kind=f.kind or ("image" if f.category == "image" else "file"),
            object_key=f.object_key,
            original_filename=f.original_filename,
            mime_type=f.mime_type,
            size_bytes=f.size_bytes,
            created_at=f.created_at,
        )
        for f in file_records
    ]

    return post_read


@router.delete(
    "/{post_id}",
    summary="게시글 삭제",
    description="게시글 작성자(또는 운영자)가 게시글을 삭제합니다.",
    response_description="삭제 결과를 반환합니다.",
)
async def delete_post(
    post_id: int = Path(description="삭제할 게시글 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
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
            logger.warning(
                f"Unauthorized delete attempt: post_id={post_id}, user_id={current_user.id}"
            )
        raise
    return {"status": "success", "message": "Post deleted successfully"}


@router.post(
    "/{post_id}/report",
    summary="게시글 신고",
    description="게시글을 신고합니다. 누적 5회 이상이면 자동 블라인드 처리됩니다.",
    response_description="신고 처리 결과와 누적 신고 수를 반환합니다.",
)
async def report_post(
    report_data: ReportRequest,
    post_id: int = Path(description="신고할 게시글 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """게시글 신고 (1회 이상 신고 시 자동 블라인드)"""
    if current_user.is_suspended:
        raise HTTPException(
            status_code=403, detail="이용이 정지된 사용자입니다. 접근이 제한됩니다."
        )
    db_post = await session.get(GrowthClubPost, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    if db_post.author_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="자신의 게시물은 신고할 수 없습니다."
        )

    # 기존 신고 여부 확인
    existing_report_query = select(GrowthClubPostReport).where(
        GrowthClubPostReport.post_id == post_id,
        GrowthClubPostReport.reporter_id == current_user.id,
    )
    existing_report_result = await session.execute(existing_report_query)
    if existing_report_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 신고한 게시물입니다.")

    # 신고 기록 생성
    new_report = GrowthClubPostReport(
        post_id=post_id, reporter_id=current_user.id, reason=report_data.reason
    )
    session.add(new_report)

    # 신고 횟수 증가
    db_post.report_count += 1

    # 1회 이상 신고 시 자동 블라인드 처리
    if db_post.report_count >= 1:
        db_post.is_blinded = True
        message = "게시글이 누적 신고로 인해 블라인드 처리되었습니다."

        # 블라인드 처리 시 감사 로그 기록
        author = await session.get(User, db_post.author_id)
        from app.features.ops.application.audit_logs.service import save_audit_log

        await save_audit_log(
            session=session,
            user_id=current_user.id,
            action="growth_club.post.blind",
            target_type="post",
            target_id=str(post_id),
            target_author=author.email if author else None,
            details=f"게시글 '{db_post.title[:20]}...' 누적 신고로 블라인드 처리 (자동)",
        )
    else:
        message = "게시글이 신고되었습니다."

    session.add(db_post)
    await session.commit()

    return {
        "status": "success",
        "message": message,
        "report_count": db_post.report_count,
        "is_blinded": db_post.is_blinded,
    }


@router.post(
    "/{post_id}/like",
    summary="게시글 좋아요 토글",
    description="게시글 좋아요를 추가/해제합니다.",
    response_description="토글 결과와 최신 좋아요 수를 반환합니다.",
)
async def toggle_like_post(
    post_id: int = Path(description="좋아요를 토글할 게시글 ID"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """게시글 좋아요 토글"""
    db_post = await session.get(GrowthClubPost, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    query = select(GrowthClubPostLike).where(
        GrowthClubPostLike.post_id == post_id,
        GrowthClubPostLike.user_id == current_user.id,
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
        # Notify post author on like (not self-like)
        if db_post.author_id != current_user.id:
            like_notification = Notification(
                user_id=db_post.author_id,
                content=f"{current_user.full_name or current_user.email}님이 당신의 게시물을 좋아합니다.",
                type="like",
                link=f"/growth-club#post-{post_id}",
                resource_id=post_id,
            )
            session.add(like_notification)

    await session.commit()

    # SSE push for like notification
    if liked and db_post.author_id != current_user.id:
        from app.services.notification_pubsub import publish_notification
        await publish_notification(db_post.author_id, {"type": "new_notification"})

    # 최신 좋아요 수 조회
    count_query = (
        select(func.count())
        .select_from(GrowthClubPostLike)
        .where(GrowthClubPostLike.post_id == post_id)
    )
    count_result = await session.execute(count_query)
    likes_count = count_result.scalar() or 0

    return {"status": "success", "liked": liked, "likes_count": likes_count}
