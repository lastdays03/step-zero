import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.config import get_settings
from app.models.growth_club import GrowthClubPost, GrowthClubPostAttachment
from app.models.profile import UserProfile
from app.models.user import AuthenticatedUser

settings = get_settings()


def _as_non_empty(value: Optional[str], fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _generate_upload_name(kind: str, filename: Optional[str]) -> str:
    extension = os.path.splitext(filename or "")[1]
    if not extension:
        extension = ".bin"
    return f"{uuid.uuid4().hex}_{kind}{extension.lower()}"


def _build_upload_path(kind: str, filename: Optional[str]) -> tuple[Path, str]:
    now = datetime.utcnow()
    relative_dir = Path("growth-club") / kind / f"{now.year}" / f"{now.month:02d}"
    generated_name = _generate_upload_name(kind, filename)
    relative_path = relative_dir / generated_name
    absolute_path = settings.STORAGE_ROOT_PATH / relative_path
    return absolute_path, relative_path.as_posix()


def _remove_saved_files(object_keys: list[str]) -> None:
    for object_key in object_keys:
        if not object_key:
            continue
        target = settings.STORAGE_ROOT_PATH / object_key
        try:
            if target.exists():
                target.unlink()
        except OSError:
            continue


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
    ) -> int:
        attachment_rows: list[GrowthClubPostAttachment] = []
        saved_object_keys: list[str] = []

        try:
            for upload, data in prepared_images:
                file_path, object_key = _build_upload_path("image", upload.filename)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(data)
                saved_object_keys.append(object_key)
                attachment_rows.append(
                    GrowthClubPostAttachment(
                        kind="image",
                        object_key=object_key,
                        original_filename=upload.filename,
                        mime_type=upload.content_type,
                        size_bytes=len(data),
                    )
                )

            for upload, data in prepared_files:
                file_path, object_key = _build_upload_path("file", upload.filename)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_bytes(data)
                saved_object_keys.append(object_key)
                attachment_rows.append(
                    GrowthClubPostAttachment(
                        kind="file",
                        object_key=object_key,
                        original_filename=upload.filename,
                        mime_type=upload.content_type,
                        size_bytes=len(data),
                    )
                )

            profile_stmt = select(UserProfile).where(UserProfile.user_id == current_user.id)
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
            db_post.attachments = attachment_rows
            self.session.add(db_post)
            await self.session.flush()
            post_id = db_post.id
            await self.session.commit()
            return int(post_id)
        except Exception:
            await self.session.rollback()
            _remove_saved_files(saved_object_keys)
            raise

    async def delete_post(self, *, post_id: int, current_user: AuthenticatedUser) -> None:
        query = (
            select(GrowthClubPost)
            .where(GrowthClubPost.id == post_id)
            .options(selectinload(GrowthClubPost.attachments))
        )
        result = await self.session.execute(query)
        db_post = result.scalar_one_or_none()
        if not db_post:
            raise HTTPException(status_code=404, detail="Post not found")

        if db_post.author_id != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized to delete this post")

        attachment_keys = [attachment.object_key for attachment in db_post.attachments]
        await self.session.delete(db_post)
        await self.session.commit()
        _remove_saved_files(attachment_keys)
