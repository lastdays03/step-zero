# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-12
- Branch: `develop` (clean)

## Sprint Focus
- 다음 작업 선정 대기

## Current State
- `docs/plans/active/` 비어있음 — 모든 진행 중 계획 완료
- Backend: full pytest 451 passed / smoke subset 338 passed / Frontend lint 0 errors
- 개발서버 마이그레이션 완료: `018_add_actionkit_events` 적용됨
- pre-push 훅 최적화 완료 (27초 → 5.6초)
- 브라우저 디버깅 표준은 Playwright MCP로 통일됨

## Completed (최근)
- **playwright-mcp-integration**: Phase 0~3 전체 완료, done/ 아카이브 (`75d1409`)
  - data-testid 11개 컴포넌트 반영, snippet 3종, Web Vitals 베이스라인 5페이지 측정
  - public(login) + authenticated(social-mock → dashboard) MCP 시나리오 재현 성공
- **pre-push-optimization**: smoke subset + fail-fast, done/ 아카이브 (`8dc3eb9`)
- **exception-handler-integration (PR #31)**: Phase A~D 전체 완료

## In Progress
- 없음

## Risks And Blockers
- 배포 시 프로덕션 `.env`에 `ADMIN_EMAILS`, `SENTRY_DSN` 설정 필수
- `/growth-club`: TTFB 838ms, FCP 888ms — 다른 페이지 대비 현저히 느림 (최적화 후보)

## Next 3 Actions
1. 다음 작업 선정 (기능 개발 / 성능 최적화 / 인프라)
2. (선택) `/growth-club` 성능 개선 (이미지 404, SSR 최적화)
3. (선택) Sentry DSN 프로덕션 환경 설정

## Test Status
- Frontend lint: 0 errors, 0 warnings
- Backend full pytest: 451 passed, 10 deselected
- Backend smoke subset: 338 passed, 10 deselected
