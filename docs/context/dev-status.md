# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-05
- Branch: `feature/5-pkg-manager-migration`

## Sprint Focus
- Runtime Upgrade (uv 0.10 + 백엔드 의존성 하한 + Docker .venv 충돌 해결)

## Current State
- Phase 0~4: 전체 완료 (develop 머지 완료)
- Runtime Upgrade: 코드 변경 + Docker 검증 완료, 커밋/PR 대기

## Completed (최근)
- Runtime Upgrade Phase 1~3: Dockerfile uv 0.10, pyproject.toml 의존성 하한, .venv 볼륨 제외
- Docker pytest 393 passed, alembic check diff 없음

## In Progress
- Runtime Upgrade Phase 4: 커밋 + PR 생성 (docs/plans/done/runtime-upgrade/)
- R2 Storage Migration (docs/plans/active/r2-integration/)

## Risks And Blockers
- pytest flaky 2건: test_real_oos_lawsuit, test_real_oos_health (기존 이슈, OpenAI 임베딩 비결정성)

## Next 3 Actions
1. docker-compose.dev.yml + 문서 변경 커밋
2. PR 생성: `feature/5-pkg-manager-migration` → `develop`
3. R2 Storage Migration 계속 진행

## Test Status
- Backend pytest (Docker): 393 passed, 15 skipped, 2 failed (flaky)
- Alembic check: No diff
- Frontend lint: 0 errors

## Sync Notes
- 2026-03-05: Runtime Upgrade 전체 검증 완료, Docker .venv 충돌 발견+해결
