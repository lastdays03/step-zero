# Handoff

> **크기 가이드**: 이 문서는 40줄 이내로 유지한다.

## 마지막 업데이트
- Date: 2026-03-11
- Branch: `develop` (clean)

## 이번 세션 요약
- 개발서버 마이그레이션 `018_add_actionkit_events` 적용 완료
- dev-docs 업데이트 (문서 정리)

## Uncommitted Changes
- `CLAUDE.example.md` 수정 (minor)

## 다음 세션 시작점
1. 다음 작업 선정 — `docs/plans/active/` 비어있음
2. (선택) 프로덕션 SENTRY_DSN 설정
3. (선택) `docs/plans/reports/` 리포트 아카이브 검토

## 핵심 주의사항
- 프로덕션 배포 시 `ADMIN_EMAILS`, `SENTRY_DSN` 환경변수 설정 필수
- `pnpm build`는 `next build --webpack` 사용 (Turbopack CSS panic 회피)
- 루트 `.gitignore`에 `test_*.py` 패턴 → 새 테스트 파일은 `git add -f` 필요
- `get_session()` auto-commit 안됨 → 명시적 `session.commit()` 필수

## 참조 문서
- 완료: `docs/plans/done/exception-handler-integration/`
