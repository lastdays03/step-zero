# Handoff

> **크기 가이드**: 이 문서는 40줄 이내로 유지한다.

## 마지막 업데이트
- Date: 2026-03-06
- Branch: `develop` (clean, PR #26 머지)

## 이번 세션 요약
- legacy-file-cleanup Phase B+C 구현 → PR #26 머지
  - A-1 DB 스크립트 실행 (71건 데이터 복사 + 검증 PASS)
  - B: FK 재매핑 + Alembic 016 마이그레이션
  - C: ActionKit/GrowthClub/Profile 코드 전환 (FileRepository 단일 소스)
- dind DB + app-db 모두 적용 확인

## Uncommitted Changes
- 없음 (dev-docs-update 문서 갱신 커밋 대기)

## 다음 세션 시작점
1. Phase D 착수 (레거시 테이블 DROP + 모델/코드 정리)
   - D-1: Alembic DROP 마이그레이션 (actionkit_files, growthclubpostattachment, profile_img 컬럼)
   - D-2: 모델 클래스 삭제 + import 정리
   - D-3: pnpm types:sync + 최종 검증

## 핵심 주의사항
- Profile: profile_img 컬럼 듀얼라이트 유지 중 (Phase D에서 제거)
- GrowthClub: attachments relationship 아직 모델에 존재 (Phase D에서 삭제)
- Phase D는 비가역 마이그레이션 — downgrade 불가

## 참조 문서
- 레거시 파일 정리: `docs/plans/active/legacy-file-cleanup/`
