# PLAN: Exception Handler 통합 구현

> **Last Updated:** 2026-03-10
> **기반 보고서:** `docs/plans/reports/REPORT-exception-handler-integration.md`
> **범위:** 에러 처리 체계 전면 개선 — 커스텀 Exception 계층, RFC 9457, GlitchTip(Sentry 호환), 구조화 로깅

---

## Executive Summary

Step Zero 백엔드의 에러 처리를 체계화한다. 117개 HTTPException을 DDD 기반 도메인 Exception 트리로 전환하고, RFC 7807 → 9457 업그레이드, Sentry SDK 연동, structlog 기반 구조화 로깅을 도입한다.

**핵심 수치:**
- HTTPException 117개 (21파일) → 도메인 Exception 자동 변환
- 커스텀 Exception 2개 → 30+ 계층 구조
- 에러 트래킹 0% → 100% 가시성 (GlitchTip — Sentry SDK 호환)
- 텍스트 로깅 → JSON 구조화 로깅

---

## Phase A: 기반 구축 (난이도: M)

### 목표
기존 동작을 깨뜨리지 않으면서 Exception 계층, Sentry, structlog 인프라를 설치한다.

### 작업 항목

**A-1. Exception 계층 생성** (S)
- `app/core/exceptions.py` 신규 생성
- `AppException` 기본 클래스 + 6개 중간 클래스 + 20+ 구체 클래스
- 계층: AppException → NotFoundError / BusinessRuleError / AuthenticationError / AppPermissionError / AppValidationError / ExternalServiceError
- 수용 기준: import 가능, 기존 테스트 영향 없음

**A-2. Sentry SDK 연동 (GlitchTip 호환)** (S)
- `pyproject.toml`에 `sentry-sdk[fastapi]>=2.19.0` 추가
- `app/core/sentry.py` 신규 생성 (setup_sentry, _before_send, set_user_context)
- `app/core/config.py`에 `SENTRY_DSN: str = ""` 추가
- `.env` 파일에 `SENTRY_DSN=` 기본값 추가
- `app/main.py`에서 `setup_sentry(settings)` 호출
- GlitchTip 호환: `sentry-sdk`가 Sentry/GlitchTip 모두 지원 — DSN만 변경
- GlitchTip 미지원 옵션 제외: `profiles_sample_rate`, `enable_logs` 비활성화
- 수용 기준: DSN 빈 문자열이면 완전 비활성화, 외부 GlitchTip 서버 DSN 설정 시 즉시 활성화

**A-3. structlog 전환** (M)
- `pyproject.toml`에 `structlog>=24.4.0` 추가
- `app/core/logging.py` 전면 교체 (structlog 기반)
- 개발 환경: ConsoleRenderer (컬러), 프로덕션: JSONRenderer
- `app/core/config.py`에 `LOG_JSON_OUTPUT: bool = True` 추가
- uvicorn 로깅 통합 (log_config=None 또는 --log-config="")
- 수용 기준: 기존 `get_logger()` 호출 호환, JSON/컬러 출력 전환 가능

**A-4. 요청 컨텍스트 미들웨어** (S)
- `app/middleware/logging.py` 신규 생성 (순수 ASGI 미들웨어)
- request_id 생성/바인딩 (X-Request-ID 헤더 존재 시 사용)
- structlog contextvars에 request_id, method, path 바인딩
- Sentry에 request_id 태깅
- 응답 헤더에 X-Request-ID 주입
- `app/main.py`의 기존 `log_request_response` 미들웨어 교체
- 수용 기준: SSE 스트리밍과 호환, 모든 요청에 request_id 부여

**A-5. RFC 9457 업그레이드 + 글로벌 핸들러 체인** (M)
- `app/api/problem.py` 개선:
  - `HTTP_STATUS_TITLES` 딕셔너리 추가 (동적 title)
  - `app_exception_to_problem()` 핸들러 추가 (AppException → RFC 9457)
  - `error_code`, `timestamp`, `extensions` 필드 추가
  - 기존 `http_exception_to_problem()` 유지 (하위 호환)
- `app/main.py` 핸들러 등록 순서 재구성:
  1. AppException → app_exception_to_problem (신규)
  2. RequestValidationError → validation_exception_to_problem (기존)
  3. RateLimitExceeded → rate_limit_to_problem (기존)
  4. HTTPException → http_exception_to_problem (기존, 마이그레이션 기간 유지)
  5. Exception → global_exception_handler (기존, Sentry 캡처 추가)
- 수용 기준: 기존 테스트 100% 통과, AppException raise 시 RFC 9457 응답 반환

**A-6. 테스트** (S)
- Exception 계층 단위 테스트 (status_code, error_code, detail 검증)
- AppException → RFC 9457 응답 변환 통합 테스트
- Sentry _before_send 필터링 테스트 (4xx 필터, 5xx 통과)
- 수용 기준: `make test` 전체 통과 (기존 436 + 신규)

---

## Phase B: 핵심 Feature 마이그레이션 (난이도: L)

### 목표
가장 많이 사용되는 핵심 경로(deps, auth, roadmaps, actionkit, worker)를 도메인 Exception으로 전환한다.

### 작업 항목

**B-1. deps.py 전환** (M)
- 7개 HTTPException → 도메인 Exception 교체
- `get_current_user()`: AuthenticationError, AccountRestrictedError
- `get_current_team()`: AppValidationError, TeamAccessDeniedError
- `require_platform_admin()`: AdminRequiredError
- 수용 기준: `grep -c "HTTPException" app/api/deps.py` = 0

**B-2. Auth Feature 전환** (M)
- `auth_service.py`: `_raise_suspension_error()` → AccountRestrictedError raise
- `auth/router.py`: 6개 HTTPException → InvalidCredentialsError, InvalidTokenError, TokenReuseDetectedError, ExternalServiceError, DatabaseUnavailableError
- Sentry set_user_context() 호출 추가 (로그인 성공 시)
- 수용 기준: `pytest tests/api/test_auth.py` 통과

**B-3. Roadmaps Feature 전환** (M)
- `InvalidRoadmapStepStatusError` → StepOrderViolationError, InvalidStatusTransitionError, NotFoundError 분리
- `roadmap_progress_service.py`: 문자열 메시지 기반 → 타입 기반 분기
- `roadmaps/get.py`, `roadmaps/jobs.py`: HTTPException → 도메인 Exception
- 테스트 assertion 전환 (detail 문자열 → error_code, 2곳)
- 수용 기준: `pytest tests/api/test_roadmaps.py tests/api/test_roadmap_*.py` 통과

**B-4. ActionKit Feature 전환** (S)
- `files.py`: HTTPException → AppFileNotFoundError, AppValidationError
- `service.py`: ValueError → NotFoundError
- 수용 기준: `pytest tests/api/test_actionkit*.py` 통과

**B-5. Worker 에러 처리 강화** (M)
- `process_roadmap_job()`: try/except 추가 (UUID 파싱, 세션 에러, 도메인 에러)
- structlog 컨텍스트 바인딩 (job_id, worker)
- Sentry scope 태깅 (job_id)
- 실패 시 새 세션으로 job.mark_failed() 보상 로직
- ARQ WorkerSettings: max_tries=3, retry_delay=30, job_timeout=300
- 수용 기준: 의도적 에러 발생 시 Job FAILED 상태 전환 + Sentry 이벤트

---

## Phase C: 나머지 Feature 마이그레이션 (난이도: L)

### 목표
전체 코드베이스의 HTTPException을 도메인 Exception으로 전환한다. ops 라우터 47개 포함.

### 작업 항목

**C-1. Growth Club Feature 전환** (M)
- `posts.py`: PostNotFoundError, SuspendedUserError, SelfReportError, AlreadyReportedError, ResourceOwnershipError
- `comments.py`: 동일 패턴 적용
- `post_service.py`: HTTPException → 도메인 Exception
- 수용 기준: `pytest tests/api/test_growth_club*.py` 통과

**C-2. Chat Feature 전환 + SSE 에러 정렬** (M)
- `session_service.py`: HTTPException → NotFoundError, ResourceOwnershipError
- `chat_service.py`: SSE error 이벤트 코드를 Exception error_code와 정렬
- SSE except 블록에 `sentry_sdk.capture_exception()` 명시 호출
- 수용 기준: SSE 에러 이벤트에 `error_code` 필드 포함

**C-3. Ops Feature 전환** (L — 47개 HTTPException)
- `ops/roadmap_templates.py` (20개): NotFoundError, InvalidStatusTransitionError, AdminRequiredError
- `ops/actionkit.py` (15개): NotFoundError, AppValidationError
- `ops/growth_club.py` (8개): PostNotFoundError, BusinessRuleError
- `ops/announcements.py` (2개): NotFoundError
- `ops/users.py` (1개): NotFoundError
- `ops/files.py` (1개): AppFileNotFoundError
- 수용 기준: `pytest tests/api/test_ops*.py` 통과

**C-4. 기타 Feature 전환** (S)
- `notifications.py` (2개): NotFoundError + SSE 에러 미처리 보완
- `storage.py` (2개): AppFileNotFoundError, AppValidationError
- `announcements.py` 사용자 측 (1개): NotFoundError
- `dashboard/` 관련: 해당 시 전환
- `app/services/law_api_client.py`: LawApiError → AppLawApiError 전환
- 수용 기준: `grep -rc "raise HTTPException" app/` < 20

**C-5. RAG/Chat 서비스 전환** (S)
- `rag_service.py`: bare Exception catch → ExternalServiceError
- `chat_service.py`: HTTPException catch → 도메인 Exception
- 수용 기준: RAG 에러 시 RagServiceUnavailableError raise

---

## Phase D: 마무리 및 검증 (난이도: M)

### 목표
레거시 제거, 프론트엔드 동기화, Sentry 운영 설정 완료.

### 작업 항목

**D-1. 레거시 Exception 제거** (S)
- `LawApiError` 클래스 삭제 (AppLawApiError로 대체됨)
- `InvalidRoadmapStepStatusError` 클래스 삭제 (분리된 Exception들로 대체됨)
- 수용 기준: import 참조 0건

**D-2. 프론트엔드 에러 파싱 수정** (M)
- `LoginForm.tsx:29`: `data?.code` → `data?.error_code`
- `SocialAuthModal.tsx:67,97`: `data?.code` → `data?.error_code`
- `SocialAuthModal.tsx:69-71,99-101`: `data.status/reason` → `data.extensions?.status/reason`
- `SocialAuthModal.tsx:83`: `data?.detail === '...'` → `data?.error_code === 'DATABASE_UNAVAILABLE'`
- `ProblemDetail` TypeScript 인터페이스 추가 (`api-errors.ts`)
- 수용 기준: `pnpm lint` 통과, 에러 응답 파싱 정상 동작

**D-3. Sentry 정리 + 운영 설정** (S)
- `_before_send`에서 HTTPException 4xx 필터링 라인 제거
- Sentry 알림 규칙 설정 문서화
- 수용 기준: HTTPException 필터 코드 없음

**D-4. 전체 검증** (M)
- 백엔드: `make test` 전체 통과
- 프론트엔드: `pnpm lint && pnpm build` 통과
- `grep -rc "raise HTTPException" app/` < 5 (SSE 등 특수 케이스만)
- RFC 9457 응답 형식 수동 검증 (error_code, timestamp, extensions)
- 수용 기준: 모든 품질 게이트 통과, HTTPException 5개 미만

---

## 리스크 및 완화

| 리스크 | 발생 가능성 | 영향도 | 완화 방안 |
|--------|-----------|--------|----------|
| FE 호환성 깨짐 | 낮음 | 높음 | error_code는 추가 필드, 기존 detail/status 유지. Phase D에서 FE 동시 수정 |
| 마이그레이션 중 응답 불일치 | 중간 | 중간 | 공존 전략 (AppException + HTTPException 핸들러 병행) |
| GlitchTip 서버 다운 | 낮음 | 낮음 | SDK는 전송 실패 시 자동 무시, 앱 영향 없음 |
| Worker 재시도 무한 루프 | 낮음 | 높음 | max_tries=3 제한, 재시도 불가 에러 즉시 종료 |
| 테스트 대량 수정 | 낮음 | 중간 | HTTP 상태 코드 assertion 유지, error_code는 선택적 추가 |

## 롤백 계획

- **Phase A**: pyproject.toml 의존성 제거 + 신규 파일 삭제로 즉시 복원
- **Phase B/C**: Feature 단위 revert (각 PR 독립)
- **에러 트래킹 비활성화**: `SENTRY_DSN=""` 환경 변수만 제거

## 성공 지표

| 지표 | 현재 | 목표 |
|------|------|------|
| HTTPException raise 수 | 117 | < 5 |
| 커스텀 Exception 클래스 | 2 | 30+ |
| 에러 트래킹 가시성 (GlitchTip) | 0% | 100% |
| 에러 응답 일관성 | 부분적 | RFC 9457 완전 준수 |
| 에러 원인 파악 시간 | 10-30분 | 1-3분 |
