"""Sentry SDK 초기화 — GlitchTip 호환.

DSN이 빈 문자열이면 완전 비활성화되어 앱에 영향 없음.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

if TYPE_CHECKING:
    from app.core.config import Settings


def setup_sentry(settings: Settings) -> None:
    """Sentry/GlitchTip SDK를 초기화한다."""
    import logging

    dsn = settings.SENTRY_DSN.strip() if settings.SENTRY_DSN else ""
    if not dsn:
        return

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=settings.ENVIRONMENT,
            release=f"stepzero-backend@{settings.VERSION}",
            traces_sample_rate=0.2,
            before_send=_before_send,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
            ],
            send_default_pii=False,
        )
    except Exception:
        logging.getLogger(__name__).warning(
            "Sentry SDK 초기화 실패 — DSN을 확인하세요. 에러 트래킹이 비활성화됩니다.",
            exc_info=True,
        )


def _before_send(
    event: dict[str, Any], hint: dict[str, Any]
) -> dict[str, Any] | None:
    """4xx 에러는 Sentry에 전송하지 않는다."""
    from fastapi import HTTPException

    from app.core.exceptions import AppException

    exc = hint.get("exc_info")
    if exc:
        exc_value = exc[1]
        # AppException 4xx 필터
        if isinstance(exc_value, AppException) and exc_value.status_code < 500:
            return None
        # HTTPException 4xx 필터 (마이그레이션 기간)
        if isinstance(exc_value, HTTPException) and exc_value.status_code < 500:
            return None

    return event


def set_user_context(user_id: str, email: str | None = None) -> None:
    """Sentry 이벤트에 사용자 컨텍스트를 설정한다."""
    ctx: dict[str, str] = {"id": user_id}
    if email:
        ctx["email"] = email
    sentry_sdk.set_user(ctx)
