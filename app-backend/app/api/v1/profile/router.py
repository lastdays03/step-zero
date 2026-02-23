from fastapi import APIRouter

from app.api.v1.profile import me

router = APIRouter()
router.include_router(me.router)
