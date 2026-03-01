import time
from contextlib import asynccontextmanager
from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response
from starlette.types import Scope

from app.api.problem import (
    http_exception_to_problem,
    problem_response,
    validation_exception_to_problem,
)
from app.core import config
from app.core.logging import get_logger, setup_logging
from app.features.rag.application.deps import get_rag_service

# 로깅 설정 초기화
setup_logging()
logger = get_logger("app.main")

settings = config.get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up StepZero Backend...")
    # Warm the shared RAG dependency once at startup.
    get_rag_service()
    yield
    logger.info("Shutting down StepZero Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    openapi_url="/api/openapi.json",
    openapi_tags=[
        {"name": "health", "description": "서비스 상태 점검 API"},
        {"name": "auth", "description": "인증/로그인 API"},
        {"name": "dashboard", "description": "대시보드 요약 지표 API"},
        {"name": "generation", "description": "레거시 로드맵 생성 API"},
        {"name": "roadmaps", "description": "로드맵 생성/조회/진행 상태 API"},
        {"name": "profile", "description": "내 프로필 조회/수정 API"},
        {"name": "actionkits", "description": "액션키트 조회/파일 업로드 API"},
        {"name": "growth-club", "description": "그로스클럽 게시글/댓글 API"},
        {"name": "community", "description": "그로스클럽 하위호환(alias) API"},
        {"name": "ops", "description": "플랫폼 운영자 전용 API"},
        {"name": "rag", "description": "법률 가이드 RAG 질의 API"},
    ],
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve user-uploaded files from the shared storage root.
upload_dir = settings.STORAGE_ROOT_PATH
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")


# 1. 로깅 미들웨어 추가
@app.middleware("http")
async def log_request_response(request: Request, call_next):
    start_time = time.time()

    # 요청 정보 로깅
    auth_header = request.headers.get("Authorization")
    logger.info(
        f"Request: {request.method} {request.url.path} | Auth: {'Present' if auth_header else 'Missing'}"
    )

    response = await call_next(request)

    # 응답 시간 및 상태 코드 로깅
    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Elapsed: {process_time:.4f}s"
    )

    return response


# RFC7807-style error responses
app.add_exception_handler(HTTPException, http_exception_to_problem)
app.add_exception_handler(RequestValidationError, validation_exception_to_problem)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return problem_response(
        request=request,
        status_code=500,
        title="Internal Server Error",
        detail="서버 내부 오류가 발생했습니다. 관리자에게 문의하세요.",
        type_uri="https://stepzero.dev/problems/internal-error",
    )


# Static files for ActionKit
# Custom StaticFiles to handle double-encoded URLs from reverse proxy
# (e.g. Korean characters: %EC%A0%84 → %25EC%25A0%2584)
class DecodingStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        decoded = unquote(path)
        if decoded != path:
            logger.debug("StaticFiles path decoded: %s → %s", path, decoded)
        return await super().get_response(decoded, scope)


actionkit_storage_dir = settings.ACTIONKIT_STORAGE_PATH
actionkit_storage_dir.mkdir(parents=True, exist_ok=True)
logger.info("ActionKit storage mounted at: %s", actionkit_storage_dir)
app.mount(
    "/api/v1/actionkits/files",
    DecodingStaticFiles(directory=str(actionkit_storage_dir)),
    name="actionkit-files",
)

from app.api.v1.api import api_router as api_v1_router


@app.get(
    "/health",
    tags=["health"],
    summary="헬스체크",
    description="백엔드 프로세스 상태를 확인합니다.",
    response_description="정상 상태(`status=ok`)를 반환합니다.",
)
async def health_check():
    return {"status": "ok"}


app.include_router(api_v1_router, prefix="/api/v1")
