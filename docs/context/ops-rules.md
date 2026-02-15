# Ops Rules

목적: 세션 운영/협업 절차만 짧게 유지한다.

## Core Rules
- 브랜치 전략: `main` 직접 푸시 금지, 개발 기본은 `develop`, 기능은 `feature/*`.
- 커밋/푸시 전 원격 동기화 우선: `git fetch` 후 behind면 `git pull --rebase`.
- PR 제목/본문은 한국어로 작성하고, 로그 원문 붙여넣기는 금지.

## Context Rules
- 세션 시작 복구 순서:
1. `docs/context/dev-status.md`
2. `docs/context/decisions.md`
3. `docs/context/handoff.md`
4. `docs/context/ops-rules.md`
- 세션 중 PC 전환(종료 없이):
1. `git fetch origin`
2. `git pull --rebase`
3. `dev-status.md`, `handoff.md` 재확인
4. 의미 있는 변경이 있을 때만 `dev-status.md`에 1~2줄 Sync Note 추가

## Handoff Trigger
- 사용자가 `핸드오프`, `마무리`, `종료`를 요청하면:
1. `docs/context/handoff.md` 갱신
2. 관련 변경 커밋
3. 현재 브랜치 푸시
- 실패 시 실패 원인과 현재 git 상태를 즉시 보고한다.
