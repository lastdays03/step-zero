# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-06
- Branch: `feature/0-legacy-file-cleanup-phase-b` (Phase B+C 구현 중)

## Sprint Focus
- legacy-file-cleanup Phase B+C 구현

## Current State
- legacy-file-cleanup Phase A: 완료 (PR #25 머지 + A-1 DB 스크립트 실행 완료)
- legacy-file-cleanup Phase B: 완료 (FK 재매핑 + Alembic 마이그레이션)
- legacy-file-cleanup Phase C: 완료 (ActionKit/GrowthClub/Profile 코드 전환)
- legacy-file-cleanup Phase D: 미착수

## Completed (최근)
- A-1 DB 스크립트 실행 (71건: ActionKit 67, GrowthClub 3, Profile 1)
- B-1 FK 데이터 재매핑 (ID 매핑 67건, FK 대상 0건)
- B-2 Alembic 마이그레이션 016 적용 (actionkit_files → files FK 변경)
- C-1 ActionKit: FileRepository 전환, 레거시 메서드 4개 제거
- C-2 GrowthClub: File 기반 attachment 생성/조회/삭제
- C-3 Profile: File primary source, profile_img 컬럼 동기화 유지

## In Progress
- PR 준비 (Phase B+C 커밋)

## Risks And Blockers
- Phase D (레거시 테이블 DROP)는 별도 PR로 진행 권장

## Next 3 Actions
1. Phase B+C 커밋 → PR 생성 → develop 머지
2. Phase D 착수: 레거시 테이블 DROP + 코드 정리
3. 프론트엔드 types:sync + 통합 테스트

## Test Status
- Backend pytest: 421 passed, 10 skipped
- Frontend lint: 통과 (warning 1건: ops/files img element)
