# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-12
- Branch: `develop` (dirty)

## Sprint Focus
- Playwright MCP 통합 디버깅 인프라 정착

## Current State
- `docs/plans/active/playwright-mcp-integration` 진행 중 (Phase 0~2 완료, Phase 3 대기)
- `scripts/playwright/` README + snippet 3종 추가 완료 (`public-only` / `credentials` / `social-mock`)
- login/layout/nav/roadmap/chat 핵심 프로덕션 컴포넌트에 `data-testid` 반영 완료
- Backend: full pytest 451 passed / smoke subset 338 passed / Frontend lint 0 errors
- 개발서버 마이그레이션 완료: `018_add_actionkit_events` 적용됨
- pre-push 훅 최적화 완료 (27초 → 5.6초), done/ 아카이브됨
- 브라우저 디버깅 표준은 Playwright MCP로 통일됨

## Completed (최근)
- **playwright-mcp-integration**: Phase 0~2 구현 완료 (`data-testid` + snippet source + README + frontend lint)
- **pre-push-optimization**: smoke subset + fail-fast + 문서 반영, 커밋 & 푸시 완료 (`8dc3eb9`)
- **browser-debugging-standard**: Playwright MCP를 기본 브라우저 디버깅 도구로 전환, CLAUDE/보고서/결정 문서 반영
- **개발서버 마이그레이션** (018_add_actionkit_events) 적용 완료
- **exception-handler-integration (PR #31)**: Phase A~D 전체 완료

## In Progress
- `playwright-mcp-integration`: Playwright MCP 실측 실행/성능 베이스라인(Phase 3) 대기

## Risks And Blockers
- 배포 시 프로덕션 `.env`에 `ADMIN_EMAILS`, `SENTRY_DSN` 설정 필수
- Playwright CLI/MCP 실측은 로컬 실행기 상태에 영향받아 재현이 불안정할 수 있음

## Next 3 Actions
1. Playwright MCP로 public/auth smoke 실제 실행 후 계획 Phase 3 반영
2. 주요 5개 페이지 Web Vitals baseline 측정
3. (선택) Sentry DSN 프로덕션 환경 설정

## Test Status
- Frontend lint: 0 errors, 0 warnings
- Backend full pytest: 451 passed, 10 deselected
- Backend smoke subset: 338 passed, 10 deselected
