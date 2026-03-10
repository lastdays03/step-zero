"""순수 ASGI 요청 컨텍스트 미들웨어.

BaseHTTPMiddleware를 사용하지 않아 SSE 스트리밍과 호환된다.
모든 요청에 request_id를 부여하고 structlog contextvars에 바인딩한다.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import sentry_sdk
import structlog
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RequestContextMiddleware:
    """ASGI 미들웨어: request_id 생성, 로깅 컨텍스트, Sentry 태깅."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # request_id: 클라이언트 제공 헤더 우선, 없으면 자동 생성
        headers = dict(scope.get("headers", []))
        request_id = (
            headers.get(b"x-request-id", b"").decode("latin-1")
            or str(uuid.uuid4())
        )

        method = scope.get("method", "WS")
        path = scope.get("path", "/")

        # structlog contextvars 바인딩
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=method,
            path=path,
        )

        # Sentry에 request_id 태깅
        sentry_sdk.set_tag("request_id", request_id)

        logger = structlog.get_logger("app.request")
        start = time.perf_counter()

        status_code = 0

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                # 응답 헤더에 X-Request-ID 주입
                raw_headers: list[Any] = list(message.get("headers", []))
                raw_headers.append((b"x-request-id", request_id.encode("latin-1")))
                message["headers"] = raw_headers
            await send(message)

        await logger.ainfo("request_started")

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed = time.perf_counter() - start
            await logger.ainfo(
                "request_finished",
                status_code=status_code,
                elapsed=round(elapsed, 4),
            )
            structlog.contextvars.clear_contextvars()
