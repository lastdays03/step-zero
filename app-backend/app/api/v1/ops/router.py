from fastapi import APIRouter, Depends

from app.api import deps
from app.api.v1.ops import reports, users

router = APIRouter(
    dependencies=[Depends(deps.require_platform_admin)],
)
router.include_router(reports.router)
router.include_router(users.router)
