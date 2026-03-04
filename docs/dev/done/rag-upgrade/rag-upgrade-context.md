# RAG 파이프라인 업그레이드 - 컨텍스트 문서

> Last Updated: 2026-02-24

---

## 1. 핵심 파일 맵

### RAG 파이프라인 (수정 대상)

| 파일 | 역할 | 변경 내용 |
|------|------|----------|
| `app-backend/app/services/vector_store.py` | 벡터 저장 | 청킹 로직 추가, 메타데이터 스키마 확장 |
| `app-backend/app/services/law_etl.py` | ETL 변환 | ActionKitETLBridge 추가 (LLM 우회) |
| `app-backend/app/services/law_fetcher.py` | 데이터 수집 | ActionKitDataSource 추가 (LawDataSource ABC 확장) |
| `app-backend/app/features/rag/application/rag_service.py` | RAG 서비스 | k=3→5 상향 검토, metadata filter 옵션 |
| `app-backend/app/core/config.py` | 설정 | ACTIONKIT_STORAGE_PATH 확인 |

### 평가 시스템 (수정 대상)

| 파일 | 역할 | 변경 내용 |
|------|------|----------|
| `app-backend/tests/eval/conftest.py` | pytest fixtures | baseline helper 추가, rag_service fixture 통합 검토 |
| `app-backend/tests/eval/data/golden_dataset.json` | 골든 데이터셋 | oos-003~005 추가 (21→24), Phase 4에서 50+로 확장 |
| `app-backend/tests/eval/test_tier1_basic.py` | Tier 1 테스트 | 미사용 fixture 활용 테스트 추가 |
| `app-backend/tests/eval/test_tier2_metrics.py` | Tier 2 테스트 | latest_run.json 자동 저장 |
| `app-backend/tests/eval/test_tier3_full.py` | Tier 3 테스트 | OOS 하드코딩 제거 → fixture 주입 |
| `app-backend/scripts/eval/run_evaluation.py` | 실행 스크립트 | --update-baseline 플래그 추가, 회귀 감지 |
| `app-backend/scripts/eval/generate_golden_dataset.py` | Q&A 생성 | seed 쿼리 5→13개 확장 |

### ActionKit 데이터 소스

| 파일 | 역할 |
|------|------|
| `app-backend/scripts/seeds/actionkit_seed_source.py` | LAW_DATA(21) + ACTION_KIT_DATA(25) 정의 |
| `app-backend/uploads/actionkit/laws/chapter-{1~6}/` | 법령 PDF 21개 |
| `app-backend/uploads/actionkit/kits/{legal,tax,hr,grant}/` | 킷 파일 25개 (PDF 18 + HWP 6 + PPTX 1) |

### 신규 생성 파일

| 파일 | 역할 |
|------|------|
| `app-backend/app/services/actionkit_data_source.py` | ActionKitDataSource 클래스 |
| `app-backend/app/services/actionkit_etl.py` | ActionKitETLBridge (LLM 우회 변환) |
| `app-backend/scripts/seed_rag_vectors.py` | 통합 재인덱싱 스크립트 |

---

## 2. 기술적 의사결정 기록

### 결정 1: 통합 컬렉션 (law_vectors 단일)

**배경:** ActionKit 문서를 별도 컬렉션(actionkit_vectors)에 저장할지, 기존 law_vectors에 통합할지.

**결정:** 통합 (law_vectors 하나)
**근거:**
- 전체 벡터 수가 500~800개 수준 → 단일 컬렉션으로 충분
- RAG 코드(rag_service.py) 변경 최소화 — retriever 1개 유지
- 메타데이터 `source` 필드로 소스 구분 가능
- 분리 필요 시 메타데이터 기반 마이그레이션 용이

**대안 검토:**
- 분리 (actionkit_vectors): 관리 독립성 확보, 하지만 EnsembleRetriever 또는 라우터 추가 필요 → 복잡도 증가

### 결정 2: 청킹 파라미터

**배경:** 현재 청킹 없음. 문서 전체가 1벡터로 저장.

**결정:** RecursiveCharacterTextSplitter, chunk_size=600, overlap=100
**근거:**
- 한국어 600자 ≈ 900토큰
- k=5일 때 총 4,500토큰, text-embedding-3-small 한도(8,191)의 55%
- ETL 거친 guide_text가 불릿 포인트 구조 → `\n\n` 단락 분리에 최적화
- 원문 법령 PDF는 chunk_size=800, overlap=150으로 별도 적용

**검증:** 재인덱싱 전 샘플 10개로 청크 결과 수동 확인 후 확정

### 결정 3: ActionKit ETL — LLM 우회

**배경:** 기존 LawETLProcessor는 GPT-4-turbo로 변환. ActionKit에도 필요한가?

**결정:** LLM 우회, seed 메타데이터 직접 매핑
**근거:**
- seed 데이터가 이미 사람이 큐레이션한 구조화 데이터 (summary, highlights, relatedLaws)
- LLM 비용 $0
- 기존 ProcessedLawData 포맷과 호환 가능

### 결정 4: 데이터 적재 방식 — 옵션C (seed + 파일 텍스트 결합)

**배경:** seed 메타데이터만? 파일 파싱만? 결합?

**결정:** 결합 (옵션C)
**근거:**
- seed의 summary/highlights는 사용자 질문과 의미적으로 가까움 (창업자 관점)
- 파일 원문은 법적 근거 보강
- 두 소스를 결합하면 검색 + 답변 품질 모두 개선

**파일별 전략:**
- PDF 39개: pdfplumber 파싱 + seed 결합
- HWP 6개 + PPTX 1개: seed 메타데이터만 (파싱 fallback)

### 결정 5: 중복 문서 — 아이템별 별개 적재

**배경:** 46개 파일 중 12개가 중복 (같은 PDF가 다른 챕터/카테고리에 존재)

**결정:** 별개 적재 (중복 허용)
**근거:**
- 같은 식품위생법이라도 chapter-1(입지), chapter-2(영업), chapter-4(준수)에서 다른 검색 컨텍스트
- 벡터 수 증가(34→46 Document 기준)는 허용 범위
- metadata.sha256으로 중복 추적, 검색 후처리 de-dup 가능

### 결정 6: baseline 관리 — C안 (스냅샷 + 자동 생성 병행)

**배경:** 현재 baseline이 수동 작성, 실제 결과와 불일치.

**결정:** baseline.json(고정) + latest_run.json(자동) + --update-baseline 플래그
**근거:**
- 수동 입력 오류 차단 (faithfulness 0.15→0.12 사례)
- 고정 기준점으로 Phase별 개선 효과 측정
- 점진적 악화(gradual degradation) 감지

### 결정 7: OOS 테스트 — A안 (골든 데이터셋 연동)

**배경:** test_tier3_full.py에 OOS 질문 3개 하드코딩, 골든 데이터셋 미사용.

**결정:** 하드코딩 3개를 oos-003~005로 골든 데이터셋에 편입, fixture로만 동작
**근거:**
- 단일 진실 소스 (golden_dataset.json)
- 데이터셋 확장 시 OOS 테스트 자동 확장
- 사문화된 out_of_scope_cases fixture 활용

---

## 3. 데이터 정확성 확인 결과 (seed 파일 직접 카운팅)

### ActionKit 아이템 수 (확정)

| 도메인 | 카테고리 | 아이템 수 |
|--------|---------|-----------|
| laws | chapter-1 (입지 적법성) | 5 |
| laws | chapter-2 (영업 성립 요건) | 3 |
| laws | chapter-3 (안전소방 요건) | 3 |
| laws | chapter-4 (영업 중 준수의무) | 3 |
| laws | chapter-5 (위반 시 대응 절차) | 1 |
| laws | chapter-6 (행정처분 및 구제) | 6 |
| **laws 소계** | | **21** |
| kits | legal (법률 키트) | 11 |
| kits | tax (세무 키트) | 3 |
| kits | hr (인사 키트) | 8 |
| kits | grant (공고문 키트) | 3 |
| **kits 소계** | | **25** |
| **합계** | | **46** |

### 파일 존재 확인 (확정)

| 형식 | 예상 | 실제 | 경로 |
|------|------|------|------|
| PDF | 39 | **39** | uploads/actionkit/{laws,kits}/ |
| HWP | 6 | **6** | uploads/actionkit/kits/hr/ |
| PPTX | 1 | **1** | uploads/actionkit/kits/hr/39/ |
| **합계** | 46 | **46** | 전부 존재 |

### 중복 현황

- 46개 파일 중 **34개 고유** (MD5 기준), **12개 중복**
- laws↔kits 간 동일 파일: 10개 (9그룹)
- laws 내부 동일 파일: 2개 (식품위생법 3회, 시행규칙 2회)

---

## 4. 메타데이터 스키마 (통합 컬렉션용)

```python
metadata = {
    # 공통
    "source": "local" | "actionkit",
    "category": str,           # "휴게음식점" | "actionkit/laws/chapter-1" | "actionkit/kits/tax"
    "title": str,              # 문서 제목
    "chunk_index": int,        # 문서 내 청크 순번
    "total_chunks": int,       # 문서 총 청크 수
    "law_reference": str,      # 법령 참조
    "summary": str,            # 한줄 요약
    # ActionKit 전용
    "domain": "laws" | "kits" | None,
    "item_id": int | None,
    "tag": str | None,         # "[용도 확인]", "[근로계약]" 등
    "sha256": str | None,      # 파일 해시 (중복 추적)
    "file_type": "PDF" | "HWP" | "PPTX" | None,
    "parse_status": "full" | "metadata_only",  # 파싱 상태
}
```

---

## 5. ProcessedLawData 매핑 (ActionKit → 기존 포맷)

### laws 아이템 매핑

```
title         = item.name                     # "건축법 제2조 (용도 분류)"
summary       = item.summary                  # "건축물 용도 분류 체계..."
guide_text    = "\n".join(f"- {h}" for h in item.highlights)  # 불릿 포인트
law_reference = item.name (자체가 법령 참조)
category      = f"actionkit/laws/{chapter_slug}"
```

### kits 아이템 매핑

```
title         = item.name                     # "건축법 제2조 기반 검토 키트"
summary       = item.summary
guide_text    = highlights(불릿) + relatedLaws("**{name}**: {summary}" 형식)
law_reference = item.relatedLaws[0].name      # 대표 관련 법령
category      = f"actionkit/kits/{category_slug}"
```

---

## 6. 골든 데이터셋 확장 계획

### OOS 추가 (Step 1)

```json
{"id": "oos-003", "question": "일본 식품위생법의 내용은?",
 "ground_truth": "OUT_OF_SCOPE", "expected_source": "general",
 "category": "out_of_scope", "difficulty": "easy",
 "expected_keywords": [], "expected_law_reference": null, "requires_citation": false},

{"id": "oos-004", "question": "2035년 예상 법률 변화는?",
 "ground_truth": "OUT_OF_SCOPE", "expected_source": "general",
 "category": "out_of_scope", "difficulty": "easy",
 "expected_keywords": [], "expected_law_reference": null, "requires_citation": false},

{"id": "oos-005", "question": "양자역학의 기본 원리를 설명해주세요",
 "ground_truth": "OUT_OF_SCOPE", "expected_source": "general",
 "category": "out_of_scope", "difficulty": "easy",
 "expected_keywords": [], "expected_law_reference": null, "requires_citation": false}
```

### Q&A 확장 seed 쿼리 (Step 4)

기존 5개 → 13개 확장:

```python
seed_queries = [
    # 기존 (법령 일반)
    "영업신고 절차", "허가 요건", "위생 기준", "법인 설립", "사업자 등록",
    # 세무 도메인
    "부가가치세 신고 절차", "사업자 세금계산서 발행", "세금 납부 기한",
    # 인사노무 도메인
    "4대보험 가입 방법", "근로계약서 작성 요건", "표준취업규칙 작성",
    # 공고문/행정법 도메인
    "소상공인 정책자금 신청", "행정심판 신청 절차",
]
```

### ID 컨벤션

```
기존:    legal-001~015, routing-001~004, oos-001~005
신규:    kit-legal-001~, kit-tax-001~, kit-hr-001~, kit-grant-001~
```

### 목표 분포

| 도메인 | 현재 | 추가 | 최종 |
|--------|------|------|------|
| legal_rag (법령) | 15 | +20 | 35 |
| general | 2 | +3 | 5 |
| routing_edge | 2 | +3 | 5 |
| out_of_scope | 5 | 0 | 5 |
| **합계** | **24** | **+26** | **50** |

---

## 7. results/ 디렉토리 구조 (재설계)

```
tests/eval/results/
├── baseline.json                # [신규] 고정 스냅샷 (--update-baseline으로만 변경)
├── latest_run.json              # [신규] 매 실행 자동 덮어쓰기
├── tier2_baseline.json          # [유지] 기존 참조용 보존
├── tier3_baseline.json          # [유지] 기존 참조용 보존
├── faithfulness.json            # [유지] 최신 Tier 2 상세
├── correctness.json             # [유지] 최신 Tier 2 상세
├── legal_accuracy_full.json     # [유지] 최신 Tier 3 상세
└── summary_report.json          # [수정] baseline 비교 섹션 추가
```

### baseline.json / latest_run.json 스키마

```json
{
  "created_at": "2026-02-24T13:25:00",
  "git_commit": "956725f",
  "description": "Initial baseline after Phase 1-2 evaluation",
  "metrics": {
    "hit_rate_at_3": 0.4118,
    "faithfulness": 0.12,
    "answer_relevancy": 0.240,
    "answer_correctness": 0.000,
    "legal_accuracy": 0.000,
    "oos_refusal_rate": 1.0,
    "routing_accuracy": 0.857
  },
  "case_count": {
    "legal": 15,
    "general": 2,
    "routing_edge": 2,
    "out_of_scope": 5
  }
}
```

---

## 8. 의존성 및 전제 조건

### 실행 환경

| 항목 | 요구사항 |
|------|---------|
| Python | >= 3.11 |
| Docker (PostgreSQL + pgvector) | 필수 (Step 2부터) |
| OPENAI_API_KEY | 필수 (Step 2부터) |
| DATABASE_URL | 필수 (Step 2부터) |

### 패키지 의존성

| 패키지 | 상태 | 용도 |
|--------|------|------|
| pdfplumber >= 0.10.3 | 기존 설치 | PDF 파싱 |
| langchain_text_splitters | 확인 필요 | RecursiveCharacterTextSplitter |
| langchain_postgres | 기존 설치 | PGVector |
| langchain_openai | 기존 설치 | 임베딩, LLM |

추가 의존성 없음 (HWP/PPTX는 seed fallback)

---

## 9. 선행 태스크 참조

| 문서 | 경로 | 관계 |
|------|------|------|
| RAG 평가 계획서 | `dev/active/rag-evaluation/rag-evaluation-plan.md` | Phase 1~2 완료, Phase 3~5 본 계획으로 대체 |
| RAG 평가 태스크 | `dev/active/rag-evaluation/rag-evaluation-tasks.md` | T-1.x~T-2.x 완료, T-3.x 이후 본 계획으로 대체 |
| Feasibility Report | `dev/active/rag-evaluation/rag-actionkit-feasibility-report.md` | 조사 완료, 실행 계획은 본 문서로 대체 |
| 데이터 분석 | `dev/active/rag-evaluation/research-data-analysis.md` | 참조 (파일 부재 오보 정정 필요) |
| 문서 파싱 분석 | `dev/active/rag-evaluation/research-document-parsing.md` | 참조 |
| 통합 설계 | `dev/active/rag-evaluation/research-integration-design.md` | 참조 (아이템 수 오류 정정 필요) |
