# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-06
- Branch: `feature/0-dashboard-cleanup`

## Sprint Focus
- 메인 대시보드 정리 및 품질 개선

## Current State
- 대시보드 정리: Phase 1~5 전체 완료
- 신규 계획 2건: dashboard-enhance, ops-file-manager (구현 미착수)

## Completed (최근)
- Phase 1: 미사용 소스 정리 (StatsGrid, mock, api, types 삭제)
- Phase 2: AccountMenu 추출, nav-config 공유, AuthModalProvider 단일화, GLASS_CARD, #36a4f2 제거
- Phase 3: router.push 전환, activeRoadmapId storage 동기화
- Phase 4: Header 시간대 인사말, 스켈레톤 UI, ColdStartHero button, md:grid-cols-4
- Phase 5: DashboardResult typed dataclass, 게스트 데이터 단일화, URL 검증, 테스트 통일

## In Progress
- dashboard-cleanup PR 생성 대기
- dashboard-enhance, ops-file-manager: 계획 수립만 완료

## Risks And Blockers
- 없음

## Next 3 Actions
1. 커밋 후 develop PR 생성
2. dashboard-enhance 또는 ops-file-manager 착수
3. 브라우저 실 테스트 (sm/md/lg 반응형)

## Test Status
- Backend pytest: 406 passed, 10 skipped
- Frontend test: 133 passed (21 suites)
- Frontend lint: 통과
