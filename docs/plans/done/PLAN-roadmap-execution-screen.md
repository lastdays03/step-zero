# PLAN-roadmap-execution-screen: 실행형 로드맵 화면 구현 계획

> 목표: 로드맵을 단순 조회 화면이 아니라, 단계별 작업을 실제로 진행/완료할 수 있는 실행형 화면으로 전환한다.

## 1) 선행 계획 대비 실행 현황 (2026-02-19)

완료:
- 비동기 생성 잡/폴링 구조(`jobs`) 적용
- 입력 검증 API(`POST /api/v1/roadmaps/jobs/validate`) 적용
- 상세 조회 API(`GET /api/v1/roadmaps/{id}/detail`) 확장
- 단계 상태 전이 API 추가: `PATCH /api/v1/roadmaps/tasks/{step_id}`
- 상태 전이 기본 규칙 적용:
  - 이전 단계 미완료 시 `IN_PROGRESS/COMPLETED` 불가
  - 단계 `COMPLETED` 시 다음 단계 자동 `IN_PROGRESS`

미완료(이번 계획 범위):
- 실행형 로드맵 UI(Phase 타임라인 + Task 실행 패널) 구현
- Task 카드별 CTA 연동(문서/가이드/체크리스트)
- 대시보드와 로드맵 화면의 실행 상태 UI 완전 통합

---

## 2) 화면 목표 (시안 기준)

- 좌측: Phase 진행 타임라인 (완료/현재/잠금 상태)
- 중앙: 현재 Phase 상세 작업(Task) 카드
- 우측: 진행률/일정/도움 패널
- 핵심: 각 Task에서 바로 “시작/완료/가이드 보기”가 가능해야 함

---

## 3) 백엔드 계약 (확정/추가)

현재 사용:
- `GET /api/v1/roadmaps/{roadmap_id}/detail`
- `PATCH /api/v1/roadmaps/tasks/{step_id}` body: `{ "status": "PENDING|IN_PROGRESS|COMPLETED|BLOCKED" }`

추가 예정(API v1 유지):
1. `GET /api/v1/roadmaps/{roadmap_id}/execution`
- 목적: UI 친화적 구조(phase 그룹 + task 정렬 + progress 계산) 단일 응답 제공

2. `PATCH /api/v1/roadmaps/tasks/{step_id}/action/{action_id}`
- 목적: 체크리스트 action 단위 완료 처리(후속)

3. 상태 전이 에러 코드 정규화
- `PREVIOUS_STEP_INCOMPLETE`
- `INVALID_STATUS_TRANSITION`
- `STEP_NOT_FOUND`

---

## 4) 프론트 구현 계획 (우선순위)

## P0. 실행 화면 골격 (필수)
1. `RoadmapExecutionPage` 레이아웃 3컬럼 구성
2. `PhaseTimeline` 컴포넌트
3. `TaskExecutionPanel` 컴포넌트
4. `RoadmapSidePanel` 컴포넌트(진행률/일정/도움 카드)

완료 기준:
- 상세 로드맵 로드 후 시안과 유사한 정보 구조 표시

## P1. 상태 전이/즉시 반영 (필수)
1. Task 카드에 상태 버튼(`시작`, `완료`, `보류`)
2. `PATCH /roadmaps/tasks/{step_id}` 연동
3. 낙관적 업데이트 + 실패 롤백
4. 현재 단계 강조/다음 단계 자동 활성 반영

완료 기준:
- 사용자 액션 후 1초 내 UI 상태 반영

## P2. Action 상세 실행 (권장)
1. 체크리스트/법적근거/서류 목록 분리 렌더
2. 체크리스트 action 완료 토글(후속 API 연동)
3. 문서/근거 링크 클릭 추적

완료 기준:
- 단계 내부 task-action 단위 진행 가능

## P3. 대시보드 동기화 (필수)
1. `/dashboard`에서 현재 단계/진행률 동일 계산
2. 로드맵 생성 전/생성 중/생성 후 상태를 `/roadmap`과 동일하게 표시

완료 기준:
- 두 화면에서 진행률/현재 단계 표시값 불일치 0건

---

## 5) 구현 순서 (작업 단위)

1. API 응답 어댑터 정의 (`execution view model`)
2. 화면 골격 컴포넌트 추가 (목업 데이터)
3. 실제 API 연동 및 상태 전이 버튼 연결
4. 에러/빈/로딩 상태 정리
5. 대시보드 동기화 점검
6. QA + 린트/빌드/테스트

---

## 6) 테스트 계획

백엔드:
- `pytest`:
  - 정상 전이: `PENDING -> IN_PROGRESS -> COMPLETED`
  - 순서 위반 차단: 이전 단계 미완료 상태에서 완료 시도
  - 자동 진행: 완료 후 다음 단계 `IN_PROGRESS`

프론트:
- `npm run lint`, `npm run build`
- 수동 시나리오:
  1) 생성 완료 로드맵 진입
  2) 1단계 완료 처리
  3) 다음 단계 자동 활성화 확인
  4) 대시보드 반영 확인

---

## 7) 위험요소 및 대응

1. 응답 구조 복잡도 증가
- 대응: `execution` 전용 view model로 분리

2. 프론트 상태 분기 증가
- 대응: `EMPTY/GENERATING/EXECUTION_READY` 명시 상태머신 유지

3. 상태 전이 규칙 누락
- 대응: 서버 규칙 우선 + 프론트는 메시지 매핑만 수행

---

## 8) 즉시 다음 작업 (이번 스프린트)

1. `/roadmap`에 실행형 레이아웃 골격(P0) 적용
2. Task 상태 버튼 + PATCH 연동(P1) 적용
3. `/dashboard`와 현재 단계/진행률 동기화 검증(P3) 완료
