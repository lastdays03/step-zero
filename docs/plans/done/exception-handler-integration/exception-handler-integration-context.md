# Context: Exception Handler 통합 구현

> **Last Updated:** 2026-03-10

---

## 핵심 파일 맵

### 신규 생성 파일 (Phase A)

| 파일 | 역할 |
|------|------|
| `app/core/exceptions.py` | DDD 기반 도메인 Exception 계층 |
| `app/core/sentry.py` | Sentry SDK 초기화 + 필터링 + 사용자 컨텍스트 |
| `app/middleware/logging.py` | 순수 ASGI 요청 컨텍스트 미들웨어 (request_id) |

### 수정 파일 (Phase A)

| 파일 | 현재 라인 | 수정 내용 |
|------|----------|----------|
| `app/core/logging.py` | 33줄 | structlog 전면 교체 |
| `app/core/config.py` | 152줄 | SENTRY_DSN, LOG_JSON_OUTPUT 추가 |
| `app/api/problem.py` | 68줄 | RFC 9457 + app_exception_to_problem 추가 |
| `app/main.py` | 158줄 | 핸들러 체인 재구성, 미들웨어 교체, Sentry init |
| `pyproject.toml` | 88줄 | sentry-sdk, structlog 의존성 추가 |
| `.env` | - | SENTRY_DSN= 기본값 추가 |

### 마이그레이션 대상 파일 (Phase B~D)

**Phase B — 핵심 Feature (12파일)**

| 파일 | HTTPException 수 | 변환 대상 |
|------|-----------------|----------|
| `app/api/deps.py` | 7 | AuthenticationError, AccountRestrictedError, TeamAccessDeniedError, AdminRequiredError 등 |
| `app/features/auth/application/auth_service.py` | 1 (서비스 레이어 위반) | AccountRestrictedError |
| `app/api/v1/auth/router.py` | 6 | InvalidCredentialsError, InvalidTokenError, TokenReuseDetectedError, ExternalServiceError 등 |
| `app/features/roadmaps/application/roadmap_progress_service.py` | - (ValueError 기반) | StepOrderViolationError, InvalidStatusTransitionError, NotFoundError 분리 |
| `app/api/v1/roadmaps/get.py` | ~5 | RoadmapNotFoundError |
| `app/api/v1/roadmaps/jobs.py` | ~3 | AppValidationError |
| `app/api/v1/actionkit/files.py` | ~3 | AppFileNotFoundError, AppValidationError |
| `app/features/actionkit/application/service.py` | - (ValueError) | NotFoundError |
| `app/workers/roadmap_worker.py` | 0 (에러 처리 부재) | try/except + Sentry + structlog 추가 |

**Phase C — 나머지 Feature (20파일)**

| 파일 | HTTPException 수 | 비고 |
|------|-----------------|------|
| `app/api/v1/growth_club/posts.py` | ~10 | PostNotFoundError, SuspendedUserError, SelfReportError 등 |
| `app/api/v1/growth_club/comments.py` | ~6 | ResourceOwnershipError, SelfReportError 등 |
| `app/features/growth_club/application/post_service.py` | 2 (서비스 레이어 위반) | PostNotFoundError, ResourceOwnershipError |
| `app/features/rag/application/chat_service.py` | - | SSE error 코드 정렬 + Sentry 캡처 |
| `app/features/rag/application/chat_session_service.py` | 2 | NotFoundError, ResourceOwnershipError |
| `app/api/v1/ops/roadmap_templates.py` | **20** | 최대 파일 |
| `app/api/v1/ops/actionkit.py` | 15 | |
| `app/api/v1/ops/growth_club.py` | 8 | |
| `app/api/v1/ops/announcements.py` | 2 | |
| `app/api/v1/ops/users.py` | 1 | |
| `app/api/v1/ops/files.py` | 1 | |
| `app/api/v1/notifications.py` | 2 + SSE 에러 보완 | |
| `app/api/v1/storage.py` | 2 | |
| `app/api/v1/announcements.py` | 1 | |
| `app/services/law_api_client.py` | - | LawApiError → AppLawApiError |

**Phase D — 프론트엔드 (4곳)**

| 파일 | 수정 내용 |
|------|----------|
| `src/features/auth/LoginForm.tsx:29` | `data?.code` → `data?.error_code` |
| `src/features/auth/SocialAuthModal.tsx:67,97` | `data?.code` → `data?.error_code` |
| `src/features/auth/SocialAuthModal.tsx:69-71,99-101` | `data.status/reason` → `data.extensions?.status/reason` |
| `src/features/auth/SocialAuthModal.tsx:83` | `data?.detail === '...'` → `data?.error_code === 'DATABASE_UNAVAILABLE'` |

---

## 의존성 추가

```toml
# pyproject.toml
sentry-sdk = { version = ">=2.19.0", extras = ["fastapi"] }
structlog = ">=24.4.0"
```

## 환경 변수 추가

```bash
# .env
SENTRY_DSN=                    # 빈 문자열이면 비활성화
LOG_JSON_OUTPUT=false           # 개발: false (컬러), 프로덕션: true (JSON)
```

## 에러 트래킹: GlitchTip (외부 모니터링 서버)

- **GlitchTip**: Sentry 호환 오픈소스 에러 트래킹 (셀프호스팅)
- **외부 서버에 별도 구축** — 이 프로젝트의 docker-compose에 포함하지 않음
- `sentry-sdk`가 Sentry/GlitchTip 모두 지원 — DSN 주소만 다름
- GlitchTip 미지원 기능: `profiles_sample_rate`, `enable_logs` → 설정에서 제외
- DSN 형식: `https://key@glitchtip.your-domain.com/1`
- 서버 미준비 시 `SENTRY_DSN=""` → 완전 비활성화 (앱 영향 0)

---

## 확정된 설계 결정

| 결정 | 근거 |
|------|------|
| Result/Either 모나드 패턴 **비채택** | 프로젝트 규모 대비 과도한 복잡성 |
| OpenTelemetry **비채택** | 단일 서비스 구조, Sentry tracing으로 충분 |
| i18n **연기** | error_code 기반 구조화 후 FE에서 처리 |
| BaseHTTPMiddleware **미사용** | SSE 스트리밍 호환 문제, 순수 ASGI 미들웨어 채택 |
| SSE 에러는 글로벌 핸들러 대상 아님 | 이미 200 응답 시작 후이므로 각 SSE except 블록에서 직접 처리 |
| 기존 HTTPException 핸들러 유지 (마이그레이션 기간) | 점진적 전환 지원, Phase D에서 제거 검토 |

---

## 공존 전략 (마이그레이션 기간)

Phase A 완료 후 ~ Phase D까지:
```python
# 핸들러 우선순위
1. AppException → app_exception_to_problem  # 마이그레이션된 코드
2. HTTPException → http_exception_to_problem  # 아직 미전환 코드
```

GlitchTip `_before_send`에서 두 타입 모두 4xx 필터링:
- AppException: `exc.status_code < 500` → 필터
- HTTPException: `exc.status_code < 500` → 필터 (Phase D에서 제거)

---

## 테스트 영향

- 기존 테스트(436건): HTTP 상태 코드 기반 assertion → **수정 불요**
- detail 문자열 비교 assertion (2곳): error_code 기반으로 전환 필요
  - `test_roadmap_task_status.py:92`
  - `test_roadmap_jobs_validate.py:136`
- 신규 테스트: Exception 계층 + RFC 9457 변환 + Sentry 필터링

---

## 프론트엔드 Breaking Change

**ACCOUNT_RESTRICTED 응답 구조 변경:**
```json
// 현재 (RFC 7807 위반 — status 필드 충돌)
{ "status": "suspended", "code": "ACCOUNT_RESTRICTED", "reason": "..." }

// RFC 9457 전환 후
{ "status": 403, "error_code": "ACCOUNT_RESTRICTED", "extensions": { "status": "suspended", "reason": "..." } }
```

**에러 메시지 문자열 비교 → error_code:**
```typescript
// 현재: data?.detail === 'Authentication backend unavailable'
// 전환: data?.error_code === 'DATABASE_UNAVAILABLE'
```

Phase D에서 백엔드-프론트엔드 동시 수정 필수.
