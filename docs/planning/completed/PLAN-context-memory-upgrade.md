# PLAN: Context Memory Upgrade

## 진행 상태 (2026-03-04)
- [x] Phase 1 문서 구조 고정(README 단일 진입점 + 컨텍스트 4종 템플릿 정리)
- [x] Phase 1 운영 검증(회고 평가로 합격 판정 — 47커밋/2.5주 실전 운영)
- [x] Phase 2 Validation 완료 (템플릿 경량화 + 트리거 보정)
- [x] Phase 3 전략 재정의(공통 규칙 team-standards + 프로젝트 실행 문서 중심 운영)
- [x] Phase 3 운영 활성화 (Gate 3조건 충족 + Track A/B 구현 완료)
- [x] Phase 3 구현 시작(분석→반영 루틴/템플릿/로그 파일 생성)

### Phase Gate (명시)
- **전체 계획 완료** (2026-03-04)
- `Phase 1`: **완료** (2026-03-04 회고 평가 합격)
- `Phase 2`: **완료** (2026-03-04 보정안 확정 + 적용)
- `Phase 3`: **완료** (2026-03-04 Gate 3조건 충족)

## 목표
- PC 변경 시 작업 맥락 복구 시간을 최소화한다.
- 과도한 기록 없이 경량 메모리 중심으로 운영한다.
- 공통 규칙은 `team-standards`(Git)에서 관리하고, 결과 반영은 실행 문서(L1) 중심으로 운영한다.

## Phase 1 (완료): Lightweight Memory Only
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
- 성공 기준: 3/3 합격 (회고 평가 2026-03-04)
1. 다른 PC에서 10분 내 맥락 복구 가능 — **합격**
2. 1주간 운영 중 누락 없이 핸드오프 유지 — **합격** (25회 갱신)
3. 이어서 작업 성공률 80% 이상 — **합격** (100%, 4개 Phase 완수)

### Phase 1 검증 결과 요약
- 일일 로그: 1/7 기록 (형식적 미완)
- 실질 운영: 47커밋/2.5주, 4개 Phase 성공 이행
- 판정: git 기반 실질 증거로 합격 (상세: `context-memory-validation-log.md`)

## Phase 2 (완료): Validation + Template Refinement
- 기간: 2026-03-04 (일괄 적용)
- 점검 결과:
1. 자주 빠지는 정보 유형: 없음 (문서 기반 복구 성공)
2. 문서 유지 비용: dev-status/handoff가 비대화 경향 (77줄) → 크기 가이드 도입
3. 실제 이어서 작업 성공률: 100%

### Phase 2 보정안 (확정, 적용 완료)
1. **dev-status.md 경량화**: Completed 섹션 요약화, 50줄 이내 가이드 도입
2. **handoff.md 경량화**: 이번 세션 요약 3~5줄 + 다음 액션 중심, 40줄 이내 가이드 도입
3. **ops-rules.md 정리**: 만료된 Validation Routine 섹션 제거, Document Size Management 규칙 추가
4. **README.md 정리**: 만료된 Background Validation 섹션 제거, 크기 가이드를 File Roles에 통합
5. **일일 검증 로그 운영 폐기**: git log 자체가 더 신뢰할 수 있는 검증 원천
6. **validation scripts 참조 제거**: README.md에서 스크립트 명령어 참조 삭제

## Phase 3 (Strategy): Shared Rules + L1 Action Model
- 목적: 공통 규칙은 `team-standards`(Git)에서 관리하고, 프로젝트 실행 문서를 즉시 반영 가능한 형태로 유지한다.

### Layer Model
- L1 (Project Source Of Truth): 레포 문서(`AGENTS.md`, `docs/context/*`)
- L2-A (Shared Rules): `team-standards`(Git 공통 규칙)
- 충돌 규칙: 실행 기준은 L1 우선, L2-A는 보조 참조

### Track A: 공통 표준 관리 (Cross-Project)
- 범위:
1. 개발 아키텍처 원칙
2. 운영/협업 가이드
3. 품질/테스트 기준
4. API 설계 기준
- 산출:
1. 공통 표준 문서 세트(`team-standards` 템플릿/스크립트)
2. 새 작업 시작 체크리스트 템플릿
3. 프로젝트 예외 기록 템플릿

### Track B: 프로젝트 실행 반영 (Per-Project)
- 범위:
1. 프로젝트 관련 실행 문서(`docs/context/*`, `docs/planning/*`) 정합성 유지
2. 결정/상태/리스크를 작업 단위 기준으로 반영
- 산출:
1. 프로젝트별 실행 문서 갱신 로그
2. 작업 단위 기준의 변경 근거 기록

### Phase 3 Gate — **충족 (2026-03-04)**
- 활성화 최소 조건:
1. L1/L2-A 충돌 규칙 문서화 완료 — **✅** `ops-rules.md` Layer Model 섹션
2. 표준 체크리스트/예외 템플릿 준비 완료 — **✅** `docs/dev-guide/new-work-checklist.md`, `exception-record-template.md`
3. 분석 결과의 L1 반영 루틴 정의 완료 — **✅** `ops-rules.md` Work-Unit Change Logging 섹션

### Phase 3 산출물
- `ops-rules.md`: Layer Model (L1/L2-A 충돌 규칙) + Work-Unit Change Logging 루틴
- `docs/dev-guide/new-work-checklist.md`: 새 작업 시작 체크리스트
- `docs/dev-guide/exception-record-template.md`: 표준 예외 기록 양식
- `team-standards` 외부 repo: **보류** (단일 프로젝트 — `AGENTS.md`/`CLAUDE.md`가 L2-A 겸임)
- `scripts/context/` validation scripts: **폐기** (Phase 2 결정 — git log로 대체)

### Phase 3 운영 결정
- 현재 프로젝트 1개이므로 `team-standards` 외부 repo 생성은 보류
- `AGENTS.md`/`CLAUDE.md`가 사실상 L2-A(공통 규칙) 역할 수행
- 다중 프로젝트 전환 시 `team-standards` repo 분리 검토

## 리스크
- 경량 문서가 오래되면 무용화
- 규칙 미준수 시 핸드오프 누락
- 외부 보조기억 도입 시 출처 단일화 실패 가능성

## 대응
- `마무리/종료` 트리거로 `handoff.md` 강제 갱신
- 문서 크기 가이드 (dev-status 50줄, handoff 40줄) 로 비대화 방지
- 외부 도구 도입 시 "레포 문서 우선" 원칙 유지
