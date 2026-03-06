# REPORT: Exception Handler 통합 구현 계획 보고서

> **작성일:** 2026-03-06
> **대상:** Step Zero Backend (`app-backend/`)
> **범위:** 에러 처리 체계 전면 개선 — 커스텀 Exception 계층, RFC 9457 업그레이드, Sentry 연동, 구조화 로깅
> **현황:** 분석 완료 / 구현 미착수

---

## 목차

1. [Executive Summary](#1-executive-summary)
2. [현행 시스템 진단](#2-현행-시스템-진단)
3. [업계 트렌드 및 베스트 프랙티스](#3-업계-트렌드-및-베스트-프랙티스)
4. [통합 구현 설계](#4-통합-구현-설계)
5. [세부 구현 명세](#5-세부-구현-명세)
6. [현 프로젝트 적용 가능성 평가](#6-현-프로젝트-적용-가능성-평가)
7. [마이그레이션 전략](#7-마이그레이션-전략)
8. [리스크 및 완화 방안](#8-리스크-및-완화-방안)
9. [비용 및 영향도 분석](#9-비용-및-영향도-분석)
10. [결론 및 권장사항](#10-결론-및-권장사항)

---

## 1. Executive Summary

Step Zero 백엔드는 RFC 7807 기반의 에러 응답 구조를 갖추고 있으나, **커스텀 Exception이 2개뿐이고 125+ 위치에서 HTTPException을 직접 raise**하며, **Sentry 미연동·구조화 로깅 부재**라는 구조적 한계를 가진다.

본 보고서는 최신 트렌드(RFC 9457, DDD Exception Hierarchy, Structured Logging, Sentry v8)를 반영한 **Exception Handler 통합 구현 계획**을 제시하고, 현 프로젝트에 대한 **적용 가능성을 8개 축으로 평가**한다.

### 핵심 제안 요약

| 영역 | 현재 | 목표 | 적용 가능성 |
|------|------|------|------------|
| Exception 계층 | 커스텀 2개 + ValueError | DDD 기반 도메인 Exception 트리 | **높음** — 점진적 마이그레이션 가능 |
| 에러 응답 표준 | RFC 7807 (부분 준수) | RFC 9457 (완전 준수) | **높음** — 하위 호환 |
| 에러 트래킹 | 없음 (로깅만) | Sentry v8 + Performance | **높음** — SDK 자동 통합 |
| 로깅 | 표준 logging (텍스트) | structlog (JSON 구조화) | **중간** — 기존 코드 수정 필요 |
| 서비스-API 경계 | 혼재 (서비스에서 HTTPException) | 명확 분리 (서비스는 도메인 Exception만) | **중간** — 리팩토링 범위 큼 |
| Worker 에러 처리 | 서비스 레이어 의존 | 전용 에러 핸들링 + 재시도 정책 | **높음** — ARQ 설정만 |
| 트랜잭션 안전성 | 암시적 | 명시적 rollback + 에러 전파 | **높음** — 패턴 표준화 |
| 에러 메시지 | 한/영 혼용 | 한국어 통일 + i18n 대비 error_code | **높음** — 점진적 적용 |

---

## 2. 현행 시스템 진단

### 2.1 아키텍처 개요

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                    │
├─────────────────────────────────────────────────────────┤
│  Global Exception Handler (catch-all → 500)              │
│  ├── HTTPException → http_exception_to_problem()         │
│  ├── RequestValidationError → validation_exception_to_problem() │
│  ├── RateLimitExceeded → _rate_limit_exceeded_handler()  │
│  └── Exception → global_exception_handler()              │
├─────────────────────────────────────────────────────────┤
│  API Routers (try/except → HTTPException 변환)           │
│  ├── ValueError → 400/404                                │
│  ├── InvalidRoadmapStepStatusError → 400/404 (문자열 비교)│
│  └── Exception → 500 (일부만)                            │
├─────────────────────────────────────────────────────────┤
│  Service Layer (ValueError/HTTPException 혼재)           │
│  ├── auth_service.py: HTTPException 직접 raise           │
│  ├── roadmap_templates/service.py: ValueError raise      │
│  ├── chat_service.py: HTTPException catch + 폴백         │
│  └── rag_service.py: Exception catch + 폴백              │
├─────────────────────────────────────────────────────────┤
│  Domain/Repository Layer                                 │
│  └── SQLAlchemy 예외 미처리 (IntegrityError 등)          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 정량적 현황

| 지표 | 수치 | 비고 |
|------|------|------|
| HTTPException raise 위치 | **125+** | 14개 라우터 파일에 분산 |
| ValueError raise 위치 | **22+** | 서비스/설정 레이어 |
| 커스텀 Exception 클래스 | **2개** | `LawApiError`, `InvalidRoadmapStepStatusError` |
| try/except 블록 | **45+** | bare `Exception` catch 25+ |
| 서비스 레이어 HTTPException | **5곳** | auth_service, chat_session_service, post_service |
| IntegrityError 처리 | **1곳** | roadmap_chat_repository만 |
| Sentry/에러 트래킹 | **0** | 미연동 |
| 구조화 로깅 | **0** | 텍스트 포맷만 |

### 2.3 핵심 문제점 상세

#### 문제 1: 문자열 비교 기반 에러 분기

**파일:** `app/api/v1/roadmaps/get.py:244-248`

```python
except InvalidRoadmapStepStatusError as exc:
    message = str(exc)
    if "not found" in message:
        raise HTTPException(status_code=404, detail=message)
    raise HTTPException(status_code=400, detail=message)
```

**위험:** 에러 메시지 변경 시 HTTP 상태 코드 매핑이 깨짐. 타입 안전하지 않음.

#### 문제 2: 서비스-API 레이어 경계 위반

**파일:** `app/features/auth/application/auth_service.py:193-202`

```python
# 서비스 레이어에서 HTTPException 직접 raise — 프레임워크 종속
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail={
        "code": "ACCOUNT_RESTRICTED",
        "status": user.status,
        ...
    },
)
```

**영향:** 서비스 레이어가 FastAPI에 종속되어 재사용 불가, 테스트 시 HTTP 컨텍스트 필요.

#### 문제 3: RFC 7807 title 고정값

**파일:** `app/api/problem.py:35`

```python
title = "HTTP Error"  # 모든 HTTPException에 동일한 title
```

**영향:** 클라이언트가 에러 유형을 title로 구분할 수 없음. RFC 9457 위반.

#### 문제 4: 에러 메시지 한/영 혼용

```python
# 한국어
raise HTTPException(400, "자신의 게시글은 신고할 수 없습니다.")  # growth_club/posts.py:116
# 영문
raise HTTPException(401, "Could not validate credentials")  # deps.py:28
# 혼합
raise HTTPException(404, "Post not found")  # growth_club/posts.py:82
```

**영향:** 프론트엔드 에러 표시 불일관, i18n 대응 불가.

#### 문제 5: Worker 예외 처리 갭

**파일:** `app/workers/roadmap_worker.py:18-21`

```python
async def process_roadmap_job(ctx, job_id: str):
    async with get_async_session() as session:
        service = RoadmapGenerationService(session)
        await service.process_job(UUID(job_id))
    # ← 세션 생성 실패, UUID 파싱 실패 시 미처리
```

**영향:** Worker 프로세스 크래시 가능, Job 상태 QUEUED에서 영구 정체.

---

## 3. 업계 트렌드 및 베스트 프랙티스

### 3.1 RFC 9457 — Problem Details for HTTP APIs (RFC 7807 후속)

RFC 7807은 2024년 **RFC 9457**로 대체되었다. 주요 변경:

| 항목 | RFC 7807 | RFC 9457 |
|------|----------|----------|
| 상태 | 폐기(Obsoleted) | 현행 표준 |
| `type` 필드 | 선택, `"about:blank"` 기본 | **등록 레지스트리 권장**, URI 명확화 |
| 다중 문제 | 미지원 | **`errors` 배열 확장 권장** |
| Content-Type | `application/problem+json` | 동일 (하위 호환) |
| 확장 필드 | 자유 | **네임스페이스 가이드라인 강화** |

**적용 판단:** Step Zero는 이미 `application/problem+json`을 사용하므로, `type` URI 체계화와 에러 레지스트리 도입만으로 RFC 9457 완전 준수 가능. **하위 호환 100%.**

### 3.2 DDD 기반 도메인 Exception 계층

2025-2026년 Python 백엔드 생태계의 주류 패턴:

```
                    AppException (base)
                    ├── status_code: int
                    ├── error_code: str
                    └── detail: str
                        │
           ┌────────────┼────────────┐
     NotFoundError   BusinessError  AuthenticationError
     (404)           (400/409/422)  (401)
           │              │              │
   ┌───────┤        ┌─────┤        ┌─────┤
Roadmap  Team    Validation Permission Token
NotFound NotFound Error     Error     Expired
```

**핵심 원칙:**
1. **서비스 레이어는 도메인 Exception만 raise** — HTTPException 금지
2. **API 레이어에서 자동 변환** — 글로벌 핸들러가 Exception → HTTP 응답
3. **error_code로 머신 식별** — 문자열 비교 제거, enum 기반
4. **detail로 사용자 메시지** — 한국어 통일

### 3.3 Structured Logging (structlog)

2025-2026년 Python 로깅 표준:

```python
# 기존 (비구조화)
logger.error(f"Unhandled error: {str(exc)}", exc_info=True)

# 구조화 (structlog)
logger.error("unhandled_error", exc_info=True,
             error_type=type(exc).__name__,
             request_path=request.url.path,
             user_id=str(user.id))
```

**이점:**
- JSON 출력 → ELK/Datadog/CloudWatch 직접 인제스트
- 컨텍스트 자동 바인딩 (request_id, user_id, team_id)
- Sentry breadcrumb 자동 연동
- 성능: 표준 logging 대비 동등 (lazy evaluation)

### 3.4 Sentry v8 FastAPI 통합

Sentry SDK v2+ (2025-2026)는 FastAPI 자동 통합 제공:

```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://...",
    traces_sample_rate=0.2,        # 성능 모니터링 20%
    profiles_sample_rate=0.1,       # 프로파일링 10%
    enable_tracing=True,
    environment="production",
    release="stepzero@1.0.0",
    # FastAPI 자동 감지 — 별도 integration 불요
)
```

**자동 캡처 항목:**
- 미처리 예외 (500 에러)
- 느린 트랜잭션 (>2s)
- 요청 컨텍스트 (URL, method, headers)
- 사용자 컨텍스트 (user_id, email)
- breadcrumb (로그, DB 쿼리, HTTP 호출)

### 3.5 Result 패턴 (모나딕 에러 처리)

2025-2026년 Python 커뮤니티에서 부상 중인 패턴:

```python
from returns.result import Result, Success, Failure

def get_roadmap(roadmap_id: UUID) -> Result[Roadmap, AppException]:
    roadmap = repo.find(roadmap_id)
    if not roadmap:
        return Failure(RoadmapNotFoundError(roadmap_id))
    return Success(roadmap)
```

**적용 판단:** Step Zero에는 **과도한 복잡성**. 기존 Exception 기반이 팀 규모와 프로젝트 복잡도에 적합. Result 패턴은 **비채택** 권장.

### 3.6 FastAPI 레이어 분리 원칙 (2025-2026 컨센서스)

```
┌──────────────────┐  도메인 Exception만
│  Service Layer   │  raise AppException/ValueError
│  (프레임워크 무관) │  ← HTTPException 금지
└────────┬─────────┘
         │ 도메인 Exception 전파
┌────────▼─────────┐
│  API Layer       │  자동 변환 (Global Handler)
│  (FastAPI 종속)   │  AppException → RFC 9457 응답
└──────────────────┘
```

**업계 컨센서스:**
- 서비스 레이어에서 `HTTPException` raise는 **안티패턴**으로 간주
- FastAPI `add_exception_handler()`로 **중앙 집중 변환**이 모범 사례
- 라우터의 try/except는 **최소화** (특수 케이스만)

---

## 4. 통합 구현 설계

### 4.1 목표 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                        │
├─────────────────────────────────────────────────────────────┤
│  Sentry SDK (자동 캡처 + Performance)                        │
├─────────────────────────────────────────────────────────────┤
│  Structured Logging Middleware (request_id, user_id 바인딩)  │
├─────────────────────────────────────────────────────────────┤
│  Exception Handler Chain (우선순위 순)                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 1. AppException → RFC 9457 응답 (자동 status_code 매핑) ││
│  │ 2. RequestValidationError → RFC 9457 (422)              ││
│  │ 3. RateLimitExceeded → RFC 9457 (429)                   ││
│  │ 4. HTTPException → RFC 9457 (하위 호환)                  ││
│  │ 5. Exception → RFC 9457 (500) + Sentry 캡처             ││
│  └─────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────┤
│  API Routers (try/except 최소화)                             │
│  └── 특수 케이스만: SSE 스트리밍, 파일 업로드 롤백           │
├─────────────────────────────────────────────────────────────┤
│  Service Layer (도메인 Exception만 raise)                    │
│  ├── NotFoundError("roadmap", roadmap_id)                   │
│  ├── BusinessRuleError("STEP_ORDER_VIOLATION", ...)         │
│  └── ExternalServiceError("rag", "timeout", ...)            │
├─────────────────────────────────────────────────────────────┤
│  Domain/Repository Layer                                     │
│  └── IntegrityError → DuplicateResourceError 변환           │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Exception 계층 설계

```python
# app/core/exceptions.py (신규)

class AppException(Exception):
    """Step Zero 전역 기본 예외.

    모든 도메인/비즈니스 예외의 부모 클래스.
    Global exception handler가 이 타입을 캐치하여 RFC 9457 응답으로 변환.
    """
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    detail: str = "서버 내부 오류가 발생했습니다."
    type_uri: str = "https://stepzero.dev/problems/internal-error"

    def __init__(self, detail: str | None = None, **extra):
        self.detail = detail or self.__class__.detail
        self.extra = extra
        super().__init__(self.detail)


# ── 404 계열 ──

class NotFoundError(AppException):
    status_code = 404
    error_code = "NOT_FOUND"
    type_uri = "https://stepzero.dev/problems/not-found"

    def __init__(self, resource: str, identifier: Any = None):
        detail = f"{resource}을(를) 찾을 수 없습니다."
        super().__init__(detail, resource=resource, identifier=str(identifier) if identifier else None)


class RoadmapNotFoundError(NotFoundError):
    error_code = "ROADMAP_NOT_FOUND"
    def __init__(self, roadmap_id=None):
        super().__init__("로드맵", roadmap_id)


class TeamNotFoundError(NotFoundError):
    error_code = "TEAM_NOT_FOUND"
    def __init__(self, team_id=None):
        super().__init__("팀", team_id)


class PostNotFoundError(NotFoundError):
    error_code = "POST_NOT_FOUND"
    def __init__(self, post_id=None):
        super().__init__("게시글", post_id)


class FileNotFoundError_(NotFoundError):
    error_code = "FILE_NOT_FOUND"
    def __init__(self, file_id=None):
        super().__init__("파일", file_id)


# ── 400 계열: 비즈니스 규칙 위반 ──

class BusinessRuleError(AppException):
    status_code = 400
    error_code = "BUSINESS_RULE_VIOLATION"
    type_uri = "https://stepzero.dev/problems/business-rule"


class StepOrderViolationError(BusinessRuleError):
    error_code = "STEP_ORDER_VIOLATION"
    def __init__(self):
        super().__init__("이전 단계를 먼저 완료해야 합니다.")


class InvalidStatusTransitionError(BusinessRuleError):
    error_code = "INVALID_STATUS_TRANSITION"
    def __init__(self, current: str, target: str):
        super().__init__(
            f"상태를 '{current}'에서 '{target}'(으)로 변경할 수 없습니다.",
            current_status=current, target_status=target,
        )


class DuplicateResourceError(BusinessRuleError):
    status_code = 409
    error_code = "DUPLICATE_RESOURCE"
    type_uri = "https://stepzero.dev/problems/duplicate"
    def __init__(self, resource: str, field: str = None):
        detail = f"이미 존재하는 {resource}입니다."
        super().__init__(detail, resource=resource, field=field)


class SelfReportError(BusinessRuleError):
    error_code = "SELF_REPORT"
    def __init__(self, resource: str):
        super().__init__(f"자신의 {resource}은(는) 신고할 수 없습니다.")


class AlreadyReportedError(BusinessRuleError):
    error_code = "ALREADY_REPORTED"
    def __init__(self, resource: str):
        super().__init__(f"이미 신고한 {resource}입니다.")


# ── 401 계열: 인증 ──

class AuthenticationError(AppException):
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    type_uri = "https://stepzero.dev/problems/authentication"
    detail = "인증에 실패했습니다."


class InvalidCredentialsError(AuthenticationError):
    error_code = "INVALID_CREDENTIALS"
    detail = "이메일 또는 비밀번호가 올바르지 않습니다."


class TokenExpiredError(AuthenticationError):
    error_code = "TOKEN_EXPIRED"
    detail = "토큰이 만료되었습니다."


class InvalidTokenError(AuthenticationError):
    error_code = "INVALID_TOKEN"
    detail = "유효하지 않은 토큰입니다."


class TokenReuseDetectedError(AuthenticationError):
    error_code = "TOKEN_REUSE_DETECTED"
    detail = "토큰 재사용이 감지되었습니다. 모든 세션이 폐기됩니다."


# ── 403 계열: 권한 ──

class PermissionError_(AppException):
    status_code = 403
    error_code = "PERMISSION_DENIED"
    type_uri = "https://stepzero.dev/problems/permission"
    detail = "접근 권한이 없습니다."


class AccountRestrictedError(PermissionError_):
    error_code = "ACCOUNT_RESTRICTED"
    def __init__(self, user_status: str, reason: str = None,
                 suspended_until: str = None):
        detail = "계정이 제한되었습니다."
        super().__init__(detail, status=user_status, reason=reason,
                        suspended_until=suspended_until)


class TeamAccessDeniedError(PermissionError_):
    error_code = "TEAM_ACCESS_DENIED"
    detail = "팀 접근이 거부되었습니다."


class AdminRequiredError(PermissionError_):
    error_code = "ADMIN_REQUIRED"
    detail = "관리자 권한이 필요합니다."


class ResourceOwnershipError(PermissionError_):
    error_code = "NOT_RESOURCE_OWNER"
    def __init__(self, resource: str):
        super().__init__(f"이 {resource}에 대한 권한이 없습니다.")


# ── 422 계열: 입력 검증 ──

class ValidationError_(AppException):
    status_code = 422
    error_code = "VALIDATION_FAILED"
    type_uri = "https://stepzero.dev/problems/validation"
    detail = "입력값이 유효하지 않습니다."


# ── 503 계열: 외부 서비스 ──

class ExternalServiceError(AppException):
    status_code = 503
    error_code = "EXTERNAL_SERVICE_UNAVAILABLE"
    type_uri = "https://stepzero.dev/problems/external-service"

    def __init__(self, service_name: str, reason: str = None):
        detail = f"{service_name} 서비스를 사용할 수 없습니다."
        super().__init__(detail, service=service_name, reason=reason)


class DatabaseUnavailableError(ExternalServiceError):
    error_code = "DATABASE_UNAVAILABLE"
    def __init__(self):
        super().__init__("데이터베이스")


class RagServiceUnavailableError(ExternalServiceError):
    error_code = "RAG_UNAVAILABLE"
    def __init__(self, reason: str = None):
        super().__init__("RAG", reason)


class LawApiError_(ExternalServiceError):
    error_code = "LAW_API_ERROR"
    def __init__(self, reason: str = None):
        super().__init__("국가법령정보센터 API", reason)
```

### 4.3 RFC 9457 준수 에러 응답 설계

```python
# 개선된 app/api/problem.py

HTTP_STATUS_TITLES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Validation Error",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}

async def app_exception_to_problem(request: Request, exc: AppException) -> JSONResponse:
    """AppException → RFC 9457 Problem Details 자동 변환."""
    payload = {
        "type": exc.type_uri,
        "title": HTTP_STATUS_TITLES.get(exc.status_code, "Error"),
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": str(request.url.path),
        "error_code": exc.error_code,        # RFC 9457 확장 필드
        "timestamp": datetime.utcnow().isoformat() + "Z",  # RFC 9457 확장
    }
    if exc.extra:
        payload["extensions"] = exc.extra     # RFC 9457 확장 네임스페이스
    return JSONResponse(
        status_code=exc.status_code,
        content=payload,
        media_type="application/problem+json",
    )
```

**RFC 9457 응답 예시:**

```json
{
    "type": "https://stepzero.dev/problems/not-found",
    "title": "Not Found",
    "status": 404,
    "detail": "로드맵을(를) 찾을 수 없습니다.",
    "instance": "/api/v1/roadmaps/abc-123",
    "error_code": "ROADMAP_NOT_FOUND",
    "timestamp": "2026-03-06T10:30:00Z",
    "extensions": {
        "resource": "로드맵",
        "identifier": "abc-123"
    }
}
```

### 4.4 글로벌 Exception Handler 체인

```python
# app/main.py — 개선된 핸들러 등록 순서

# 1. 도메인 예외 (최우선)
app.add_exception_handler(AppException, app_exception_to_problem)

# 2. Pydantic 검증 오류
app.add_exception_handler(RequestValidationError, validation_exception_to_problem)

# 3. Rate Limit
app.add_exception_handler(RateLimitExceeded, rate_limit_to_problem)

# 4. HTTPException (하위 호환 — 마이그레이션 기간 유지)
app.add_exception_handler(HTTPException, http_exception_to_problem)

# 5. 미처리 예외 (catch-all)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    sentry_sdk.capture_exception(exc)
    logger.error("unhandled_exception",
                 error_type=type(exc).__name__,
                 path=request.url.path)
    return problem_response(request, 500, ...)
```

---

## 5. 세부 구현 명세

### 5.1 Sentry v8 연동

#### 설치 및 초기화

```toml
# pyproject.toml 추가
[project.dependencies]
sentry-sdk = { version = ">=2.19.0", extras = ["fastapi"] }
```

```python
# app/core/sentry.py (신규)

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.arq import ArqIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration

def setup_sentry(settings) -> None:
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,            # "development" | "production"
        release=f"stepzero@{settings.VERSION}",

        # Performance
        traces_sample_rate=0.2,                       # 프로덕션 20%
        profiles_sample_rate=0.1,                     # 프로파일링 10%

        # Logging
        enable_logs=True,

        # Integrations
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            ArqIntegration(),
            HttpxIntegration(),
            LoggingIntegration(
                level=logging.INFO,                   # breadcrumb 수준
                event_level=logging.ERROR,            # Sentry 이벤트 수준
                sentry_logs_level=logging.WARNING,    # Sentry Logs 수준
            ),
        ],

        # Filtering
        before_send=_before_send,

        # PII
        send_default_pii=False,
    )


def _before_send(event, hint):
    """민감 정보 필터링 + 불필요 이벤트 제거."""
    # AppException 중 4xx는 이벤트로 보내지 않음 (로그만)
    exc_info = hint.get("exc_info")
    if exc_info:
        exc_type, exc_value, _ = exc_info
        if isinstance(exc_value, AppException) and exc_value.status_code < 500:
            return None
    return event


def set_user_context(user_id: str, email: str = None, team_id: str = None):
    """인증 후 Sentry 사용자 컨텍스트 설정."""
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
    })
    if team_id:
        sentry_sdk.set_tag("team_id", team_id)
```

#### 환경 변수 추가

```python
# app/core/config.py 추가 필드
SENTRY_DSN: str = ""                    # 빈 문자열이면 비활성화
ENVIRONMENT: str = "development"         # development | staging | production
```

#### Worker 연동

```python
# app/workers/roadmap_worker.py 수정
async def process_roadmap_job(ctx, job_id: str):
    with sentry_sdk.new_scope() as scope:
        scope.set_tag("job_id", job_id)
        scope.set_context("arq", {"job_id": job_id, "function": "process_roadmap_job"})
        # ... 기존 로직
```

### 5.2 구조화 로깅 (structlog)

#### 설치

```toml
# pyproject.toml 추가
structlog = ">=24.4.0"
```

#### 설정

```python
# app/core/logging.py (전면 교체)

import logging
import sys
import structlog
from structlog.types import Processor


def setup_logging(json_output: bool = True) -> None:
    """structlog 기반 구조화 로깅 초기화."""

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,         # request_id, user_id 등
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer = structlog.processors.JSONRenderer(ensure_ascii=False)
    else:
        renderer = structlog.dev.ConsoleRenderer()       # 개발 환경 컬러 출력

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # 제3자 라이브러리 레벨 제어
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
```

#### 요청 컨텍스트 미들웨어

```python
# app/middleware/logging.py (신규)

import uuid
import structlog
from starlette.middleware.base import BaseHTTPMiddleware

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        # Sentry에도 request_id 태깅
        sentry_sdk.set_tag("request_id", request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

### 5.3 Feature별 마이그레이션 매핑

각 feature에서 현재 `HTTPException`/`ValueError`를 어떤 도메인 Exception으로 교체하는지:

#### Auth Feature

| 현재 코드 (파일:라인) | 현재 예외 | 변환 대상 |
|----------------------|----------|----------|
| `auth/router.py:138` | `HTTPException(401, "Incorrect email or password")` | `InvalidCredentialsError()` |
| `auth/router.py:132` | `HTTPException(503, "Authentication backend unavailable")` | `DatabaseUnavailableError()` |
| `auth/router.py:169` | `HTTPException(401, "Invalid Google token")` | `InvalidTokenError()` |
| `auth/router.py:175` | `HTTPException(503, "Google authentication service unavailable")` | `ExternalServiceError("Google OAuth")` |
| `auth_service.py:193` | `HTTPException(403, dict(...))` | `AccountRestrictedError(status, reason, suspended_until)` |
| `auth/router.py:256` | `HTTPException(401, "Refresh token reuse detected...")` | `TokenReuseDetectedError()` |

#### Roadmaps Feature

| 현재 코드 (파일:라인) | 현재 예외 | 변환 대상 |
|----------------------|----------|----------|
| `roadmaps/get.py:109` | `HTTPException(404, message)` | `RoadmapNotFoundError(roadmap_id)` |
| `roadmap_progress_service.py:42` | `InvalidRoadmapStepStatusError("Previous steps...")` | `StepOrderViolationError()` |
| `roadmap_progress_service.py:28` | `InvalidRoadmapStepStatusError("Unsupported status")` | `InvalidStatusTransitionError(current, target)` |
| `roadmaps/jobs.py:75` | `HTTPException(422, ...)` | `ValidationError_(detail)` |

#### Growth Club Feature

| 현재 코드 (파일:라인) | 현재 예외 | 변환 대상 |
|----------------------|----------|----------|
| `posts.py:82` | `HTTPException(404, "Post not found")` | `PostNotFoundError(post_id)` |
| `posts.py:95` | `HTTPException(403, "Not authorized to update this post")` | `ResourceOwnershipError("게시글")` |
| `posts.py:116` | `HTTPException(400, "자신의 게시글은 신고할 수 없습니다.")` | `SelfReportError("게시글")` |
| `posts.py:122` | `HTTPException(400, "이미 신고한 게시물입니다.")` | `AlreadyReportedError("게시글")` |
| `comments.py:138` | `HTTPException(403, "Not authorized")` | `ResourceOwnershipError("댓글")` |

#### ActionKit Feature

| 현재 코드 (파일:라인) | 현재 예외 | 변환 대상 |
|----------------------|----------|----------|
| `files.py:121` | `HTTPException(404, "No file found for this item")` | `FileNotFoundError_(item_id)` |
| `files.py:43` | `HTTPException(400, "Filename is required")` | `ValidationError_("파일명은 필수입니다.")` |
| `service.py:199` | `ValueError("ActionKit item not found")` | `NotFoundError("액션키트 아이템", item_id)` |

#### Deps (인증/권한)

| 현재 코드 (파일:라인) | 현재 예외 | 변환 대상 |
|----------------------|----------|----------|
| `deps.py:27-31` | `HTTPException(401, "Could not validate credentials")` | `AuthenticationError()` |
| `deps.py:64-66` | `HTTPException(403, "Inactive user")` | `AccountRestrictedError("inactive")` |
| `deps.py:99-101` | `HTTPException(403, "Team access denied")` | `TeamAccessDeniedError()` |
| `deps.py:215-218` | `HTTPException(403, "Platform admin access denied")` | `AdminRequiredError()` |

#### Ops Feature (roadmap_templates/service.py)

| 현재 코드 (파일:라인) | 현재 예외 | 변환 대상 |
|----------------------|----------|----------|
| `service.py:119` | `ValueError("Roadmap ... not found")` | `RoadmapNotFoundError(roadmap_id)` |
| `service.py:212` | `ValueError("Cannot edit template in ... status")` | `InvalidStatusTransitionError(current, "editable")` |
| `service.py:295` | `ValueError("Cannot add steps to non-editable template")` | `BusinessRuleError("편집 불가능한 템플릿에 단계를 추가할 수 없습니다.")` |

### 5.4 Worker 에러 처리 강화

```python
# app/workers/roadmap_worker.py (개선)

async def process_roadmap_job(ctx, job_id: str):
    """ARQ Worker 태스크 — 완전한 에러 처리."""
    structlog.contextvars.bind_contextvars(job_id=job_id, worker="roadmap")
    logger = get_logger("worker.roadmap")

    try:
        job_uuid = UUID(job_id)
    except ValueError:
        logger.error("invalid_job_id", job_id=job_id)
        sentry_sdk.capture_message(f"Invalid job_id: {job_id}", level="error")
        return  # 재시도 불가, 즉시 종료

    try:
        async with get_async_session() as session:
            service = RoadmapGenerationService(session)
            await service.process_job(job_uuid)
    except AppException as exc:
        logger.error("job_domain_error", error_code=exc.error_code)
        # 서비스 레이어에서 이미 job.mark_failed() 호출
    except Exception as exc:
        logger.exception("job_unexpected_error")
        sentry_sdk.capture_exception(exc)
        # 세션이 닫혔으므로 새 세션으로 mark_failed
        try:
            async with get_async_session() as session:
                repo = RoadmapJobRepository(session)
                job = await repo.get(job_uuid)
                if job:
                    await repo.mark_failed(job, "WORKER_ERROR", str(exc))
                    await session.commit()
        except Exception:
            logger.exception("failed_to_mark_job_failed")
```

```python
# ARQ WorkerSettings 개선
class WorkerSettings:
    functions = [process_roadmap_job]
    max_tries = 3                     # 최대 3회 재시도
    retry_delay = 30                  # 30초 후 재시도
    job_timeout = 300                 # 5분 타임아웃
    health_check_interval = 30        # 30초 헬스체크
    cron_jobs = [cron(...)]
```

### 5.5 트랜잭션 안전성 패턴

```python
# 표준 패턴 — 서비스 레이어 트랜잭션

class PostService:
    async def create_post(self, ...):
        saved_files = []
        try:
            # 파일 업로드
            for file in files:
                key = await storage.upload(file)
                saved_files.append(key)

            # DB 작업
            post = Post(...)
            self.session.add(post)
            await self.session.commit()
            return post

        except Exception:
            await self.session.rollback()
            # 보상 트랜잭션: 업로드된 파일 정리
            for key in saved_files:
                try:
                    await storage.delete(key)
                except Exception as cleanup_err:
                    logger.warning("file_cleanup_failed", key=key, error=str(cleanup_err))
            raise
```

### 5.6 프론트엔드 에러 타입 자동 생성

```typescript
// app-frontend/src/lib/api-errors.ts (자동 생성 대상)

export interface ProblemDetail {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
  error_code: string;      // 머신 식별용
  timestamp: string;
  extensions?: Record<string, unknown>;
  errors?: ValidationError[];  // 422 전용
}

export const ERROR_CODES = {
  NOT_FOUND: "NOT_FOUND",
  ROADMAP_NOT_FOUND: "ROADMAP_NOT_FOUND",
  INVALID_CREDENTIALS: "INVALID_CREDENTIALS",
  TOKEN_EXPIRED: "TOKEN_EXPIRED",
  ACCOUNT_RESTRICTED: "ACCOUNT_RESTRICTED",
  // ... 자동 생성
} as const;

export type ErrorCode = typeof ERROR_CODES[keyof typeof ERROR_CODES];
```

**프론트엔드 에러 처리 개선:**

```typescript
// 현재 (문자열 비교)
if (error.response?.data?.detail === "Post not found") { ... }

// 개선 (error_code 비교)
if (error.response?.data?.error_code === "POST_NOT_FOUND") { ... }
```

---

## 6. 현 프로젝트 적용 가능성 평가

### 6.1 평가 매트릭스

| 평가 축 | 점수 (1-5) | 근거 |
|---------|-----------|------|
| **기술적 호환성** | 5/5 | FastAPI 네이티브 `add_exception_handler`, 하위 호환 |
| **마이그레이션 용이성** | 4/5 | 점진적 적용 가능, 기존 HTTPException과 공존 |
| **팀 학습 비용** | 4/5 | Exception 계층은 직관적, structlog은 약간의 학습 필요 |
| **테스트 영향** | 4/5 | SQLite 테스트 환경 유지, Exception 타입 assert 가능 |
| **프론트엔드 호환** | 5/5 | RFC 9457은 JSON 응답, error_code 추가만 |
| **성능 영향** | 5/5 | Exception 생성 비용 무시 가능, structlog lazy eval |
| **운영 안정성** | 4/5 | Sentry는 opt-in (DSN 빈 문자열이면 비활성화) |
| **코드 품질 향상** | 5/5 | 125+ HTTPException → 타입 안전 도메인 Exception |

**종합 점수: 36/40 (90%) — 적용 강력 권장**

### 6.2 적용 가능 근거 상세

#### 근거 1: FastAPI 네이티브 지원

FastAPI의 `add_exception_handler()`는 **Exception 클래스 계층을 자동 탐색**한다:

```python
# AppException 핸들러 등록 시, 모든 하위 클래스도 자동 캐치
app.add_exception_handler(AppException, app_exception_to_problem)

# → NotFoundError, BusinessRuleError, AuthenticationError 등 모두 자동 처리
```

기존 `HTTPException` 핸들러와 **공존 가능**하므로 점진적 마이그레이션 지원.

#### 근거 2: 테스트 코드 영향 최소화

현재 테스트(`tests/`)는 대부분 **HTTP 상태 코드 기반 assertion**:

```python
# 현재 테스트 (변경 불요)
assert response.status_code == 404

# 추가 가능한 테스트
assert response.json()["error_code"] == "ROADMAP_NOT_FOUND"
```

기존 테스트는 **수정 없이 통과**하고, error_code assertion은 선택적으로 추가.

#### 근거 3: 기존 RFC 7807 인프라 재활용

`app/api/problem.py`의 `problem_response()`를 확장하여 사용:

```python
# 현재 함수 시그니처 (유지)
def problem_response(*, request, status_code, title, detail, type_uri, extra)

# AppException 핸들러에서 호출 (추가)
async def app_exception_to_problem(request, exc):
    return problem_response(
        request=request,
        status_code=exc.status_code,
        title=HTTP_STATUS_TITLES[exc.status_code],
        detail=exc.detail,
        type_uri=exc.type_uri,
        extra={"error_code": exc.error_code, **exc.extra},
    )
```

#### 근거 4: Sentry 자동 통합

Sentry SDK는 FastAPI를 **자동 감지**:

```python
pip install sentry-sdk[fastapi]
# → FastApiIntegration 자동 등록
# → 미처리 예외 자동 캡처
# → 요청 컨텍스트 자동 첨부
```

`sentry_sdk.init()` 한 줄로 즉시 동작. DSN 미설정 시 완전 비활성화 (성능 오버헤드 0).

### 6.3 적용 불가/부적합 사항

| 항목 | 판단 | 사유 |
|------|------|------|
| **Result 패턴 (모나드)** | 비채택 | 팀 규모 대비 학습 비용 과다, 기존 코드 전면 리팩토링 필요 |
| **OpenTelemetry 분산 추적** | 시기상조 | 단일 서비스 구조, Sentry tracing으로 충분 |
| **에러 응답 다국어(i18n)** | 연기 | error_code 기반 구조 먼저, 다국어는 프론트엔드에서 처리 |
| **커스텀 에러 페이지** | 해당 없음 | API 전용 백엔드, HTML 에러 페이지 불요 |

---

## 7. 마이그레이션 전략

### 7.1 Phase 구분

```
Phase A: 기반 구축 (예상 작업량: 중)
  ├── app/core/exceptions.py 신규 생성
  ├── app/core/sentry.py 신규 생성
  ├── app/core/logging.py structlog 전환
  ├── app/api/problem.py RFC 9457 업그레이드
  ├── app/main.py 핸들러 체인 재구성
  ├── pyproject.toml 의존성 추가
  └── .env 파일 업데이트 (SENTRY_DSN, ENVIRONMENT)

Phase B: 핵심 Feature 마이그레이션 (예상 작업량: 대)
  ├── app/api/deps.py → 도메인 Exception 전환
  ├── app/features/auth/ → 전환
  ├── app/features/roadmaps/ → 전환 (InvalidRoadmapStepStatusError 대체)
  ├── app/features/actionkit/ → 전환
  └── app/workers/ → 에러 처리 강화

Phase C: 나머지 Feature 마이그레이션 (예상 작업량: 중)
  ├── app/features/growth_club/ → 전환
  ├── app/features/chat/ → 전환
  ├── app/features/rag/ → 전환
  ├── app/features/ops/ → 전환
  ├── app/features/dashboard/ → 전환
  └── app/services/ (law_api_client 등) → 전환

Phase D: 마무리 및 검증 (예상 작업량: 소)
  ├── 레거시 Exception 클래스 제거 (LawApiError, InvalidRoadmapStepStatusError)
  ├── 전체 테스트 통과 확인
  ├── error_code 기반 프론트엔드 에러 처리 가이드 작성
  └── Sentry 알림 규칙 설정
```

### 7.2 공존 전략 (마이그레이션 기간)

Phase A 완료 후 ~ Phase D 완료까지, **기존 HTTPException과 새 AppException이 공존**:

```python
# app/main.py — 핸들러 우선순위

# 1순위: 새 도메인 예외 (마이그레이션된 코드)
app.add_exception_handler(AppException, app_exception_to_problem)

# 2순위: 기존 HTTPException (아직 마이그레이션 안 된 코드)
app.add_exception_handler(HTTPException, http_exception_to_problem)

# 이 구조로 점진적 전환 가능 — 한 파일씩 마이그레이션해도 시스템 동작
```

### 7.3 각 Phase별 검증 기준

| Phase | 검증 기준 | 방법 |
|-------|----------|------|
| A | 기존 테스트 100% 통과 | `make test` |
| A | RFC 9457 응답 형식 확인 | health 외 아무 404 엔드포인트 호출 |
| A | Sentry 이벤트 수신 확인 | 개발 환경에서 의도적 500 발생 |
| B | deps.py HTTPException 0개 | `grep -c "HTTPException" app/api/deps.py` |
| B | auth, roadmaps 테스트 통과 | `pytest tests/api/test_auth.py tests/api/test_roadmaps.py` |
| C | 전체 HTTPException 수 50% 감소 | `grep -rc "HTTPException" app/` |
| D | HTTPException raise 20개 미만 (특수 케이스만) | `grep -rc "raise HTTPException" app/` |
| D | Sentry 대시보드 정상 | 에러율, 성능 메트릭 확인 |

---

## 8. 리스크 및 완화 방안

### 8.1 리스크 매트릭스

| 리스크 | 발생 가능성 | 영향도 | 완화 방안 |
|--------|-----------|--------|----------|
| **프론트엔드 호환성 깨짐** | 낮음 | 높음 | `error_code`는 추가 필드, 기존 `detail`/`status` 유지 |
| **마이그레이션 중 에러 응답 불일치** | 중간 | 중간 | 공존 전략으로 점진적 전환, Feature 단위 PR |
| **Sentry 비용 초과** | 낮음 | 낮음 | `before_send`로 4xx 필터링, sample_rate 조절 |
| **structlog 성능 영향** | 매우 낮음 | 낮음 | lazy evaluation, 벤치마크상 동등 |
| **테스트 대량 수정 필요** | 낮음 | 중간 | HTTP 상태 코드 기반 assertion 유지, error_code는 선택적 |
| **Worker 재시도 무한 루프** | 낮음 | 높음 | `max_tries=3` 제한, 재시도 불가 에러 즉시 종료 |

### 8.2 롤백 계획

모든 Phase는 독립 PR로 제출. 문제 발생 시:

1. **Phase A 롤백:** `pyproject.toml` 의존성 제거 + `exceptions.py` 삭제로 즉시 복원
2. **Phase B/C 롤백:** Feature 단위 revert (각 PR 독립)
3. **Sentry 비활성화:** `SENTRY_DSN=""` 환경 변수 제거만으로 즉시 비활성화

---

## 9. 비용 및 영향도 분석

### 9.1 개발 비용

| Phase | 수정 파일 수 | 신규 파일 수 | 난이도 |
|-------|------------|------------|--------|
| A (기반 구축) | 4 | 3 | 중 |
| B (핵심 Feature) | ~12 | 0 | 대 |
| C (나머지 Feature) | ~15 | 0 | 중 |
| D (마무리) | ~5 | 1 | 소 |
| **합계** | **~36** | **4** | - |

### 9.2 신규 의존성

| 패키지 | 버전 | 용도 | 크기 |
|--------|------|------|------|
| `sentry-sdk[fastapi]` | >=2.19.0 | 에러 트래킹 + 성능 | ~2.5MB |
| `structlog` | >=24.4.0 | 구조화 로깅 | ~300KB |

### 9.3 운영 비용

| 항목 | 비용 | 비고 |
|------|------|------|
| Sentry Team | $26/월 (50K 이벤트) | 개발 팀 규모 적합 |
| Sentry Developer (무료) | $0/월 (5K 이벤트) | MVP 단계 적합 |
| structlog | $0 | 오픈소스 |

### 9.4 예상 효과

| 지표 | 현재 | 목표 | 개선율 |
|------|------|------|--------|
| 에러 원인 파악 시간 | 10-30분 (로그 수동 검색) | 1-3분 (Sentry 대시보드) | **~90%** |
| 에러 응답 일관성 | 부분적 (한/영 혼용, title 고정) | 완전 (RFC 9457 + error_code) | **100%** |
| 서비스 레이어 테스트 용이성 | 낮음 (HTTPException 의존) | 높음 (도메인 Exception) | - |
| 프론트엔드 에러 처리 안정성 | 문자열 비교 | error_code enum | **타입 안전** |
| 프로덕션 에러 가시성 | 0% (로그 파일만) | 100% (Sentry 실시간) | **무한대** |

---

## 10. 결론 및 권장사항

### 10.1 결론

Step Zero 백엔드는 **RFC 7807 기반의 에러 응답 구조를 이미 갖추고 있어**, 통합 Exception Handler 도입의 기술적 장벽이 매우 낮다. 현재 125+ HTTPException이 14개 파일에 분산된 상황은 **DDD 기반 Exception 계층 + 글로벌 핸들러**로 체계화할 수 있으며, **Sentry 연동과 structlog 전환**으로 프로덕션 운영 가시성을 확보할 수 있다.

### 10.2 권장 우선순위

```
1순위 (즉시 착수 권장):
  ✅ Phase A — Exception 계층 + Sentry + structlog 기반 구축
  ✅ 이유: 신규 파일 생성 위주, 기존 코드 변경 최소, 즉시 효과 발휘

2순위 (Phase A 머지 후):
  ✅ Phase B — deps.py + auth + roadmaps 마이그레이션
  ✅ 이유: 가장 많이 사용되는 핵심 경로, 효과 극대화

3순위 (안정화 후):
  ⬜ Phase C — 나머지 Feature 마이그레이션
  ⬜ Phase D — 레거시 제거 + 프론트엔드 가이드
```

### 10.3 비채택 권장 사항

| 항목 | 사유 |
|------|------|
| Result/Either 모나드 패턴 | 프로젝트 규모 대비 과도한 복잡성. Exception 기반이 적합 |
| OpenTelemetry | 단일 서비스 구조에서 불필요. Sentry tracing으로 충분 |
| 에러 메시지 i18n | error_code 기반 구조화 후 프론트엔드에서 처리가 적합 |
| 커스텀 에러 미들웨어 | FastAPI 네이티브 exception_handler가 더 효율적 |

---

## 참고 자료

- [RFC 9457 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)
- [RFC 7807 → 9457 마이그레이션 가이드 (codecentric)](https://www.codecentric.de/en/knowledge-hub/blog/charge-your-apis-volume-19-understanding-problem-details-for-http-apis-a-deep-dive-into-rfc-7807-and-rfc-9457)
- [FastAPI Error Handling Best Practices (Better Stack)](https://betterstack.com/community/guides/scaling-python/error-handling-fastapi/)
- [Sentry FastAPI Integration 공식 문서](https://docs.sentry.io/platforms/python/integrations/fastapi/)
- [FastAPI Error Handling: Types, Methods, and Best Practices (Honeybadger)](https://www.honeybadger.io/blog/fastapi-error-handling/)
- [Building Robust Error Handling in FastAPI (DEV Community)](https://dev.to/buffolander/building-robust-error-handling-in-fastapi-and-avoiding-rookie-mistakes-ifg)
- [Problem Details RFC 9457: Doing API Errors Well (Swagger)](https://swagger.io/blog/problem-details-rfc9457-doing-api-errors-well/)
- [Python DDD Exception 패턴 (Architecture Patterns with Python)](https://www.oreilly.com/library/view/architecture-patterns-with/9781492052197/ch01.html)
- [Sentry FastAPI Error & Performance Monitoring](https://sentry.io/for/fastapi/)
