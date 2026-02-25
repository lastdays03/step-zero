# RAG-ActionKit 통합 연동 종합 계획서

> Last Updated: 2026-02-25
> 선행 태스크: `dev/active/rag-upgrade/` (Step 1~5 완료)

---

## 1. Executive Summary

ActionKit 데이터 46개(314벡터)가 벡터 DB에 적재된 상태에서, 챗봇과 로드맵 생성 시스템이 이 데이터를 **실질적으로 활용**하도록 연동한다. 현재 챗봇은 영어 프롬프트 + 키워드 13개 기반 라우팅으로 ActionKit 지식을 충분히 전달하지 못하며, 로드맵 생성은 LLM 자유 생성에 의존하여 ActionKit의 법적 근거(legal_basis)와 서류(documents)를 정확히 매핑하지 못한다. 이 계획은 데이터 정합성 교정, 챗봇 고도화, 로드맵 직접 매핑의 3단계로 진행하며, 최종적으로 통합 평가 체계를 구축하여 품질을 정량적으로 보증한다.

### 핵심 변경사항
- 골든 데이터셋 교정: legal-001~015 중 커버리지 밖 질문 재작성 + ActionKit 매핑
- 챗봇 라우팅 고도화: 키워드 13개 → 의미 기반 분류기 (임베딩 + 코사인 유사도)
- 시스템 프롬프트 한국어 전환 + ActionKit 메타데이터 활용 프롬프트
- 로드맵-ActionKit 직접 매핑: ActionKit = 팩트 레이어, LLM = 지능 레이어 (맞춤화)
- GenerationPayload 전체 활용: 업종/지역/형태/일정/예산/경험에 따른 개인화
- 통합 평가 파이프라인: 챗봇 품질 + 로드맵 생성 품질 동시 평가

### 예상 성과

| 메트릭 | 현재 baseline | 목표 | 비고 |
|--------|-------------|------|------|
| Hit Rate@3 | 86.1% | 90%+ | 라우팅 개선 효과 |
| Faithfulness | 0.73 | 0.80+ | 한국어 프롬프트 + 메타데이터 주입 |
| Answer Correctness | 0.36 | 0.55+ | 데이터셋 교정 + 프롬프트 개선 |
| Answer Relevancy | 0.44 | 0.60+ | 프롬프트 한국어 전환 효과 |
| Routing Accuracy | 80.0% | 95%+ | 의미 기반 분류기 |
| 로드맵 ActionKit 매핑률 | 0% | 80%+ | 신규 메트릭 |
| 로드맵 legal_basis 정확도 | 미측정 | 70%+ | 신규 메트릭 |
| 로드맵 개인화 수준 | 0% | 70%+ | 신규 메트릭: 사용자 입력(startup_type, budget 등)이 결과에 반영된 비율 |

---

## 2. Current State Analysis

### 2.1 챗봇 시스템 현황

```
사용자 질문
    |
    v
classify_query()         ← 키워드 13개 매칭 (frozenset)
    |                       "법", "허가", "등록", "신고", "인가", "규정",
    |                       "법률", "법령", "조례", "면허", "신청", "영업", "위생"
    |
    +-- "legal"  →  RagService.query()
    |                  retriever k=3, law_vectors
    |                  영어 시스템 프롬프트
    |                  "You are an AI assistant for startup founders..."
    |
    +-- "general" → ChatOpenAI 직접 호출
                      영어 시스템 프롬프트
                      "You are a friendly AI assistant..."
```

**식별된 문제:**

| # | 문제 | 영향 | 근거 |
|---|------|------|------|
| P-3 | classify_query 키워드 사전 불완전 | 9건 오분류 (routing 80%) | 행정심판, 소방, 개인정보 등 미등록 |
| P-4 | 영어 시스템 프롬프트 | 한국어 답변 품질 저하 | Answer Relevancy 0.44 |
| -- | 메타데이터 미활용 | ActionKit 구조화 정보 버림 | format_docs가 page_content만 사용 |
| -- | retriever k=3 고정 | 다양한 ActionKit 소스 노출 부족 | 314벡터 중 3개만 검색 |

### 2.2 로드맵 생성 시스템 현황

```
RoadmapGenerationService.process_job()
    |
    v
_generate_master_with_retry()    ← rag_service.query(프롬프트)
    |                                  LLM이 phases 자유 생성
    v
_generate_details_parallel()     ← phase별 rag_service.query(프롬프트)
    |                                  LLM이 checklist/legal_basis/documents 자유 생성
    v
create_steps_with_details()      ← DB 저장
    |                                  RoadmapStep + RoadmapStepDetail + RoadmapStepAction
    v
결과: LLM 환각 기반의 legal_basis, 존재하지 않는 document URL
```

**식별된 문제:**

| # | 문제 | 영향 |
|---|------|------|
| 1 | LLM이 legal_basis를 자유 생성 | 실제 ActionKit 법령과 불일치 |
| 2 | documents URL이 환각 | source_url이 존재하지 않는 링크 |
| 3 | ActionKit item_id와 무관 | RoadmapStepAction에 ActionKit 추적 불가 |
| 4 | 업종별 맞춤 부재 | 모든 업종에 동일한 자유 생성 |

### 2.3 데이터 정합성 현황

| 항목 | 현황 | 문제 |
|------|------|------|
| golden_dataset legal-001~015 | 15건 | 12건이 "정보를 찾을 수 없습니다"로 답변 실패 |
| 원인 | `.temp/rag/` 부재, 샘플 3건 미적재 | 질문이 ActionKit 커버리지 밖 |
| 벡터 DB | ActionKit 314벡터만 | 기존 법령 샘플 0벡터 |
| baseline metrics | Answer Correctness 0.36 | 목표 0.40 미달 (91% 달성) |

### 2.4 최종 baseline (2026-02-24)

```json
{
  "routing_accuracy": 0.80,
  "hit_rate_at_3": 0.86,
  "faithfulness": 0.73,
  "answer_relevancy": 0.44,
  "answer_correctness": 0.36
}
```

---

## 3. Proposed Future State (목표 아키텍처)

### 3.1 챗봇 아키텍처 (Phase 2 완료 후)

```
사용자 질문
    |
    v
SemanticRouter (NEW)            ← 임베딩 기반 의미 분류
    |  의도 벡터 vs 카테고리 앵커 벡터 코사인 유사도
    |  threshold 0.7 이상 → "legal"
    |  fallback → LEGAL_KEYWORDS 매칭
    |
    +-- "legal"  →  EnhancedRagService (MODIFIED)
    |                  retriever k=5 (3→5 상향)
    |                  한국어 시스템 프롬프트 (NEW)
    |                  metadata-aware format_docs (NEW)
    |                  ActionKit 구조화 응답 (highlights, relatedLaws 활용)
    |
    +-- "general" → ChatOpenAI
                      한국어 시스템 프롬프트 (MODIFIED)
```

### 3.2 로드맵 생성 아키텍처 (Phase 2 완료 후)

**핵심 원칙: ActionKit = 팩트 레이어, LLM = 지능 레이어**
- ActionKit: 정확한 법령명, 체크리스트 원문, 파일 경로 제공 (수정 금지)
- LLM: 업종/지역/형태/일정/예산에 맞춤화 (판단하고 재구성)

```
Step 1: ActionKit 매칭 (팩트 레이어)
─────────────────────────────────────────────
ActionKitMatcher (NEW)
    |  1. 벡터 유사도 검색: "{business_type} 창업" → k=10
    |     → metadata에서 item_id 추출
    |  2. 관계형 DB 조회:
    |     → ActionKitItem + Highlight + RelatedLaw + File
    |  3. 카테고리별 그룹핑 → phase 결정
    |
    v  MatchedActionKit 리스트 (구조화된 팩트 데이터)

Step 2: LLM 맞춤화 (지능 레이어) ← 핵심 변경
─────────────────────────────────────────────
LLMPersonalizer (NEW)
    |  입력: ActionKit 구조화 데이터 + GenerationPayload 전체
    |
    |  GenerationPayload 활용:
    |    - business_type → ActionKit 매칭 키
    |    - location → 지역별 조례/임대 환경 반영
    |    - startup_type (신규/프랜차이즈/양수양도)
    |      → 절차 완전 분기 (양수양도: 영업양도 추가, 신규 등록 제외)
    |    - open_timeline (3개월/6개월)
    |      → phase 병행 여부 결정, estimated_days 조정
    |    - budget_range (3000만/1억)
    |      → 정책자금 우선순위, 인허가 규모 기준 차이
    |    - experience_level (BEGINNER/EXPERIENCED)
    |      → 체크리스트 세분화 수준, 용어 설명 유무
    |
    |  LLM 역할 (7가지):
    |    1. checklist: highlights 원문 → 우선순위 재배열 + 불필요 항목 필터 + 보충
    |    2. legal_basis: 법령명/요약 → 해당 업종에 중요한 조항 강조
    |    3. documents: 파일 경로 → 제출 순서 + 준비 가이드 추가
    |    4. phases: 카테고리 기반 구성 → 순서 조정 + 병행 가능 판단
    |    5. objective: 업종/지역 맞춤 목표 생성
    |    6. risk_notes: 업종 특화 위험요소 생성
    |    7. estimated_days: open_timeline 기반 현실적 소요일 산출
    |
    |  규칙: ActionKit이 제공한 법령명, 파일경로는 수정 금지
    |        LLM은 "판단하고 맞춤화"하는 역할만 수행
    |
    v  개인화된 StepDetail 리스트

Step 3: DB 저장
─────────────────────────────────────────────
create_steps_with_details()
    |  RoadmapStepAction.metadata_json에 actionkit_item_id 포함
    |  mapping_source: "actionkit_direct" | "llm_personalized" | "llm_generated"
```

### 3.3 통합 평가 아키텍처 (Phase 3 완료 후)

```
run_evaluation.py
    |
    +-- --tier 2  →  챗봇 품질 평가 (기존)
    |                  + 라우팅 정확도 (개선)
    |
    +-- --tier 3  →  챗봇 + 로드맵 품질 평가 (확장)
    |                  + 로드맵 ActionKit 매핑률 (신규)
    |                  + 로드맵 legal_basis 정확도 (신규)
    |
    +-- --tier 4  →  E2E 통합 평가 (신규)
                       시나리오 기반: 업종 입력 → 로드맵 생성 → 항목 검증
```

---

## 4. 아키텍처 결정 사항

### 4.1 라우팅 전략: 의미 기반 + 키워드 fallback (하이브리드)

**선택:** 임베딩 코사인 유사도 분류 + LEGAL_KEYWORDS fallback
**근거:**
- 키워드만으로는 "4대보험 가입 절차" 같은 간접 법률 질문을 놓침
- 별도 분류 모델 학습 없이 기존 임베딩 모델(text-embedding-3-small) 재활용
- 카테고리별 앵커 텍스트 5~10개로 초기 구성, 점진적 확장 가능
- 키워드 fallback으로 false negative 최소화

**대안 검토:**
- 키워드만 확장: 구현 간단하나 장기적으로 유지보수 부담
- 전용 분류 모델(fine-tuned): 학습 데이터 부족, 현 규모에서 과도

### 4.2 시스템 프롬프트: 한국어 전환 + 역할 구체화

**선택:** 한국어 프롬프트로 전면 교체
**근거:**
- 모든 사용자 질문이 한국어, 응답도 한국어
- LLM(GPT-4o-mini)의 한국어 이해는 영어 지시보다 한국어 지시에서 더 일관됨
- ActionKit 메타데이터(highlights, relatedLaws)가 한국어

**프롬프트 설계 방향:**
```
[역할] 한국 창업 법률/행정 전문 AI 어시스턴트
[규칙] 컨텍스트에 없으면 솔직히 모른다고 답변
[형식] 관련 법령 인용, 불릿 포인트, 출처 명시
[톤] 창업 초보자가 이해할 수 있는 쉬운 한국어
```

### 4.3 로드맵 매핑: 하이브리드 방식 (ActionKit 팩트 + LLM 맞춤화)

**선택:** ActionKit = 팩트 레이어 (정확한 데이터 제공), LLM = 지능 레이어 (사용자 입력 기반 맞춤화)
**근거:**
- 현재 LLM 자유 생성은 legal_basis에 환각 포함 (존재하지 않는 법조문)
- ActionKit에 이미 정확한 highlights, relatedLaws, files가 구조화되어 있음
- 직접 매핑으로 actionkit_item_id 추적 가능 → 프론트엔드에서 원문 링크 제공
- 그러나 "LLM은 3개만 생성"으로 축소하면 개인화 부재 → **LLM의 역할을 맞춤화로 확대**
- LLM이 7가지 영역에서 팩트 데이터를 사용자 상황에 맞게 재구성

**LLM의 실질적 역할 (7가지):**
1. **checklist**: ActionKit highlights 원문을 받아서 업종에 맞게 우선순위 재배열 + 불필요 항목 필터링 + 보충
2. **legal_basis**: 정확한 법령명/요약을 받아서 해당 업종에 특히 중요한 조항 강조
3. **documents**: 실제 파일 경로를 받아서 제출 순서와 준비 가이드 추가
4. **phases**: 카테고리 기반 구성을 받아서 순서 조정 + 병행 가능 판단
5. **objective**: 업종/지역 맞춤 목표 생성
6. **risk_notes**: 업종 특화 위험요소 생성
7. **estimated_days**: open_timeline 기반 현실적 소요일 산출

**규칙:** ActionKit이 제공한 법령명, 파일경로는 수정 금지. LLM은 "판단하고 맞춤화"만 담당.

**GenerationPayload 활용 전략:**

| GenerationPayload 필드 | LLM 맞춤화 영향 |
|------------------------|----------------|
| `business_type` | ActionKit 매칭 키 |
| `location` | 지역별 조례/임대 환경 반영 |
| `startup_type` (신규/프랜차이즈/양수양도) | 절차가 완전히 다름. 신규: 사업자등록 신규 신청 강조, 양수양도: 영업양도 절차 추가 + 신규 등록 제외, 프랜차이즈: 가맹사업법 관련 추가 |
| `open_timeline` (3개월/6개월) | phase 병행 여부 결정, estimated_days 타이트하게 조정, risk_notes에 일정 차질 위험 추가 |
| `budget_range` (3000만/1억) | 정책자금 phase 우선순위 조정, 소규모/대규모 인허가 기준 차이 반영 |
| `experience_level` (BEGINNER/EXPERIENCED) | 체크리스트 세분화 수준, 용어 설명 유무 |

**대안 검토:**
- LLM 자유 생성 유지 + 후처리 매칭: 매칭 실패율 높음, 부정확
- 완전 템플릿 (LLM 없이): 유연성 부족, 업종/지역 맞춤 불가
- LLM은 3개만 생성 (objective, risk_notes, estimated_days): 개인화 부족, 모든 업종에 동일 checklist 제공

### 4.4 RoadmapStepAction.metadata_json 확장

**선택:** 기존 metadata_json 필드에 actionkit_item_id 추가
**근거:**
- 스키마 변경(마이그레이션) 없이 구현 가능
- JSON 필드이므로 유연한 확장 가능
- 프론트엔드에서 ActionKit 원문 조회 시 item_id 활용

```python
# LEGAL_BASIS 액션 예시
metadata_json = {
    "title": "식품위생법 제37조",
    "snippet": "영업허가를 받으려는 자는...",
    "source_url": None,
    "actionkit_item_id": 5,       # NEW
    "actionkit_domain": "laws",   # NEW
    "actionkit_category": "chapter-2",  # NEW
}
```

### 4.5 검색 결과 포맷: metadata-aware format_docs

**선택:** page_content + metadata(title, category, source) 결합 포맷
**근거:**
- 현재 `format_docs`는 `doc.page_content`만 연결 → 출처 정보 손실
- LLM이 "어떤 법령에서 왔는지" 알아야 정확한 인용 가능
- metadata의 title, category, law_reference를 컨텍스트에 포함

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

---

## 5. Implementation Phases

### Phase 1: 데이터 정합성 + 즉시 수정 (2일)

**목표:** 골든 데이터셋과 실제 데이터 커버리지를 일치시키고, 즉시 적용 가능한 수정을 반영한다.

**담당:** data-analyst + chat-engineer (병렬)

| # | 태스크 | 담당 | 파일 | Size |
|---|--------|------|------|------|
| 1.1 | legal-001~015 vs ActionKit 커버리지 매핑표 작성 | data-analyst | `dev/active/rag-integration/coverage-matrix.md` (신규) | M |
| 1.2 | 커버리지 밖 12건 질문 재작성 (ActionKit 매핑 가능한 질문으로) | data-analyst | `tests/eval/data/golden_dataset.json` | L |
| 1.3 | classify_query 키워드 사전 확장 (+7개) | chat-engineer | `app/features/rag/application/chat_service.py` | S |
| 1.4 | 기존 법령 샘플 3건 청킹 재적재 | data-analyst | `scripts/seed_rag_vectors.py` | M |
| 1.5 | Tier 1 검증 (구조 테스트) | data-analyst | `tests/eval/test_tier1_basic.py` | S |
| 1.6 | Tier 2 재실행 + baseline 비교 | data-analyst | `scripts/eval/run_evaluation.py` | S |

**Phase 1 완료 기준:**
- golden_dataset legal 질문 전체가 ActionKit 커버리지 내
- Routing Accuracy >= 90%
- Answer Correctness >= 0.45 (baseline 0.36 대비 +25%)

### Phase 2: 핵심 연동 구현 (5일)

**목표:** 챗봇과 로드맵 생성에서 ActionKit 데이터를 직접 활용하는 코어 로직을 구현한다.

**담당:** chat-engineer + roadmap-engineer (병렬)

#### Section 2A: 챗봇 고도화 (chat-engineer)

| # | 태스크 | 파일 | Size |
|---|--------|------|------|
| 2A.1 | 시스템 프롬프트 한국어 전환 (RAG + General) | `app/features/rag/application/rag_service.py`, `chat_service.py` | M |
| 2A.2 | format_docs → format_docs_with_metadata 교체 | `app/features/rag/application/rag_service.py` | M |
| 2A.3 | retriever k=3 → k=5 상향 | `app/features/rag/application/rag_service.py` | S |
| 2A.4 | SemanticRouter 구현 (임베딩 기반 분류) | `app/features/rag/application/semantic_router.py` (신규) | L |
| 2A.5 | ChatService.classify_query를 SemanticRouter로 교체 | `app/features/rag/application/chat_service.py` | M |
| 2A.6 | 챗봇 단위 테스트 갱신 | `tests/eval/test_tier1_basic.py` | M |

#### Section 2B: 로드맵 ActionKit 매칭 + LLM 맞춤화 (roadmap-engineer)

| # | 태스크 | 파일 | Size |
|---|--------|------|------|
| 2B.1 | ActionKitMatcher 구현 (벡터 + 관계형 DB 하이브리드 검색) | `app/features/roadmaps/application/actionkit_matcher.py` (신규) | XL |
| 2B.2 | LLMPersonalizer 구현 (ActionKit 팩트 데이터 + GenerationPayload 전체 → 7가지 영역 개인화 맞춤화) | `app/features/roadmaps/application/llm_personalizer.py` (신규) | XL |
| 2B.3 | RoadmapGenerationService 리팩토링 (ActionKit 매칭 → LLMPersonalizer 맞춤화 → DB 저장, fallback 포함) | `app/features/roadmaps/application/roadmap_generation_service.py` | XL |
| 2B.4 | RoadmapStepAction.metadata_json에 actionkit_item_id 추가 | `app/repositories/roadmap_repository.py` | M |
| 2B.5 | 로드맵 생성 통합 테스트 | `tests/integration/test_roadmap_generation.py` (신규) | L |

**Phase 2 완료 기준:**
- 챗봇: Routing Accuracy >= 95%, Faithfulness >= 0.80
- 로드맵: 생성된 legal_basis의 80%+ ActionKit 직접 매핑
- 로드맵: documents의 file_url이 실제 ActionKitFile과 일치
- 로드맵: startup_type/budget_range 등 사용자 입력이 결과에 반영됨 (수동 검증 3건)

### Phase 3: 통합 검증 (2일)

**목표:** 전체 시스템의 품질을 정량적으로 검증하고 baseline을 갱신한다.

**담당:** eval-engineer + data-analyst

| # | 태스크 | 담당 | 파일 | Size |
|---|--------|------|------|------|
| 3.1 | 로드맵 품질 평가 메트릭 구현 (매핑률, 정확도, 개인화 포함 5종) | eval-engineer | `scripts/eval/roadmap_evaluator.py` (신규) | L |
| 3.2 | run_evaluation.py에 --tier 4 추가 (로드맵 E2E) | eval-engineer | `scripts/eval/run_evaluation.py` | L |
| 3.3 | 로드맵 평가 골든 데이터셋 작성 (기본 5건 + 개인화 변형 3건 = 8건) | data-analyst | `tests/eval/data/roadmap_golden_dataset.json` (신규) | L |
| 3.4 | 개인화 품질 평가 (동일 업종, 다른 startup_type/budget/timeline으로 비교) | eval-engineer | `scripts/eval/roadmap_evaluator.py` | M |
| 3.5 | 전체 Tier 2~4 실행 (기본 5건 + 개인화 3건 포함) | eval-engineer | -- | M |
| 3.6 | baseline 갱신 + EVALUATION_REPORT_V2.md 작성 | eval-engineer | `tests/eval/results/` | M |
| 3.7 | 회귀 감지 임계값 조정 (새 메트릭 반영, personalization_score 포함) | eval-engineer | `scripts/eval/run_evaluation.py` | S |

**Phase 3 완료 기준:**
- 모든 Tier 2 메트릭이 목표치 달성
- 로드맵 ActionKit 매핑률 >= 80%
- 로드맵 legal_basis 정확도 >= 70%
- 로드맵 개인화 수준 >= 70% (사용자 입력이 결과에 반영된 비율)
- 개인화 비교 검증: 동일 업종에서 startup_type/budget 변경 시 결과 차이 확인
- EVALUATION_REPORT_V2.md 작성 완료

---

## 6. Risk Assessment

| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|----------|
| SemanticRouter 임베딩 비용 증가 | 낮 | 중 | 앵커 벡터 사전 캐싱, 요청당 임베딩 1회만 |
| legal-001~015 재작성 시 기존 baseline 비교 불가 | 높 | 중 | 교체 전 old_baseline 스냅샷 보존, 변경 로그 기록 |
| ActionKitMatcher 검색 정밀도 부족 | 중 | 높 | 벡터 유사도 + 관계형 DB JOIN 하이브리드로 보완 |
| LLM 맞춤화에서 ActionKit 팩트 변조 (법령명, 파일경로 수정) | 중 | 높 | 프롬프트에 "법령명, 파일경로 수정 금지" 명시 + 후처리 검증 |
| LLM 맞춤화 프롬프트 복잡성으로 인한 품질 불안정 | 중 | 중 | 단계적 프롬프트: 구조 지시 → 맞춤화 지시 → 제약 조건 순서로 구성 |
| GenerationPayload 입력 조합 폭발 (startup_type x budget x timeline) | 중 | 중 | 핵심 3개 조합(신규/프랜차이즈/양수양도)만 우선 검증, 점진적 확장 |
| 프론트엔드 로드맵 UI가 새 metadata 무시 | 낮 | 낮 | metadata_json 하위 호환 유지, 프론트엔드 변경은 후속 |
| 한국어 프롬프트 전환 시 일시적 품질 하락 | 중 | 중 | A/B 비교: 영어 vs 한국어 프롬프트 10건 동시 실행 |
| 로드맵 평가 골든 데이터셋 품질 불균일 | 중 | 중 | 수동 검수 + 실제 로드맵 생성 결과 대조 |

---

## 7. 비용 추정

| 항목 | 비용 |
|------|------|
| Phase 1: Tier 2 재실행 1회 | ~$3-5 |
| Phase 2A: SemanticRouter 앵커 임베딩 | ~$0.01 (1회성) |
| Phase 2A: A/B 프롬프트 테스트 20건 | ~$2-3 |
| Phase 2B: LLM 맞춤화 프롬프트 개발 + 테스트 10건 | ~$8-12 |
| Phase 3: Tier 2~4 전체 실행 2회 + 개인화 비교 평가 | ~$18-30 |
| **합계** | **~$31-50** |

---

## 8. 타임라인

```
Phase 1 (2일)
  T+1  data-analyst: 커버리지 매핑표 + 질문 재작성
       chat-engineer: 키워드 사전 확장 + 샘플 재적재
  T+2  data-analyst: Tier 1/2 검증 + baseline 비교

Phase 2 (5일, 병렬)
  T+3  chat-engineer: 한국어 프롬프트 + metadata format
       roadmap-engineer: ActionKitMatcher 설계 + 구현
  T+4  chat-engineer: SemanticRouter 구현
       roadmap-engineer: LLM 맞춤화 프롬프트 설계 (LLMPersonalizer)
  T+5  chat-engineer: ChatService 통합 + 테스트
       roadmap-engineer: RoadmapGenerationService 리팩토링 (ActionKit→LLM 맞춤화→저장)
  T+6  chat-engineer: retriever k=5 + A/B 테스트
       roadmap-engineer: metadata_json 확장 + 통합 테스트
  T+7  양쪽 버퍼 (예비)

Phase 3 (3일)
  T+8  eval-engineer: 로드맵 평가 메트릭 + 골든 데이터셋 (개인화 변형 포함)
       data-analyst: 로드맵 골든 데이터셋 검수
  T+9  eval-engineer: 개인화 품질 평가 (동일 업종, 다른 입력으로 비교)
  T+10 eval-engineer: 전체 평가 + baseline 갱신 + 최종 리포트
```

**총 기간: 10일 (3 Phases)**

---

## 9. 성공 메트릭

### 챗봇 품질

| 메트릭 | 현재 | 목표 | 측정 방법 |
|--------|------|------|----------|
| Routing Accuracy | 80% | 95%+ | golden_dataset 50건 분류 정확도 |
| Hit Rate@3 | 86% | 90%+ | retriever k=3 기준 관련 문서 적중 |
| Faithfulness | 0.73 | 0.80+ | LLM judge (GPT-4o) |
| Answer Relevancy | 0.44 | 0.60+ | LLM judge (GPT-4o) |
| Answer Correctness | 0.36 | 0.55+ | LLM judge (GPT-4o) |

### 로드맵 품질 (신규)

| 메트릭 | 현재 | 목표 | 측정 방법 |
|--------|------|------|----------|
| ActionKit 매핑률 | 0% | 80%+ | legal_basis 중 actionkit_item_id 보유 비율 |
| legal_basis 정확도 | 미측정 | 70%+ | 매핑된 법령이 해당 업종에 실제 관련되는 비율 |
| documents 유효성 | 미측정 | 90%+ | file_url이 실제 파일로 연결되는 비율 |
| 생성 성공률 | 미측정 | 95%+ | fallback 없이 정상 생성된 비율 |
| 개인화 수준 | 0% | 70%+ | 사용자 입력(startup_type, budget 등)이 결과에 반영된 비율 (LLM judge) |

---

## 부록 A: 팀 구성 및 역할

| 역할 | 미션 | 주요 Phase |
|------|------|-----------|
| data-analyst | 데이터 정합성 확보, golden dataset 교정, 커버리지 매핑 | Phase 1, 3 |
| chat-engineer | 챗봇-ActionKit 지식 연동, 라우팅 고도화, 한국어 프롬프트 | Phase 1, 2A |
| roadmap-engineer | 로드맵-ActionKit 직접 매핑, 템플릿 시스템, legal_basis 정확 연결 | Phase 2B |
| eval-engineer | 통합 평가, 로드맵 생성 품질 평가, baseline 갱신 | Phase 3 |

## 부록 B: 선행 작업 (rag-upgrade) 미해결 이슈 매핑

| 이슈 | 원래 ID | 본 계획에서 해결 | Phase |
|------|---------|----------------|-------|
| 기존 법령 샘플 3건 재적재 | P-1 | T-1.4 | Phase 1 |
| golden_dataset legal-001~015 재검토 | P-2 | T-1.1, T-1.2 | Phase 1 |
| classify_query 키워드 사전 확장 | P-3 | T-1.3 | Phase 1 |
| 시스템 프롬프트 한국어 전환 | P-4 | T-2A.1 | Phase 2 |
| 리랭킹 도입 검토 | P-5 | 후속 (본 계획 범위 밖) | -- |
