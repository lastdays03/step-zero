# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-06
- Branch: `develop` (최신)

## Sprint Focus
- 활성 작업 없음 — 다음 작업 선정 대기

## Current State
- 모든 계획 작업 완료, `docs/plans/active/` 비어있음
- hardcode-cleanup: PR #28 머지 완료, `done/` 아카이브 완료
- legacy-file-cleanup: PR #25~#27 머지 완료, `done/` 아카이브 완료

## Completed (최근)
- hardcode-cleanup (PR #28):
  - Phase A: ADMIN_EMAILS 환경변수, SOCIAL_MOCK 프로덕션 차단
  - Phase B: stats-dashboard 실데이터 전환, growth_club 큐 실쿼리
  - Phase C: env.ts URL 유틸리티, DiceBear 제거
  - Phase D: utc_now(), alembic.ini, CORS 5173, 중복 상수

## In Progress
- 없음

## Risks And Blockers
- 배포 시 프로덕션 `.env`에 `ADMIN_EMAILS` 설정 필수

## Next 3 Actions
1. 프로젝트 감사 리포트 기반 다음 작업 선정
2. `REPORT-project-audit-2026-03-06.md` 참조
3. (사용자 결정 대기)

## Test Status
- Backend pytest: 421 passed, 10 skipped
- Frontend lint: 0 errors (warning 1건: ops/files img element)
