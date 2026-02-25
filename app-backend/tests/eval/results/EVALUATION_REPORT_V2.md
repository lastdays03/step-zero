# RAG-ActionKit 통합 연동 평가 리포트 V2

> 작성일: 2026-02-25
> 선행 리포트: `EVALUATION_REPORT.md` (V1, rag-upgrade Step 1~5 완료, 2026-02-24)
> 기준 baseline: `baseline.json` (git commit 8789565, 2026-02-24 측정)
> 로드맵 평가: `roadmap_eval_results.json` (mock 모드, 2026-02-25 측정)

---

## 목차

1. [Executive Summary](#1-executive-summary)
2. [챗봇 품질 메트릭 추이](#2-챗봇-품질-메트릭-추이)
3. [로드맵 품질 메트릭 (신규)](#3-로드맵-품질-메트릭-신규)
4. [구현 변경사항 요약](#4-구현-변경사항-요약)
5. [아키텍처 변경](#5-아키텍처-변경)
6. [개인화 평가 결과](#6-개인화-평가-결과)
7. [테스트 커버리지](#7-테스트-커버리지)
8. [잔여 이슈 및 후속 작업](#8-잔여-이슈-및-후속-작업)
9. [비용 분석](#9-비용-분석)
10. [결론](#10-결론)

---

## 1. Executive Summary

### 작업 범위

RAG-ActionKit 통합 연동 계획(`dev/active/rag-integration/rag-integration-plan.md`)에 정의된 3단계(Phase 1~3), 24개 태스크를 기반으로 진행되었다. V1(rag-upgrade Step 1~5) 완료 시점의 baseline 위에서 출발하여 다음 세 축의 개선을 목표로 했다.

- **Phase 1 (데이터 정합성)**: 골든 데이터셋 커버리지 교정, 키워드 라우터 확장, 법령 데이터 재적재
- **Phase 2A (챗봇 고도화)**: SemanticRouter(임베딩 기반 분류), 한국어 시스템 프롬프트, metadata-aware 검색 포맷, retriever k=3→5
- **Phase 2B (로드맵 ActionKit 매칭)**: ActionKitMatcher, LLMPersonalizer, RoadmapGenerationService 리팩토링, metadata_json에 actionkit_item_id 추가
- **Phase 3 (통합 평가 체계)**: 로드맵 평가 메트릭 5종, roadmap_evaluator.py, 골든 데이터셋 8건(기본 5건 + 개인화 변형 3건), Tier 4 평가 추가

### 주요 성과

| 항목 | 상태 |
|------|------|
| 커버리지 매핑표 작성 (coverage-matrix.md) | 완료 |
| legal-001~015 커버리지 분석 (6건 유지 / 9건 교체 대상 확인) | 완료 |
| 로드맵 평가 메트릭 5종 구현 | 완료 (mock) |
| 로드맵 골든 데이터셋 8건 작성 | 완료 |
| mock 평가 전체 시나리오 통과 (overall 0.8333) | 완료 |
| Tier 2 (챗봇 품질) 재실행 | 실행 대기 |
| Tier 4 (E2E 통합) 실제 평가 | 실행 대기 |

### 잔여 항목

- T-1.2: golden_dataset.json에서 교체 대상 9건 질문 재작성 (커버리지 밖 → ActionKit 커버 가능 주제)
- T-1.3: `classify_query` 키워드 사전 확장 (+7개: 행정심판, 행정조사, 소방, 개인정보, 근로계약, 화재배상, 원산지)
- T-1.4: 기존 법령 샘플 3건 청킹 재적재
- T-2A.1~2A.6: 챗봇 고도화 코드 구현 (SemanticRouter, 한국어 프롬프트, metadata format)
- T-2B.1~2B.5: 로드맵 ActionKit 매칭 코드 구현 (ActionKitMatcher, LLMPersonalizer)
- T-3.5: 전체 Tier 2~4 실제 실행 및 최종 baseline 갱신

---

## 2. 챗봇 품질 메트릭 추이

아래 표는 V1 완료 시점의 최종 baseline(`baseline.json`, git 8789565)과 rag-integration 계획의 목표치를 비교한다. Phase 1~2A 구현 후 Tier 2 재실행은 **실행 대기** 상태이므로, "Phase 2A 후" 열은 예상 개선치를 나타낸다.

| 메트릭 | V1 Baseline (2026-02-24) | Phase 2A 후 (예상) | 목표 | 달성 가능성 |
|--------|:---:|:---:|:---:|:---:|
| Routing Accuracy | 80.0% | ~95% | 95%+ | 실행 대기 |
| Hit Rate@3 | 86.1% | ~90% | 90%+ | 실행 대기 |
| Faithfulness | 0.73 | ~0.80 | 0.80+ | 실행 대기 |
| Answer Relevancy | 0.44 | ~0.60 | 0.60+ | 실행 대기 |
| Answer Correctness | 0.36 | ~0.55 | 0.55+ | 실행 대기 |

> 주: V1 Baseline 수치는 `baseline.json` 실측값이며, "Phase 2A 후" 수치는 계획서 섹션 1(예상 성과)에서 인용한 목표치이다. 실제 Tier 2 재실행 전까지는 예상치로 취급한다.

### V1 Baseline 세부 수치 (실측, 2026-02-24)

```json
{
  "routing_accuracy": 0.80,
  "hit_rate_at_3": 0.8605,
  "faithfulness": 0.7326,
  "answer_relevancy": 0.4395,
  "answer_correctness": 0.3643,
  "case_count": {
    "legal": 43,
    "general": 2,
    "routing_edge": 2,
    "out_of_scope": 5
  }
}
```

### V1 대비 V0 변화 (참고: rag-upgrade 효과)

| 메트릭 | V0 (업그레이드 전) | V1 (업그레이드 후) | 변화 |
|--------|:---:|:---:|:---:|
| Hit Rate@3 | 41.2% | 86.1% | +44.9pp |
| Faithfulness | 0.15 | 0.73 | +0.58 |
| Answer Correctness | 0.00 | 0.36 | +0.36 |
| Answer Relevancy | 0.24 | 0.44 | +0.20 |
| Routing Accuracy | 78.9% | 80.0% | +1.1pp |

### V1 라우팅 오분류 분석 (9건 잔존)

V1 골든 데이터셋 45건 중 36건 정확, 9건 오분류. 오분류 원인별 구분:

| 원인 | 건수 | 대상 질문 키워드 |
|------|:---:|----------------|
| 키워드 사전 미등록 (legal → general 오분류) | 7 | 행정심판(2건), 행정조사(1건), 소방(1건), 화재배상(1건), 개인정보(1건), 근로계약(1건) |
| 과잉 매칭 (general → legal 오분류) | 2 | "창업" (routing-001), "투자" (routing-002) |

Phase 1(T-1.3) 키워드 사전 확장으로 7건 해소 가능. 과잉 매칭 2건은 SemanticRouter(Phase 2A)의 의미 기반 분류로 해소 예상.

---

## 3. 로드맵 품질 메트릭 (신규)

로드맵 생성 품질을 정량화하기 위해 5종의 신규 메트릭을 정의하고, mock 모드로 8개 시나리오를 평가했다(`roadmap_eval_results.json`, 2026-02-25).

### 3.1 전체 요약

| 메트릭 | 목표 | Mock 평가 결과 | 평가 모드 | 비고 |
|--------|:---:|:---:|:---:|------|
| actionkit_mapping_rate | 80%+ | **100%** (1.0) | mock | 모든 단계가 ActionKit에 매핑됨 |
| legal_basis_accuracy | 70%+ | **25%** (0.25) | mock (keyword_match) | 목표 미달 — mock 데이터 한계 |
| document_validity | 90%+ | **100%** (1.0) | mock (n/a) | 문서 0건 (mock에서 미생성) |
| generation_success_rate | 95%+ | **100%** (1.0) | mock | 8건 전부 정상 생성 |
| personalization_score | 70%+ | **91.7%** (0.9167) | mock | 목표 초과 달성 |
| overall_score | - | **83.3%** (0.8333) | mock | 종합 점수 |

> legal_basis_accuracy가 25%인 이유: mock 데이터에서 법령명이 "관련 법령 1~N" 형태의 플레이스홀더로 생성되어 keyword_match 방식으로는 관련성 판단 불가. 실제 구현(Phase 2B) 완료 후 실제 법령명이 입력되면 목표 70%+ 달성 예상.
>
> document_validity가 100%이나 실제 문서가 0건인 이유: mock 모드에서 문서 파일 경로를 생성하지 않아 "검증 대상 없음(n/a)"으로 처리됨. Phase 2B ActionKitMatcher 구현 후 실제 파일 경로가 연결되어야 의미 있는 측정 가능.

### 3.2 시나리오별 상세 결과

| 시나리오 ID | 설명 | ActionKit 매핑률 | legal_basis 정확도 | 개인화 점수 | 종합 점수 |
|:-----------:|------|:---:|:---:|:---:|:---:|
| roadmap-001 | 카페 / 서울강남 / 신규 / 초보자 | 1.00 | 0.00 | 0.67 | 0.73 |
| roadmap-002 | 일반음식점 / 부산 / 신규 / 경험자 | 1.00 | 0.00 | 1.00 | 0.80 |
| roadmap-003 | 편의점 / 대구 / 신규 / 초보자 | 1.00 | 0.00 | 0.67 | 0.73 |
| roadmap-004 | 프랜차이즈 음식점 / 인천 / 프랜차이즈 / 초보자 | 1.00 | **1.00** | 1.00 | **1.00** |
| roadmap-005 | 미용실 / 수원 / 신규 / 경험자 | 1.00 | 0.00 | 1.00 | 0.80 |
| roadmap-006 | 카페 / 서울강남 / 신규 / 초보자 (빠른 오픈) | 1.00 | 0.00 | 1.00 | 0.80 |
| roadmap-007 | 카페 / 서울강남 / 양수양도 / 경험자 | 1.00 | 0.00 | 1.00 | 0.80 |
| roadmap-008 | 일반음식점 / 부산 / 프랜차이즈 / 초보자 | 1.00 | **1.00** | 1.00 | **1.00** |

> roadmap-004와 roadmap-008은 `non_empty_check` 모드로 legal_basis 정확도 1.0 달성. 나머지 6건은 mock 플레이스홀더 법령명으로 인해 `keyword_match` 모드에서 0.0.

### 3.3 개인화 신호 검출 현황

| 시나리오 | 신호 검출 | 총 신호 | 미반영 신호 |
|---------|:---:|:---:|------------|
| roadmap-001 | 2/3 | 3 | timeline (6개월 미반영) |
| roadmap-002 | 3/3 | 3 | - |
| roadmap-003 | 2/3 | 3 | timeline (6개월 미반영) |
| roadmap-004 | 4/4 | 4 | - |
| roadmap-005 | 3/3 | 3 | - |
| roadmap-006 | 3/3 | 3 | - |
| roadmap-007 | 4/4 | 4 | - |
| roadmap-008 | 4/4 | 4 | - |

`business_type`과 `experience_level`은 8건 모두 정상 반영. `startup_type`(프랜차이즈, 양수양도)도 감지된 4건 모두 반영. `open_timeline` 6개월은 roadmap-001, roadmap-003에서 미반영 — mock 생성 데이터에서 일정 관련 텍스트가 포함되지 않은 것으로 추정.

---

## 4. 구현 변경사항 요약

### 4.1 Phase 1: 데이터 정합성

**T-1.1 커버리지 매핑표 작성 (완료)**

`dev/active/rag-integration/coverage-matrix.md` 작성. legal-001~015 총 15건 분석 결과:

- 유지 가능(커버됨): 6건 — legal-001, 002, 003, 008, 009, 015
- 교체 필요(커버리지 밖): 9건 — legal-004, 005, 006, 007, 010, 011, 012, 013, 014

커버리지 밖 9건의 주된 이유는 ActionKit이 식품접객업 창업 특화 법규(건축법, 식품위생법, 소방법, 행정법)와 세무·인사·공고 키트로 구성되어 있어, 주류판매 허가·상법 자본금·전자상거래법·가맹사업법·개인정보보호법 등이 미포함이기 때문이다.

**T-1.2 질문 재작성 (잔여)**

교체 대상 9건을 ActionKit 커버 가능 주제(건축법 용도 분류, 학교보건법 교육환경보호구역, 소방시설 설치 의무, 행정기본법 제재처분 제척기간 등)로 재작성 예정.

**T-1.3 키워드 사전 확장 (잔여)**

`app/features/rag/application/chat_service.py`의 `classify_query()` frozenset에 7개 키워드 추가 예정: "행정심판", "행정조사", "소방", "개인정보", "근로계약", "화재배상", "원산지".

**T-1.4 법령 샘플 재적재 (잔여)**

기존 법령 샘플 3건을 `scripts/seed_rag_vectors.py`를 통해 청킹 재적재 예정. 완료 시 legal-001~003, legal-008, legal-009, legal-015 답변 품질 향상 예상.

**T-1.5~1.6 Tier 1/2 검증 (실행 대기)**

T-1.2~1.4 완료 후 Tier 1(구조 테스트) 및 Tier 2(메트릭 평가) 순차 실행 예정.

### 4.2 Phase 2A: 챗봇 고도화

**T-2A.1 시스템 프롬프트 한국어 전환 (잔여)**

`rag_service.py` 및 `chat_service.py`의 영어 프롬프트를 다음 구조로 교체 예정:

```
[역할] 한국 창업 법률/행정 전문 AI 어시스턴트
[규칙] 컨텍스트에 없으면 솔직히 모른다고 답변
[형식] 관련 법령 인용, 불릿 포인트, 출처 명시
[톤] 창업 초보자가 이해할 수 있는 쉬운 한국어
```

**T-2A.2 format_docs_with_metadata 교체 (잔여)**

현재 `format_docs`는 `doc.page_content`만 연결하여 출처 정보를 버린다. 아래 형식으로 교체 예정:

```python
def format_docs_with_metadata(docs):
    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        header = f"[출처 {i}] {meta.get('title', '제목 없음')} ({meta.get('category', '')})"
        ref = f"법령 참조: {meta.get('law_reference', '')}"
        parts.append(f"{header}\n{ref}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)
```

**T-2A.3 retriever k=3 → k=5 상향 (잔여)**

`rag_service.py` 내 retriever 설정 변경. 314벡터에서 3개만 검색하던 것을 5개로 늘려 다양한 ActionKit 소스 노출.

**T-2A.4 SemanticRouter 구현 (잔여)**

`app/features/rag/application/semantic_router.py` 신규 작성. 임베딩 코사인 유사도 기반 분류, threshold 0.7, fallback은 기존 LEGAL_KEYWORDS 매칭.

**T-2A.5 ChatService.classify_query → SemanticRouter 교체 (잔여)**

T-2A.4 완료 후 ChatService에서 SemanticRouter 호출로 교체.

**T-2A.6 챗봇 단위 테스트 갱신 (잔여)**

`tests/eval/test_tier1_basic.py` 내 라우팅 테스트를 SemanticRouter 기준으로 갱신.

### 4.3 Phase 2B: 로드맵 ActionKit 매칭

**T-2B.1 ActionKitMatcher 구현 (잔여)**

`app/features/roadmaps/application/actionkit_matcher.py` 신규 작성. 벡터 유사도 검색(k=10) + 관계형 DB JOIN(ActionKitItem + Highlight + RelatedLaw + File) 하이브리드 방식.

**T-2B.2 LLMPersonalizer 구현 (잔여)**

`app/features/roadmaps/application/llm_personalizer.py` 신규 작성. ActionKit 구조화 데이터 + GenerationPayload 전체를 입력으로 7가지 영역(checklist, legal_basis, documents, phases, objective, risk_notes, estimated_days)을 맞춤화.

핵심 규칙: ActionKit이 제공한 법령명과 파일경로는 LLM이 수정 금지. LLM은 "판단하고 맞춤화"하는 역할만 수행.

**T-2B.3 RoadmapGenerationService 리팩토링 (잔여)**

현재 아키텍처(LLM 자유 생성 → DB 저장)에서 신규 아키텍처(ActionKit 매칭 → LLM 맞춤화 → DB 저장, fallback 포함)로 변경. 환각 기반 legal_basis와 존재하지 않는 document URL 문제 해소 목표.

**T-2B.4 metadata_json에 actionkit_item_id 추가 (잔여)**

`app/repositories/roadmap_repository.py`에서 `RoadmapStepAction.metadata_json`에 `actionkit_item_id`, `actionkit_domain`, `actionkit_category` 필드 추가. 스키마 마이그레이션 없이 기존 JSON 필드 확장으로 구현.

**T-2B.5 로드맵 생성 통합 테스트 (잔여)**

`tests/integration/test_roadmap_generation.py` 신규 작성. ActionKit 매핑 → LLM 맞춤화 → DB 저장 전 과정 검증.

### 4.4 Phase 3: 통합 평가 체계

**T-3.1 로드맵 평가 메트릭 구현 (완료)**

`scripts/eval/roadmap_evaluator.py` 구현. 5종 메트릭 정의 및 측정 가능.

**T-3.2 run_evaluation.py에 --tier 4 추가 (완료)**

E2E 통합 평가 경로 추가. 시나리오 기반: 업종 입력 → 로드맵 생성 → 항목 검증.

**T-3.3 로드맵 골든 데이터셋 작성 (완료)**

`tests/eval/data/roadmap_golden_dataset.json` 8건 작성:
- 기본 시나리오 5건 (roadmap-001~005): 업종 다양화(카페, 일반음식점, 편의점, 프랜차이즈 음식점, 미용실)
- 개인화 비교 변형 3건 (roadmap-006~008): 동일 업종/지역에서 startup_type, experience_level, budget_range 변경

**T-3.4 개인화 품질 평가 (완료)**

비교 쌍 2개에 대해 개인화 수준 측정:
- 쌍 1: roadmap-006 vs roadmap-007 (카페 / 신규 BEGINNER vs 양수양도 EXPERIENCED)
- 쌍 2: roadmap-008 vs roadmap-002 (프랜차이즈 음식점 BEGINNER vs 일반음식점 EXPERIENCED)

**T-3.5 전체 Tier 2~4 실행 (실행 대기)**

Phase 2A, 2B 구현 완료 후 실제 환경에서 전체 평가 실행 및 baseline 갱신 예정.

**T-3.6 baseline 갱신 (본 리포트가 임시 문서)**

Tier 2~4 실제 실행 완료 후 `roadmap_baseline.json` 및 `baseline.json`을 최종 수치로 갱신 예정.

**T-3.7 회귀 감지 임계값 조정 (완료)**

`run_evaluation.py`에 personalization_score(임계 0.70) 포함 신규 메트릭 회귀 감지 기준 추가.

---

## 5. 아키텍처 변경

### 5.1 챗봇 아키텍처: Before vs After

**Before (V1 — rag-upgrade 완료 시점)**

```
사용자 질문
    |
    v
classify_query()         ← 키워드 13개 frozenset 매칭
    |                       "법", "허가", "등록", "신고", "인가", "규정",
    |                       "법률", "법령", "조례", "면허", "신청", "영업", "위생"
    |
    +-- "legal"  -->  RagService.query()
    |                  retriever k=3
    |                  format_docs (page_content만 반환)
    |                  영어 시스템 프롬프트
    |                  "You are an AI assistant for startup founders..."
    |
    +-- "general" -> ChatOpenAI
                      영어 시스템 프롬프트
                      "You are a friendly AI assistant..."
```

문제: 9건 오분류, 메타데이터 손실, 한국어 답변 품질 저하, k=3으로 다양성 부족

**After (V2 목표 — Phase 2A 완료 후)**

```
사용자 질문
    |
    v
SemanticRouter (신규)      ← 임베딩 코사인 유사도 분류
    |  의도 벡터 vs 카테고리 앵커 벡터
    |  threshold 0.7 이상 --> "legal"
    |  fallback --> LEGAL_KEYWORDS 확장 매칭 (+7개)
    |
    +-- "legal"  -->  EnhancedRagService (수정)
    |                  retriever k=5 (3 --> 5)
    |                  format_docs_with_metadata (출처 포함)
    |                  한국어 시스템 프롬프트
    |                  ActionKit 메타데이터(title, category, law_reference) 컨텍스트 주입
    |
    +-- "general" -> ChatOpenAI
                      한국어 시스템 프롬프트 (수정)
```

### 5.2 로드맵 생성 아키텍처: Before vs After

**Before (V1 — LLM 자유 생성)**

```
RoadmapGenerationService.process_job()
    |
    v
_generate_master_with_retry()    ← rag_service.query(프롬프트)
    |                               LLM이 phases 자유 생성
    v
_generate_details_parallel()     ← phase별 rag_service.query(프롬프트)
    |                               LLM이 checklist/legal_basis/documents 자유 생성
    v
create_steps_with_details()      ← DB 저장
    |
결과: 환각 기반 legal_basis, 존재하지 않는 document URL, 개인화 부재
```

**After (V2 목표 — ActionKit 팩트 + LLM 맞춤화)**

```
Step 1: ActionKit 매칭 (팩트 레이어)
ActionKitMatcher (신규)
    |  1. 벡터 유사도 검색: "{business_type} 창업" --> k=10
    |     --> metadata에서 item_id 추출
    |  2. 관계형 DB 조회:
    |     --> ActionKitItem + Highlight + RelatedLaw + File
    |  3. 카테고리별 그룹핑 --> phase 결정
    v  MatchedActionKit 리스트 (구조화된 팩트 데이터)

Step 2: LLM 맞춤화 (지능 레이어)
LLMPersonalizer (신규)
    |  입력: ActionKit 구조화 데이터 + GenerationPayload 전체
    |
    |  GenerationPayload 활용:
    |    business_type    --> ActionKit 매칭 키
    |    location         --> 지역별 조례/임대 환경 반영
    |    startup_type     --> 절차 완전 분기 (신규/프랜차이즈/양수양도)
    |    open_timeline    --> phase 병행 여부, estimated_days 조정
    |    budget_range     --> 정책자금 우선순위, 규모 기준
    |    experience_level --> 체크리스트 세분화, 용어 설명 유무
    |
    |  LLM 역할 7가지:
    |    1. checklist    : highlights 원문 --> 우선순위 재배열 + 필터 + 보충
    |    2. legal_basis  : 법령명/요약 --> 업종 중요 조항 강조
    |    3. documents    : 파일 경로 --> 제출 순서 + 준비 가이드
    |    4. phases       : 카테고리 구성 --> 순서 + 병행 가능 판단
    |    5. objective    : 업종/지역 맞춤 목표
    |    6. risk_notes   : 업종 특화 위험요소
    |    7. estimated_days: open_timeline 기반 현실적 소요일
    |
    |  규칙: 법령명, 파일경로 수정 금지
    v  개인화된 StepDetail 리스트

Step 3: DB 저장
create_steps_with_details()
    |  RoadmapStepAction.metadata_json에 actionkit_item_id 포함
    |  mapping_source: "actionkit_direct" / "llm_personalized" / "llm_generated"
```

### 5.3 신규 컴포넌트 목록

| 컴포넌트 | 경로 | 상태 | 역할 |
|---------|------|:---:|------|
| SemanticRouter | `app/features/rag/application/semantic_router.py` | 잔여 | 임베딩 기반 의도 분류 |
| format_docs_with_metadata | `app/features/rag/application/rag_service.py` | 잔여 | 메타데이터 포함 문서 포맷 |
| ActionKitMatcher | `app/features/roadmaps/application/actionkit_matcher.py` | 잔여 | 벡터+관계형 DB 하이브리드 매칭 |
| LLMPersonalizer | `app/features/roadmaps/application/llm_personalizer.py` | 잔여 | 7가지 영역 개인화 맞춤화 |
| roadmap_evaluator.py | `scripts/eval/roadmap_evaluator.py` | 완료 | 로드맵 품질 5종 메트릭 측정 |
| roadmap_golden_dataset.json | `tests/eval/data/roadmap_golden_dataset.json` | 완료 | 8개 평가 시나리오 |

---

## 6. 개인화 평가 결과

### 6.1 비교 쌍 설계 목적

개인화가 실질적으로 동작하는지 검증하기 위해 "동일 업종/지역, 다른 입력 조건"으로 비교 쌍을 구성했다. 입력 조건이 다를 때 생성 결과가 충분히 달라야 한다.

### 6.2 비교 쌍 1: 카페 / 신규 BEGINNER vs 양수양도 EXPERIENCED

| 평가 항목 | 측정값 | 해석 |
|----------|:---:|------|
| 체크리스트 차이 (Jaccard) | 1.00 | 두 로드맵의 체크리스트 항목이 완전히 다름 |
| 단계 구성 차이 | 0.33 | 일부 단계가 다르게 구성됨 |
| 위험 메모 차이 | 0.33 | 업종별 위험요소 부분 분기 |
| 예상 소요일 차이 | 0.33 | 일정 차이 반영 |
| **개인화 종합 점수** | **0.60** | **높음** |

입력 차이: startup_type (신규 vs 양수양도), experience_level (BEGINNER vs EXPERIENCED), budget_range (3000만원 vs 1억원)

양수양도 시나리오(roadmap-007)에서 `startup_type: "FOUND (양수양도)"` 신호가 감지되어 개인화 분기가 작동한 것이 확인됨. 단, 체크리스트 항목의 실질적 내용 차이(영업양도 절차 포함 여부)는 Phase 2B 구현 후 실제 평가에서 검증 필요.

### 6.3 비교 쌍 2: 프랜차이즈 음식점 BEGINNER vs 일반음식점 EXPERIENCED

| 평가 항목 | 측정값 | 해석 |
|----------|:---:|------|
| 체크리스트 차이 (Jaccard) | 1.00 | 두 로드맵의 체크리스트 항목이 완전히 다름 |
| 단계 구성 차이 | 0.20 | 프랜차이즈 특화 단계(가맹계약 검토) 포함 여부 반영 |
| 위험 메모 차이 | 0.20 | 가맹사업 위험요소 부분 반영 |
| 예상 소요일 차이 | 0.43 | 3개월 vs 6개월 일정 차이 |
| **개인화 종합 점수** | **0.55** | **높음** |

입력 차이: business_type (프랜차이즈 음식점 vs 일반음식점), startup_type (프랜차이즈 vs 신규), experience_level (BEGINNER vs EXPERIENCED), budget_range (3000만원 vs 1억원)

### 6.4 개인화 평균 차이 지수

평가 결과 `avg_personalization_difference: 0.5772`. 이 수치는 동일 업종/지역에서 사용자 입력이 달라질 때 생성 결과가 평균 57.7% 수준으로 다른 결과를 반환함을 의미한다. mock 모드에서도 유의미한 분기를 보여주고 있으나, Phase 2B 실제 구현 후 측정이 필요하다.

### 6.5 개인화 미반영 케이스 분석

roadmap-001, roadmap-003에서 `open_timeline: "6개월"`이 미반영. mock 생성 데이터에 일정 관련 텍스트("6개월", "병렬 진행" 등)가 포함되지 않아 발생. LLMPersonalizer가 `estimated_days`와 `phases`를 생성할 때 open_timeline을 명시적으로 반영하는 프롬프트 규칙 추가 필요.

---

## 7. 테스트 커버리지

| 테스트 유형 | 대상 파일 | 테스트 수 | 상태 |
|------------|----------|:---:|:---:|
| Tier 1 (기본 구조) | `tests/eval/test_tier1_basic.py` | ~15 | 완료 (V1) |
| Tier 2 (챗봇 메트릭) | 골든 데이터셋 50건 | 50 | 완료 (V1), 재실행 대기 |
| Tier 3 (챗봇+로드맵) | 기존 Tier 2 확장 | - | 잔여 |
| Tier 4 (E2E 통합) | `scripts/eval/run_evaluation.py --tier 4` | 8 | 구조 완료, 실행 대기 |
| SemanticRouter 단위 테스트 | `tests/eval/test_tier1_basic.py` (갱신) | - | 잔여 (T-2A.6) |
| 로드맵 통합 테스트 | `tests/integration/test_roadmap_generation.py` | - | 잔여 (T-2B.5) |
| 로드맵 mock 평가 | `roadmap_eval_results.json` | 8 | 완료 |
| 개인화 비교 평가 | `roadmap_evaluator.py` 비교 쌍 | 2쌍 | 완료 (mock) |

### 골든 데이터셋 구성 현황

| 데이터셋 파일 | 총 건수 | 카테고리 분포 | 상태 |
|-------------|:---:|------------|:---:|
| `golden_dataset.json` | 50건 | legal 43, general 2, routing_edge 2, out_of_scope 5 | 완료 (9건 재작성 대기) |
| `roadmap_golden_dataset.json` | 8건 | 기본 5건 + 개인화 변형 3건 | 완료 |

---

## 8. 잔여 이슈 및 후속 작업

### 8.1 Phase 1 잔여 (고우선순위)

| ID | 태스크 | 이유 | 예상 효과 |
|----|--------|------|----------|
| T-1.2 | golden_dataset.json 교체 대상 9건 재작성 | 커버리지 밖 질문이 Answer Correctness를 낮춤 | Answer Correctness +0.15~0.20 |
| T-1.3 | classify_query 키워드 +7개 확장 | 현재 7건 오분류 발생 | Routing Accuracy +15pp (80% → 95%) |
| T-1.4 | 법령 샘플 3건 청킹 재적재 | legal-* 도메인 답변 실패 보완 | Hit Rate@3 소폭 개선 |

### 8.2 Phase 2 잔여 (핵심 구현)

| ID | 태스크 | 의존성 | 난이도 |
|----|--------|--------|:---:|
| T-2A.1 | 한국어 시스템 프롬프트 전환 | - | M |
| T-2A.2 | format_docs_with_metadata 교체 | - | M |
| T-2A.3 | retriever k=5 상향 | - | S |
| T-2A.4 | SemanticRouter 구현 | 임베딩 모델 재활용 | L |
| T-2A.5 | ChatService SemanticRouter 연동 | T-2A.4 완료 | M |
| T-2B.1 | ActionKitMatcher 구현 | 벡터 DB + 관계형 DB | XL |
| T-2B.2 | LLMPersonalizer 구현 | ActionKitMatcher 완료 | XL |
| T-2B.3 | RoadmapGenerationService 리팩토링 | T-2B.1, T-2B.2 완료 | XL |
| T-2B.4 | metadata_json 확장 | - | M |
| T-2B.5 | 로드맵 통합 테스트 | T-2B.3 완료 | L |

### 8.3 Phase 3 잔여 (평가 완결)

| ID | 태스크 | 선행 조건 |
|----|--------|----------|
| T-3.5 | 전체 Tier 2~4 실제 실행 | Phase 2 전체 완료 |
| T-3.6 | baseline.json, roadmap_baseline.json 최종 갱신 | T-3.5 완료 |

### 8.4 후속 과제 (계획 범위 밖)

계획서 부록 B에 명시된 미해결 이슈 중 본 계획 범위 밖의 항목:

| 코드 | 내용 |
|------|------|
| F-1 | 리랭킹(Reranking) 도입: 검색 결과 재정렬로 Answer Relevancy 추가 개선 |
| F-2 | .temp/rag/ 원본 법령 파일 수집 및 적재 (현재 미확보, 12건 답변 실패 핵심 원인) |
| F-3 | Answer Correctness 목표 0.55+ 달성 후 0.70+ 2차 목표 수립 |
| F-4 | 프론트엔드 로드맵 UI에서 actionkit_item_id를 활용한 원문 링크 제공 |
| F-5 | 지역별 조례 데이터 수집 (location 필드 실질적 활용을 위한 선행 조건) |
| F-6 | open_timeline 6개월 미반영 이슈 해소 (LLMPersonalizer 프롬프트 개선) |

---

## 9. 비용 분석

### 9.1 계획 대비 실제

| 항목 | 계획 예산 | 실제 소비 | 비고 |
|------|:---:|:---:|------|
| Phase 1: Tier 2 재실행 1회 | $3~5 | 실행 대기 | T-1.2~1.4 완료 후 집행 |
| Phase 2A: SemanticRouter 앵커 임베딩 | $0.01 | 실행 대기 | 1회성 |
| Phase 2A: A/B 프롬프트 테스트 20건 | $2~3 | 실행 대기 | 영어 vs 한국어 비교 |
| Phase 2B: LLM 맞춤화 개발 + 테스트 10건 | $8~12 | 실행 대기 | LLMPersonalizer 프롬프트 개발 |
| Phase 3: Tier 2~4 전체 + 개인화 비교 | $18~30 | 실행 대기 | 가장 큰 비중 |
| **합계** | **$31~50** | **$0 (mock 단계)** | 실제 구현 후 집행 |

### 9.2 비용 최적화 고려사항

- SemanticRouter 앵커 벡터 사전 캐싱으로 요청당 임베딩 1회 유지
- Phase 3 Tier 2~4 실행 전 Phase 1~2 완료 확인 후 집행하여 재실행 최소화
- LLMPersonalizer 개발 시 단계별 프롬프트 검증으로 테스트 횟수 절감

---

## 10. 결론

### 달성한 것

V2 작업의 1단계 성과로, **평가 체계의 기반이 완성**되었다.

1. **커버리지 분석 완료**: legal-001~015 전수 분석으로 ActionKit 커버 가능 여부를 정량화했다. 6건 유지 / 9건 교체 기준이 문서화되어 이후 데이터셋 교정 작업의 근거가 마련되었다.

2. **로드맵 평가 체계 구축**: 5종 신규 메트릭(actionkit_mapping_rate, legal_basis_accuracy, document_validity, generation_success_rate, personalization_score)을 정의하고, 8건 골든 데이터셋과 mock 평가를 통해 측정 파이프라인을 검증했다. 전체 mock 점수 0.8333으로 평가 인프라 자체의 안정성을 확인했다.

3. **개인화 지표 확립**: 비교 쌍 분석을 통해 동일 업종에서 사용자 입력이 달라질 때 평균 57.7%의 결과 차이가 발생함을 확인했다. 이 기준치가 Phase 2B 실제 구현 후 비교 기준점이 된다.

### 다음 우선순위

현재 가장 중요한 병목은 **Phase 2B 구현**(ActionKitMatcher, LLMPersonalizer)이다. 이 두 컴포넌트가 완성되어야 로드맵 생성에서 환각 기반 legal_basis가 실제 ActionKit 데이터로 대체되고, legal_basis_accuracy 목표(70%+)를 달성할 수 있다.

Phase 1 (T-1.2~1.4)과 Phase 2A (T-2A.1~2A.5)는 비교적 작은 변경으로 즉각적인 챗봇 품질 개선(Routing Accuracy 80%→95%, Answer Correctness 0.36→0.55+)을 기대할 수 있어 병렬로 진행을 권장한다.

Tier 2~4 실제 평가가 완료된 후 본 리포트를 수치 업데이트하여 최종판으로 확정한다.

---

## 부록: 파일 참조 목록

| 파일 경로 | 설명 |
|----------|------|
| `app-backend/tests/eval/results/EVALUATION_REPORT.md` | V1 최종 평가 리포트 |
| `app-backend/tests/eval/results/baseline.json` | V1 챗봇 메트릭 baseline (실측) |
| `app-backend/tests/eval/results/roadmap_baseline.json` | 로드맵 메트릭 baseline (mock) |
| `app-backend/tests/eval/results/roadmap_eval_results.json` | 로드맵 8건 평가 결과 (mock) |
| `app-backend/tests/eval/data/golden_dataset.json` | 챗봇 골든 데이터셋 (50건) |
| `app-backend/tests/eval/data/roadmap_golden_dataset.json` | 로드맵 골든 데이터셋 (8건) |
| `dev/active/rag-integration/rag-integration-plan.md` | 통합 연동 종합 계획서 |
| `dev/active/rag-integration/coverage-matrix.md` | legal-001~015 커버리지 분석 |
