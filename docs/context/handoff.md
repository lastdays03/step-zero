# Handoff

> **크기 가이드**: 이 문서는 40줄 이내로 유지한다.

## 마지막 업데이트
- Date: 2026-03-06
- Branch: `feature/0-hardcode-cleanup` (커밋 완료)

## 이번 세션 요약
- 프로젝트 전수조사 → 13건 목업/하드코딩 이슈 식별
- hardcode-cleanup 상세 계획서 작성 (3파일 세트)
- Phase A~D 전량 구현 + 테스트 통과 (421 passed, 0 lint errors)
- 상세 변경 보고서 작성 (`REPORT-hardcode-cleanup.md`)

## Uncommitted Changes
- `docs/context/dev-status.md`, `docs/context/handoff.md` — 핸드오프 문서
- `docs/plans/reports/REPORT-hardcode-cleanup.md` — 상세 보고서

## 다음 세션 시작점
1. 핸드오프 문서 커밋
2. `feature/0-hardcode-cleanup` → `develop` PR 생성 + 머지
3. `docs/plans/active/hardcode-cleanup/` → `done/` 아카이브
4. legacy-file-cleanup `done/` 아카이브 잔여분 처리

## 핵심 주의사항
- 프로덕션 배포 시 `ADMIN_EMAILS` 환경변수 설정 필수 (미설정 시 신규 가입 superuser 불가)
- `stats-dashboard.tsx`가 수정 전 원본으로 되돌아감 (system-reminder에 표시) — 이는 lint/linter 자동 변경이 아닌 시스템 표시일 뿐, 실제 파일은 수정 완료 상태
- `alembic.ini` DB URL이 placeholder로 변경됨 — `alembic/env.py`가 환경변수로 override하므로 영향 없음

## 참조 문서
- 계획: `docs/plans/active/hardcode-cleanup/`
- 보고서: `docs/plans/reports/REPORT-hardcode-cleanup.md`
