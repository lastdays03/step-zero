# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-10
- Branch: `develop` (PR #30 머지, feature 브랜치 삭제)

## Sprint Focus
- actionkit-analytics-tracking 완료 → 다음 작업 선정 대기

## Current State
- `docs/plans/active/` 비어있음 (actionkit-analytics-tracking → done/ 아카이브 예정)
- Backend: 436 passed, Frontend: lint 0 errors
- 개발서버 마이그레이션 대기: `018_add_actionkit_events`

## Completed (최근)
- **actionkit-analytics-tracking (PR #30)**: Phase 1~4 완료
  - ActionKitEvent 모델 + 018 마이그레이션
  - 서버사이드 view/download 자동 추적 + 클라이언트 트래킹 API
  - 통계 집계 서비스 (KPI 3종, 인기 서류 TOP5, 검색어, 인사이트)
  - 관리자 대시보드 하드코딩 → 실데이터 전환
  - ARQ cron 90일 이벤트 정리
  - 테스트 13건 추가
- project-audit-fixes (PR #29): done/ 아카이브 완료
- hardcode-cleanup (PR #28): done/ 아카이브 완료

## In Progress
- 없음

## Risks And Blockers
- 배포 시 프로덕션 `.env`에 `ADMIN_EMAILS` 설정 필수
- **개발서버 마이그레이션 미적용**: `docker compose exec app-backend uv run alembic upgrade head`

## Next 3 Actions
1. 개발서버 마이그레이션 적용 (018_add_actionkit_events)
2. actionkit-analytics-tracking docs → done/ 아카이브 커밋
3. 다음 작업 선정

## Test Status
- Frontend lint: 0 errors, 0 warnings
- Backend pytest: 436 passed, 10 skipped
