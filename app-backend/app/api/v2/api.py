from fastapi import APIRouter

from app.api.v2 import auth, dashboard, rag, roadmaps

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth-v2"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard-v2"])
api_router.include_router(roadmaps.router, prefix="/roadmaps", tags=["roadmaps-v2"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag-v2"])
