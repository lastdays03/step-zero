# RAG 파이프라인 업그레이드 - 작업 체크리스트

> Last Updated: 2026-02-25
> Status: **전체 완료** (Step 1~5 + 후속 P-1~P-4)

---

## Step 1: 구조 정비 — 완료 ✅

> 목표: 평가 프레임워크의 구조적 문제 해결, 이후 측정 신뢰성 확보

### Section 1.1: baseline 자동화 (C안)

- [x] **T-1.1.1** baseline.json 통합 생성
- [x] **T-1.1.2** run_evaluation.py에 --update-baseline 플래그 추가
- [x] **T-1.1.3** run_evaluation.py에 latest_run.json 자동 저장 로직 추가
- [x] **T-1.1.4** 회귀 감지 로직 구현 (detect_regression 함수, 메트릭별 마진 비교)

### Section 1.2: OOS 테스트 수정

- [x] **T-1.2.1** golden_dataset.json에 oos-003~005 추가 (총 OOS 5개)
- [x] **T-1.2.2** test_tier3_full.py OOS 하드코딩 제거 → out_of_scope_cases fixture 주입

### Section 1.3: 미사용 fixture 활용

- [x] **T-1.3.1** general_cases fixture 활용 테스트 2개 추가
- [x] **T-1.3.2** routing_edge_cases fixture 활용 테스트 2개 추가

### Section 1.4: 검증

- [x] **T-1.4.1** Tier 1 전체 실행 → **29 passed, 0 failed**

---

## Step 2: 청킹 + 재인덱싱 — 완료 ✅

> 목표: RecursiveCharacterTextSplitter 도입, 기존 law_vectors 재인덱싱

- [x] **T-2.1.1** VectorStoreService에 청킹 로직 추가 (chunk_size=600, overlap=100)
- [x] **T-2.1.2** 샘플 10개로 청크 결과 검증 (10 PDF → 80청크, 파라미터 적절)
- [x] **T-2.2.1** law_vectors 백업 (scripts/backup_law_vectors.py)
- [x] **T-2.2.2** law_vectors 삭제 + 청킹 적용 재인덱싱
- [x] **T-2.3** Step 2 검증: Tier 1 PASS + faithfulness +76% (0.12→0.21)

---

## Step 3: ActionKit 적재 — 완료 ✅

> 목표: ActionKit 46개 아이템을 청킹 적용하여 law_vectors에 적재

- [x] **T-3.1.1** ActionKitDataSource 클래스 구현 (46개 LawData, PDF 39 파싱 + HWP/PPTX 7 메타데이터)
- [x] **T-3.1.2** ActionKitETLBridge 구현 (46개 ProcessedLawData, LLM 0회)
- [x] **T-3.2.1** seed_rag_vectors.py 통합 인제스트 스크립트 (--include-actionkit/--actionkit-only/--clean)
- [x] **T-3.2.2** ActionKit 적재 실행 → 314벡터 (laws=168, kits=146)
- [x] **T-3.3** 검증: 회귀 0건, Hit Rate +23.5%, Faithfulness +576%

---

## Step 4: 골든 데이터셋 확장 — 완료 ✅

> 목표: 50개+ 데이터셋 구축

- [x] **T-4.1.1** seed 쿼리 5→13개 확장
- [x] **T-4.1.2** Q&A 46개 생성 (80개 시도, JSON 파싱 실패로 46개)
- [x] **T-4.2.1** 검수: 26개 선별 (20개 제외: 모호 13, 중복 4, 불일치 2, 부정답변 1)
- [x] **T-4.2.2** 병합: 기존 24 + 신규 26 = **총 50개**
- [x] **T-4.3.1** Tier 1 검증: 29/29 PASSED

---

## Step 5: 최종 평가 + baseline 갱신 — 완료 ✅

> 목표: 전체 Tier 2/3 평가 실행, 새 baseline 확정

- [x] **T-5.1.1** Tier 2 전체 실행 (50 케이스, 144.8초)
- [x] **T-5.2.1** baseline 갱신 완료
- [x] **T-5.2.2** 최종 리포트 작성 (EVALUATION_REPORT.md)

---

## 진행 상태 요약

| Step | 상태 | 완료/전체 |
|------|------|----------|
| Step 1: 구조 정비 | **완료** ✅ | 9/9 |
| Step 2: 청킹 + 재인덱싱 | **완료** ✅ | 5/5 |
| Step 3: ActionKit 적재 | **완료** ✅ | 5/5 |
| Step 4: 데이터셋 확장 | **완료** ✅ | 5/5 |
| Step 5: 최종 평가 | **완료** ✅ | 4/4 |
| 후속 작업 | **완료** ✅ | 5/5 |
| **합계** | | **33/33** |

---

## 후속 작업 — 완료 ✅

> rag-integration 계획(dev/active/rag-integration/)에서 해결

- [x] **P-1** 기존 법령 샘플 3건 재적재
  - rag-integration T-1.4 → `--restore-backup` 구현
  - 2026-02-25 실행 완료: 3건 → 5청크 적재
- [x] **P-2** golden_dataset legal-001~015 재검토
  - rag-integration T-1.1 + T-1.2 → 커버리지 매핑 + 9건 재작성
- [x] **P-3** classify_query 키워드 사전 확장
  - rag-integration T-1.3 → 13개 → 20개
- [x] **P-4** 시스템 프롬프트 한국어 전환
  - rag-integration T-2A.1 → RAG+General 한국어 전환
- [x] **P-5** 리랭킹(Reranking) 도입 검토
  - rag-integration F-1로 이관 → `dev/active/rag-integration/rag-integration-tasks.md`
