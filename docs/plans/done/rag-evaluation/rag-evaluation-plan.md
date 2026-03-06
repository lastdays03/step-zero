# RAG 성능 평가 종합 계획서

> Last Updated: 2026-02-24

---

## 1. Executive Summary

StepZero 프로젝트의 RAG(Retrieval-Augmented Generation) 시스템은 한국 스타트업 창업자를 위한 법률 가이드 챗봇으로, pgvector + OpenAI 기반 파이프라인으로 구축되어 있다. 현재 시스템은 기본적인 유사도 검색과 LLM 생성을 수행하지만, **체계적인 성능 평가 체계가 부재**한 상태였다.

본 계획은 RAG 시스템의 품질을 **객관적으로 측정**하고, **지속적으로 모니터링**하며, **데이터 기반 개선 의사결정**을 내릴 수 있는 평가 프레임워크를 수립하는 것을 목표로 한다.

### 핵심 산출물
- 3-Tier 자동화 평가 파이프라인 (pytest 기반)
- 20개 골든 데이터셋 (수동 큐레이션) + 자동 생성 스크립트
- 8종 핵심 메트릭 측정 체계
- 베이스라인 성능 기록 및 회귀 감지 시스템

---

## 2. 현재 시스템 상태 분석 (As-Is)

### 2.1 RAG 아키텍처 전체 구조

```
┌──────────────────────────────────────────────────────────────────┐
│                    사용자 질문 입력                               │
│                  POST /api/v1/rag/chat                           │
└─────────────────────┬────────────────────────────────────────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │   classify_query()  │  ← 키워드 13개 매칭
            │  (chat_service.py)  │
            └──────┬──────┬───────┘
                   │      │
          "legal"  │      │  "general"
                   ▼      ▼
   ┌───────────────────┐  ┌───────────────────┐
   │    RagService      │  │  General LLM      │
   │   rag_service.py   │  │  (gpt-4o-mini)    │
   └───────┬───────────┘  └───────────────────┘
           │
           ▼
   ┌───────────────────┐     ┌──────────────────┐
   │   PGVector         │────▶│  PostgreSQL +     │
   │   Retriever (k=3)  │     │  pgvector         │
   └───────┬───────────┘     │  "law_vectors"    │
           │                  └──────────────────┘
           │  Top-3 Documents
           ▼
   ┌───────────────────┐
   │  ChatPromptTemplate│  ← 영어 System Prompt
   │  + gpt-4o-mini     │  → 한국어 답변 생성
   └───────┬───────────┘
           │
           ▼
   ┌───────────────────┐
   │    답변 반환       │
   │  source: legal_rag │
   └───────────────────┘
```

### 2.2 각 컴포넌트 상세 분석

#### (A) 데이터 수집 레이어 (`law_fetcher.py`)

| 항목 | 상세 |
|---|---|
| 데이터 소스 | 로컬 파일 (.pdf, .md) |
| 수집 경로 | `.temp/rag/` 디렉토리 재귀 탐색 |
| 카테고리 분류 | 디렉토리 구조에서 자동 추출 (예: `휴게음식점/영업신고/`) |
| PDF 파싱 | pdfplumber (페이지별 텍스트 추출) |
| 확장성 | `LawDataSource` ABC를 통한 API 소스 확장 가능 (미구현) |

**분석**: 단일 소스(로컬 파일)에 의존하며, API 기반 법령 자동 수집(국가법령정보센터 API 등)이 없어 데이터 최신성 보장이 어렵다.

#### (B) ETL 레이어 (`law_etl.py`)

| 항목 | 상세 |
|---|---|
| 변환 모델 | `gpt-4-turbo-preview` (temperature=0) |
| 입력 | 원본 법률 텍스트 (최대 10,000자 잘림) |
| 출력 | ProcessedLawData (title, summary, guide_text, law_reference, category) |
| 에러 처리 | 실패 시 원본 텍스트 500자를 fallback으로 저장 |

**분석**: ETL이 LLM에 의존하므로 변환 품질이 모델 성능에 좌우된다. 10,000자 잘림은 긴 법령의 정보 손실 가능성이 있다.

#### (C) 벡터 저장 레이어 (`vector_store.py`)

| 항목 | 상세 |
|---|---|
| 임베딩 모델 | `text-embedding-3-small` (OpenAI) |
| 벡터 DB | PostgreSQL + pgvector |
| Collection | `law_vectors` |
| JSONB 메타데이터 | title, category, summary, law_reference |
| **청킹 전략** | **없음 - 문서 전체를 1개 벡터로 저장** |

**분석 (핵심 약점)**: 청킹이 없으므로 긴 문서의 경우 임베딩이 전체 내용의 평균 의미를 표현하게 되어, 특정 조항에 대한 정밀 검색이 어려울 수 있다. `text-embedding-3-small`의 최대 입력은 8,191 토큰이므로 긴 문서는 잘릴 위험도 있다.

#### (D) 검색 레이어 (`rag_service.py`)

| 항목 | 상세 |
|---|---|
| 검색 방법 | Cosine similarity (pgvector 기본) |
| Top-K | 3 (고정) |
| 고급 전략 | 없음 (MMR, Reranking, Hybrid 미적용) |

**분석**: k=3은 소규모 문서 컬렉션에서는 충분할 수 있으나, 문서 수가 증가하면 관련 없는 문서가 상위에 오를 확률이 높아진다.

#### (E) 생성 레이어 (`rag_service.py`)

| 항목 | 상세 |
|---|---|
| 모델 | `gpt-4o-mini` (timeout 20s, max_retries 2) |
| System Prompt | **영어** ("You are an AI assistant for startup founders in Korea.") |
| 거부 메시지 | "제공된 법령 문서에서는 해당 정보를 찾을 수 없습니다." |
| 출력 언어 | 한국어 (프롬프트에서 지시) |

**분석**: System prompt가 영어이고 답변은 한국어를 요구하는 언어 불일치가 있다. 이는 답변 품질에 영향을 줄 수 있으며, 한국 법률 용어의 정확한 사용에 제약이 될 수 있다.

#### (F) 쿼리 라우팅 (`chat_service.py`)

| 항목 | 상세 |
|---|---|
| 분류 방법 | 키워드 포함 여부 체크 |
| Legal 키워드 | 법, 허가, 등록, 신고, 인가, 규정, 법률, 법령, 조례, 면허, 신청, 영업, 위생 (13개) |
| 한계 | "4대보험 의무?", "근로계약서 작성법" 등은 general로 오분류 |

**분석**: 키워드 기반 분류는 빠르고 예측 가능하지만, 법률 키워드가 없는 법률 질문을 놓친다. Tier 1 테스트에서 이 한계가 문서화되었다.

### 2.3 식별된 6대 약점 요약

| # | 약점 | 영향도 | 개선 난이도 |
|---|---|---|---|
| 1 | **청킹 부재** | 높음 - 검색 정밀도 저하 | 중 |
| 2 | **단순 검색** (유사도만) | 중간 - 관련 없는 문서 검색 가능 | 중 |
| 3 | **k=3 고정** | 낮음 - 복잡한 질문에 정보 부족 | 낮 |
| 4 | **키워드 라우팅 한계** | 중간 - 법률 질문 누락 | 중 |
| 5 | **Prompt 영어/한국어 불일치** | 중간 - 답변 품질 저하 | 낮 |
| 6 | **평가 체계 부재** | 높음 - 개선 효과 측정 불가 | ← **본 프로젝트에서 해결** |

---

## 3. 평가 전략 상세 설명 (Proposed Future State)

### 3.1 3-Tier 평가 전략의 설계 철학

RAG 평가는 **비용-정밀도 트레이드오프**가 핵심이다. LLM-as-Judge는 정밀하지만 비용과 시간이 든다. 따라서 피라미드 구조로 설계했다:

```
          ┌──────────┐
          │  Tier 3  │  ← 릴리즈 전: GPT-4o 정밀 평가 ($15-25, 15분)
          │ 전체 평가 │     법률 정확성, 환각 분석, 법령 인용 검증
         ┌┴──────────┴┐
         │   Tier 2   │  ← PR/주간: GPT-4o-mini Judge ($2-5, 5분)
         │ LLM 평가   │     Faithfulness, Relevancy, Correctness
        ┌┴────────────┴┐
        │    Tier 1    │  ← 매 커밋: 무비용 (<1초)
        │  기본 검증   │     라우팅, 데이터셋 무결성, 서비스 상태
        └──────────────┘
```

### 3.2 Tier 1 - 무비용 기본 검증 (Gate Keeper)

**목적**: LLM 호출 없이 코드 변경의 기본 건전성을 빠르게 확인
**실행 시점**: 모든 커밋, CI/CD 파이프라인의 첫 번째 단계
**비용**: $0 | **시간**: <1초

#### 테스트 항목 (24개 테스트)

| 클래스 | 테스트 수 | 검증 내용 |
|---|---|---|
| `TestQueryRouting` | 16 | 11개 고정 케이스 + 13개 키워드 전수 + 4개 경계 문서화 |
| `TestGoldenDatasetRouting` | 1 | 골든 데이터셋 전체의 라우팅 정확도 >= 70% |
| `TestServiceBasicBehavior` | 2 | API 키 없을 때 폴백 메시지, 분류 함수 반환값 검증 |
| `TestGoldenDatasetIntegrity` | 5 | 데이터셋 크기, 필수 필드, ID 고유성, 카테고리 분포 |

#### 설계 근거
- 라우팅 오류는 법률 질문이 일반 LLM으로 빠져 **완전히 틀린 답변**이 나올 수 있으므로 최우선 검증
- 골든 데이터셋 무결성은 이후 Tier 2/3의 신뢰성 기반
- 임계값 70%는 키워드 기반 한계를 감안한 현실적 기준 (향후 LLM 라우팅으로 전환 시 상향)

### 3.3 Tier 2 - LLM 기반 메트릭 평가 (Quality Gate)

**목적**: RAG 파이프라인의 핵심 품질 지표를 객관적으로 측정
**실행 시점**: PR 머지 전 또는 주간 정기 실행
**비용**: ~$2-5 (GPT-4o-mini) | **시간**: ~5분

#### 평가 메트릭 상세 해석

##### (1) Faithfulness (충실도) - 임계값 >= 0.50

**정의**: 생성된 답변의 각 주장(claim)이 검색된 컨텍스트에 의해 뒷받침되는 비율

**측정 방식**: LLM Judge가 답변과 컨텍스트를 비교하여 0.0~1.0 점수 부여

**해석 가이드**:
| 점수 범위 | 해석 | 조치 |
|---|---|---|
| 0.9~1.0 | 답변이 컨텍스트에 완전히 근거 | 이상적 상태 |
| 0.7~0.9 | 대부분 근거하나 일부 추론 포함 | 허용 가능, 프롬프트 강화 고려 |
| 0.5~0.7 | 절반 정도만 컨텍스트에 근거 | 경고, 프롬프트 수정 필요 |
| < 0.5 | 심각한 환각(hallucination) | **즉시 조치 필요** |

**왜 0.50인가?**: 초기 베이스라인이므로 보수적으로 설정. 시스템이 완전히 다른 내용을 생성하지 않는다는 최소한의 보장. 베이스라인 측정 후 0.70 이상으로 상향 예정.

##### (2) Answer Relevancy (답변 관련성) - 임계값 >= 0.50

**정의**: 답변이 질문에 실제로 응답하는 정도 (질문과 답변의 의미적 일치)

**측정 방식**: LLM Judge가 질문-답변 쌍을 평가

**해석 가이드**:
| 점수 범위 | 해석 |
|---|---|
| 0.9~1.0 | 질문에 정확히 답함 |
| 0.7~0.9 | 관련있으나 불필요한 정보 포함 |
| 0.3~0.7 | 부분적으로만 관련 |
| < 0.3 | 질문과 무관한 답변 |

**Faithfulness와의 차이**: Faithfulness는 "답변이 컨텍스트에 근거하는가?"이고, Relevancy는 "답변이 질문에 대답하는가?"이다. 둘 다 높아야 좋은 RAG이다.
- Faithfulness 높음 + Relevancy 낮음 = 컨텍스트에서 가져왔지만 엉뚱한 부분을 가져옴 → **Retrieval 문제**
- Faithfulness 낮음 + Relevancy 높음 = 질문에는 잘 답하지만 컨텍스트와 무관 → **Hallucination 문제**

##### (3) Answer Correctness (답변 정확도) - 임계값 >= 0.40

**정의**: 생성된 답변과 골든 데이터셋의 정답(ground truth)이 의미적으로 일치하는 정도

**측정 방식**: LLM Judge가 0-3 정수 스케일로 평가 후 0.0~1.0으로 정규화

| 점수 | 의미 | 정규화 |
|---|---|---|
| 3 | 핵심 의미 완전 일치 | 1.00 |
| 2 | 대체로 정확, 사소한 차이 | 0.67 |
| 1 | 부분적 정확, 핵심 정보 누락 | 0.33 |
| 0 | 핵심 사실 오류 또는 완전 무관 | 0.00 |

**왜 0-3 스케일인가?**: Databricks 연구(2024)에 따르면 0-3 정수 스케일이 0-10 실수 스케일보다 LLM Judge의 일관성이 높고, 인간 평가와의 일치율도 유사하다.

**왜 임계값이 0.40인가?**: RAG이 검색 실패 시 정답과 완전히 다른 답을 할 수 있으므로, 초기에는 "평균적으로 최소 부분적 정확(score 1+)은 나온다"를 보장하는 수준.

##### (4) Hit Rate@3 (검색 적중률) - 임계값 >= 0.60

**정의**: Top-3 검색 결과에 관련 문서가 최소 1개 포함되는 질문의 비율

**측정 방식**: 골든 데이터셋의 `expected_keywords`가 검색 결과에 하나라도 포함되면 hit

**해석**: 검색이 실패하면 아무리 좋은 LLM도 올바른 답을 낼 수 없다. Hit Rate는 RAG의 가장 근본적인 품질 지표이다.

##### (5) RAGAS 프레임워크 메트릭 (선택적)

RAGAS(Retrieval Augmented Generation Assessment)는 EACL 2024에서 발표된 학술 표준 평가 프레임워크:

- **context_precision**: 검색된 chunk 중 관련 있는 비율
- **context_recall**: 정답에 필요한 정보가 검색된 비율
- **faithfulness**: 답변 주장의 컨텍스트 근거 비율 (claim-level)
- **answer_relevancy**: 질문-답변 의미적 일치도

`ragas` 패키지 설치 필요 (`pip install ragas datasets`). 미설치 시 자동 skip.

### 3.4 Tier 3 - 전체 정밀 평가 (Release Gate)

**목적**: 릴리즈 전 법률 도메인 전문성을 포함한 종합 품질 보증
**실행 시점**: 릴리즈 전, 주요 RAG 변경 시
**비용**: ~$15-25 (GPT-4o 사용) | **시간**: ~15분

#### 법률 도메인 전문 평가 항목

##### (1) Legal Accuracy (법률 정확성) - GPT-4o Judge

**왜 GPT-4o인가?**: 법률 사실 판단은 고난이도 추론이 필요하므로 GPT-4o-mini보다 강력한 모델 사용. 비용은 ~15배 높지만 법률 오류의 위험 대비 가치가 있다.

**0-3 스케일 (법률 특화)**:
| 점수 | 기준 | 예시 |
|---|---|---|
| 3 | 완전히 정확, 법령 올바르게 인용 | "식품위생법 제37조에 따라..." |
| 2 | 대체로 정확, 사소한 오류 | 조항 번호 하나 틀림 |
| 1 | 부분적 정확, 핵심 요건/기한 누락 | 기한 3개월을 언급하지 않음 |
| 0 | 법적 사실 오류 | "별도 허가 필요 없음" (실제는 필요) |

**환각 사실(Hallucinated Facts) 추출**: Judge가 답변에서 컨텍스트에 없는 주장을 명시적으로 나열. 이를 통해 어떤 유형의 환각이 빈번한지 패턴 분석 가능.

##### (2) 법령 인용 검증

- **Citation Rate**: 인용이 필요한 케이스에서 실제 법령명/조항이 답변에 포함되는 비율
- **Citation Validity**: 인용된 법령명이 실제 존재하는지 GPT-4o로 검증
- 패턴 매칭: `제\d+조`, `[가-힣]+법`, `시행규칙`, `시행령`

##### (3) 범위 밖 거부 테스트 (Out-of-Scope Refusal)

**법률 RAG 핵심 안전장치**: 모르는 내용을 자신있게 답하는 것(confident hallucination)은 법률 도메인에서 치명적이다.

테스트 질문:
- "일본 식품위생법의 내용은?" (다른 국가 법률)
- "2035년 예상 법률 변화는?" (미래 예측)
- "양자역학의 기본 원리를 설명해주세요" (완전 무관 주제)

거부 응답 인디케이터: "찾을 수 없습니다", "해당 정보", "범위", "알 수 없", "확인되지 않" 등

##### (4) 응답 지연 시간

| 메트릭 | 임계값 | 근거 |
|---|---|---|
| 평균 latency | <= 15초 | 챗봇 UX 적정 기준 |
| 최대 latency | <= 25초 | RagService의 timeout(25초)과 동일 |

---

## 4. 골든 데이터셋 설계

### 4.1 현재 데이터셋 구성 (20개)

| 카테고리 | 수량 | ID 범위 | 설명 |
|---|---|---|---|
| Factual (사실 확인) | 6 | legal-003,005,007,009,011,013 | 직접적 사실 질문 |
| Procedural (절차) | 4 | legal-001,002,006,010 | 절차/방법 질문 |
| Interpretive (해석) | 3 | legal-004,008,014 | 상황 판단 필요 질문 |
| General (일반) | 2 | routing-001,002 | 비법률 질문 |
| Routing Edge (경계) | 2 | routing-003,004 | 라우팅 경계 케이스 |
| Out-of-scope (범위 밖) | 2 | oos-001,002 | 범위 밖 질문 |
| Hard (고난이도) | 1 | legal-015 | 복수 법률 교차 |

### 4.2 각 데이터 필드의 역할

| 필드 | 용도 | 사용하는 Tier |
|---|---|---|
| `id` | 케이스 추적 및 결과 매핑 | 전체 |
| `question` | RAG 입력 | 전체 |
| `ground_truth` | 정답 비교 기준 | Tier 2, 3 |
| `expected_source` | 라우팅 검증 (legal_rag/general) | Tier 1 |
| `category` | 카테고리별 성능 분석 | Tier 2, 3 |
| `difficulty` | 난이도별 성능 분석 | Tier 3 |
| `expected_keywords` | 무비용 Hit Rate 계산 | Tier 1, 2 |
| `expected_law_reference` | 법령 검색 정확도 | Tier 2 |
| `requires_citation` | 인용 필요 케이스 표시 | Tier 3 |

### 4.3 데이터셋 확장 전략

1. **자동 생성**: `generate_golden_dataset.py`로 벡터 DB 문서 기반 Q&A 생성
2. **전문가 검수**: 생성된 Q&A를 법률 전문가가 검토/수정
3. **프로덕션 피드백**: 실제 사용자 질문 중 실패 케이스를 골든 데이터셋에 추가
4. **목표**: 100개 이상 (factual 40%, procedural 25%, interpretive 15%, OOS 10%, edge 10%)

---

## 5. 구현 상세

### 5.1 파일 구조 및 역할

```
app-backend/
├── tests/eval/
│   ├── __init__.py
│   ├── conftest.py                  # pytest fixtures 정의
│   │   ├── golden_dataset()         # 골든 데이터셋 로드
│   │   ├── legal_cases()            # 법률 케이스 필터
│   │   ├── general_cases()          # 일반 케이스 필터
│   │   ├── routing_edge_cases()     # 경계 케이스 필터
│   │   ├── out_of_scope_cases()     # OOS 케이스 필터
│   │   └── ensure_results_dir()     # 결과 디렉토리 보장
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   └── golden_dataset.json      # 20개 수동 큐레이션 Q&A
│   │
│   ├── test_tier1_basic.py          # 24 tests, <1초, $0
│   │   ├── TestQueryRouting          # 라우팅 정확성
│   │   ├── TestGoldenDatasetRouting  # 골든 데이터셋 라우팅
│   │   ├── TestServiceBasicBehavior  # 서비스 기본 동작
│   │   └── TestGoldenDatasetIntegrity # 데이터셋 무결성
│   │
│   ├── test_tier2_metrics.py        # LLM 평가, ~5분, ~$3
│   │   ├── TestRetrievalQuality      # Hit Rate, Context Relevance
│   │   ├── TestGenerationQuality     # Faithfulness, Relevancy, Keywords
│   │   ├── TestEndToEndQuality       # Correctness, E2E Routing
│   │   └── TestRAGASMetrics          # RAGAS 프레임워크 (선택)
│   │
│   ├── test_tier3_full.py           # 전체 평가, ~15분, ~$20
│   │   ├── TestLegalAccuracy         # GPT-4o 법률 정확성
│   │   ├── TestStatuteCitation       # 법령 인용 검증
│   │   ├── TestOutOfScopeRefusal     # OOS 거부율
│   │   ├── TestResponseLatency       # 응답 지연 시간
│   │   └── TestGenerateReport        # 종합 리포트
│   │
│   └── results/                     # 평가 결과 (gitignore 대상)
│       ├── tier1_routing.json
│       ├── tier2_metrics.json
│       ├── faithfulness.json
│       ├── correctness.json
│       ├── legal_accuracy_full.json
│       └── summary_report.json
│
├── scripts/eval/
│   ├── __init__.py
│   ├── run_evaluation.py            # 종합 평가 CLI
│   └── generate_golden_dataset.py   # Q&A 자동 생성
│
└── pyproject.toml                   # eval markers, eval 의존성
```

### 5.2 실행 명령어 체계

```bash
cd app-backend
source .venv/bin/activate

# ─── Tier 1 (매 커밋) ───────────────────
pytest tests/eval/test_tier1_basic.py -v
# 결과: 24 passed in 0.42s

# ─── Tier 2 (PR/주간) ───────────────────
pytest tests/eval/test_tier2_metrics.py -v -s
# 또는 마커로 필터:
pytest -m eval -v -s

# ─── Tier 3 (릴리즈 전) ─────────────────
pytest tests/eval/test_tier3_full.py -v -s
pytest -m full_eval -v -s

# ─── 종합 실행 스크립트 ─────────────────
python -m scripts.eval.run_evaluation --tier 1       # Tier 1만
python -m scripts.eval.run_evaluation --tier 2       # Tier 1+2
python -m scripts.eval.run_evaluation --report-only  # 기존 결과로 리포트만

# ─── 골든 데이터셋 확장 ─────────────────
python -m scripts.eval.generate_golden_dataset --count 50
```

---

## 6. Pass/Fail 임계값 및 의사결정 기준

### 6.1 현재 임계값 (초기 베이스라인)

| 메트릭 | 임계값 | 근거 |
|---|---|---|
| Routing Accuracy | >= 0.70 | 키워드 기반 한계 감안 |
| Faithfulness | >= 0.50 | 최소 환각 방지 보장 |
| Answer Relevancy | >= 0.50 | 최소 관련성 보장 |
| Answer Correctness | >= 0.40 | 평균 "부분적 정확" 이상 |
| Hit Rate@3 | >= 0.60 | 검색 기본 성능 |
| Legal Accuracy | >= 0.50 | 법률 최소 정확성 |
| Refusal Rate | >= 0.30 | OOS 기본 감지 |
| Avg Latency | <= 15s | UX 기준 |

### 6.2 목표 임계값 (1차 개선 후)

| 메트릭 | 초기 | 목표 | 달성 전략 |
|---|---|---|---|
| Routing Accuracy | 0.70 | 0.90 | LLM 기반 의도 분류 |
| Faithfulness | 0.50 | 0.75 | 한국어 프롬프트 + few-shot |
| Answer Relevancy | 0.50 | 0.70 | 프롬프트 최적화 |
| Answer Correctness | 0.40 | 0.65 | 청킹 + Reranking |
| Hit Rate@3 | 0.60 | 0.85 | 청킹 + MMR |
| Legal Accuracy | 0.50 | 0.70 | 청킹 + 법률 프롬프트 |

---

## 7. 위험 평가 및 완화 전략

| 위험 | 확률 | 영향 | 완화 |
|---|---|---|---|
| LLM Judge 불일치 (같은 케이스 다른 점수) | 중 | 중 | temperature=0 고정, 일관성 테스트 추가 |
| 골든 데이터셋 편향 | 중 | 높 | 카테고리 분포 검증, 전문가 검수 |
| API 비용 초과 | 낮 | 중 | Tier별 케이스 수 제한, 비용 추적 |
| 벡터 DB 변경 시 기존 결과 무효화 | 높 | 중 | 버전 태깅, 베이스라인 기록 |
| 한국어 LLM Judge 정확도 | 중 | 높 | GPT-4o (한국어 강함) 사용, 한국어 프롬프트 |
| RAGAS 버전 호환성 | 중 | 낮 | 선택적 import, skip 처리 |

---

## 8. 향후 개선 로드맵

### Phase 1: 베이스라인 측정 (현재)
- [x] 3-Tier 평가 체계 구축
- [x] 골든 데이터셋 20개 작성
- [x] Tier 1 테스트 통과 확인 (24/24 passed)
- [ ] Tier 2 실행 → 베이스라인 기록
- [ ] Tier 3 실행 → 법률 정확성 베이스라인

### Phase 2: 데이터 품질 개선
- [ ] 골든 데이터셋 100개로 확장 (자동 생성 + 전문가 검수)
- [ ] 프로덕션 실패 케이스 수집 파이프라인
- [ ] 벡터 DB 문서 현황 감사

### Phase 3: RAG 파이프라인 개선 (평가 결과 기반)
- [ ] 청킹 도입 → Hit Rate/Context Precision 개선 검증
- [ ] 한국어 프롬프트 전환 → Faithfulness/Relevancy 개선 검증
- [ ] MMR 또는 Hybrid search → 검색 다양성 개선 검증
- [ ] 라우팅 LLM 전환 → Routing Accuracy 개선 검증

### Phase 4: CI/CD 통합
- [ ] GitHub Actions에 Tier 1 자동 실행
- [ ] PR 머지 조건에 Tier 2 통과 추가
- [ ] 주간 Tier 3 스케줄 실행
