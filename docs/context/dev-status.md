# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-06
- Branch: `develop`

## Sprint Focus
- 메인 대시보드 정리 및 품질 개선

## Current State
- R2 스토리지 마이그레이션: PR #22 머지 완료
- 프론트엔드 테스트: 133건 (21 suites)
- 대시보드 정리: 계획 수립 완료, 구현 미착수

## Completed (최근)
- R2 Phase 1-4: StorageBackend 추상화, 전체 서비스 전환, 프론트 통합
- 프론트엔드 테스트 Phase 1-3: 순수함수/훅/컴포넌트 133건
- 통합 문서 뷰어: /view 엔드포인트, MD 툴바, 포맷별 분기
- 대시보드 정리 계획 문서 수립 (코드 검증 완료)

## In Progress
- 대시보드 정리 5-Phase 계획 (docs/plans/active/dashboard-cleanup/)

## Risks And Blockers
- primary 색상 불일치: #257bf4 (tailwind) != #36a4f2 (하드코딩) — 디자인 의도 확인 필요

## Next 3 Actions
1. 대시보드 정리 Phase 1: 미사용 파일 4개 삭제
2. 대시보드 정리 Phase 2: 중복 코드 제거 (SocialAuthModal, 드롭다운, 색상)
3. 대시보드 정리 Phase 3: P0 버그 수정 (window.location.href, activeRoadmapId)

## Test Status
- Backend pytest: 406 passed, 10 skipped
- Frontend test: 133 passed (21 suites)
- Frontend lint: 0 errors

## Sync Notes
- 2026-03-06: PR #22 머지, feature/0-r2-storage-migration 브랜치 삭제, develop 전환
