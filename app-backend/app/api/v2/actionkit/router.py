from fastapi import APIRouter

from app.api.v2.actionkit import detail, listing

router = APIRouter()
router.include_router(listing.router)
router.include_router(detail.router)
