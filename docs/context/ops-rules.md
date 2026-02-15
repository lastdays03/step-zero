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

## NotebookLM Analysis-to-Action Routine
- 목적: NotebookLM 분석 결과를 프로젝트 실행 문서(L1)로 확정 반영한다.
- 공통 표준은 NotebookLM에서 관리하되, 프로젝트 실행 기준은 항상 L1 문서로 확정한다.
- 실행 순서:
1. NotebookLM 질의/분석 수행
2. 반영 대상 문서 결정(`docs/context/dev-status.md`, `docs/context/decisions.md`, `docs/planning/*`)
3. 반영 후 `docs/context/notebooklm-analysis-action-log.md`에 1줄 기록
- 최소 기록 항목:
1. 날짜
2. 분석 주제
3. 반영 문서 경로
4. 반영 요약 1~2줄

## Handoff Trigger
- 사용자가 `핸드오프`, `마무리`, `종료`를 요청하면:
1. `docs/context/handoff.md` 갱신
2. 관련 변경 커밋
3. 현재 브랜치 푸시
- 실패 시 실패 원인과 현재 git 상태를 즉시 보고한다.
