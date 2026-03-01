from fastapi import APIRouter

from app.api.v1.actionkit.router import router as actionkit_router
from app.api.v1.announcements import router as user_announcements_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.growth_club.router import router as growth_club_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.ops import router as ops_router
from app.api.v1.profile import router as profile_router
from app.api.v1.rag import router as rag_router
from app.api.v1.roadmaps import router as roadmaps_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(rag_router, prefix="/rag", tags=["rag"])
api_router.include_router(roadmaps_router, prefix="/roadmaps", tags=["roadmaps"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])
api_router.include_router(actionkit_router, prefix="/actionkits", tags=["actionkits"])
api_router.include_router(
    growth_club_router, prefix="/growth-club", tags=["growth-club"]
)
# Backward-compatible alias for older clients.
api_router.include_router(growth_club_router, prefix="/community", tags=["community"])
api_router.include_router(
    notifications_router, prefix="/notifications", tags=["notifications"]
)
api_router.include_router(
    user_announcements_router, prefix="/announcements", tags=["announcements"]
)
api_router.include_router(ops_router, prefix="/ops", tags=["ops"])
