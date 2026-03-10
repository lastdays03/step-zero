# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-10
- Branch: `develop` (PR #31 머지, feature 브랜치 삭제)

## Sprint Focus
- exception-handler-integration 완료 → 다음 작업 선정 대기

## Current State
- `docs/plans/active/` 비어있음
- Backend: 486 passed (50건 추가), Frontend: lint 0 errors
- 개발서버 마이그레이션 대기: `018_add_actionkit_events`

## Completed (최근)
- **exception-handler-integration (PR #31)**: Phase A~D 전체 완료
  - DDD 기반 Exception 계층 (30+ 클래스)
  - RFC 9457 에러 응답 (error_code, timestamp, extensions)
  - Sentry/GlitchTip 연동 + 4xx 필터링
  - structlog 구조화 로깅
  - ASGI RequestContextMiddleware
  - 21개 파일 HTTPException → 도메인 Exception 마이그레이션
  - 프론트엔드 에러 파싱 수정
  - pre-push 훅 병렬 실행 개선
- actionkit-analytics-tracking (PR #30): done/ 아카이브 완료
- project-audit-fixes (PR #29): done/ 아카이브 완료

## In Progress
- 없음

## Risks And Blockers
- 배포 시 프로덕션 `.env`에 `ADMIN_EMAILS`, `SENTRY_DSN` 설정 필수
- **개발서버 마이그레이션 미적용**: `docker compose exec app-backend uv run alembic upgrade head`

## Next 3 Actions
1. 개발서버 마이그레이션 적용 (018_add_actionkit_events)
2. 다음 작업 선정
3. (선택) Sentry DSN 프로덕션 환경 설정

## Test Status
- Frontend lint: 0 errors, 0 warnings
- Backend pytest: 486 passed, 10 skipped
