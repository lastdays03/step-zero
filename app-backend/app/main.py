
from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core import config, db
from app.core.logging import setup_logging, get_logger

# 로깅 설정 초기화
setup_logging()
logger = get_logger("app.main")

settings = config.get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up StepZero Backend...")
    await db.init_db()
    yield
    logger.info("Shutting down StepZero Backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
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
    
    # 응답 시간 및 상태 코드 로깅
    process_time = time.time() - start_time
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Elapsed: {process_time:.4f}s"
    )
    
    return response

# 2. 전역 예외 핸들러 추가
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "message": "서버 내부 오류가 발생했습니다. 관리자에게 문의하세요."
        }
    )

from app.api.v1.api import api_router

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(api_router, prefix=settings.API_V1_STR)
