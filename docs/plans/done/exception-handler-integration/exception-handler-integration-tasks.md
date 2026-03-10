# Tasks: Exception Handler 통합 구현

> **Last Updated:** 2026-03-10

---

## Phase A: 기반 구축

- [x] **A-1** Exception 계층 생성 (`app/core/exceptions.py`) [S]
  - [x] AppException 기본 클래스 (status_code, error_code, detail, type_uri, extra)
  - [x] NotFoundError + 구체 클래스 (Roadmap, Team, Post, AppFile, RoadmapJob, RoadmapStep, RoadmapStepAction, Notification, Announcement, User, Template, ActionKitItem, ChatSession)
  - [x] BusinessRuleError + 구체 클래스 (StepOrderViolation, InvalidStatusTransition, DuplicateResource, SelfReport, AlreadyReported)
  - [x] AuthenticationError + 구체 클래스 (InvalidCredentials, TokenExpired, InvalidToken, TokenReuseDetected)
  - [x] AppPermissionError + 구체 클래스 (AccountRestricted, SuspendedUser, TeamAccessDenied, AdminRequired, ResourceOwnership)
  - [x] AppValidationError
  - [x] ExternalServiceError + 구체 클래스 (DatabaseUnavailable, RagServiceUnavailable, AppLawApiError)
- [x] **A-2** Sentry SDK 연동 — GlitchTip 호환 [S]
  - [x] `pyproject.toml`에 `sentry-sdk[fastapi]>=2.19.0` 추가
  - [x] `app/core/sentry.py` 생성 (setup_sentry, _before_send, set_user_context)
  - [x] `app/core/config.py`에 `SENTRY_DSN: str = ""` 추가
  - [x] `.env.example` 파일에 SENTRY_DSN, LOG_JSON_OUTPUT 기본값
  - [x] `app/main.py`에서 `setup_sentry()` 호출
  - [x] GlitchTip 미지원 옵션 제외 (profiles_sample_rate, enable_logs)
  - [x] _before_send: AppException 4xx 필터 + HTTPException 4xx 필터 (마이그레이션용)
- [x] **A-3** structlog 전환 [M]
  - [x] `pyproject.toml`에 `structlog>=24.4.0` 추가
  - [x] `app/core/logging.py` 전면 교체
  - [x] shared_processors: contextvars, log_level, logger_name, TimeStamper, StackInfo, Unicode
  - [x] 개발: ConsoleRenderer / 프로덕션: JSONRenderer
  - [x] `app/core/config.py`에 `LOG_JSON_OUTPUT: bool = True` 추가
  - [x] get_logger() 함수 유지 (structlog.get_logger 래핑)
  - [x] uvicorn.access, sqlalchemy.engine, httpx 레벨 제어
- [x] **A-4** 요청 컨텍스트 미들웨어 [S]
  - [x] `app/middleware/__init__.py` 생성
  - [x] `app/middleware/logging.py` — RequestContextMiddleware (순수 ASGI)
  - [x] request_id 생성 (X-Request-ID 헤더 우선)
  - [x] structlog contextvars 바인딩 (request_id, method, path)
  - [x] Sentry request_id 태깅
  - [x] 응답 헤더 X-Request-ID 주입
  - [x] `app/main.py` 기존 log_request_response 미들웨어 교체
- [x] **A-5** RFC 9457 업그레이드 + 글로벌 핸들러 체인 [M]
  - [x] `app/api/problem.py`에 HTTP_STATUS_TITLES 딕셔너리 추가
  - [x] `app_exception_to_problem()` 핸들러 추가
  - [x] error_code, timestamp, extensions 필드 추가
  - [x] `app/main.py` 핸들러 등록 순서 재구성 (AppException, RequestValidation, HTTPException, global)
  - [x] global_exception_handler에 sentry_sdk.capture_exception() 추가
- [x] **A-6** Phase A 테스트 [S]
  - [x] Exception 계층 단위 테스트 (35건)
  - [x] RFC 9457 응답 변환 통합 테스트
  - [x] Sentry _before_send 필터링 테스트
  - [x] `make test` 전체 통과 확인 (471 passed)

---

## Phase B: 핵심 Feature 마이그레이션

- [x] **B-1** deps.py 전환 [M]
  - [x] `get_current_user()` JWT 실패 → InvalidCredentialsError
  - [x] `get_current_user()` inactive → AccountRestrictedError("inactive")
  - [x] `get_current_team()` invalid UUID → AppValidationError
  - [x] `get_current_team()` no access → TeamAccessDeniedError
  - [x] `get_current_team()` no membership → TeamAccessDeniedError
  - [x] `get_current_user_or_guest()` token expired → TokenExpiredError
  - [x] `require_platform_admin()` → AdminRequiredError
  - [x] 검증: `grep -c "HTTPException" app/api/deps.py` = 0
- [x] **B-2** Auth Feature 전환 [M]
  - [x] `auth_service.py:_raise_suspension_error()` → AccountRestrictedError
  - [x] `auth/router.py` login 401 → InvalidCredentialsError
  - [x] `auth/router.py` login 503 → DatabaseUnavailableError
  - [x] `auth/router.py` Google 401 → InvalidTokenError
  - [x] `auth/router.py` Google 503 → ExternalServiceError("Google OAuth")
  - [x] `auth/router.py` refresh reuse → TokenReuseDetectedError
  - [x] 로그인 성공 시 set_user_context() 호출
- [x] **B-3** Roadmaps Feature 전환 [M]
  - [x] InvalidRoadmapStepStatusError → 3개 구체 Exception 분리
  - [x] roadmap_progress_service.py 전체 전환
  - [x] roadmaps/get.py HTTPException 제거 → 도메인 Exception
  - [x] roadmaps/jobs.py HTTPException → AppValidationError, RoadmapJobNotFoundError
  - [x] 테스트 assertion 전환 (2곳: detail → error_code)
- [x] **B-4** ActionKit Feature 전환 [S]
  - [x] files.py 404 → AppFileNotFoundError
  - [x] files.py 400 → AppValidationError
  - [x] service.py ValueError 유지 (API layer에서 catch)
- [x] **B-5** Worker 에러 처리 강화 [M]
  - [x] process_roadmap_job() try/except 추가
  - [x] UUID 파싱 실패 처리
  - [x] structlog 컨텍스트 바인딩
  - [x] Sentry scope 태깅
  - [x] 실패 시 job.mark_failed() 보상 로직
  - [x] WorkerSettings: max_tries=3, retry_delay=30, job_timeout=300
- [x] **B-6** Phase B 통합 테스트 [S]
  - [x] `make test` 전체 통과 (471 passed)
  - [x] deps.py HTTPException 0개 확인

---

## Phase C: 나머지 Feature 마이그레이션

- [x] **C-1** Growth Club Feature 전환 [M]
  - [x] posts.py: HTTPException 전환 (413 2개 유지)
  - [x] comments.py: HTTPException 전환 (완전 제거)
  - [x] post_service.py: HTTPException 전환 (완전 제거)
- [x] **C-2** Chat Feature 전환 + SSE 에러 정렬 [M]
  - [x] session_service.py HTTPException → ChatSessionNotFoundError, ResourceOwnershipError
  - [x] chat_service.py SSE error 코드 정렬 (error_code 필드)
  - [x] SSE except 블록에 sentry_sdk.capture_exception()
- [x] **C-3** Ops Feature 전환 [L]
  - [x] ops/roadmap_templates.py — HTTPException 완전 제거
  - [x] ops/actionkit.py — HTTPException 완전 제거
  - [x] ops/growth_club.py — HTTPException 완전 제거
  - [x] ops/announcements.py — HTTPException 완전 제거
  - [x] ops/users.py — HTTPException 완전 제거
  - [x] ops/files.py — HTTPException 완전 제거
- [x] **C-4** 기타 Feature 전환 [S]
  - [x] notifications.py — HTTPException 완전 제거
  - [x] storage.py — HTTPException 완전 제거
  - [x] announcements.py 사용자 측 — HTTPException 완전 제거
  - [x] actionkit/detail.py — HTTPException 완전 제거
  - [x] rag/router.py — HTTPException 완전 제거
- [x] **C-5** RAG/Chat 서비스 전환 [S]
  - [x] rag_service.py bare Exception → RagServiceUnavailableError/ExternalServiceError
  - [x] chat_service.py HTTPException catch → AppException catch
- [x] **C-6** Phase C 통합 테스트 [S]
  - [x] `make test` 전체 통과 (471 passed)
  - [x] `raise HTTPException` 잔여 4개 (목표 < 5)

---

## Phase D: 마무리 및 검증

- [x] **D-1** 레거시 Exception 제거 [S]
  - [x] InvalidRoadmapStepStatusError 클래스 삭제
  - [ ] LawApiError — scripts/에서 사용 중이므로 유지
- [x] **D-2** 프론트엔드 에러 파싱 수정 [M]
  - [x] LoginForm.tsx: `data?.code` → `data?.error_code` + extensions 패턴
  - [x] SocialAuthModal.tsx: `data?.code` → `data?.error_code` (3곳)
  - [x] SocialAuthModal.tsx: `data.status/reason` → `extensions?.status/reason` (3곳)
  - [x] SocialAuthModal.tsx: detail 문자열 비교 → error_code 비교
  - [x] `pnpm lint` 통과
- [x] **D-3** Sentry 정리 [S]
  - [ ] _before_send HTTPException 4xx 필터링 — 4개 HTTPException 남아있으므로 유지
- [x] **D-4** 전체 검증 [M]
  - [x] `make test` 전체 통과 (471 passed, 10 skipped)
  - [x] `pnpm lint` 통과
  - [x] `raise HTTPException` 잔여 4개 (< 5 목표 달성)
  - [x] RFC 9457 응답 형식 구현 완료

---

## PR 전략

| Phase | 브랜치 | PR 대상 | 상태 |
|-------|--------|---------|------|
| A~D | `feature/exception-handler-phase-a` | `develop` | 구현 완료 |

전체 Phase A~D를 단일 PR로 제출 (기존 테스트 영향 없는 점진적 전환).

## 최종 결과

| 지표 | 현재 | 목표 | 달성 |
|------|------|------|------|
| HTTPException raise 수 | 4 | < 5 | ✅ |
| 커스텀 Exception 클래스 | 30+ | 30+ | ✅ |
| 에러 트래킹 (Sentry SDK) | 설치 완료 | DSN 설정 시 즉시 활성화 | ✅ |
| 에러 응답 일관성 | RFC 9457 | RFC 9457 완전 준수 | ✅ |
| 구조화 로깅 (structlog) | JSON/컬러 | 전환 완료 | ✅ |
