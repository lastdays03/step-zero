from fastapi import APIRouter, Depends

from app.api import deps
from app.api.v1.ops import (
    actionkit,
    announcements,
    audit_logs,
    growth_club,
    home,
    reports,
    roadmap_templates,
    users,
)

router = APIRouter(
    dependencies=[Depends(deps.require_platform_admin)],
)
router.include_router(home.router)
router.include_router(reports.router)
router.include_router(users.router)
router.include_router(growth_club.router)
router.include_router(actionkit.router)
router.include_router(announcements.router)
router.include_router(roadmap_templates.router)
router.include_router(audit_logs.router)
