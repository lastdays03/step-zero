from fastapi import APIRouter

from app.api.v1.actionkit import detail, files, listing, tracking

router = APIRouter()
router.include_router(listing.router)
router.include_router(detail.router)
router.include_router(files.router)
router.include_router(tracking.router)
