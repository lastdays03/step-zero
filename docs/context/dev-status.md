# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-06
- Branch: `develop` (`project-audit-fixes` Phase 4 반영 기준)

## Sprint Focus
- `project-audit-fixes` 구현/검증 완료, 커밋/PR 준비 단계

## Current State
- 활성 계획: `docs/plans/active/project-audit-fixes/`
- Phase 1 완료: chat import/export 정리, notifications API 단일화, frontend build 복구
- Phase 2 완료: refresh token rotation 중복 저장 제거, Google OAuth fallback 추가
- Phase 3 완료: Ops confirm/alert 제거, 멀티팀 기본 팀 선택 안전화, backend warning 정리
- Phase 4 완료: CI frontend test/build 추가, API v1 문서 정합성 수정, template resolution 예외 축소
- 검증 통과: `cd app-backend && uv run pytest -q`, `cd app-frontend && pnpm lint && pnpm test --runInBand && pnpm build`
- `pnpm build`는 `next build --webpack` 기준으로 정리
- hardcode-cleanup: PR #28 머지 완료, `done/` 아카이브 완료
- legacy-file-cleanup: PR #25~#27 머지 완료, `done/` 아카이브 완료

## Completed (최근)
- project-audit-fixes Phase 1: chat import/export 정리, notifications API 단일화, env/build 경로 보정
- project-audit-fixes Phase 2: refresh rotation DB row 1회 생성 보장, SocialAuthModal fallback/test 추가
- project-audit-fixes Phase 3: Ops shared confirm dialog 도입, 브라우저 confirm/alert 제거, multi-team API 회귀 테스트 추가
- project-audit-fixes Phase 3: `datetime.utcnow()` 잔존 제거, AsyncMock integration patch, pytest warning budget/cache 경로 설정
- project-audit-fixes Phase 4: frontend CI에 test/build 추가, `decisions.md`/`docs/dev-guide` API v1 정합성 수정
- project-audit-fixes Phase 4: template resolution/auto-draft check를 DB 예외만 fallback하도록 축소
- hardcode-cleanup (PR #28): Phase A~D 아카이브 완료

## In Progress
- `project-audit-fixes` 마무리: 커밋/푸시/PR 준비

## Risks And Blockers
- 배포 시 프로덕션 `.env`에 `ADMIN_EMAILS` 설정 필수

## Next 3 Actions
1. `project-audit-fixes` 커밋 메시지 정리
2. 원격 푸시 후 PR 생성
3. GitHub CI 결과 확인 및 공유

## Test Status
- Frontend lint 통과 (`0 errors, 0 warnings`)
- Frontend test 통과 (`pnpm test --runInBand`: 139 passed)
- Frontend build 통과 (`pnpm build` -> `next build --webpack`)
- Backend pytest 통과 (`uv run pytest -q`: 423 passed, 10 skipped, warning 0)
