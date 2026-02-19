from app.api.v1.roadmaps.create import router
from app.api.v1.roadmaps.get import router as get_router

router.include_router(get_router)
