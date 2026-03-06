# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-06
- Branch: `feature/0-dashboard-cleanup` (uncommitted 12 modified + 3 untracked)

## Sprint Focus
- 메인 대시보드 정리 및 품질 개선

## Current State
- 대시보드 정리: Phase 1 완료, Phase 2~5 부분 완료 (코드 변경 완료, 검증 미실행)
- 신규 계획 2건: dashboard-enhance, ops-file-manager (구현 미착수)

## Completed (최근)
- Phase 2: AccountMenu 추출, nav-config 공유, AuthModalProvider 단일화, GLASS_CARD 상수
- Phase 3: router.push 전환, activeRoadmapId storage 동기화
- Phase 4.1: Header 시간대 인사말
- Phase 5.1: DashboardResult typed dataclass + asdict()
- Phase 5.3: 테스트 mock status 소문자 통일

## In Progress
- 대시보드 정리 5-Phase 계획 — 검증(lint/test) 미실행
- dashboard-enhance, ops-file-manager: 계획 수립만 완료

## Risks And Blockers
- primary 색상 불일치: #257bf4 (tailwind) != #36a4f2 (하드코딩) — 디자인 의도 확인 필요
- 12개 파일 uncommitted — 커밋 전 반드시 lint/test 통과 확인 필요

## Next 3 Actions
1. `pnpm lint` + `pnpm test` 실행하여 현재 변경 검증
2. 검증 통과 시 커밋 (Phase 2~5 부분 완료분)
3. Phase 2.1 (#36a4f2 색상) 디자인 결정 후 토큰화, Phase 4.2~4.4 UX 작업

## Test Status
- Backend pytest: 406 passed, 10 skipped (변경 후 미확인)
- Frontend test: 133 passed (변경 후 미확인)
- Frontend lint: 미확인

## Sync Notes
- 2026-03-06: feature/0-dashboard-cleanup 브랜치에서 Phase 2~5 부분 구현 (미커밋)
