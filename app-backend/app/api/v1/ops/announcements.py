from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.db import get_session
from app.core.exceptions import AnnouncementNotFoundError
from app.features.ops.application.announcements import (
    AnnouncementCreate,
    AnnouncementItem,
    AnnouncementList,
    AnnouncementStatus,
    AnnouncementStatusUpdate,
    AnnouncementUpdate,
    create_announcement,
    list_announcements,
    update_announcement,
    update_announcement_status,
)
from app.features.ops.application.audit_logs import (
    AuditAction,
    AuditTargetType,
    record_admin_audit_log,
)
from app.models.user import AuthenticatedUser

router = APIRouter(prefix="/announcements")


class AnnouncementStatusUpdate(BaseModel):
    status: AnnouncementStatus
    audit_log_reason: str | None = Field(default=None, description="상태 변경 사유")


@router.get(
    "",
    summary="운영 공지 목록 조회",
    description="운영 공지 작성/수정/게시 관리를 위한 목록을 조회합니다.",
    response_description="운영 공지 목록을 반환합니다.",
)
async def get_announcements(
    session: AsyncSession = Depends(get_session),
) -> AnnouncementList:
    return await list_announcements(session)


@router.post(
    "",
    response_model=AnnouncementItem,
    summary="운영 공지 생성",
    description="운영 공지를 draft 상태로 생성하고 감사로그를 남깁니다.",
    response_description="생성된 운영 공지를 반환합니다.",
)
async def create_ops_announcement(
    payload: AnnouncementCreate,
    session: AsyncSession = Depends(get_session),
    admin_user: AuthenticatedUser = Depends(deps.get_current_user),
) -> AnnouncementItem:
    row = await create_announcement(
        session,
        title=payload.title,
        content=payload.content,
        actor_id=admin_user.id,
    )
    await record_admin_audit_log(
        session,
        admin_id=admin_user.id,
        action=AuditAction.ANNOUNCEMENT_CREATED,
        target_type=AuditTargetType.ANNOUNCEMENT,
        target_id=str(row.id),
        meta={"after": {"title": row.title, "status": row.status}},
    )
    await session.commit()
    return AnnouncementItem.model_validate(row, from_attributes=True)


@router.patch(
    "/{announcement_id}",
    response_model=AnnouncementItem,
    summary="운영 공지 수정",
    description="운영 공지 제목/내용을 수정하고 감사로그를 남깁니다.",
    response_description="수정된 운영 공지를 반환합니다.",
)
async def update_ops_announcement(
    payload: AnnouncementUpdate,
    announcement_id: int = Path(description="수정할 공지 ID"),
    session: AsyncSession = Depends(get_session),
    admin_user: AuthenticatedUser = Depends(deps.get_current_user),
) -> AnnouncementItem:
    row = await update_announcement(
        session,
        announcement_id=announcement_id,
        title=payload.title,
        content=payload.content,
        actor_id=admin_user.id,
    )
    if not row:
        raise AnnouncementNotFoundError()

    await record_admin_audit_log(
        session,
        admin_id=admin_user.id,
        action=AuditAction.ANNOUNCEMENT_UPDATED,
        target_type=AuditTargetType.ANNOUNCEMENT,
        target_id=str(row.id),
        meta={
            "after": {"title": row.title, "status": row.status},
        },
    )
    await session.commit()
    return AnnouncementItem.model_validate(row, from_attributes=True)


@router.patch(
    "/{announcement_id}/status",
    response_model=AnnouncementItem,
    summary="운영 공지 상태 변경",
    description="운영 공지 상태(draft/published/archived)를 변경하고 감사로그를 남깁니다.",
    response_description="상태 변경된 운영 공지를 반환합니다.",
)
async def update_ops_announcement_status(
    payload: AnnouncementStatusUpdate,
    announcement_id: int = Path(description="상태를 변경할 공지 ID"),
    session: AsyncSession = Depends(get_session),
    admin_user: AuthenticatedUser = Depends(deps.get_current_user),
) -> AnnouncementItem:
    status = payload.status
    row = await update_announcement_status(
        session,
        announcement_id=announcement_id,
        status=payload.status,
        actor_id=admin_user.id,
    )
    if not row:
        raise AnnouncementNotFoundError()

    action_code = {
        "draft": AuditAction.ANNOUNCEMENT_DRAFTED,
        "published": AuditAction.ANNOUNCEMENT_PUBLISHED,
        "archived": AuditAction.ANNOUNCEMENT_ARCHIVED,
    }[payload.status]
    await record_admin_audit_log(
        session,
        admin_id=admin_user.id,
        action=action_code,
        target_type=AuditTargetType.ANNOUNCEMENT,
        target_id=str(row.id),
        reason=payload.audit_log_reason,
        meta={"after": {"status": row.status}},
    )

    await session.commit()
    return AnnouncementItem.model_validate(row, from_attributes=True)
