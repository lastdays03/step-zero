# RAG 파이프라인 업그레이드 종합 계획서

> Last Updated: 2026-02-24
> 선행 태스크: `dev/active/rag-evaluation/` (Phase 1~2 완료)

---

## 1. Executive Summary

StepZero RAG 시스템의 핵심 약점(청킹 부재, 문서 커버리지 부족)을 해결하고, ActionKit 데이터 46개를 벡터 DB에 적재하여 실제 RAG 서비스 품질을 개선한다. 동시에 평가 프레임워크의 구조적 문제(baseline 수동 관리, OOS 하드코딩, 미사용 fixture)를 정비하고, 골든 데이터셋을 21개 → 50개+로 확장하여 의미 있는 평가 체계를 완성한다.

### 핵심 변경사항
- 청킹 도입 + 기존 law_vectors 재인덱싱
- ActionKit 46개 아이템 벡터 DB 통합 적재
- 평가 프레임워크 구조 정비 (baseline 자동화, OOS fixture 연동)
- 골든 데이터셋 확장 (21 → 50+개, 세무/인사/공고문 도메인 추가)

### 예상 성과
| 메트릭 | 현재 | 목표 |
|--------|------|------|
| Hit Rate@3 | 41% | 70%+ |
| Faithfulness | 0.12 | 0.50+ |
| Answer Correctness | 0.00 | 0.40+ |
| Legal Accuracy | 0.00 | 0.30+ |
| 골든 데이터셋 | 21개 | 50개+ |
| 도메인 커버리지 | legal만 | legal + 세무 + 인사 + 공고문 |

---

## 2. Current State Analysis

### 2.1 RAG 파이프라인 현재 아키텍처

```
.temp/rag/*.pdf/md
      → LocalFileSource (fetch_all_laws)
      → LawETLProcessor (GPT-4-turbo, content[:10000])
      → VectorStoreService (1 doc = 1 vector, NO chunking)
      → PGVector: law_vectors (text-embedding-3-small)
      → RagService (retriever k=3, gpt-4o-mini)
      → ChatService (키워드 13개 기반 라우팅)
```

### 2.2 식별된 핵심 문제 6가지

| # | 문제 | 영향 | 본 계획에서 해결 |
|---|------|------|----------------|
| 1 | **청킹 부재** | Hit Rate 41%, 검색 정밀도 저하 | **Yes** |
| 2 | **문서 커버리지 부족** | 세무/인사/공고문 답변 불가 | **Yes** |
| 3 | **단순 검색** (유사도만) | 관련 없는 문서 검색 | 부분 (k 상향) |
| 4 | **키워드 라우팅 한계** | 법률 질문 누락 | 향후 |
| 5 | **영어 시스템 프롬프트** | 답변 품질 저하 | 향후 |
| 6 | **평가 체계 미흡** | baseline 수동 오류, OOS 하드코딩 | **Yes** |

### 2.3 베이스라인 측정값 (2026-02-24)

| 메트릭 | 값 | 비고 |
|--------|---|------|
| Hit Rate@3 | 0.4118 (41%) | 임계값 60% 미달 |
| Faithfulness | **0.12** (공식) | tier2_baseline의 0.15는 수동 입력 오류 |
| Answer Relevancy | 0.240 | 임계값 50% 미달 |
| Answer Correctness | 0.000 | 전 케이스 "정보를 찾을 수 없습니다" |
| Legal Accuracy | 0.000 | 17개 전부 0점 |
| Hallucination Count | **8건** (공식) | tier3_baseline의 7은 집계 오류 |
| OOS Refusal Rate | 100% (3/3) | 강점 |
| Latency | < 5s | 임계값 15s 대비 양호 |

### 2.4 테스트 코드 구조 문제

| 문제 | 상세 |
|------|------|
| baseline 파일 수동 작성 | tier2_baseline.json, tier3_baseline.json이 수동 생성. 실제 결과와 불일치 |
| OOS 하드코딩 | test_tier3_full.py:336~340에 질문 3개 하드코딩, 골든 데이터셋 미사용 |
| conftest fixture 3개 사문화 | general_cases, routing_edge_cases, out_of_scope_cases 미사용 |
| rag_service fixture 중복 | tier2, tier3 양쪽에 거의 동일한 fixture 각각 정의 |

### 2.5 ActionKit 데이터 현황

| 항목 | 수치 |
|------|------|
| laws 아이템 | 21개 (6개 챕터) |
| kits 아이템 | 25개 (4개 카테고리: legal 11, tax 3, hr 8, grant 3) |
| 합계 | **46개** |
| highlights | 42개 (laws 14/21 아이템 보유) |
| relatedLaws | 38개 (kits 25/25 전부 보유) |
| 파일 | PDF 39 + HWP 6 + PPTX 1 = **46개 전부 존재** |
| 고유 콘텐츠 | 34개 (12개 중복: laws↔kits 10, laws 내부 2) |

---

## 3. Proposed Future State (목표 아키텍처)

```
  Source A                    Source B
  .temp/rag/*.pdf/md          uploads/actionkit/**/*
         |                            |
         v                            v
  LocalFileSource             ActionKitDataSource (NEW)
  (fetch_all_laws)            (seed 메타데이터 + 파일 파싱)
         |                            |
         +------------+---------------+
                      |
                      v
            [ETL 분기]
            기존 문서 → LawETLProcessor (LLM 변환)
            ActionKit → ActionKitETLBridge (LLM 우회, 직접 매핑)
                      |
                      v
          RecursiveCharacterTextSplitter
          chunk_size=600, overlap=100
          separators=["\n\n", "\n", ".", " "]
                      |
                      v [1 doc → N chunks]
          PGVector: law_vectors (통합 컬렉션)
          메타데이터: {source, domain, category, title,
                     chunk_index, total_chunks, item_id, sha256}
          ~500~800 벡터 (현재 수십 개 → 10~20배 증가)
                      |
                      v
          RagService (k=5로 상향 검토)
          + metadata filter 옵션
```

---

## 4. 아키텍처 결정 사항

### 4.1 컬렉션 구조: 통합 (law_vectors 단일)

**선택:** 기존 law_vectors에 ActionKit 문서도 함께 적재
**근거:**
- 현재 규모(수백~2,000 청크)에서 분리 불필요
- RAG 코드 변경 최소화 (retriever 1개 유지)
- 메타데이터(`source`, `domain`) 필터로 소스별 분리 검색도 가능
- 향후 분리 필요 시 메타데이터 기반 마이그레이션 용이

### 4.2 청킹 전략

| 대상 | chunk_size | overlap | separators |
|------|-----------|---------|------------|
| ETL 거친 guide_text | 600자 | 100자 | `["\n\n", "\n", ".", " "]` |
| 원문 법령 PDF | 800자 | 150자 | `["\n제", "\n\n", "\n", " "]` |

- 한국어 600자 ≈ 900토큰, k=5이면 총 4,500토큰 (8,191 한도의 55%)
- 재인덱싱 전 샘플 10개로 검증 후 파라미터 확정

### 4.3 ActionKit 데이터 적재 방식: 옵션C (seed + 파일 텍스트 결합)

```
content_body = f"""
[아이템명]: {item.name}
[요약]: {item.summary}
[핵심 포인트]:
- {highlight_1}
- {highlight_2}
[관련 법령]:
- {related_law.name}: {related_law.summary}
[법령 원문 발췌]:
{parsed_text[:3000]}
"""
```

- PDF 39개: pdfplumber (기존 코드 재사용)
- HWP 6개 + PPTX 1개: seed 메타데이터만 (추가 의존성 없음)

### 4.4 ETL 전략: ActionKit은 LLM 우회

ActionKit seed 데이터가 이미 구조화(name, summary, highlights, relatedLaws)되어 있으므로 LLM 변환 불필요.

```
ProcessedLawData.title         = item.name
ProcessedLawData.summary       = item.summary
ProcessedLawData.guide_text    = highlights → "- {h}" 불릿 + relatedLaws → "**{name}**: {summary}"
ProcessedLawData.law_reference = relatedLaws[0].name (대표) 또는 item.name
ProcessedLawData.category      = f"actionkit/{domain}/{category_slug}"
```

### 4.5 중복 문서 처리: 아이템별 별개 적재

- 46개 파일 중 34개 고유 (12개 중복)
- 같은 파일이라도 다른 챕터 컨텍스트 보존 (검색 다양성)
- `metadata.sha256`으로 중복 추적, 검색 후처리에서 de-dup 가능

### 4.6 baseline 관리: C안 (스냅샷 + 자동 생성 병행)

```
results/
├── baseline.json        ← 고정 기준점 (--update-baseline으로만 변경)
├── latest_run.json      ← 매 실행마다 자동 덮어쓰기
├── faithfulness.json    ← 상세 결과 (기존 유지)
├── correctness.json
├── legal_accuracy_full.json
└── summary_report.json  ← baseline 비교 섹션 추가
```

### 4.7 OOS 테스트: 골든 데이터셋 연동 (A안)

- 하드코딩 3개 → oos-003~005로 골든 데이터셋에 편입
- test_tier3_full.py가 `out_of_scope_cases` fixture 주입받도록 변경
- 총 OOS 5개 (기존 2 + 이관 3)

---

## 5. Implementation Phases

### Phase 1: 구조 정비 (Step 1)

평가 프레임워크의 구조적 문제를 먼저 해결하여 이후 측정의 신뢰성을 확보한다.

### Phase 2: 청킹 + 재인덱싱 (Step 2)

RecursiveCharacterTextSplitter를 도입하고 기존 law_vectors를 재인덱싱하여 검색 품질을 개선한다.

### Phase 3: ActionKit 적재 (Step 3)

ActionKitDataSource를 구현하고 46개 아이템을 청킹 적용하여 law_vectors에 적재한다.

### Phase 4: 골든 데이터셋 확장 (Step 4)

풍부해진 벡터 DB 기반으로 Q&A를 자동 생성하고 검수하여 50개+ 데이터셋을 구축한다.

### Phase 5: 최종 평가 + baseline 갱신 (Step 5)

전체 Tier 2/3 평가를 실행하고 새로운 baseline을 확정한다.

---

## 6. Risk Assessment

| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|----------|
| 청킹 후 기존 Hit Rate 오히려 하락 | 중 | 높 | 샘플 10개 사전 검증, chunk_size 조정 여유 |
| HWP/PPTX 파싱 불가 | 높 | 낮 | seed 메타데이터 fallback (7/46개만 해당) |
| 중복 문서가 k=5를 독점 | 중 | 중 | metadata.sha256 기반 후처리 de-dup |
| 법령 PDF 노이즈 (머리글/바닥글) | 중 | 중 | 정규식 페이지번호 패턴 제거 |
| LLM 생성 Q&A 품질 불균일 | 중 | 중 | 수동 검수, temperature=0.7 |
| 재인덱싱 후 롤백 필요 | 낮 | 높 | 사전 백업 (pg_dump 또는 COPY) |
| ActionKit seed ↔ 실제 파일 경로 불일치 | 중 | 중 | seed path → uploads/ 경로 매핑 함수 |
| generate_golden_dataset.py가 ActionKit 문서 못 찾음 | 중 | 중 | seed 쿼리 13개로 확장 + --source 필터 |

---

## 7. 비용 추정

| 항목 | 비용 |
|------|------|
| ETL (ActionKit) | $0 (LLM 우회) |
| Tier 2 실행 3회 (Step 2, 3, 5) | ~$10-15 |
| Tier 3 실행 1회 (Step 5) | ~$15-25 |
| Q&A 자동 생성 (Step 4) | ~$3-5 |
| **합계** | **~$28-45** |

---

## 8. 타임라인

```
T+1일 (Step 1)    구조 정비
T+2일 (Step 2)    청킹 + 재인덱싱
T+3일 (Step 3)    ActionKit 적재
T+4일 (Step 4)    골든 데이터셋 확장
T+5일 (Step 5)    최종 평가 + baseline 갱신
```

---

## 부록: 리서치 문서 오류 정정표

이전 조사(rag-evaluation)에서 발견된 오류를 정리한다.

| 문서 | 오류 내용 | 정정 |
|------|----------|------|
| research-data-analysis.md | "uploads/actionkit/files/ 비어있음" | **오보** — 46개 전부 존재. 경로가 files/가 아니라 laws/, kits/ |
| research-integration-design.md | laws 20개, kits 22개, relatedLaws 32개 | **오류** — 정확값: laws 21, kits 25, relatedLaws 38 |
| tier2_baseline.json | faithfulness: 0.150 | **수동 입력 오류** — 실제 LLM 결과: 0.12 |
| tier3_baseline.json | hallucination_count: 7 | **집계 오류** — 실제 GPT-4o 결과: 8 |
| rag-actionkit-feasibility-report.md | "generate_golden_dataset.py 없음" | **오판** — 파일 존재 (벡터 DB 기반, ActionKit 미연결) |
