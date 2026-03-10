"""DDD 기반 도메인 Exception 계층.

모든 비즈니스/도메인 에러는 AppException 하위 클래스로 표현한다.
글로벌 핸들러가 이를 RFC 9457 problem+json 응답으로 자동 변환한다.
"""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """모든 도메인 Exception의 기본 클래스."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    detail: str = "서버 내부 오류가 발생했습니다."
    type_uri: str = "about:blank"

    def __init__(
        self,
        detail: str | None = None,
        *,
        error_code: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        if detail is not None:
            self.detail = detail
        if error_code is not None:
            self.error_code = error_code
        self.extra = extra or {}
        super().__init__(self.detail)


# ── NotFound ─────────────────────────────────────────────────────────

class NotFoundError(AppException):
    status_code = 404
    error_code = "NOT_FOUND"
    detail = "요청한 리소스를 찾을 수 없습니다."


class RoadmapNotFoundError(NotFoundError):
    error_code = "ROADMAP_NOT_FOUND"
    detail = "Roadmap not found"


class TeamNotFoundError(NotFoundError):
    error_code = "TEAM_NOT_FOUND"
    detail = "Team not found"


class PostNotFoundError(NotFoundError):
    error_code = "POST_NOT_FOUND"
    detail = "Post not found"


class CommentNotFoundError(NotFoundError):
    error_code = "COMMENT_NOT_FOUND"
    detail = "Comment not found"


class AppFileNotFoundError(NotFoundError):
    error_code = "FILE_NOT_FOUND"
    detail = "File not found"


class RoadmapJobNotFoundError(NotFoundError):
    error_code = "ROADMAP_JOB_NOT_FOUND"
    detail = "Job not found"


class RoadmapStepNotFoundError(NotFoundError):
    error_code = "ROADMAP_STEP_NOT_FOUND"
    detail = "Roadmap step not found"


class RoadmapStepActionNotFoundError(NotFoundError):
    error_code = "ROADMAP_STEP_ACTION_NOT_FOUND"
    detail = "Roadmap step action not found"


class NotificationNotFoundError(NotFoundError):
    error_code = "NOTIFICATION_NOT_FOUND"
    detail = "Notification not found"


class AnnouncementNotFoundError(NotFoundError):
    error_code = "ANNOUNCEMENT_NOT_FOUND"
    detail = "Announcement not found"


class UserNotFoundError(NotFoundError):
    error_code = "USER_NOT_FOUND"
    detail = "User not found"


class TemplateNotFoundError(NotFoundError):
    error_code = "TEMPLATE_NOT_FOUND"
    detail = "Template not found"


class ActionKitItemNotFoundError(NotFoundError):
    error_code = "ACTIONKIT_ITEM_NOT_FOUND"
    detail = "ActionKit item not found"


class ChatSessionNotFoundError(NotFoundError):
    error_code = "CHAT_SESSION_NOT_FOUND"
    detail = "세션을 찾을 수 없습니다."


# ── BusinessRule ─────────────────────────────────────────────────────

class BusinessRuleError(AppException):
    status_code = 400
    error_code = "BUSINESS_RULE_VIOLATION"
    detail = "비즈니스 규칙 위반입니다."


class StepOrderViolationError(BusinessRuleError):
    error_code = "STEP_ORDER_VIOLATION"
    detail = "Previous steps must be completed first"


class InvalidStatusTransitionError(BusinessRuleError):
    error_code = "INVALID_STATUS_TRANSITION"
    detail = "유효하지 않은 상태 전환입니다."


class DuplicateResourceError(BusinessRuleError):
    status_code = 409
    error_code = "DUPLICATE_RESOURCE"
    detail = "이미 존재하는 리소스입니다."


class SelfReportError(BusinessRuleError):
    error_code = "SELF_REPORT"
    detail = "자신의 콘텐츠는 신고할 수 없습니다."


class AlreadyReportedError(BusinessRuleError):
    error_code = "ALREADY_REPORTED"
    detail = "이미 신고한 콘텐츠입니다."


# ── Authentication ───────────────────────────────────────────────────

class AuthenticationError(AppException):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    detail = "인증에 실패했습니다."


class InvalidCredentialsError(AuthenticationError):
    error_code = "INVALID_CREDENTIALS"
    detail = "Could not validate credentials"


class TokenExpiredError(AuthenticationError):
    error_code = "TOKEN_EXPIRED"
    detail = "Token expired"


class InvalidTokenError(AuthenticationError):
    error_code = "INVALID_TOKEN"
    detail = "유효하지 않은 토큰입니다."


class TokenReuseDetectedError(AuthenticationError):
    error_code = "TOKEN_REUSE_DETECTED"
    detail = "Token reuse detected — all sessions revoked"


# ── Permission ───────────────────────────────────────────────────────

class AppPermissionError(AppException):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    detail = "권한이 없습니다."


class AccountRestrictedError(AppPermissionError):
    error_code = "ACCOUNT_RESTRICTED"
    detail = "계정이 제한되었습니다."

    def __init__(
        self,
        detail: str | None = None,
        *,
        status: str = "suspended",
        reason: str = "",
        suspended_until: str | None = None,
        expiry_iso: str | None = None,
    ) -> None:
        extra: dict[str, Any] = {"status": status, "reason": reason}
        if suspended_until is not None:
            extra["suspended_until"] = suspended_until
        if expiry_iso is not None:
            extra["expiry_iso"] = expiry_iso
        super().__init__(detail, extra=extra)


class SuspendedUserError(AppPermissionError):
    error_code = "USER_SUSPENDED"
    detail = "이용이 정지된 사용자입니다. 접근이 제한됩니다."


class TeamAccessDeniedError(AppPermissionError):
    error_code = "TEAM_ACCESS_DENIED"
    detail = "Team access denied"


class AdminRequiredError(AppPermissionError):
    error_code = "ADMIN_REQUIRED"
    detail = "Platform admin access denied"


class ResourceOwnershipError(AppPermissionError):
    error_code = "RESOURCE_OWNERSHIP"
    detail = "리소스에 대한 접근 권한이 없습니다."


# ── Validation ───────────────────────────────────────────────────────

class AppValidationError(AppException):
    status_code = 400
    error_code = "VALIDATION_ERROR"
    detail = "입력값이 유효하지 않습니다."


# ── ExternalService ──────────────────────────────────────────────────

class ExternalServiceError(AppException):
    status_code = 503
    error_code = "EXTERNAL_SERVICE_ERROR"
    detail = "외부 서비스 연결에 실패했습니다."


class DatabaseUnavailableError(ExternalServiceError):
    error_code = "DATABASE_UNAVAILABLE"
    detail = "Authentication backend unavailable"


class RagServiceUnavailableError(ExternalServiceError):
    error_code = "RAG_SERVICE_UNAVAILABLE"
    detail = "RAG 서비스를 사용할 수 없습니다."


class AppLawApiError(ExternalServiceError):
    error_code = "LAW_API_ERROR"
    detail = "법령 API 호출에 실패했습니다."
