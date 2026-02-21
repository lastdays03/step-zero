import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api import deps
from app.core.db import get_session
from app.models.profile import UserProfileRead, UserProfileUpdate
from app.models.user import AuthenticatedUser, User
from app.features.profile.application.service import ProfileService

router = APIRouter()
logger = logging.getLogger(__name__)


async def _build_profile_read(
    session: AsyncSession,
    service: ProfileService,
    current_user: AuthenticatedUser,
) -> UserProfileRead:
    profile = await service.get_profile(current_user.id)
    user_result = await session.execute(select(User).where(User.id == current_user.id))
    user = user_result.scalar_one()
    rate = await service.calculate_completeness(user, profile)
    formatted_date = service.get_formatted_updated_at(profile)
    return UserProfileRead(
        **profile.model_dump(exclude={"updated_at"}),
        full_name=user.full_name,
        email=user.email,
        updated_at=formatted_date,
        completeness_rate=rate,
    )


@router.get(
    "/me",
    response_model=UserProfileRead,
    summary="내 프로필 조회",
    description="현재 로그인한 사용자의 프로필 정보를 조회합니다.",
    response_description="프로필 상세 정보와 완성도 정보를 반환합니다.",
)
async def get_my_profile(
    current_user: Annotated[AuthenticatedUser, Depends(deps.get_current_user)],
    session: AsyncSession = Depends(get_session),
):
    logger.info("Fetching profile for user_id=%s", current_user.id)
    service = ProfileService(session)
    return await _build_profile_read(session, service, current_user)


@router.put(
    "/me",
    response_model=UserProfileRead,
    summary="내 프로필 수정",
    description="현재 로그인한 사용자의 프로필 정보를 수정합니다.",
    response_description="수정된 최신 프로필 정보를 반환합니다.",
)
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: Annotated[AuthenticatedUser, Depends(deps.get_current_user)],
    session: AsyncSession = Depends(get_session),
):
    logger.info("Updating profile for user_id=%s", current_user.id)
    service = ProfileService(session)
    await service.update_profile(current_user.id, profile_update)
    return await _build_profile_read(session, service, current_user)


@router.post(
    "/me/image",
    response_model=UserProfileRead,
    summary="프로필 이미지 업로드",
    description="현재 로그인한 사용자의 프로필 이미지를 업로드/교체합니다.",
    response_description="이미지 반영 후 최신 프로필 정보를 반환합니다.",
)
async def upload_my_profile_image(
    current_user: Annotated[AuthenticatedUser, Depends(deps.get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
    file: UploadFile = File(..., description="업로드할 프로필 이미지 파일"),
):
    service = ProfileService(session)
    await service.save_profile_image(current_user.id, file)
    return await _build_profile_read(session, service, current_user)
