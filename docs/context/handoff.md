# Handoff

> **크기 가이드**: 이 문서는 40줄 이내로 유지한다.

## 마지막 업데이트
- Date: 2026-03-06
- Branch: `feature/0-legacy-file-cleanup-phase-b`

## 이번 세션 요약
- A-1 DB 스크립트 실행 완료 (71건 마이그레이션 + 검증 PASS)
- Phase B: FK 재매핑 + Alembic 016 마이그레이션 적용
- Phase C: ActionKit/GrowthClub/Profile 코드 전환
  - ActionKit: FileRepository 전환, 레거시 메서드 4개 삭제
  - GrowthClub: GrowthClubPostAttachment 생성 제거, File 기반 조회
  - Profile: File primary, profile_img 컬럼 동기화 유지 (AuthorRead 호환)

## Uncommitted Changes
- Phase B+C 전체 코드 변경 (커밋 대기)

## 다음 세션 시작점
1. Phase B+C 커밋 → PR 생성 → develop 머지
2. Phase D 착수 (레거시 테이블 DROP + 모델/코드 정리)

## 핵심 주의사항
- Profile: profile_img 컬럼 듀얼 라이트 유지 (Phase D에서 제거)
- GrowthClub: 기존 attachments relationship은 Phase D에서 삭제
- Ops 콘솔 파일 삭제: Phase C 완료로 안전하게 사용 가능

## 참조 문서
- 레거시 파일 정리: `docs/plans/active/legacy-file-cleanup/`
