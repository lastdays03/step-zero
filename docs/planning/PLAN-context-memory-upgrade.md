# PLAN: Context Memory Upgrade

## 진행 상태 (2026-02-15)
- [x] Phase 1 문서 구조 고정(README 단일 진입점 + 컨텍스트 4종 템플릿 정리)
- [ ] Phase 1 운영 검증(1주, 개발과 병행)
- [ ] Phase 2 Validation 착수
- [x] Phase 3 전략 재정의(공통 표준 + 프로젝트별 보조기억 이중 레이어)
- [ ] Phase 3 운영 활성화

### Phase Gate (명시)
- 현재 활성 페이즈: `Phase 1`
- `Phase 2` 상태: `잠금` (아래 3개 조건 충족 전 착수 금지)
1. 7일 로그 누락 없이 기록 완료
2. 합격 기준 3개 중 2개 이상 충족
3. 보정안을 `decisions.md` 또는 본 문서에 확정 반영

### 운영 검증 진행률
- 현재: `1/7` (2026-02-15 기록 완료)
- 다음 체크포인트:
1. 2026-02-17: 3일차 중간 점검(누락 유형 반복 여부)
2. 2026-02-19: 5일차 작성 시간 과다 여부 점검
3. 2026-02-21: 주간 집계 및 보정안 확정

## 목표
- PC 변경 시 작업 맥락 복구 시간을 최소화한다.
- 과도한 기록 없이 경량 메모리 중심으로 운영한다.
- NotebookLM을 프로젝트 자료 탐색/분석 도구로 활용하고, 분석 결과를 실행 문서(L1)에 반영한다.

## Phase 1 (Now): Lightweight Memory Only
- 범위:
1. `docs/context/dev-status.md`
2. `docs/context/ops-rules.md`
3. `docs/context/decisions.md`
4. `docs/context/handoff.md`
5. `docs/context/README.md`
- 운영:
1. 작업 중 `dev-status.md` 갱신
2. 운영 규칙 변경 시 `ops-rules.md` 갱신
3. 확정 사항은 `decisions.md` 반영
4. 세션 종료 시 `handoff.md` 갱신
- 성공 기준:
1. 다른 PC에서 10분 내 맥락 복구 가능
2. 1주간 운영 중 누락 없이 핸드오프 유지

### Phase 1 적용 메모 (2026-02-15)
- `docs/context/README.md`에 시작/종료 30초 체크리스트 추가
- `dev-status.md` 고정 섹션 템플릿 도입(상태/리스크/테스트/Sync Notes)
- `decisions.md`를 `날짜 | 결정 | 근거` 포맷으로 통일
- `handoff.md`/`ops-rules.md`를 트리거 기반 운영 형태로 정리
- `context-memory-validation-log.md`에 7일 입력 슬롯 + 주간 집계 템플릿 추가

## Phase 2 (Validation)
- 기간: 1~2주
- 점검 항목:
1. 자주 빠지는 정보 유형(결정 근거/남은 리스크/테스트 상태)
2. 문서 유지 비용(작성 시간)
3. 실제 이어서 작업 성공률
- 산출:
1. 템플릿 경량화 또는 필드 보강
2. 작성 트리거 규칙 보정

### Phase 1 운영 검증 실행안 (2026-02-15 시작)
- 운영 기간: 2026-02-15 ~ 2026-02-21 (7일)
- 기록 위치: `docs/context/context-memory-validation-log.md`
- 실행 정책: 운영 검증은 개발을 차단하지 않는다. 기능 개발과 병행한다.
- 일일 기록 입력: `scripts/context/context_memory_log_update.py --date <YYYY-MM-DD> --recovery <분> --missing <유형> --writing <분> --success <성공|부분성공|실패> --notes <메모>`
- 일일 누락 점검: `scripts/context/context_memory_summary.py --check`
- 집계 명령: `scripts/context/context_memory_summary.py`
- 주간 요약 초안 생성: `scripts/context/context_memory_summary.py --format markdown`
- 주간 요약 반영: `scripts/context/context_memory_summary.py --write-weekly`
- 일일 기록 항목:
1. 세션 시작 맥락 복구 시간(분)
2. 누락 정보 유형(없음/결정 근거/남은 리스크/테스트 상태/기타)
3. 문서 작성/갱신 총 시간(분)
4. 이어서 작업 성공 여부(성공/부분성공/실패)
5. 보정 필요 사항(템플릿 필드/트리거 규칙)
- 합격 기준:
1. 복구 시간 중앙값 10분 이하
2. `handoff.md` 누락 0회
3. 이어서 작업 성공률 80% 이상
- 실패 시 조치:
1. 누락 항목이 2회 이상 반복되면 해당 필드를 템플릿 고정 섹션으로 승격
2. 작성 시간 평균이 8분 초과면 중복 섹션 통합 또는 선택 입력화

### Phase 2 진입 조건
- 아래 조건을 모두 만족할 때 진입:
1. 7일 로그가 누락 없이 기록됨
2. 합격 기준 3개 중 2개 이상 충족
3. 보정안이 `decisions.md` 또는 본 문서에 확정됨

### 운영 원칙 (합의)
- 2026-02-15 합의: `Background Validation` 방식 적용
- 의미: 7일 검증은 병행 수행하고, 기능 개발은 즉시 진행한다.

## 남은 작업 (Context Upgrade Only)
- [ ] 2026-02-21까지 `context-memory-validation-log.md` 일일 기록 유지
- [ ] 주간 집계 1회 작성(복구시간 중앙값, 성공률, 누락 유형 상위 2개)
- [ ] 보정안 확정(템플릿 필드 승격/삭제) 후 `decisions.md` 반영
- [ ] 본 문서의 `진행 상태`에서 Phase 1 운영 검증 완료 체크

## Phase 3 (Strategy): NotebookLM Analysis-to-Action Model
- 목적: 공통 표준은 유지하면서, 프로젝트 자료 탐색/분석 결과를 즉시 실행 문서에 반영한다.

### Layer Model
- L1 (Project Source Of Truth): 레포 문서(`AGENTS.md`, `docs/context/*`)
- L2 (Shared Knowledge Base): NotebookLM
- 충돌 규칙: L1 우선, L2는 보조/분석 역할

### Track A: 공통 표준 관리 (Cross-Project)
- 범위:
1. 개발 아키텍처 원칙
2. 운영/협업 가이드
3. 품질/테스트 기준
4. API 설계 기준
- 산출:
1. 공통 표준 문서 세트(NotebookLM 소스)
2. 새 작업 시작 체크리스트 템플릿
3. 프로젝트 예외 기록 템플릿

### Track B: 프로젝트별 자료 탐색/분석 (Per-Project)
- 범위:
1. 프로젝트 관련 자료(기획/회의/아키텍처/이슈) 탐색
2. NotebookLM 기반 질의/요약/근거 추적/비교 분석
3. 분석 결과를 `docs/context/*`와 실행 계획/결정에 반영
- 산출:
1. 프로젝트별 분석 소스 목록(우선순위/갱신 주기 포함)
2. 질의 패턴 세트(예: 결정 근거 재확인, 관련 자료 찾기, 대안 비교)
3. `Analysis -> Action` 반영 로그(무엇을 어떤 문서에 반영했는지)

### Phase 3 Gate
- `Track A` 설계/정의는 Phase 1~2와 병행 가능
- `Track B` 운영 활성화는 Phase 2 보정안 확정 후 착수
- 활성화 최소 조건:
1. L1/L2 충돌 규칙 문서화 완료
2. 표준 체크리스트/예외 템플릿 준비 완료
3. 분석 결과의 L1 반영 루틴 정의 완료

### Phase 3 Success Criteria
1. 새 프로젝트 시작 시 표준 적용 시작 시간이 단축됨
2. 프로젝트 자료 탐색/비교 분석 시간이 단축됨
3. 분석 결과가 L1 문서(결정/계획/상태)에 누락 없이 반영됨

## 리스크
- 경량 문서가 오래되면 무용화
- 규칙 미준수 시 핸드오프 누락
- 외부 보조기억 도입 시 출처 단일화 실패 가능성

## 대응
- `마무리/종료` 트리거로 `handoff.md` 강제 갱신
- 주 1회 `dev-status.md`/`decisions.md` 정리
- 외부 도구 도입 시 “레포 문서 우선” 원칙 유지
