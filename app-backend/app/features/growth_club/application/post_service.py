import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.logging import get_logger
from app.models.file import File
from app.repositories.file_repository import FileRepository
from app.models.growth_club import (
    GrowthClubPost,
    GrowthClubTag,
)
from app.models.profile import UserProfile
from app.models.user import AuthenticatedUser
from app.services.storage import get_storage_backend

logger = get_logger(__name__)


def _as_non_empty(value: Optional[str], fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _generate_upload_name(kind: str, filename: Optional[str]) -> str:
    extension = os.path.splitext(filename or "")[1]
    if not extension:
        extension = ".bin"
    return f"{uuid.uuid4().hex}_{kind}{extension.lower()}"


def _build_object_key(kind: str, filename: Optional[str]) -> str:
    now = datetime.now(timezone.utc)
    generated_name = _generate_upload_name(kind, filename)
    return f"growth-club/{kind}/{now.year}/{now.month:02d}/{generated_name}"


async def _remove_saved_files(object_keys: list[str]) -> None:
    storage = get_storage_backend()
    for object_key in object_keys:
        if not object_key:
            continue
        try:
            await storage.delete(object_key)
        except Exception as e:
            logger.error(
                f"Failed to remove saved file: object_key={object_key}, error={e}"
            )


class GrowthClubPostService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_post(
        self,
        *,
        current_user: AuthenticatedUser,
        title: str,
        content: str,
        category: str,
        prepared_images: list[tuple[UploadFile, bytes]],
        prepared_files: list[tuple[UploadFile, bytes]],
        tags: list[str] = [],
    ) -> int:
        saved_object_keys: list[str] = []
        file_records: list[dict] = []

        try:
            storage = get_storage_backend()

            for upload, data in prepared_images:
                object_key = _build_object_key("image", upload.filename)
                await storage.put(
                    object_key, data, content_type=upload.content_type or "image/png"
                )
                saved_object_keys.append(object_key)
                file_records.append(
                    dict(
                        kind="image",
                        object_key=object_key,
                        original_filename=upload.filename,
                        mime_type=upload.content_type,
                        size_bytes=len(data),
                    )
                )

            for upload, data in prepared_files:
                object_key = _build_object_key("file", upload.filename)
                await storage.put(
                    object_key,
                    data,
                    content_type=upload.content_type or "application/octet-stream",
                )
                saved_object_keys.append(object_key)
                file_records.append(
                    dict(
                        kind="file",
                        object_key=object_key,
                        original_filename=upload.filename,
                        mime_type=upload.content_type,
                        size_bytes=len(data),
                    )
                )

            profile_stmt = select(UserProfile).where(
                UserProfile.user_id == current_user.id
            )
            profile_result = await self.session.execute(profile_stmt)
            profile = profile_result.scalar_one_or_none()
            neighborhood = _as_non_empty(profile.region if profile else None, "미지정")
            industry = _as_non_empty(profile.category if profile else None, "기타")

            db_post = GrowthClubPost(
                title=title,
                content=content,
                category=category,
                author_id=current_user.id,
                neighborhood=neighborhood,
                industry=industry,
            )

            # 태그 처리
            if tags:
                tag_rows = []
                for tag_name in tags:
                    tag_name = tag_name.strip()
                    if not tag_name:
                        continue
                    tag_stmt = select(GrowthClubTag).where(
                        GrowthClubTag.name == tag_name
                    )
                    tag_result = await self.session.execute(tag_stmt)
                    tag_obj = tag_result.scalar_one_or_none()
                    if not tag_obj:
                        tag_obj = GrowthClubTag(name=tag_name)
                        self.session.add(tag_obj)
                    tag_rows.append(tag_obj)
                db_post.tags = tag_rows

            self.session.add(db_post)
            await self.session.flush()
            post_id = db_post.id

            file_repo = FileRepository(self.session)
            for rec in file_records:
                file_obj = File(
                    owner_type="growth_club_post",
                    owner_id=int(post_id),
                    category="image" if rec["kind"] == "image" else "document",
                    object_key=rec["object_key"],
                    original_filename=rec["original_filename"],
                    mime_type=rec["mime_type"],
                    size_bytes=rec["size_bytes"],
                    kind=rec["kind"],
                )
                await file_repo.create(file=file_obj)

            await self.session.commit()
            return int(post_id)
        except Exception:
            await self.session.rollback()
            await _remove_saved_files(saved_object_keys)
            raise

    async def delete_post(
        self, *, post_id: int, current_user: AuthenticatedUser
    ) -> None:
        query = select(GrowthClubPost).where(GrowthClubPost.id == post_id)
        result = await self.session.execute(query)
        db_post = result.scalar_one_or_none()
        if not db_post:
            raise HTTPException(status_code=404, detail="Post not found")

        if db_post.author_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this post"
            )

        file_repo = FileRepository(self.session)
        file_records = await file_repo.get_by_owner(
            owner_type="growth_club_post", owner_id=post_id
        )
        attachment_keys = [f.object_key for f in file_records]
        await file_repo.delete_by_owner(owner_type="growth_club_post", owner_id=post_id)
        await self.session.delete(db_post)
        await self.session.commit()
        try:
            await _remove_saved_files(attachment_keys)
        except Exception as e:
            logger.error(
                f"Failed to remove attachment files after post delete: post_id={post_id}, error={e}"
            )
