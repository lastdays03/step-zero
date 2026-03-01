from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def problem_response(
    *,
    request: Request,
    status_code: int,
    title: str,
    detail: str,
    type_uri: str = "about:blank",
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": str(request.url.path),
    }
    if extra:
        payload.update(extra)
    return JSONResponse(
        status_code=status_code, content=payload, media_type="application/problem+json"
    )


async def http_exception_to_problem(
    request: Request, exc: HTTPException
) -> JSONResponse:
    title = "HTTP Error"
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


async def validation_exception_to_problem(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return problem_response(
        request=request,
        status_code=422,
        title="Validation Error",
        detail="Request validation failed",
        type_uri="https://stepzero.dev/problems/validation-error",
        extra={"errors": exc.errors()},
    )
