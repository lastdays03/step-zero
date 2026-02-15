from fastapi import APIRouter

from app.api.v2.community import feed, posts

router = APIRouter()
router.include_router(feed.router)
router.include_router(posts.router)
