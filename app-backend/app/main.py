
from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.api.problem import (
    http_exception_to_problem,
    problem_response,
    validation_exception_to_problem,
)
from app.core import config
from app.core.logging import setup_logging, get_logger
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
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
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
    logger.info(f"Request: {request.method} {request.url.path}")
    
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
actionkit_storage_dir = settings.ACTIONKIT_STORAGE_PATH
actionkit_storage_dir.mkdir(parents=True, exist_ok=True)
logger.info("ActionKit storage mounted at: %s", actionkit_storage_dir)
app.mount(
    "/api/v1/actionkits/files",
    StaticFiles(directory=str(actionkit_storage_dir)),
    name="actionkit-files",
)

from app.api.v1.api import api_router as api_v1_router

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(api_v1_router, prefix="/api/v1")
