# Context Memory (Lightweight)

목적: PC 전환/세션 재시작 시 10분 안에 작업 맥락을 복구한다.

## Source Of Truth
- 실행 규칙 우선순위:
1. `AGENTS.md`
2. `docs/context/ops-rules.md`
3. `docs/context/dev-status.md`, `docs/context/decisions.md`, `docs/context/handoff.md`
- 외부 보조 도구(예: NotebookLM)는 검색 보조만 수행한다.
- NotebookLM 분석 결과는 반드시 L1 문서(`docs/context/*`, 계획/결정 문서)에 반영해 실행 기준으로 고정한다.

## 30-Second Start Checklist
1. `docs/context/dev-status.md` 읽기
2. `docs/context/decisions.md` 읽기
3. `docs/context/handoff.md` 읽기
4. `docs/context/ops-rules.md` 읽기
5. `dev-status.md`의 `Next 3 Actions` 기준으로 첫 작업 1개 선택

## 30-Second End Checklist
1. `dev-status.md`의 상태/다음 액션 갱신
2. 이번 세션 신규 확정사항을 `decisions.md`에 반영
3. `handoff.md` 갱신
4. 사용자 트리거(`핸드오프`, `마무리`, `종료`)가 있으면 갱신 내용 공유 후 `커밋`/`푸시` 요청 대기

## Background Validation (2026-02-15 ~ 2026-02-21)
- 위치: `docs/context/context-memory-validation-log.md`
- 원칙: 운영 검증은 기능 개발을 멈추지 않고 병행 수행한다.
- 매일 최소 1회 기록: 복구 시간, 누락 유형, 작성 시간, 이어서 작업 성공 여부
- 일일 기록 입력: `scripts/context/context_memory_log_update.py --date <YYYY-MM-DD> --recovery <분> --missing <유형> --writing <분> --success <성공|부분성공|실패> --notes <메모>`
- 일일 누락 점검: `scripts/context/context_memory_summary.py --check`
- 중간 집계: `scripts/context/context_memory_summary.py`
- 주간 요약 초안: `scripts/context/context_memory_summary.py --format markdown`
- 주간 요약 반영: `scripts/context/context_memory_summary.py --write-weekly`

## File Roles And Triggers
- `dev-status.md`
  - 역할: 현재 상태, 진행 중, 리스크, 다음 액션 유지
  - 갱신 트리거: 작업 단위 완료/우선순위 변경/PC 동기화 직후
- `decisions.md`
  - 역할: 확정된 기술 결정과 근거 기록
  - 갱신 트리거: 롤백 가능성이 낮은 구조/운영 결정 확정 시
- `handoff.md`
  - 역할: 세션 종료 시점의 다음 시작점 전달
  - 갱신 트리거: 세션 종료 직전, 또는 사용자 종료 트리거 입력 시
- `ops-rules.md`
  - 역할: 협업 절차와 문서 운영 규칙 정의
  - 갱신 트리거: 운영 방식/체크리스트 변경 시
- `notebooklm-query-templates.md`
  - 역할: NotebookLM 분석 질의 템플릿 표준 관리
  - 갱신 트리거: 분석 패턴/질문 포맷 개선 시
- `notebooklm-analysis-action-log.md`
  - 역할: NotebookLM 분석 결과의 L1 반영 이력 추적
  - 갱신 트리거: 분석 결과를 문서/계획/결정에 반영한 직후
- `notebooklm-mcp-runbook.md`
  - 역할: NotebookLM MCP 등록/점검/대체 루틴 운영 가이드
  - 갱신 트리거: MCP 인증/호출 방식 변경 시

## Writing Policy
- 전체 로그 대신 결론/상태만 기록한다.
- 문서는 짧게 유지하되, 다음 행동과 리스크는 항상 남긴다.
- 템플릿 섹션 제목은 유지하고, 내용만 갱신한다.
