
from fastapi import APIRouter
from app.api.v1 import auth, dashboard, generation, rag

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(generation.router, prefix="/generate", tags=["generation"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
