# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-12
- Branch: `develop` (clean)

## Sprint Focus
- 다음 작업 선정 대기

## Current State
- `docs/plans/active/` 비어있음
- Backend: full pytest 451 passed / smoke subset 338 passed / Frontend lint 0 errors
- 개발서버 마이그레이션 완료: `018_add_actionkit_events` 적용됨
- pre-push 훅 최적화 완료 (27초 → 5.6초), done/ 아카이브됨

## Completed (최근)
- **pre-push-optimization**: smoke subset + fail-fast + 문서 반영, 커밋 & 푸시 완료 (`8dc3eb9`)
- **개발서버 마이그레이션** (018_add_actionkit_events) 적용 완료
- **exception-handler-integration (PR #31)**: Phase A~D 전체 완료
- actionkit-analytics-tracking (PR #30): done/ 아카이브 완료

## In Progress
- 없음

## Risks And Blockers
- 배포 시 프로덕션 `.env`에 `ADMIN_EMAILS`, `SENTRY_DSN` 설정 필수

## Next 3 Actions
1. 다음 작업 선정
2. (선택) Sentry DSN 프로덕션 환경 설정
3. (선택) pre-push Phase 3 후보(`client` fixture A/B, SQLite/xdist) 검토

## Test Status
- Frontend lint: 0 errors, 0 warnings
- Backend full pytest: 451 passed, 10 deselected
- Backend smoke subset: 338 passed, 10 deselected
