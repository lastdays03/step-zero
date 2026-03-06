import uuid
from datetime import datetime

from app.core.security import utc_now
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import get_settings
from app.models.file import File
from app.models.profile import UserProfile, UserProfileUpdate
from app.models.roadmap import Roadmap
from app.models.user import User
from app.repositories.file_repository import FileRepository


class ProfileService:
    def __init__(self, session: AsyncSession):
        self.session = session
        settings = get_settings()
        self.upload_dir = settings.STORAGE_ROOT_PATH / "profile"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def get_profile(self, user_id: int) -> UserProfile:
        statement = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.session.execute(statement)
        profile = result.scalar_one_or_none()

        if not profile:
            # Create a default profile if it doesn't exist
            profile = UserProfile(user_id=user_id)
            self.session.add(profile)
            await self.session.commit()
            await self.session.refresh(profile)

        # UX Data Binding: 대시보드에서 입력한 업종/지역 정보 연동
        if not profile.category or not profile.region:
            roadmap_stmt = (
                select(Roadmap)
                .where(Roadmap.created_by == user_id)
                .where(Roadmap.deleted_at.is_(None))
                .order_by(desc(Roadmap.created_at))
                .limit(1)
            )
            roadmap_result = await self.session.execute(roadmap_stmt)
            latest_roadmap = roadmap_result.scalar_one_or_none()

            if latest_roadmap:
                if not profile.category and latest_roadmap.business_type:
                    profile.category = latest_roadmap.business_type
                if not profile.region and latest_roadmap.location:
                    profile.region = latest_roadmap.location

        return profile

    async def update_profile(
        self, user_id: int, profile_update: UserProfileUpdate
    ) -> UserProfile:
        profile = await self.get_profile(user_id)

        update_data = profile_update.model_dump(exclude_unset=True)

        # full_name은 User 모델에 있으므로 따로 처리함
        if "full_name" in update_data:
            full_name = update_data.pop("full_name")
            user_stmt = select(User).where(User.id == user_id)
            user_result = await self.session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            if user:
                user.full_name = full_name
                self.session.add(user)

        for key, value in update_data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = utc_now()
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def save_profile_image(self, user_id: int, file: UploadFile) -> str:
        profile = await self.get_profile(user_id)

        # Generate unique filename
        ext = Path(file.filename or "").suffix or ".png"
        filename = f"{uuid.uuid4()}{ext}"
        filepath = self.upload_dir / filename

        # Save file
        with open(filepath, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Update profile
        profile.profile_img = f"profile/{filename}"
        profile.updated_at = utc_now()
        self.session.add(profile)

        # Dual-write: File 레코드 생성 (같은 트랜잭션)
        file_repo = FileRepository(self.session)
        await file_repo.delete_by_owner(owner_type="user_profile", owner_id=user_id)
        file_record = File(
            owner_type="user_profile",
            owner_id=user_id,
            category="profile_image",
            object_key=f"profile/{filename}",
            original_filename=file.filename,
            mime_type=file.content_type,
            size_bytes=len(content),
        )
        await file_repo.create(file=file_record)

        await self.session.commit()
        await self.session.refresh(profile)

        return filename

    async def calculate_completeness(self, user: User, profile: UserProfile) -> int:
        # 1. Core fields (4 fields)
        core_fields = [
            user.full_name,
            profile.category,
            profile.region,
            profile.philosophy,
        ]
        filled = sum(1 for f in core_fields if f and str(f).strip())

        # 2. List fields (3 items)
        if profile.experiences:
            filled += 1
        if profile.awards:
            filled += 1
        if profile.certificates:
            filled += 1

        # Total 7 metrics
        rate = int((filled / 7) * 100)
        return rate

    def get_formatted_updated_at(self, profile: UserProfile) -> str:
        # User requested YYYY-MM-DD-HH:MM
        # We use local time for the display value as per project context (Korean timezone usually)
        # But for now let's just format the UTC to the requested string
        return profile.updated_at.strftime("%Y-%m-%d-%H:%M")
