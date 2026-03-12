# Handoff

> **크기 가이드**: 이 문서는 40줄 이내로 유지한다.

## 마지막 업데이트
- Date: 2026-03-12
- Branch: `develop` (clean)

## 이번 세션 요약
- pre-push 훅 최적화 Phase 1~2 완료 (27초 → 5.6초)
  - `.husky/pre-push`: smoke subset(`tests/services`, `tests/repositories`, `tests/integration`) + `-x` fail-fast
  - `test_law_api_client.py`: `_REQUEST_INTERVAL=0` autouse fixture 추가
  - `CLAUDE.md`, `README.md`, `docs/operations/` 문서 반영
- 커밋 & 푸시 완료 (`8dc3eb9`)
- pre-push-optimization 계획/보고서 done/ 아카이브

## Uncommitted Changes
- 없음 (dev-docs-update 커밋 대기)

## 다음 세션 시작점
1. 다음 작업 선정 — `docs/plans/active/` 비어있음
2. (선택) 프로덕션 SENTRY_DSN 설정
3. (선택) pre-push Phase 3 후보 검토 (`done/pre-push-optimization/` 참조)

## 핵심 주의사항
- 프로덕션 배포 시 `ADMIN_EMAILS`, `SENTRY_DSN` 환경변수 설정 필수
- `pnpm build`는 `next build --webpack` 사용 (Turbopack CSS panic 회피)
- 루트 `.gitignore`에 `test_*.py` 패턴 → 새 테스트 파일은 `git add -f` 필요
- `get_session()` auto-commit 안됨 → 명시적 `session.commit()` 필수

## 참조 문서
- 완료: `docs/plans/done/pre-push-optimization/`
- 보고서: `docs/plans/done/REPORT-pre-push-performance.md`
