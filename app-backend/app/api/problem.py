"""RFC 9457 (Problem Details for HTTP APIs) 에러 응답.

기존 RFC 7807 호환을 유지하면서 error_code, timestamp, extensions 필드를 추가한다.
"""

import json as _json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException

# ── HTTP 상태 코드 → 제목 매핑 ───────────────────────────────────────

HTTP_STATUS_TITLES: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    413: "Payload Too Large",
    422: "Unprocessable Content",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}


def _get_title(status_code: int) -> str:
    return HTTP_STATUS_TITLES.get(status_code, "HTTP Error")


# ── 공통 응답 빌더 ───────────────────────────────────────────────────

def problem_response(
    *,
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    type_uri: str = "about:blank",
    error_code: str | None = None,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
        "error_code": error_code or f"HTTP_{status_code}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if extra:
        payload.update(extra)
    return JSONResponse(
        status_code=status_code,
        content=payload,
        media_type="application/problem+json",
    )


# ── AppException → RFC 9457 ─────────────────────────────────────────

async def app_exception_to_problem(
    request: Request, exc: AppException
) -> JSONResponse:
    payload: dict[str, Any] = {
        "type": exc.type_uri,
        "title": _get_title(exc.status_code),
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": str(request.url.path),
        "error_code": exc.error_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if exc.extra:
        payload["extensions"] = exc.extra
    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
        media_type="application/problem+json",
    )


# ── HTTPException → problem+json (레거시 호환) ──────────────────────

async def http_exception_to_problem(
    request: Request, exc: HTTPException
) -> JSONResponse:
    title = _get_title(exc.status_code)
    extra = None

    if isinstance(exc.detail, str):
        detail = exc.detail
    elif isinstance(exc.detail, dict):
        detail = exc.detail.get("message", "Request failed")
        extra = exc.detail
    else:
        detail = "Request failed"

    return problem_response(
        request=request,
        status_code=exc.status_code,
        title=title,
        detail=detail,
        extra=extra,
    )


# ── RequestValidationError → problem+json ────────────────────────────

async def validation_exception_to_problem(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = _json.loads(_json.dumps(exc.errors(), default=str))
    return problem_response(
        request=request,
        status_code=422,
        title="Unprocessable Content",
        detail="Request validation failed",
        type_uri="https://stepzero.dev/problems/validation-error",
        error_code="REQUEST_VALIDATION_ERROR",
        extra={"errors": errors},
    )
