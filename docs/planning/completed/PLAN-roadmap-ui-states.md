# PLAN-roadmap-ui-states: 로드맵 생성 UI 상태/질문 플로우 설계

> Goal: 로드맵 생성 UX를 "채팅형 질문 강제 수집" 방식으로 고정하고, 필수 정보가 없으면 생성을 시작하지 않도록 상태 전이와 API 연동 규칙을 정의한다.

> Update (2026-02-19): 현재 구현은 채팅형 수집 대신 `단일 입력 + AI validate` 방식으로 전환되었다.
> 실행형 로드맵 화면의 최신 계획은 `docs/planning/PLAN-roadmap-execution-screen.md`를 기준으로 한다.

---

## 1) 범위

- 대상 화면
  - `/roadmap` (나의 로드맵)
  - `/dashboard` (로드맵 미생성 시 본문 Empty Hero)
- 대상 기능
  - 채팅형 입력 수집
  - 필수값 검증(업종/지역)
  - 생성 시작 후 상태 폴링
  - 생성 완료/실패 분기

---

## 2) UX 원칙

1. 입력은 채팅형(assistant 질문 -> user 응답)으로 진행
2. `업종`, `지역` 2개는 필수. 누락 시 다음 단계 진행 금지
3. 필수값 수집 완료 전에는 생성 API 호출 금지
4. 생성 중 화면은 "진행 여부 폴링"에 집중(복잡한 인터랙션 최소화)
5. 추후 질문 확장은 질문 스키마 추가만으로 가능하도록 설계

---

## 3) 상태 모델

- `EMPTY`: 로드맵 없음, 시작 CTA 노출
- `CHAT_COLLECTING`: 채팅형 질문 수집
- `CHAT_BLOCKED`: 필수값 누락/형식 오류로 진행 불가
- `SUBMIT_READY`: 필수값 충족, 생성 시작 가능
- `GENERATING`: 생성 중(폴링)
- `GENERATED`: 생성 완료
- `FAILED`: 생성 실패

---

## 4) 필수 데이터 계약 (초기)

required:
- `business_type` (업종)
- `location` (지역)

optional:
- `description` (사업 설명)
- `goal_horizon_days` (기본 30)
- `experience_level` (기본 BEGINNER)

검증 규칙:
- 공백/빈 문자열 불가
- 최대 길이 제한(예: 100자)
- 정규화(trim, 내부 공백 정리) 후 저장

---

## 5) 채팅형 질문 플로우

기본 시퀀스:
1. Assistant: "어떤 업종으로 창업을 준비하시나요?"
2. User 입력 -> `business_type` 저장
3. Assistant: "어느 지역에서 시작하시나요?"
4. User 입력 -> `location` 저장
5. Assistant: "(선택) 현재 구상 중인 사업 설명이 있나요?"
6. User 입력/스킵 -> `description` 저장
7. 필수값 검증 통과 시 `SUBMIT_READY`
8. User가 "생성 시작" 클릭 시 Jobs API 호출

진행 차단:
- 필수값 미입력 시 다음 단계 버튼 비활성
- 형식 오류 시 즉시 인라인 메시지 노출

---

## 6) API 연동 규칙

생성 시작:
- `POST /api/v1/roadmaps/jobs`
- payload: 수집된 채팅 데이터
- response: `job_id`

상태 폴링:
- `GET /api/v1/roadmaps/jobs/{job_id}`
- interval: 2초(초기), 3초(30초 이후)
- 종료 조건:
  - `SUCCEEDED`: 결과 조회
  - `FAILED`: 오류 상태 전환
  - 최대 대기 시간 초과: 실패 처리

결과 조회:
- `GET /api/v1/roadmaps/jobs/{job_id}/result`
- `roadmap_id` 획득 후 상세 조회/화면 전환

---

## 7) 생성 중 화면(Generating) 요구사항

필수 요소:
- 현재 상태 문구: "로드맵 생성 중입니다"
- 간단한 단계 표시: 상위 단계 생성 -> 상세 단계 생성 -> 저장
- 폴링 상태 표시(상태값/진행률)
- "다른 화면 이동 가능" 안내

비목표(초기):
- 복잡한 실시간 스트리밍 UI
- 취소 후 롤백

---

## 8) 확장 전략

- 질문 추가 시 `question schema`에 항목만 추가
- 필수/선택 여부를 스키마에서 제어
- 채팅 UI 로직은 스키마 기반 렌더링 유지

예시 확장 필드:
- 예산 범위
- 창업 유형(개인/법인)
- 예상 오픈 시점

---

## 9) 구현 체크리스트

1. 채팅형 수집 컴포넌트 추가
2. 필수값 검증/진행 차단 로직 추가
3. Jobs API 호출로 생성 시작 경로 변경
4. Generating 화면 폴링 연결
5. 성공/실패 상태 분기 처리
6. `/dashboard` 빈 상태 CTA를 채팅형 플로우로 연결

---

## 10) 완료 기준 (DoD)

- 필수값(`업종`, `지역`) 누락 시 생성 시작 불가
- 채팅형 플로우로 필수값 수집 후에만 Jobs API 호출
- 생성 중 화면에서 폴링으로 상태 갱신
- 성공 시 결과 화면 전환, 실패 시 재시도 동작 제공
- `dashboard`와 `roadmap` 양쪽에서 동일한 시작 진입점 제공
