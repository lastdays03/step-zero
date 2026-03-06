# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-06
- Branch: `feature/0-hardcode-cleanup` (커밋 완료, PR 미생성)

## Sprint Focus
- hardcode-cleanup 전체 완료 → PR 생성 대기

## Current State
- hardcode-cleanup Phase A~D: 전량 구현 완료 + 커밋 완료
- legacy-file-cleanup: 전체 완료 (PR #25~#27 머지), done/ 아카이브 대기

## Completed (최근)
- hardcode-cleanup (feature/0-hardcode-cleanup 브랜치):
  - Phase A: ADMIN_EMAILS 환경변수 도입, SOCIAL_MOCK 프로덕션 차단
  - Phase B: stats-dashboard 가짜 데이터 제거, growth_club 큐 실제 쿼리, 가짜 수치 제거
  - Phase C: env.ts URL 유틸리티 추출 (4곳 교체), DiceBear 제거
  - Phase D: utc_now(), alembic.ini, CORS 5173, 중복 상수
- 상세 보고서: `docs/plans/reports/REPORT-hardcode-cleanup.md`

## In Progress
- 없음

## Risks And Blockers
- 배포 시 프로덕션 `.env`에 `ADMIN_EMAILS` 설정 필수

## Next 3 Actions
1. `feature/0-hardcode-cleanup` → `develop` PR 생성 + 머지
2. hardcode-cleanup docs → `done/` 아카이브
3. legacy-file-cleanup docs → `done/` 아카이브 (미완료분)

## Test Status
- Backend pytest: 421 passed, 10 skipped
- Frontend lint: 0 errors (warning 1건: ops/files img element)
