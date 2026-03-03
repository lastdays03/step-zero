from app.api.v1.roadmaps.chat import router as chat_router
from app.api.v1.roadmaps.create import router
from app.api.v1.roadmaps.get import router as get_router
from app.api.v1.roadmaps.jobs import router as jobs_router

router.include_router(get_router)
router.include_router(jobs_router)
router.include_router(chat_router)
