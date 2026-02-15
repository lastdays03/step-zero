from fastapi import APIRouter

from app.api.v2.ops import reports, users

router = APIRouter()
router.include_router(reports.router)
router.include_router(users.router)
