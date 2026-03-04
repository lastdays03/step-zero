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
- 확정 결정 발생 시: `decisions.md` 갱신 (날짜 | 결정 | 근거)
- 운영 규칙 변경 시: `ops-rules.md` 갱신
- 세션 종료 직전: `handoff.md` 갱신
- 표준 예외 발생 시: `decisions.md`에 1줄 + 상세는 `docs/dev-guide/exception-record-template.md` 양식 사용

## Work-Unit Change Logging
- 작업 단위(feature/fix/refactor) 완료 시 아래를 기록한다:
1. `dev-status.md`: Completed에 1줄 요약, Next 3 Actions 갱신
2. `decisions.md`: 새로운 구조적 결정이 있으면 근거 포함 기록
3. `handoff.md`: 세션 종료 시 이번 세션 요약 + 다음 시작점
4. `dev-status.md` Sync Notes: 날짜 + 1줄 변경 기록
- 기록하지 않는 것: 단순 버그 수정, 스타일 변경, 테스트 추가 (결정 아닌 것)

## Document Size Management
- `dev-status.md`: 50줄 이내. Completed 섹션은 요약만 (상세 → handoff.md 또는 계획 문서)
- `handoff.md`: 40줄 이내. 이번 세션 요약 3~5줄 + 다음 액션 중심
- 문서가 가이드 초과 시: 세션 종료 전 이전 내용 정리/축소

## Layer Model (L1/L2-A 충돌 규칙)
- **L1 (Project Source Of Truth)**: 레포 문서 (`AGENTS.md`, `CLAUDE.md`, `docs/context/*`)
- **L2-A (Shared Rules)**: 현재는 `AGENTS.md`/`CLAUDE.md`가 겸임 (단일 프로젝트). 다중 프로젝트 시 `team-standards` repo로 분리.
- **충돌 시**: L1 우선. L2-A는 보조 참조로만 사용.
- **적용 순서**: `AGENTS.md` → `ops-rules.md` → `dev-status.md`/`decisions.md`/`handoff.md`

## Shared Rules Sync Routine
- 목적: 공통 규칙 변경을 L1 문서에 반영한다.
- 트리거: 아키텍처/운영/품질/API 설계 기준 변경 시
- 실행 순서:
1. 변경된 규칙을 `AGENTS.md` 또는 `CLAUDE.md`에서 확인
2. 프로젝트 영향 항목을 L1 문서(`docs/context/*`, `docs/planning/*`)에 반영
3. 반영 결과를 `docs/context/dev-status.md`의 `Sync Notes`에 1줄 기록
4. 구조적 결정이면 `decisions.md`에 근거 포함 기록

## Handoff Trigger
- 사용자가 `핸드오프`, `마무리`, `종료`를 요청하면:
1. `docs/context/handoff.md` 갱신
2. 갱신 내용을 공유하고 `커밋`/`푸시` 명시 요청 전까지 대기
- 실패 시 실패 원인과 현재 git 상태를 즉시 보고한다.
