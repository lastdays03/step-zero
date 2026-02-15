from fastapi import APIRouter

from app.api.v2.profile import me

router = APIRouter()
router.include_router(me.router)
