from datetime import datetime, timezone
from typing import Optional, Any
from sqlmodel import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.announcement import OpsAnnouncement
from app.models.ops_audit_log import OpsAuditLog
from app.features.ops.application.announcements.schemas import (
    OpsAnnouncementCreate,
    OpsAnnouncementUpdate,
    OpsAnnouncementList,
    OpsAnnouncementRead
)

class AnnouncementService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_announcements(
        self, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None
    ) -> OpsAnnouncementList:
        query = select(OpsAnnouncement)
        if status:
            query = query.where(OpsAnnouncement.status == status)
        
        query = query.order_by(desc(OpsAnnouncement.created_at))
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()
        
        # Get items
        items_result = await self.session.execute(query.offset(skip).limit(limit))
        items = items_result.scalars().all()
        
        return OpsAnnouncementList(
            items=[OpsAnnouncementRead.model_validate(item) for item in items],
            total=total
        )

    async def create_announcement(
        self, 
        admin_id: int, 
        data: OpsAnnouncementCreate
    ) -> OpsAnnouncement:
        announcement = OpsAnnouncement(
            **data.model_dump(),
            admin_id=admin_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        self.session.add(announcement)
        await self.session.commit()
        await self.session.refresh(announcement)
        
        # Audit Log
        await self._record_audit_log(
            admin_id=admin_id,
            action="ANNOUNCEMENT_CREATED",
            target_id=str(announcement.id),
            description=f"Created announcement: {announcement.title}",
            extra_data={"title": announcement.title}
        )
        
        return announcement

    async def update_announcement(
        self, 
        admin_id: int, 
        announcement_id: int, 
        data: OpsAnnouncementUpdate
    ) -> OpsAnnouncement:
        result = await self.session.execute(
            select(OpsAnnouncement).where(OpsAnnouncement.id == announcement_id)
        )
        announcement = result.scalar_one_or_none()
        if not announcement:
            raise ValueError("Announcement not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(announcement, key, value)
        
        # Handle status logic for published_at
        old_status = announcement.status
        if update_data.get("status") == "published" and old_status != "published":
            announcement.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
        
        announcement.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.session.add(announcement)
        await self.session.commit()
        await self.session.refresh(announcement)
        
        # Audit Log
        action = "ANNOUNCEMENT_UPDATED"
        if update_data.get("status") == "published":
            action = "ANNOUNCEMENT_PUBLISHED"
        elif update_data.get("status") == "draft" and old_status == "published":
            action = "ANNOUNCEMENT_UNPUBLISHED"
        elif update_data.get("status") == "archived":
            action = "ANNOUNCEMENT_ARCHIVED"
            
        await self._record_audit_log(
            admin_id=admin_id,
            action=action,
            target_id=str(announcement.id),
            description=f"Updated announcement {announcement_id}",
            extra_data=update_data
        )
        
        return announcement

    async def delete_announcement(self, admin_id: int, announcement_id: int) -> None:
        result = await self.session.execute(
            select(OpsAnnouncement).where(OpsAnnouncement.id == announcement_id)
        )
        announcement = result.scalar_one_or_none()
        if not announcement:
            raise ValueError("Announcement not found")
        
        title = announcement.title
        await self.session.delete(announcement)
        await self.session.commit()
        
        # Audit Log
        await self._record_audit_log(
            admin_id=admin_id,
            action="ANNOUNCEMENT_DELETED",
            target_id=str(announcement_id),
            description=f"Deleted announcement: {title}",
            extra_data={"title": title}
        )

    async def _record_audit_log(
        self, 
        admin_id: int, 
        action: str, 
        target_id: str, 
        description: str,
        extra_data: Optional[dict[str, Any]] = None
    ) -> None:
        audit_log = OpsAuditLog(
            admin_id=admin_id,
            action=action,
            target_type="announcement",
            target_id=target_id,
            description=description,
            extra_data=extra_data,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        self.session.add(audit_log)
        await self.session.commit()
