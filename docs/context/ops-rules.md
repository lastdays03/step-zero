# Ops Rules

목적: 세션 운영/협업 절차만 짧게 유지한다.

## Core Rules
- 규칙 우선순위는 `AGENTS.md` -> `docs/context/ops-rules.md` 순서로 적용한다.
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

## Update Triggers
- 작업 단위 완료/우선순위 변경 시: `dev-status.md` 갱신
- 확정 결정 발생 시: `decisions.md` 갱신
- 운영 규칙 변경 시: `ops-rules.md` 갱신
- 세션 종료 직전: `handoff.md` 갱신

## Validation Routine
- 기간: 2026-02-15 ~ 2026-02-21
- 파일: `docs/context/context-memory-validation-log.md`
- 규칙: 하루 최소 1회 기록, 검증은 기능 개발과 병행(개발 비차단)

## Shared Rules Sync Routine
- 목적: 공통 규칙은 `team-standards`(Git)에서 관리하고, 프로젝트 실행 기준은 레포 문서(L1)로 고정한다.
- 실행 순서:
1. 공통 규칙 변경사항을 `team-standards`에서 확인
2. 프로젝트 영향 항목을 L1 문서(`docs/context/*`, `docs/planning/*`)에 반영
3. 반영 결과를 `docs/context/dev-status.md`의 `Sync Notes`에 1줄 기록

## Handoff Trigger
- 사용자가 `핸드오프`, `마무리`, `종료`를 요청하면:
1. `docs/context/handoff.md` 갱신
2. 갱신 내용을 공유하고 `커밋`/`푸시` 명시 요청 전까지 대기
- 실패 시 실패 원인과 현재 git 상태를 즉시 보고한다.
