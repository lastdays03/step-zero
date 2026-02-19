# PLAN-rag-driven-roadmap-dashboard: RAG 기반 상세 로드맵/대시보드 연동 계획

> **Goal**: `RAG -> Roadmaps -> Dashboard` 의존 구조를 기준으로, RAG에서 검색/정리한 절차 데이터를 기반으로 단계별 상세 로드맵을 생성하고 대시보드까지 일관되게 노출한다.

---

## 1) 현재 상태 요약 (As-Is)

- `RAG` 응답은 현재 `answer: string` 단일 필드 중심.
- `Roadmaps` 생성은 현재 하드코딩 기본 단계(`build_default_steps`)를 사용.
- `Dashboard`는 저장된 `roadmap_steps`를 집계/요약해 표시.
- 결론: 현재 구현은 `RAG -> Roadmaps` 직접 연동이 없다.

---

## 2) 목표 상태 (To-Be)

- RAG가 `업종/지역/설명` 맥락에서 절차 후보를 구조화된 형태(JSON)로 반환.
- Roadmaps는 해당 구조 데이터를 정규화/검증하여 "상세 단계"로 저장.
- Dashboard는 상세 단계를 요약 규칙으로 렌더링(현재 단계, 진행률, 남은 작업).
- 실패 시 fallback(기본 템플릿 단계)로 강등하여 서비스 중단 방지.

---

## 3) 핵심 결정사항 (먼저 확정)

### 3.1 합의 완료 항목 (2026-02-19)

1. 생성 방식: **비동기 잡 + 폴링 갱신**
- 생성 중 다른 화면 이동 허용
- 복귀 시 `job_id` 기준 상태/결과 재조회

2. 출력 강제: **JSON 스키마 강제 + 이탈 시 재생성(retry)**
- 자유 텍스트 출력은 실패로 처리
- 재시도 한도 초과 시 fallback

3. 생성 구조: **2단계 생성**
- 1차: 전체 로드맵(상위 단계/위상) 생성
- 2차: 각 상위 단계별 상세 로드맵 생성

4. 상세 생성 실행: **병렬 처리**
- 동시성 제한(예: 2~3)으로 부하 제어

5. 비동기 잡 런타임: **ARQ**
- 스택: `FastAPI + Redis + ARQ`

6. API 경로 전략: **Jobs API 분리**
- 생성 시작: `POST /api/v1/roadmaps/jobs`
- 상태 조회: `GET /api/v1/roadmaps/jobs/{job_id}`
- 결과 조회: `GET /api/v1/roadmaps/jobs/{job_id}/result`

### 3.2 설계 기준 항목

1. **RAG 출력 계약**
- 최소 필수 필드: `phase`, `step_order`, `title`, `objective`, `checklist[]`, `legal_basis[]`, `documents[]`, `estimated_days`, `risk_notes`.

2. **DB 모델링 방식**
- 확정: `roadmap_step_details`/`roadmap_step_actions` 분리 테이블(B안).

3. **생성 파이프라인**
- `RagService`(검색/근거)와 `RoadmapComposer`(구조화/검증)를 분리.
- LLM 출력 검증 실패 시 fallback 템플릿 적용.

4. **API 계약**
- `POST /api/v1/roadmaps/jobs`로 생성 시작(비동기).
- `GET /api/v1/roadmaps/{id}`는 상세 단계 반환.
- `GET /api/v1/dashboard`는 요약 스키마 유지 + 상세 기반 계산.

---

## 4) 단계별 실행 계획

## Phase 0. 분석/설계 고정 (Day 1)
**목표**: 구현 전 계약과 데이터 구조를 확정한다.

- [ ] RAG 출력 JSON 스키마 초안 작성
- [ ] 샘플 프롬프트/샘플 출력 3세트(업종/지역 케이스) 검증
- [ ] DB 변경안(A/B) 비교 후 최종 선택
- [ ] API 변경 명세 초안(OpenAPI 기준) 작성
- [ ] fallback 정책 문서화

**산출물**
- `RAG 출력 스키마`
- `Roadmap 상세 데이터 모델 명세`
- `API 계약서 v1`

## Phase 1. 백엔드 골격 구현 (Day 2)
**목표**: 생성 파이프라인과 저장 구조를 먼저 안정화한다.

- [ ] ARQ 워커/큐 구성(생성 잡 실행 파이프라인)
- [ ] Jobs API 3종 구현(생성 시작/상태 조회/결과 조회)
- [ ] Roadmap 상세 저장 모델/리포지토리 구현(`roadmap_step_details`, `roadmap_step_actions`)
- [ ] Alembic 마이그레이션 작성
- [ ] `RoadmapComposer` 구현(LLM 출력 검증 + 정규화)
- [ ] `RoadmapService`를 RAG 연동 흐름으로 변경
- [ ] fallback 경로(기본 단계) 연결

**검증**
- [ ] 단위 테스트: 파서/검증/정규화
- [ ] 통합 테스트: 생성 API 성공/실패/강등 시나리오

## Phase 2. 조회/요약 계층 정리 (Day 3)
**목표**: 상세 로드맵과 대시보드 계산 규칙을 일치시킨다.

- [ ] `GET /roadmaps/{id}` 상세 응답 확장
- [ ] 대시보드 진행률 계산을 상세 단계 기준으로 보정
- [ ] 상태 전이 규칙(`PENDING/IN_PROGRESS/COMPLETED/BLOCKED`) 고정

**검증**
- [ ] dashboard API 회귀 테스트
- [ ] 기존 클라이언트 호환성 확인(v1 유지)

## Phase 3. 프론트 연동 (Day 4)
**목표**: placeholder 제거 후 실제 데이터 플로우로 전환한다.

- [ ] 채팅형 수집/상태 전이는 `docs/planning/PLAN-roadmap-ui-states.md` 기준으로 구현
- [ ] `/roadmap` 페이지 placeholder 제거
- [ ] 로드맵 미생성(empty) 전용 UX 플로우 적용
- [ ] 생성 폼 -> 생성 API -> 상세 렌더 연결
- [ ] 단계별 checklist/legal_basis/documents 렌더 컴포넌트 추가
- [ ] 로딩/에러/빈 상태 명시

**검증**
- [ ] `npm run build`
- [ ] 주요 사용자 플로우 수동 점검(생성 -> 조회 -> 대시보드 반영)

## Phase 4. 안정화/릴리즈 게이트 (Day 5)
**목표**: 운영 가능한 품질 기준으로 고정한다.

- [ ] 성능/실패율 관측 포인트 추가(로그/메트릭)
- [ ] 프롬프트/출력 버전 관리 키 도입
- [ ] 운영 문서 업데이트(개발 가이드, API 변경점, fallback 정책)

**최종 게이트**
- [ ] `cd app-backend && .venv/bin/pytest -q`
- [ ] `cd app-frontend && npm run lint`
- [ ] `cd app-frontend && npm run build`
- [ ] 마이그레이션 체크(`./scripts/check_migrations.sh`)

---

## 5) 리스크 및 대응

1. **LLM 출력 불안정**
- 대응: strict JSON schema validation + retry + fallback template.

2. **법적 근거 누락/왜곡**
- 대응: `legal_basis` 필수화, 비어있으면 단계 생성 강등.

3. **스키마 변경에 따른 프론트 깨짐**
- 대응: API 타입 자동 동기화(`types:sync`)를 병행.

4. **성능 저하**
- 대응: RAG 검색/생성 분리, 타임아웃/캐시/비동기 처리 적용.

---

## 6) 완료 기준 (Definition of Done)

- RAG 기반으로 생성된 상세 단계가 DB에 저장되고 조회 가능하다.
- 대시보드가 해당 상세 단계를 기준으로 진행률/현재 단계를 정확히 표시한다.
- RAG 실패/빈 결과에서도 fallback 로드맵으로 사용자 플로우가 유지된다.
- 테스트/린트/빌드/마이그레이션 체크가 모두 통과한다.

---

## 7) 로드맵 생성 절차 상세 설계 (핵심)

## 7.1 입력 계약 (Generation Input)

**요청 필드**
- `business_type` (필수): 업종
- `location` (필수): 지역
- `description` (선택): 사업 설명/추가 맥락
- `goal_horizon_days` (선택, 기본 30): 계획 기간
- `experience_level` (선택): `BEGINNER | INTERMEDIATE | ADVANCED`

**전처리 규칙**
- 공백/금칙어 정리, 최대 길이 제한(예: description 2,000자)
- 업종/지역 normalize(동의어 매핑)
- 필수값 누락 시 422

## 7.2 생성 파이프라인 (Async Job + 2단계 생성)

### A. Job API 흐름

1. `POST /api/v1/roadmaps/jobs`
- 입력 검증 후 `job_id` 발급
- 상태: `QUEUED`

2. `GET /api/v1/roadmaps/jobs/{job_id}`
- 상태 조회: `QUEUED | RUNNING | SUCCEEDED | FAILED`
- 진행률: `0~100`
- 현재 단계: `MASTER_GENERATING | DETAIL_GENERATING | PERSISTING`

3. `GET /api/v1/roadmaps/jobs/{job_id}/result`
- 완료 시 생성된 `roadmap_id`와 요약 정보 반환

### B. 내부 처리 단계

1. **Intent Build**
- 입력을 기반으로 검색 질의 세트 생성
- 예: 인허가, 신고, 위생/안전, 세무, 고용 관련 쿼리 분해

2. **Master Roadmap 생성 (1차)**
- RAG 검색 결과를 바탕으로 상위 단계(phase list) 생성
- JSON schema validate (실패 시 retry)

3. **Step Detail 생성 (2차, 병렬)**
- 각 상위 단계에 대해 상세 단계를 병렬 생성
- 동시성 제한 적용(예: semaphore 2~3)
- 각 단계별 JSON schema validate (실패 단계만 retry)

4. **Validation & Normalization**
- 단계 순서/중복/필수 필드/근거 누락 검증
- 임계치 초과 실패 시 fallback 템플릿 강등

5. **Persist**
- roadmap + step + detail 저장
- 생성 메타(`generation_mode=RAG|FALLBACK`, `prompt_version`, `rag_trace_id`) 저장

6. **Job 완료**
- `SUCCEEDED`: `roadmap_id` 바인딩
- `FAILED`: 실패 이유 코드 기록

## 7.3 출력 계약 (Structured Output Schema)

```json
{
  "title": "강남구 카페 창업 로드맵",
  "summary": "지역/업종 규제를 반영한 30일 실행 계획",
  "phases": [
    {
      "phase": "준비",
      "steps": [
        {
          "step_order": 1,
          "title": "입지 및 업종 규제 확인",
          "objective": "핵심 인허가 리스크 사전 제거",
          "checklist": ["용도지역 확인", "필수 신고 항목 확인"],
          "legal_basis": [
            {
              "title": "식품위생법 제37조",
              "snippet": "영업허가 관련 조항",
              "source_url": "https://..."
            }
          ],
          "documents": [
            {"name": "영업신고서", "type": "FORM", "source_url": "https://..."}
          ],
          "estimated_days": 3,
          "risk_notes": ["입지 부적합 시 초기 계획 재수립 필요"]
        }
      ]
    }
  ]
}
```

## 7.4 검증 규칙 (Guardrails)

**필수 검증**
- 단계 최소 개수(예: 3), 최대 개수(예: 12)
- `step_order` 연속성(1..N)
- `title/objective/checklist/legal_basis` 비어있음 금지
- `legal_basis.source_url` 형식 검증
- 동일 title 중복 금지

**품질 검증**
- checklist 항목 최소 2개
- estimated_days 합계가 `goal_horizon_days` 범위 내인지 확인
- 법적 근거 없는 단계는 `BLOCKED` 또는 fallback 치환

## 7.5 상태 전이 모델

- `PENDING`: 시작 전
- `IN_PROGRESS`: 현재 진행 단계
- `COMPLETED`: 완료
- `BLOCKED`: 근거/서류 부족으로 진행 불가

**전이 규칙**
- 기본은 선형 진행(이전 단계 완료 후 다음 단계 시작)
- 강제 완료 금지(관리자 override 제외)
- `BLOCKED` 해소 시 `PENDING` 복귀 가능

## 7.6 fallback 전략

**트리거**
- RAG unavailable
- LLM 출력 파싱 실패
- 근거 필드 누락 임계치 초과

**동작**
- 업종별 기본 템플릿 단계 생성
- 응답 메타에 `generation_mode=FALLBACK` 포함
- 사용자 메시지: “기본 계획으로 생성됨, 근거 보강 필요”

## 7.7 관측/운영 지표

- `roadmap_generation_total{mode}`
- `roadmap_generation_failed_total{reason}`
- `roadmap_generation_latency_ms`
- `roadmap_fallback_ratio`
- `legal_basis_missing_ratio`

목표 SLO(초안)
- 생성 성공률 >= 95%
- fallback 비율 <= 20% (초기), <= 5% (안정화)

## 7.8 테스트 시나리오 (핵심 케이스)

1. 정상 케이스: 업종/지역 입력 -> RAG 생성 -> 상세 단계 저장/조회
2. RAG 실패 케이스: fallback 생성/응답 검증
3. 파싱 실패 케이스: 재시도 후 fallback
4. 근거 누락 케이스: 단계 상태 `BLOCKED` 처리 검증
5. 대시보드 반영 케이스: 진행률/현재 단계 계산 일치 검증

---

## 8) RAG 품질/성능 평가 계획 (운영 필수)

## 8.1 평가 목표

- 로드맵 생성에 필요한 근거 품질을 정량적으로 측정/관리
- 릴리즈 전/후 성능 비교 가능하도록 동일 기준 유지

## 8.2 평가 축과 지표

### A. Retrieval 품질
- `Recall@k`: 정답 근거 문서가 top-k에 포함되는 비율
- `MRR`: 정답 근거 문서의 상위 노출 정도
- `Context Precision`: 검색 컨텍스트 중 유효 문서 비율

### B. Generation 품질
- `Schema Valid Rate`: JSON 스키마 통과율
- `Citation Coverage`: 단계별 `legal_basis` 포함율
- `Hallucination Rate`: 근거 없는 진술 비율
- `Task Usefulness`: 단계/체크리스트 실행 가능성 점수(루브릭 기반)

### C. 성능/운영
- `P95 latency`: 상위 생성/하위 생성/전체 완료
- `Fallback ratio`
- `Retry rate`
- `Failure reason distribution`

## 8.3 골든셋(평가 데이터셋) 설계

- 초기 30~50 시나리오로 시작
- 필드:
  - `business_type`, `location`, `description`
  - 기대 근거 키워드/법령 식별자
  - 기대 단계명(핵심 3~6개)
- 난이도 구분:
  - Easy: 일반 업종/지역
  - Medium: 지역 특수 규제 포함
  - Hard: 복합 조건/예외 케이스

## 8.4 실행 방식

1. 오프라인 배치 평가 스크립트 실행
- 입력: 골든셋 JSON
- 출력: run 결과(JSON) + 요약 리포트(Markdown)
- 저장 경로: `.temp/artifacts/rag-eval/<run_id>/`

2. 자동화 주기
- PR/브랜치: 샘플 10건 스모크 평가
- 야간/릴리즈 전: 전체 평가셋 실행

3. 통과 기준(초안)
- `Schema Valid Rate >= 95%`
- `Citation Coverage >= 90%`
- `Fallback ratio <= 20%`(초기), `<= 10%`(안정화)
- `P95 전체 생성 시간 <= 45s` (비동기 기준)

## 8.5 운영 관측 대시보드

- 최근 7일 `fallback ratio`, `schema fail`, `retry`, `p95`
- 업종/지역별 실패 히트맵
- 모델/프롬프트 버전별 성능 비교

## 8.6 단계별 실행 우선순위

1. 골든셋 30건 작성
2. 평가 스크립트 1차 구현(리트리벌/스키마/지연시간)
3. CI 스모크 게이트 연결
4. 주간 리포트 운영

---

## 9) 즉시 실행 상세 구현 계획 (90분 단위)

## 9.1 Block A (0~90분): 백엔드 기초 골격

- [ ] 모델 추가
  - `roadmap_generation_jobs`
  - `roadmap_step_details`
  - `roadmap_step_actions`
- [ ] Alembic 마이그레이션 추가
- [ ] ARQ 의존성/워커 엔트리 추가
- [ ] Jobs API 스키마 초안 추가

## 9.2 Block B (90~180분): 생성 잡 플로우 연결

- [ ] `POST /roadmaps/jobs` 구현
  - job 생성 + 큐 enqueue
- [ ] `GET /roadmaps/jobs/{job_id}` 구현
  - 상태/진행률/실패코드 조회
- [ ] `GET /roadmaps/jobs/{job_id}/result` 구현
  - 완료된 roadmap id/result 조회
- [ ] ARQ task에서 상태 전이 처리
  - `QUEUED -> RUNNING -> SUCCEEDED|FAILED`

## 9.3 Block C (180~270분): 생성 로직 1차(안전모드)

- [ ] 2단계 생성 뼈대 구현
  - 마스터 단계 생성
  - 상세 단계 병렬 생성(동시성 제한)
- [ ] JSON validate + retry(최대 2회) 적용
- [ ] 실패 시 fallback 템플릿 강등
- [ ] roadmap/detail/action 저장까지 연결

## 9.4 Block D (270~360분): 조회/검증

- [ ] `GET /roadmaps/{id}` 상세 응답 확장
- [ ] 대시보드 집계에 영향 없는지 회귀 확인
- [ ] 테스트 실행
  - backend pytest
  - migration check

---

## 10) 로드맵 미생성(Empty) 화면 설계 및 구현 계획

## 10.1 상태 정의

- `EMPTY`: 생성된 로드맵 없음
- `FORM`: 생성 입력 폼 노출
- `LOADING`: 상태 확인/생성 진행 중
- `ERROR`: 상태 조회 또는 생성 실패
- `READY`: 생성된 로드맵 존재

## 10.2 Empty 화면 구성 원칙

- 사용자가 "지금 무엇을 해야 하는지"를 1초 내에 이해할 것
- 메인 CTA는 하나(`로드맵 생성 시작`)로 고정
- 보조 안내는 3개 이하(입력 정보/예상 시간/중간 이탈 가능)
- 생성 중 다른 화면 이동 가능 정책을 명시

## 10.3 UI 구성 요소

1. 헤드라인/서브카피
- 헤드라인: "아직 생성된 로드맵이 없습니다"
- 서브카피: 업종/지역 입력 후 개인화 로드맵 생성 안내

2. 안내 카드(3개)
- 입력 정보: 업종/지역/설명
- 처리 방식: 비동기 생성 + 자동 갱신
- 소요 시간: 평균 생성 시간 범위

3. 액션 버튼
- Primary: `로드맵 생성 시작`
- Secondary: `상태 다시 확인`

4. 오류 영역
- 실패 원인 요약 + 재시도 버튼

## 10.4 완료 기준 (DoD)

- 로드맵 미생성 계정에서 `/roadmap` 진입 시 Empty 화면 노출
- 로드맵 미생성 계정에서 `/dashboard` 본문도 동일 Empty Hero 노출
- CTA 클릭 시 생성 폼으로 전환
- 조회 오류 시 오류 상태와 재시도 동작 제공
- 빌드 통과 및 모바일/데스크톱 레이아웃 깨짐 없음
