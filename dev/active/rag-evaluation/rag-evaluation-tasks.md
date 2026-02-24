# RAG 성능 평가 - 작업 체크리스트

> Last Updated: 2026-02-24

---

## Phase 1: 평가 인프라 구축 (완료)

### Section 1.1: 평가 프레임워크 설계
- [x] **T-1.1.1** 현재 RAG 시스템 전체 분석 (아키텍처, 약점 식별)
  - Effort: M | Priority: P0
  - 결과: 6대 약점 식별 (청킹 부재, 단순 검색, k=3 고정, 키워드 라우팅, 영어 프롬프트, 평가 부재)

- [x] **T-1.1.2** 3-Tier 평가 전략 설계
  - Effort: M | Priority: P0
  - 결과: Tier 1(무비용) / Tier 2(LLM Judge) / Tier 3(전문 평가) 구조

- [x] **T-1.1.3** 핵심 메트릭 8종 선정 및 임계값 설정
  - Effort: S | Priority: P0
  - 결과: Faithfulness, Relevancy, Correctness, Hit Rate, Legal Accuracy, Citation, Refusal, Latency

### Section 1.2: 골든 데이터셋 구축
- [x] **T-1.2.1** 수동 큐레이션 Q&A 20개 작성 (`golden_dataset.json`)
  - Effort: L | Priority: P0
  - 결과: legal 15 + general 2 + routing edge 2 + OOS 2 = 21개

- [x] **T-1.2.2** 자동 생성 스크립트 작성 (`generate_golden_dataset.py`)
  - Effort: M | Priority: P1
  - 결과: 벡터 DB 문서 기반 GPT-4o-mini Q&A 생성

### Section 1.3: 테스트 코드 구현
- [x] **T-1.3.1** 공통 fixtures 정의 (`conftest.py`)
  - Effort: S | Priority: P0

- [x] **T-1.3.2** Tier 1 테스트 구현 (`test_tier1_basic.py`)
  - Effort: M | Priority: P0
  - 결과: 24 tests 전부 PASS (0.42s)

- [x] **T-1.3.3** Tier 2 테스트 구현 (`test_tier2_metrics.py`)
  - Effort: L | Priority: P0
  - 결과: Retrieval/Generation/E2E/RAGAS 테스트 구현

- [x] **T-1.3.4** Tier 3 테스트 구현 (`test_tier3_full.py`)
  - Effort: L | Priority: P0
  - 결과: Legal accuracy, Citation, OOS refusal, Latency 테스트 구현

- [x] **T-1.3.5** 종합 실행 스크립트 (`run_evaluation.py`)
  - Effort: M | Priority: P1
  - 결과: CLI --tier, --report-only 지원

### Section 1.4: 프로젝트 설정
- [x] **T-1.4.1** pyproject.toml에 eval 마커/의존성 추가
  - Effort: S | Priority: P0

- [x] **T-1.4.2** 계획 문서 작성 (`plan.md`)
  - Effort: M | Priority: P1

---

## Phase 2: 베이스라인 측정 (진행 중)

### Section 2.1: Tier 2 실행 및 베이스라인 기록
- [ ] **T-2.1.1** Docker PostgreSQL + pgvector 기동 확인
  - Effort: S | Priority: P0
  - Acceptance: `docker-compose up -d` 후 벡터 DB 접속 성공

- [ ] **T-2.1.2** Tier 2 테스트 첫 실행
  - Effort: S | Priority: P0
  - Command: `pytest tests/eval/test_tier2_metrics.py -v -s`
  - Acceptance: 모든 테스트 실행 완료 (pass/fail 무관), 결과 JSON 저장

- [ ] **T-2.1.3** 베이스라인 메트릭 기록
  - Effort: S | Priority: P0
  - Acceptance: `tests/eval/results/tier2_metrics.json`에 첫 측정값 저장
  - 기록할 값: Faithfulness, Answer Relevancy, Answer Correctness, Hit Rate@3

- [ ] **T-2.1.4** 베이스라인 기반 임계값 조정
  - Effort: S | Priority: P1
  - Acceptance: 측정된 베이스라인 대비 -10%를 새 임계값으로 설정
  - Depends on: T-2.1.3

### Section 2.2: Tier 3 실행 및 법률 정확성 베이스라인
- [ ] **T-2.2.1** Tier 3 테스트 첫 실행
  - Effort: S | Priority: P1
  - Command: `pytest tests/eval/test_tier3_full.py -v -s`
  - Acceptance: Legal accuracy, citation, refusal 결과 JSON 저장

- [ ] **T-2.2.2** 법률 정확성 분석 리포트 작성
  - Effort: M | Priority: P1
  - Acceptance: 난이도별/카테고리별 정확성 분석, 주요 실패 패턴 식별

- [ ] **T-2.2.3** 종합 베이스라인 리포트 생성
  - Effort: S | Priority: P1
  - Command: `python -m scripts.eval.run_evaluation --report-only`
  - Depends on: T-2.1.3, T-2.2.1

---

## Phase 3: 골든 데이터셋 확장

### Section 3.1: 자동 생성 및 검수
- [ ] **T-3.1.1** 벡터 DB 문서 현황 감사
  - Effort: S | Priority: P1
  - Acceptance: 문서 수, 카테고리 분포, 평균 문서 길이 파악

- [ ] **T-3.1.2** 자동 Q&A 50개 생성
  - Effort: S | Priority: P1
  - Command: `python -m scripts.eval.generate_golden_dataset --count 50`
  - Acceptance: `generated_qa.json` 생성, 50개 Q&A 포함

- [ ] **T-3.1.3** 생성된 Q&A 검수 및 필터링
  - Effort: L | Priority: P2
  - Acceptance: 저품질 Q&A 제거, 정답 수정, 최종 30개+ 선별

- [ ] **T-3.1.4** 골든 데이터셋에 병합 (총 50개+)
  - Effort: S | Priority: P2
  - Acceptance: golden_dataset.json에 병합, Tier 1 무결성 테스트 통과
  - Depends on: T-3.1.3

### Section 3.2: 프로덕션 피드백 수집
- [ ] **T-3.2.1** 사용자 피드백 수집 API 설계
  - Effort: M | Priority: P3
  - Acceptance: 질문, 답변, 평점(1-5), 수정 의견을 저장하는 엔드포인트

- [ ] **T-3.2.2** 실패 케이스 자동 수집 파이프라인
  - Effort: M | Priority: P3
  - Acceptance: 평점 1-2 케이스를 `production_failures.jsonl`에 자동 저장

---

## Phase 4: RAG 파이프라인 개선 (평가 결과 기반)

> Phase 2 베이스라인 결과에 따라 우선순위 결정

### Section 4.1: 검색 품질 개선
- [ ] **T-4.1.1** RecursiveCharacterTextSplitter 도입
  - Effort: M | Priority: 베이스라인 후 결정
  - chunk_size=1000, overlap=200
  - Acceptance: Hit Rate@3이 베이스라인 대비 +10% 이상 개선

- [ ] **T-4.1.2** MMR 또는 Hybrid search 적용
  - Effort: M | Priority: 베이스라인 후 결정
  - Acceptance: Context Precision 개선

- [ ] **T-4.1.3** 동적 k 구현
  - Effort: S | Priority: P3
  - 질문 복잡도에 따라 k=3~7 조절

### Section 4.2: 생성 품질 개선
- [ ] **T-4.2.1** 한국어 System Prompt 전환
  - Effort: S | Priority: P1
  - Acceptance: Faithfulness, Relevancy 개선 검증

- [ ] **T-4.2.2** Few-shot 예시 추가
  - Effort: S | Priority: P2
  - 법률 Q&A 2-3개 예시를 프롬프트에 포함

### Section 4.3: 라우팅 개선
- [ ] **T-4.3.1** LLM 기반 의도 분류 프로토타입
  - Effort: M | Priority: P2
  - Acceptance: Routing Accuracy >= 0.90

---

## Phase 5: CI/CD 통합

### Section 5.1: GitHub Actions 연동
- [ ] **T-5.1.1** Tier 1 CI 자동 실행 설정
  - Effort: S | Priority: P2
  - Acceptance: PR 생성 시 자동 실행, 실패 시 머지 차단

- [ ] **T-5.1.2** Tier 2 주간 스케줄 실행
  - Effort: M | Priority: P3
  - Acceptance: 주 1회 자동 실행, 결과를 Slack/Issue로 알림

- [ ] **T-5.1.3** 회귀 감지 자동화
  - Effort: M | Priority: P3
  - Acceptance: 베이스라인 대비 -10% 이상 하락 시 자동 알림

---

## 진행 상태 요약

| Phase | 상태 | 완료/전체 |
|---|---|---|
| Phase 1: 인프라 구축 | **완료** | 11/11 |
| Phase 2: 베이스라인 측정 | 진행 중 | 0/7 |
| Phase 3: 데이터셋 확장 | 대기 | 0/6 |
| Phase 4: 파이프라인 개선 | 대기 (베이스라인 후) | 0/6 |
| Phase 5: CI/CD 통합 | 대기 | 0/3 |
| **합계** | | **11/33** |

---

## 다음 액션 (Next Steps)

1. **즉시**: Docker 기동 후 Tier 2 첫 실행 (T-2.1.1 → T-2.1.2)
2. **이번 주**: 베이스라인 기록 및 임계값 조정 (T-2.1.3 → T-2.1.4)
3. **다음 주**: Tier 3 실행 + 데이터셋 확장 시작 (T-2.2.1, T-3.1.1)
