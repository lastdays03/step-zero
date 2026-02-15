from fastapi import APIRouter

from app.api.v2.actionkit import router as actionkit_router
from app.api.v2.community import router as community_router
from app.api.v2.dashboard.stats import router as dashboard_router
from app.api.v2.ops import router as ops_router
from app.api.v2.profile import router as profile_router
from app.api.v2.rag import router as rag_router
from app.api.v2.roadmaps.create import router as roadmaps_create_router
from app.api.v2.roadmaps.get import router as roadmaps_get_router
from app.api.v2.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth-v2"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard-v2"])
api_router.include_router(roadmaps_create_router, prefix="/roadmaps", tags=["roadmaps-v2"])
api_router.include_router(roadmaps_get_router, prefix="/roadmaps", tags=["roadmaps-v2"])
api_router.include_router(rag_router, prefix="/rag", tags=["rag-v2"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile-v2"])
api_router.include_router(actionkit_router, prefix="/actionkits", tags=["actionkits-v2"])
api_router.include_router(community_router, prefix="/community", tags=["community-v2"])
api_router.include_router(ops_router, prefix="/ops", tags=["ops-v2"])
