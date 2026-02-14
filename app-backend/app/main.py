
from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.api.problem import (
    http_exception_to_problem,
    problem_response,
    validation_exception_to_problem,
)
from app.core import config
from app.core.logging import setup_logging, get_logger
from app.services.rag.deps import get_rag_service

# 로깅 설정 초기화
setup_logging()
logger = get_logger("app.main")

settings = config.get_settings()
V1_SUNSET = "Tue, 30 Jun 2026 00:00:00 GMT"


def get_v2_successor(path: str) -> str:
    if path.startswith("/api/v1/auth"):
        return path.replace("/api/v1/auth", "/api/v2/auth", 1)
    if path.startswith("/api/v1/dashboard"):
        return path.replace("/api/v1/dashboard", "/api/v2/dashboard", 1)
    if path.startswith("/api/v1/generate"):
        return path.replace("/api/v1/generate", "/api/v2/roadmaps", 1)
    if path.startswith("/api/v1/rag"):
        return path.replace("/api/v1/rag", "/api/v2/rag", 1)
    return path.replace("/api/v1", "/api/v2", 1)

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
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. 로깅 미들웨어 추가
@app.middleware("http")
async def log_request_response(request: Request, call_next):
    start_time = time.time()
    
    # 요청 정보 로깅
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)

    if request.url.path.startswith("/api/v1"):
        successor = get_v2_successor(request.url.path)
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = V1_SUNSET
        response.headers["Link"] = f'<{successor}>; rel="successor-version"'
        response.headers["Warning"] = (
            f'299 stepzero-api "Deprecated API v1. Migrate to {successor} before {V1_SUNSET}."'
        )
    
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


from app.api.v1.api import api_router as api_v1_router
from app.api.v2.api import api_router as api_v2_router

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(api_v1_router, prefix="/api/v1")
app.include_router(api_v2_router, prefix="/api/v2")
