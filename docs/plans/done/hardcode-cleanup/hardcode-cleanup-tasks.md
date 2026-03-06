# TASKS: 목업 데이터 및 하드코딩 제거

## Phase A — 보안 및 인증 정비

- [x] A-1: `user_repository.py` — `dojyu1928@gmail.com` 제거, `ADMIN_EMAILS` 환경변수 도입
  - `app/core/config.py` — `ADMIN_EMAILS` 필드 + `admin_email_set` 프로퍼티
  - `app/repositories/user_repository.py` — `create_google_user()` 수정
  - `.env`, `.env.example` — `ADMIN_EMAILS=` 추가
  - 테스트 업데이트

- [x] A-2: `auth/router.py` — Mock 인증 프로덕션 환경 차단
  - `app/core/config.py` — `validate_security()`에 `ENABLE_SOCIAL_MOCK` 프로덕션 차단
  - `app/api/v1/auth/router.py` — Google 인증 fallback에 ENVIRONMENT 이중 검증

## Phase B — 가짜 데이터 제거

- [x] B-1: `stats-dashboard.tsx` — 하드코딩 통계 제거, summary API 데이터로 교체
  - `POPULAR_DOCS`, `SEARCH_KEYWORDS` 상수 제거
  - 하드코딩 KPI 카드 → summary 기반 실데이터 카드
  - `api.ts` 타입 불일치 수정 (`pending_reviews` → 실제 백엔드 필드)

- [x] B-2: `growth_club/service.py` — `get_queue_summary()` 실제 DB 쿼리 구현
  - `def` → `async def`, `session` 파라미터 추가
  - `report_count > 0 AND is_blinded = False` 쿼리
  - 호출부 수정 (session 전달, await 추가)

- [x] B-3: `roadmap-constants.ts` — `MILESTONE_INSIGHTS` 가짜 통계 수치 제거
  - "87%", "평균보다 빠른" 등 비교 표현 삭제
  - 동기부여 메시지만 유지

## Phase C — 프론트엔드 설정 정리

- [x] C-1: localhost fallback URL 공통 유틸리티 추출
  - `src/lib/env.ts` 신규 생성 (`getApiBaseUrl`, `getApiHost`)
  - `api-client.ts`, `sse.ts`, `url.ts`, `ActionKitLibraryView.tsx` 4곳 import 교체

- [x] C-2: `Sidebar.tsx` — DiceBear 외부 URL 제거, AvatarFallback만 사용

## Phase D — 코드 품질

- [x] D-1: `growth_club.py:155,259` + `audit_log.py:18` — `datetime.now()` → `utc_now()`
- [x] D-2: `alembic.ini:4` — DB URL placeholder로 교체
- [x] D-3: `config.py:17` — CORS `localhost:5173` 제거
- [x] D-4: `ColdStartHero.tsx` — `SUGGESTED_TAGS` → `HERO_SUGGESTIONS` import로 중복 제거
