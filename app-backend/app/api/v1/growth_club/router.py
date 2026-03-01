from fastapi import APIRouter

from . import comments, posts

router = APIRouter()
router.include_router(posts.router, prefix="/posts", tags=["posts"])
router.include_router(comments.router, prefix="/comments", tags=["comments"])
