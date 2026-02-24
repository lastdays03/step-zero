import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

import sys
import os

# Set up paths to import app
sys.path.append(os.getcwd())

from app.features.ops.application.announcements.service import AnnouncementService
from app.features.ops.application.announcements.schemas import OpsAnnouncementCreate, OpsAnnouncementUpdate
from app.models.announcement import OpsAnnouncement
from app.models.ops_audit_log import OpsAuditLog

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@stepzero-db:5432/stepzero_db"

async def verify():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        service = AnnouncementService(session)
        admin_id = 1 # Assuming admin with id 1 exists
        
        print("--- Testing Announcement Creation ---")
        create_data = OpsAnnouncementCreate(
            title="Test Announcement",
            content="This is a test content",
            status="draft"
        )
        announcement = await service.create_announcement(admin_id=admin_id, data=create_data)
        print(f"Created Announcement ID: {announcement.id}")
        assert announcement.title == "Test Announcement"
        
        # Verify Audit Log
        audit_res = await session.execute(select(OpsAuditLog).where(OpsAuditLog.target_id == str(announcement.id)))
        audit_log = audit_res.scalars().first()
        print(f"Audit Log Found: {audit_log.action}")
        assert audit_log.action == "ANNOUNCEMENT_CREATED"
        
        print("\n--- Testing Announcement Update & Publish ---")
        update_data = OpsAnnouncementUpdate(
            title="Updated Title",
            status="published"
        )
        updated = await service.update_announcement(
            admin_id=admin_id, 
            announcement_id=announcement.id, 
            data=update_data
        )
        print(f"Updated Status: {updated.status}")
        assert updated.title == "Updated Title"
        assert updated.status == "published"
        assert updated.published_at is not None
        
        # Verify Publish Audit Log
        audit_res = await session.execute(
            select(OpsAuditLog)
            .where(OpsAuditLog.target_id == str(announcement.id))
            .where(OpsAuditLog.action == "ANNOUNCEMENT_PUBLISHED")
        )
        audit_log = audit_res.scalars().first()
        print(f"Publish Audit Log Found: {audit_log.action}")
        assert audit_log is not None
        
        print("\n--- Testing List Announcements ---")
        list_res = await service.list_announcements()
        print(f"Total Announcements: {list_res.total}")
        assert list_res.total >= 1
        
        print("\n--- Testing Delete Announcement ---")
        await service.delete_announcement(admin_id=admin_id, announcement_id=announcement.id)
        
        # Verify deletion
        res = await session.execute(select(OpsAnnouncement).where(OpsAnnouncement.id == announcement.id))
        deleted = res.scalar_one_or_none()
        assert deleted is None
        print("Announcement successfully deleted")
        
        # Verify Delete Audit Log
        audit_res = await session.execute(
            select(OpsAuditLog)
            .where(OpsAuditLog.target_id == str(announcement.id))
            .where(OpsAuditLog.action == "ANNOUNCEMENT_DELETED")
        )
        audit_log = audit_res.scalars().first()
        print(f"Delete Audit Log Found: {audit_log.action}")
        assert audit_log is not None

    print("\nVerification Successful!")

if __name__ == "__main__":
    asyncio.run(verify())
