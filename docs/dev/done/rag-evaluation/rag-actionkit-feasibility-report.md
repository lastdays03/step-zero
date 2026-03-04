# ActionKit 데이터 활용 RAG 평가 데이터 자동 생성 - 실행가능성 리포트

> 작성일: 2026-02-24
> 팀: rag-actionkit-feasibility (data-analyst, doc-parser, rag-architect)
> 상태: **Go - 실행 가능**

---

## Executive Summary

ActionKit의 구조화된 메타데이터(46개 아이템, 42개 하이라이트, 38개 관련법 참조)와 46개 문서 파일(PDF 39, HWP 6, PPTX 1)을 활용하여 **RAG 평가용 Q&A 데이터를 자동 생성하는 것은 충분히 실행 가능**하다.

### 핵심 판단 근거

| 항목 | 판단 | 근거 |
|------|------|------|
| **데이터 충분성** | Go | seed 데이터만으로 120~200개 Q&A 생성 가능 (현재 21개 → 5~10배 확장) |
| **문서 파싱** | Go | 46개 파일 전부 파싱 가능 (PDF 100%, HWP olefile, PPTX python-pptx) |
| **파이프라인 호환** | Go | LawDataSource ABC 확장으로 기존 아키텍처와 자연스럽게 통합 |
| **비용 효율** | Go | Phase 1은 LLM 비용 ~$3~5, PDF 파싱 없이 즉시 시작 가능 |
| **커버리지 개선** | Go | 현재 부재한 세무/인사/공고문 도메인 완전 보완 |

---

## 1. 현재 상태 (As-Is)

### 1.1 RAG 평가 데이터 현황

| 항목 | 현재 |
|------|------|
| 골든 데이터셋 | 21개 (수동 작성) |
| 도메인 커버리지 | 법률(legal)에 편중, 세무/인사/공고문 **완전 부재** |
| 자동 생성 스크립트 | **미구현** (generate_golden_dataset.py 없음) |
| 질문 유형 | factual 33%, procedural 24%, interpretive 14% |

### 1.2 ActionKit 데이터 현황

| 항목 | 내용 |
|------|------|
| 도메인 | laws (21 아이템, 6장) + kits (25 아이템, 4카테고리) = **46개** |
| 메타데이터 | name, summary (100%), highlights (67%), relatedLaws (kits 100%) |
| 문서 파일 | PDF 39개 + HWP 6개 + PPTX 1개 = **46개, 62MB** |
| 언어 | 전체 한국어, 법령명 표기 일관 |

---

## 2. 조사 결과 종합

### 2.1 데이터 분석 결과 (Task #1)

**Q&A 생성에 가장 가치 있는 필드:**

| 필드 | 가치 | 수량 | 활용 방법 |
|------|------|------|----------|
| `item.summary` | ★★★★★ | 46개 (100%) | 답변(ground_truth)의 핵심 |
| `highlight.content` | ★★★★★ | 42개 (laws 67%) | 체크리스트/주의사항 질문 |
| `relatedLaw.law_name + summary` | ★★★★ | 38개 (kits 100%) | 법적 근거 질문 |
| `item.name` | ★★★★ | 46개 (100%) | 질문 주제 |
| `item.tag` | ★★★ | 25개 (kits 100%) | 질문 분류/그룹화 |

**Q&A 생성 전략 3가지:**

| 전략 | 예상 수량 | 구현 난이도 | 비용 | 품질 |
|------|----------|-----------|------|------|
| 1. 템플릿 기반 | ~120개 | 하 (Python 100줄) | $0 | 기계적, 단조로움 |
| 2. LLM 증강 | ~200개 | 중 | ~$3-5 | 자연스러움, 검증 필요 |
| 3. 하이브리드 (권장) | ~176개 | 중 | ~$3-5 | 기본 품질 보장 + 다양성 |

### 2.2 문서 파싱 결과 (Task #2)

| 형식 | 파일 수 | 파싱 라이브러리 | 테스트 결과 | 추가 의존성 |
|------|---------|---------------|-----------|-----------|
| **PDF** | 39 (84.8%) | pdfplumber (기존) | **39/39 성공 (100%)** | 없음 |
| **HWP** | 6 (13.0%) | olefile + PrvText | 서식 문서, 2줄 코드로 추출 | `olefile>=0.47` |
| **PPTX** | 1 (2.2%) | python-pptx | 표준 텍스트 추출 | `python-pptx>=1.0.0` |

**핵심 발견:**
- PDF 39개 전부 텍스트 기반 (스캔/이미지 PDF 0개 → OCR 불필요)
- HWP 6개는 모두 HR 서식 문서 (근로계약서, 4대보험 서식)
- 기존 `law_fetcher.py`의 PDF 파서를 그대로 활용 가능

**기존 RAG 파이프라인 갭:**

| 갭 | 현재 | 필요 | 난이도 |
|----|------|------|--------|
| 파일 형식 | PDF, MD만 | + HWP, PPTX | 중 |
| 데이터 경로 | `.temp/` 고정 | `uploads/actionkit/` 추가 | 하 |
| 카테고리 추출 | 디렉토리명 추론 | ActionKit 경로 구조 파싱 | 하 |
| 중복 제거 | 없음 | 같은 법령이 laws/kits 양쪽 존재 | 중 |

### 2.3 통합 설계 결과 (Task #3)

**통합 아키텍처 (목표 상태):**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  LawDataSource (ABC)                                        │
│  ├─ LocalFileSource ─── .temp/ (기존 PDF/MD)                │
│  └─ ActionKitDataSource (NEW) ─── ActionKit DB + 파일       │
│       │                                                     │
│       ▼                                                     │
│  ETL (ActionKit 전용: LLM 호출 불필요, 메타데이터 직접 변환)    │
│       │                                                     │
│       ▼                                                     │
│  VectorStoreService                                         │
│  ├─ "law_vectors" (기존)                                    │
│  └─ "actionkit_vectors" (신규, 별도 컬렉션)                  │
│       │                                                     │
│       ▼                                                     │
│  RagService → EnsembleRetriever (양쪽 컬렉션 통합 검색)       │
│                                                             │
│  ─── 평가 프레임워크 ───                                     │
│  golden_dataset.json (기존 21개)                             │
│  + golden_dataset_actionkit.json (자동 생성 84~176개)        │
│  = 총 105~197개 평가 데이터                                  │
└─────────────────────────────────────────────────────────────┘
```

**설계 핵심 결정:**

| 결정 | 선택 | 근거 |
|------|------|------|
| 데이터소스 패턴 | LawDataSource ABC 확장 | OCP 준수, 기존 코드 변경 최소 |
| ETL 전략 | LLM 우회 (메타데이터 직접 변환) | ActionKit은 이미 구조화, 비용 $0 |
| 벡터 컬렉션 | 별도 "actionkit_vectors" | 소스 추적, 독립 업데이트 가능 |
| Q&A 생성 | Seed 데이터 우선 (DB 불필요) | 즉시 시작 가능 |

---

## 3. 구현 로드맵

### Phase 1: 평가 데이터 자동 생성 (1~2일)

> 목표: ActionKit 메타데이터 기반 골든 데이터셋 자동 생성

| 단계 | 작업 | 산출물 | 비용 |
|------|------|--------|------|
| 1-1 | `generate_golden_dataset.py` 구현 (seed 모드) | 스크립트 | $0 |
| 1-2 | Seed 데이터 기반 84개 Q&A 생성 | `golden_dataset_actionkit.json` | ~$3-5 |
| 1-3 | 생성된 Q&A 품질 검증 (수동 샘플링 10개) | 품질 리포트 | $0 |
| 1-4 | `conftest.py` 확장 (actionkit fixtures) | 확장된 테스트 설정 | $0 |

**의존성**: 없음 (seed 데이터만 활용, DB/Docker 불필요)
**리스크**: LLM 생성 Q&A 품질 불균일 → 수동 검수 필요

### Phase 2: ActionKit → 벡터 스토어 연결 (2~3일)

> 목표: ActionKit DB 데이터를 RAG 벡터 검색에 편입

| 단계 | 작업 | 산출물 |
|------|------|--------|
| 2-1 | `ActionKitDataSource` 클래스 구현 | `actionkit_data_source.py` |
| 2-2 | `ActionKitETLProcessor` 구현 (LLM 불필요) | `actionkit_etl.py` |
| 2-3 | `VectorStoreService` 멀티 컬렉션 지원 | collection_name 파라미터화 |
| 2-4 | 인제스트 스크립트 작성 | `ingest_actionkit.py` |
| 2-5 | HWP/PPTX 파서 추가 (선택) | law_fetcher.py 확장 |
| 2-6 | Tier 1~2 평가 실행 | 평가 결과 리포트 |

**의존성**: Phase 1 완료, Docker (PostgreSQL + pgvector)
**추가 의존성**: `olefile>=0.47`, `python-pptx>=1.0.0`

### Phase 3: RagService 멀티소스 통합 (1~2일)

> 목표: 다중 벡터 컬렉션을 통합하는 검색 서비스

| 단계 | 작업 | 산출물 |
|------|------|--------|
| 3-1 | EnsembleRetriever 적용 | 확장된 RagService |
| 3-2 | 소스별 가중치 설정 | 설정 파라미터 |
| 3-3 | 응답에 소스 메타데이터 포함 | 응답 형식 확장 |
| 3-4 | Tier 3 전체 통합 평가 | 최종 평가 리포트 |

**의존성**: Phase 2 완료

### 전체 타임라인

```
Day 1~2          Day 3~5            Day 6~7
Phase 1          Phase 2            Phase 3
Q&A 자동 생성     벡터 스토어 연결     멀티소스 통합
─────────────── ─────────────────── ───────────────
스크립트 구현     DataSource 구현     EnsembleRetriever
84개 Q&A 생성    ETL 구현            가중치 최적화
품질 검증        벡터 인제스트         소스 메타 포함
conftest 확장    Tier 1~2 평가       Tier 3 전체 평가
```

---

## 4. 예상 성과

### 4.1 평가 데이터 확장

| 항목 | 현재 | Phase 1 후 | Phase 2 후 |
|------|------|-----------|-----------|
| 골든 데이터셋 크기 | 21개 | **105개** (+84) | 105개 |
| 도메인 커버리지 | legal만 | + 세무/인사/공고문 | + PDF 본문 기반 |
| 질문 유형 | 3종 | **6종** (+체크리스트/법적근거/교차) | 6종 |
| 자동 생성 | 수동만 | **스크립트 자동화** | DB 연동 자동화 |

### 4.2 RAG 평가 품질 향상

| 메트릭 | 현재 한계 | 개선 효과 |
|--------|----------|----------|
| Hit Rate@3 | 21개 케이스로만 측정 | 105개로 통계적 유의미성 확보 |
| Faithfulness | legal 편중 | 다양한 도메인에서 환각 감지 |
| Routing Accuracy | 법률 키워드 위주 | 세무/인사 키워드 포함 경계 케이스 추가 |
| Answer Correctness | 제한된 ground_truth | 구조화된 메타데이터 기반 정밀 정답 |

---

## 5. 리스크 및 완화 전략

| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|----------|
| LLM 생성 Q&A 품질 불균일 | 중 | 중 | temperature=0.7, 수동 샘플링 검수, 환각 방지 프롬프트 |
| HWP PrvText 추출 실패 | 낮 | 낮 | 6개 파일만 대상, olefile fallback, 실패 시 skip |
| 중복 문서 임베딩 | 중 | 중 | 파일명/해시 기반 중복 제거 로직 |
| ActionKit 메타데이터 불완전 | 중 | 중 | highlights 67% 커버리지 → 누락 아이템은 name+summary로 대체 |
| 기존 RAG 검색 성능 저하 | 낮 | 높 | 별도 컬렉션으로 격리, A/B 테스트 후 통합 |

---

## 6. 비용 추정

| 항목 | Phase 1 | Phase 2 | Phase 3 | 합계 |
|------|---------|---------|---------|------|
| LLM 비용 (Q&A 생성) | ~$3-5 | $0 | $0 | ~$3-5 |
| LLM 비용 (ETL) | $0 | $0 (ETL 우회) | $0 | $0 |
| LLM 비용 (평가 실행) | $0 | ~$2-5 (Tier 2) | ~$15-25 (Tier 3) | ~$17-30 |
| 인력 시간 | 1~2일 | 2~3일 | 1~2일 | **4~7일** |
| **합계** | ~$3-5 | ~$2-5 | ~$15-25 | **~$20-35** |

---

## 7. 결론 및 권장사항

### Go/No-Go 판단: **Go**

ActionKit 데이터를 활용한 RAG 평가 데이터 자동 생성은 **기술적으로 실현 가능하고, 비용 효율적이며, 현재 평가 체계의 가장 큰 약점(데이터 부족, 도메인 편중)을 직접 해결**한다.

### 즉시 실행 권장사항

1. **Phase 1부터 시작** - DB/Docker 없이 seed 데이터만으로 즉시 시작 가능
2. **하이브리드 전략 채택** - 템플릿 기반 기본 Q&A + LLM 증강으로 품질과 다양성 확보
3. **generate_golden_dataset.py 구현 우선** - 가장 높은 ROI (1~2일 투자 → 84개+ Q&A)
4. **Phase 2는 Phase 1 평가 결과 보고 진행** - 데이터 품질 확인 후 파이프라인 확장

---

## 부록: 조사 산출물 참조

| 문서 | 경로 | 담당 |
|------|------|------|
| 데이터 분석 | `dev/active/rag-evaluation/research-data-analysis.md` | data-analyst |
| 문서 파싱 분석 | `dev/active/rag-evaluation/research-document-parsing.md` | doc-parser |
| 통합 설계 | `dev/active/rag-evaluation/research-integration-design.md` | rag-architect |
| **본 리포트** | `dev/active/rag-evaluation/rag-actionkit-feasibility-report.md` | team-lead |
