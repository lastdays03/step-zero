# RAG 성능 평가 - 컨텍스트 문서

> Last Updated: 2026-02-24

---

## 1. 핵심 파일 맵

### RAG 파이프라인 구현

| 파일 | 역할 | 주요 내용 |
|---|---|---|
| `app/features/rag/application/rag_service.py` | RAG 핵심 서비스 | PGVector retriever(k=3), gpt-4o-mini, 영어 프롬프트 |
| `app/features/rag/application/chat_service.py` | 하이브리드 라우팅 | 키워드 13개 기반 legal/general 분류 |
| `app/features/rag/application/deps.py` | DI 설정 | lru_cache 싱글톤 패턴 |
| `app/api/v1/rag/router.py` | API 엔드포인트 | POST /query, POST /chat |
| `app/services/vector_store.py` | 벡터 저장 | PGVector, text-embedding-3-small, 청킹 없음 |
| `app/services/law_etl.py` | 문서 변환 | gpt-4-turbo-preview로 법률 → 가이드 변환 |
| `app/services/law_fetcher.py` | 데이터 수집 | LocalFileSource (.pdf/.md 파싱) |
| `app/core/config.py` | 설정 관리 | OPENAI_API_KEY, OPENAI_CHAT_MODEL 등 |

### 평가 시스템 구현

| 파일 | 역할 | 주요 내용 |
|---|---|---|
| `tests/eval/conftest.py` | 공통 fixtures | golden_dataset, legal_cases, ensure_results_dir |
| `tests/eval/data/golden_dataset.json` | 골든 데이터셋 | 20개 Q&A (법률15 + 일반2 + 경계2 + OOS2) |
| `tests/eval/test_tier1_basic.py` | Tier 1 테스트 | 24 tests, 라우팅/무결성 (ALL PASSED) |
| `tests/eval/test_tier2_metrics.py` | Tier 2 테스트 | LLM Judge 기반 메트릭 평가 |
| `tests/eval/test_tier3_full.py` | Tier 3 테스트 | GPT-4o 법률 정확성, 인용 검증, OOS 거부 |
| `scripts/eval/run_evaluation.py` | 종합 실행기 | CLI: --tier, --report-only |
| `scripts/eval/generate_golden_dataset.py` | Q&A 생성기 | 벡터 DB 기반 자동 생성 |

### 기존 테스트

| 파일 | 역할 |
|---|---|
| `tests/services/test_rag_service.py` | 단위 테스트 (mock 기반, 2개) |

---

## 2. 기술적 의사결정 기록

### 결정 1: 3-Tier 구조 채택

**배경**: RAG 평가는 LLM 호출 비용이 발생하므로 매 커밋마다 전체 평가를 실행할 수 없다.

**결정**: 비용-정밀도 트레이드오프에 따라 3단계로 분리
- Tier 1: 무비용, 코드 변경의 기본 건전성 (매 커밋)
- Tier 2: 중비용, 핵심 품질 지표 (PR/주간)
- Tier 3: 고비용, 법률 전문 평가 (릴리즈 전)

**대안 검토**:
- 단일 Tier: 비용 과다 또는 정밀도 부족
- 4-Tier+: 과도한 복잡성

### 결정 2: LLM-as-Judge 방식 채택

**배경**: 한국어 법률 도메인에서 BLEU/ROUGE 등 토큰 오버랩 메트릭은 신뢰도가 낮다 (한국어 형태소 특성).

**결정**: GPT-4o-mini/GPT-4o를 Judge로 사용
- 의미적 평가가 가능하여 한국어 특성에 강건
- 0-3 정수 스케일로 일관성 확보 (Databricks 2024 연구 기반)
- temperature=0으로 재현성 보장

**대안 검토**:
- BERTScore (klue/bert-base): 설치 복잡, 법률 특화 부족
- 인간 평가: 비용/시간 과다, 스케일 불가
- ROUGE-KR (KoNLPy): 의미 평가 불가, 형태소 분석 의존성

### 결정 3: 초기 임계값 보수적 설정

**배경**: 베이스라인이 없는 상태에서 높은 임계값은 의미 없는 실패만 유발.

**결정**: 모든 메트릭의 초기 임계값을 낮게 설정 (0.40~0.60)
- 첫 Tier 2 실행으로 베이스라인 측정
- 베이스라인 대비 -10%를 회귀 감지 임계값으로 조정
- 개선 작업 후 단계적으로 상향

### 결정 4: RAGAS를 선택적(optional) 의존성으로 분리

**배경**: RAGAS 패키지는 의존성이 무겁고 (datasets, transformers 등) 자주 breaking change가 있다.

**결정**: `[project.optional-dependencies] eval`에 분리, 미설치 시 pytest.skip

### 결정 5: 골든 데이터셋 수동 큐레이션 우선

**배경**: LLM 자동 생성 Q&A는 실제 사용자 질문 패턴과 차이가 있을 수 있다.

**결정**: 초기 20개는 수동 작성, 이후 자동 생성 + 전문가 검수로 확장
- 수동 작성: 실제 창업자가 물어볼 법한 자연스러운 질문
- 카테고리/난이도/법령 참조 모두 명시
- ID 체계: `legal-XXX`, `routing-XXX`, `oos-XXX`

---

## 3. 의존성 및 전제 조건

### 실행 환경 요구사항

| 항목 | Tier 1 | Tier 2 | Tier 3 |
|---|---|---|---|
| Python | >= 3.11 | >= 3.11 | >= 3.11 |
| pytest | >= 8.0 | >= 8.0 | >= 8.0 |
| OPENAI_API_KEY | 불필요 | 필수 | 필수 |
| DATABASE_URL | 불필요 | 필수 (pgvector) | 필수 |
| Docker (PostgreSQL) | 불필요 | 필수 | 필수 |
| ragas 패키지 | 불필요 | 선택 (auto-skip) | 선택 |

### 패키지 의존성

```toml
# pyproject.toml
[project.optional-dependencies]
eval = [
    "ragas>=0.1.0",
    "datasets>=2.14.0",
]
```

### pytest 마커

```toml
[tool.pytest.ini_options]
markers = [
    "eval: RAG evaluation tests",
    "slow: slow tests that call external APIs",
    "full_eval: full evaluation requiring GPT-4o",
]
```

---

## 4. 평가 메트릭 이론적 배경

### 4.1 RAG Triad (TruLens 모델)

RAG 시스템의 3대 핵심 검증 축:

```
        질문 ─────────────────────── 답변
          │                          ▲
          │  ① Answer Relevance      │  ③ Groundedness
          │  (답변이 질문에 관련?)    │  (답변이 컨텍스트에 근거?)
          │                          │
          ▼                          │
        검색된 컨텍스트 ──────────────┘
              │
              │  ② Context Relevance
              │  (컨텍스트가 질문에 관련?)
              ▼
```

- **① Answer Relevance**: 답변이 질문에 실제로 응답하는가?
- **② Context Relevance**: 검색된 문서가 질문과 관련 있는가?
- **③ Groundedness (=Faithfulness)**: 답변의 주장이 컨텍스트에서 나왔는가?

이 세 축 중 하나라도 낮으면 전체 RAG 품질이 저하된다.

### 4.2 RAGAS 메트릭 산출 방식

**Faithfulness 계산 과정**:
1. 답변에서 개별 주장(claim)을 추출 (예: "기한은 3개월이다", "세무서에 제출한다")
2. 각 주장이 컨텍스트에 의해 뒷받침되는지 판단
3. Faithfulness = 뒷받침되는 주장 수 / 전체 주장 수

**Context Precision 계산 과정**:
1. 검색된 각 문서의 관련성을 판단
2. 관련 문서가 상위 순위에 있을수록 높은 점수
3. Average Precision의 변형

**Context Recall 계산 과정**:
1. 정답(ground truth)의 각 문장을 추출
2. 각 문장이 검색된 컨텍스트에서 뒷받침되는지 판단
3. Recall = 뒷받침되는 문장 수 / 정답의 전체 문장 수

### 4.3 LLM-as-Judge 연구 근거

| 연구 | 핵심 발견 |
|---|---|
| Databricks 2024 | 0-3 정수 스케일이 0-10보다 일관성 높음. 인간 평가와 80%+ 일치율 |
| Braintrust 2025 | RAGAS가 평가 품질 98/100, 하지만 프로덕션 통합은 약함 |
| Snowflake 2024 | TruLens context relevance가 UMBRELA 대비 높은 F1 달성 |
| Ko-LongRAG (EMNLP 2025) | 한국어 RAG 평가 시 형태소 분석 기반 토큰 메트릭 필수 |
| Eval-RAG (NLLP 2023) | 법률 도메인 LLM 평가와 변호사 평가의 낮은 일치 → 검색 기반 검증 병행 필요 |

### 4.4 한국어 특수 고려사항

1. **형태소 특성**: "영업신고를" = "영업" + "신고" + "를" → 단순 문자열 매칭은 부분 매치
2. **교착어**: ROUGE/BLEU 적용 시 KoNLPy 형태소 분석 필수 (본 프로젝트에서는 미사용)
3. **법률 용어**: "제37조의2", "제1항 제3호" 등 고유 패턴 → 정규식 패턴 매칭 적용
4. **LLM Judge 언어**: 한국어 프롬프트로 한국어 텍스트 평가 (GPT-4o 한국어 성능 우수)

---

## 5. 참조 프레임워크 비교

| 프레임워크 | pytest 통합 | 한국어 | 비용 | 우리 채택 |
|---|---|---|---|---|
| **RAGAS** | 부분적 | LLM 의존 | 낮음 | O (선택적) |
| **DeepEval** | 네이티브 | LLM 의존 | 낮음 | 향후 고려 |
| **TruLens** | X (대시보드) | LLM 의존 | 낮음 | 개념만 차용 |
| **LangSmith** | X (SaaS) | LLM 의존 | SaaS | 향후 고려 |
| **Custom LLM Judge** | O | O | 낮음 | **O (주력)** |
| **RAGChecker** | X | 제한적 | 낮음 | X |

**선택 근거**: 한국어 법률 도메인 특수성 때문에 Custom LLM Judge를 주력으로 하고, RAGAS는 표준 메트릭 비교용으로 선택적 사용.

---

## 6. 비용 추정

| Tier | 모델 | 케이스 수 | 추정 비용/회 | 실행 빈도 | 월간 비용 |
|---|---|---|---|---|---|
| Tier 1 | 없음 | 24 tests | $0 | 매 커밋 (~60회/월) | $0 |
| Tier 2 | gpt-4o-mini | 10-15 | ~$2-5 | 주 2회 | ~$16-40 |
| Tier 3 | gpt-4o | 15-20 | ~$15-25 | 월 1-2회 | ~$15-50 |
| **합계** | | | | | **~$31-90/월** |

### 비용 최적화 전략
- Tier 2에서 상위 10개 케이스만 LLM 평가 (전수 아님)
- Tier 3에서 법령 인용 검증은 5개 케이스만 (GPT-4o 비용 절약)
- 결과 캐싱으로 동일 케이스 재평가 방지
