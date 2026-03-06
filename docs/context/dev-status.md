# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-06
- Branch: `develop` (clean, PR #26 머지 완료)

## Sprint Focus
- legacy-file-cleanup Phase D (레거시 테이블 제거)

## Current State
- legacy-file-cleanup Phase A~C: 완료 (PR #25, #26 머지)
- legacy-file-cleanup Phase D: 미착수

## Completed (최근)
- Phase B+C (PR #26): FK 재매핑 + 코드 전환
  - Alembic 016 마이그레이션 (actionkit_files → files FK 변경)
  - ActionKit/GrowthClub/Profile → FileRepository 전환
  - ActionKitRepository 파일 메서드 4개 제거
- Phase A (PR #25): 데이터 정합성 확보 + DB 스크립트 실행 (71건)

## In Progress
- 없음

## Risks And Blockers
- Phase D는 비가역 마이그레이션 (테이블 DROP) — 신중한 실행 필요

## Next 3 Actions
1. Phase D 착수: 레거시 테이블 DROP + 모델/코드 정리
2. 프론트엔드 types:sync + 통합 테스트
3. legacy-file-cleanup 완료 후 done/ 아카이브

## Test Status
- Backend pytest: 421 passed, 10 skipped
- Frontend lint: 통과 (warning 1건: ops/files img element)
