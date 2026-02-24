from datetime import datetime
from pydantic import BaseModel

class OpsUserRead(BaseModel):
    id: int
    email: str
    full_name: str | None
    status: str
    report_count: int
    last_login_at: datetime | None
    is_active: bool
    is_superuser: bool
    created_at: datetime

class DisciplineHistoryRead(BaseModel):
    id: int
    user_id: int
    admin_id: int
    prev_status: str
    new_status: str
    reason: str
    suspended_until: datetime | None = None
    created_at: datetime
