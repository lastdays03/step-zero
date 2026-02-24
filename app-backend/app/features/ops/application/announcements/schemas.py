from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class OpsAnnouncementBase(BaseModel):
    title: str
    content: str
    status: str = "draft"

class OpsAnnouncementCreate(OpsAnnouncementBase):
    pass

class OpsAnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None

class OpsAnnouncementRead(OpsAnnouncementBase):
    id: int
    admin_id: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OpsAnnouncementList(BaseModel):
    items: list[OpsAnnouncementRead]
    total: int
