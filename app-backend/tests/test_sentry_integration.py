"""Sentry/GlitchTip 통합 테스트.

setup_sentry, set_user_context, 글로벌 핸들러 capture_exception,
RequestContextMiddleware set_tag 동작을 검증한다.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.sentry import _before_send, set_user_context, setup_sentry


# ── setup_sentry 테스트 ──────────────────────────────────────────────


class TestSetupSentry:
    """DSN 유무에 따른 SDK 초기화 분기 검증."""

    def _make_settings(self, dsn: str = "", env: str = "test", version: str = "0.1.0"):
        return SimpleNamespace(
            SENTRY_DSN=dsn,
            ENVIRONMENT=env,
            VERSION=version,
        )

    @patch("app.core.sentry.sentry_sdk.init")
    def test_empty_dsn_skips_init(self, mock_init: MagicMock):
        setup_sentry(self._make_settings(dsn=""))
        mock_init.assert_not_called()

    @patch("app.core.sentry.sentry_sdk.init")
    def test_whitespace_dsn_skips_init(self, mock_init: MagicMock):
        setup_sentry(self._make_settings(dsn="   "))
        mock_init.assert_not_called()

    @patch("app.core.sentry.sentry_sdk.init")
    def test_none_dsn_skips_init(self, mock_init: MagicMock):
        settings = self._make_settings()
        settings.SENTRY_DSN = None
        setup_sentry(settings)
        mock_init.assert_not_called()

    @patch("app.core.sentry.sentry_sdk.init")
    def test_valid_dsn_calls_init(self, mock_init: MagicMock):
        setup_sentry(self._make_settings(dsn="https://key@glitchtip.example.com/1"))
        mock_init.assert_called_once()

    @patch("app.core.sentry.sentry_sdk.init")
    def test_init_params(self, mock_init: MagicMock):
        setup_sentry(
            self._make_settings(
                dsn="https://key@glitchtip.example.com/1",
                env="production",
                version="1.2.3",
            )
        )
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["dsn"] == "https://key@glitchtip.example.com/1"
        assert call_kwargs["environment"] == "production"
        assert call_kwargs["release"] == "stepzero-backend@1.2.3"
        assert call_kwargs["traces_sample_rate"] == 0.2
        assert call_kwargs["send_default_pii"] is False
        assert call_kwargs["before_send"] is _before_send

    @patch("app.core.sentry.sentry_sdk.init")
    def test_glitchtip_incompatible_options_excluded(self, mock_init: MagicMock):
        """GlitchTip 미지원 옵션(profiles_sample_rate, enable_logs)이 없는지 확인."""
        setup_sentry(self._make_settings(dsn="https://key@glitchtip.example.com/1"))
        call_kwargs = mock_init.call_args.kwargs
        assert "profiles_sample_rate" not in call_kwargs
        assert "enable_logs" not in call_kwargs


# ── set_user_context 테스트 ──────────────────────────────────────────


class TestSetUserContext:
    """Sentry 사용자 컨텍스트 설정 검증."""

    @patch("app.core.sentry.sentry_sdk.set_user")
    def test_sets_user_id(self, mock_set_user: MagicMock):
        set_user_context("user-123")
        mock_set_user.assert_called_once_with({"id": "user-123"})

    @patch("app.core.sentry.sentry_sdk.set_user")
    def test_sets_user_id_and_email(self, mock_set_user: MagicMock):
        set_user_context("user-456", email="test@example.com")
        mock_set_user.assert_called_once_with(
            {"id": "user-456", "email": "test@example.com"}
        )

    @patch("app.core.sentry.sentry_sdk.set_user")
    def test_omits_email_when_none(self, mock_set_user: MagicMock):
        set_user_context("user-789", email=None)
        call_args = mock_set_user.call_args[0][0]
        assert "email" not in call_args


# ── 글로벌 핸들러 capture_exception 테스트 ───────────────────────────


class TestGlobalHandlerCaptureException:
    """global_exception_handler가 sentry_sdk.capture_exception()을 호출하는지 검증."""

    @patch("sentry_sdk.capture_exception")
    async def test_unhandled_exception_captured(self, mock_capture: MagicMock):
        """main.py의 global_exception_handler를 직접 호출하여 capture_exception 검증."""
        from app.main import global_exception_handler

        # Request mock
        mock_request = MagicMock()
        mock_request.url.path = "/test"

        exc = RuntimeError("unexpected failure")
        resp = await global_exception_handler(mock_request, exc)

        # capture_exception 호출 확인
        mock_capture.assert_called_once_with(exc)
        # 500 응답 반환 확인
        assert resp.status_code == 500

    @patch("sentry_sdk.capture_exception")
    async def test_capture_receives_original_exception(self, mock_capture: MagicMock):
        from app.main import global_exception_handler

        mock_request = MagicMock()
        mock_request.url.path = "/crash"

        exc = ValueError("db connection lost")
        await global_exception_handler(mock_request, exc)

        captured = mock_capture.call_args[0][0]
        assert isinstance(captured, ValueError)
        assert str(captured) == "db connection lost"


# ── RequestContextMiddleware Sentry set_tag 테스트 ───────────────────


class TestMiddlewareSentryTag:
    """RequestContextMiddleware가 Sentry에 request_id 태그를 설정하는지 검증."""

    @pytest.fixture(scope="class")
    async def middleware_app(self):
        from fastapi import FastAPI

        from app.middleware.logging import RequestContextMiddleware

        test_app = FastAPI()
        test_app.add_middleware(RequestContextMiddleware)

        @test_app.get("/ping")
        async def ping():
            return {"ok": True}

        return test_app

    @pytest.fixture(scope="class")
    async def mw_client(self, middleware_app):
        async with AsyncClient(
            transport=ASGITransport(app=middleware_app), base_url="http://test"
        ) as c:
            yield c

    @patch("app.middleware.logging.sentry_sdk.set_tag")
    async def test_sets_request_id_tag(
        self, mock_set_tag: MagicMock, mw_client: AsyncClient
    ):
        resp = await mw_client.get("/ping")
        assert resp.status_code == 200
        mock_set_tag.assert_called()
        # 첫 번째 인수가 "request_id"인 호출이 있어야 함
        tag_calls = [c for c in mock_set_tag.call_args_list if c[0][0] == "request_id"]
        assert len(tag_calls) >= 1
        # request_id 값이 비어있지 않아야 함
        assert len(tag_calls[0][0][1]) > 0

    @patch("app.middleware.logging.sentry_sdk.set_tag")
    async def test_custom_request_id_used(
        self, mock_set_tag: MagicMock, mw_client: AsyncClient
    ):
        resp = await mw_client.get(
            "/ping", headers={"X-Request-ID": "custom-trace-id-123"}
        )
        assert resp.status_code == 200
        tag_calls = [c for c in mock_set_tag.call_args_list if c[0][0] == "request_id"]
        assert any(c[0][1] == "custom-trace-id-123" for c in tag_calls)

    async def test_response_has_request_id_header(self, mw_client: AsyncClient):
        resp = await mw_client.get("/ping")
        assert "x-request-id" in resp.headers
        assert len(resp.headers["x-request-id"]) > 0

    async def test_response_echoes_custom_request_id(self, mw_client: AsyncClient):
        resp = await mw_client.get(
            "/ping", headers={"X-Request-ID": "my-custom-id"}
        )
        assert resp.headers["x-request-id"] == "my-custom-id"
