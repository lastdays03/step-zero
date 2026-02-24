# RAG 파이프라인 업그레이드 - 작업 체크리스트

> Last Updated: 2026-02-24

---

## Step 1: 구조 정비 (T+1일)

> 목표: 평가 프레임워크의 구조적 문제 해결, 이후 측정 신뢰성 확보

### Section 1.1: baseline 자동화 (C안)

- [ ] **T-1.1.1** baseline.json 통합 생성 (기존 tier2/3_baseline 수치 병합)
  - Effort: S | Priority: P0
  - 수치: faithfulness=0.12(정정), hallucination=8(정정)
  - Acceptance: baseline.json 생성, 스키마 검증

- [ ] **T-1.1.2** run_evaluation.py에 --update-baseline 플래그 추가
  - Effort: M | Priority: P0
  - latest_run.json → baseline.json 복사 로직
  - Acceptance: `python -m scripts.eval.run_evaluation --update-baseline` 동작

- [ ] **T-1.1.3** run_evaluation.py에 latest_run.json 자동 저장 로직 추가
  - Effort: M | Priority: P0
  - 각 tier 실행 후 메트릭 집계 → latest_run.json 덮어쓰기
  - Acceptance: Tier 2 실행 시 latest_run.json 자동 생성

- [ ] **T-1.1.4** 회귀 감지 로직 구현 (latest_run vs baseline 비교)
  - Effort: M | Priority: P1
  - 메트릭별 하락폭 계산, 임계값 초과 시 경고 출력
  - Acceptance: 의도적으로 나쁜 결과 넣으면 경고 메시지 출력
  - Depends on: T-1.1.1, T-1.1.3

### Section 1.2: OOS 테스트 수정

- [ ] **T-1.2.1** golden_dataset.json에 oos-003~005 추가
  - Effort: S | Priority: P0
  - 기존 하드코딩 3개 질문을 골든 데이터셋 포맷으로 변환
  - Acceptance: golden_dataset.json 24개 항목, Tier 1 무결성 통과

- [ ] **T-1.2.2** test_tier3_full.py OOS 하드코딩 제거 → fixture 주입
  - Effort: S | Priority: P0
  - 시그니처: `(self, rag_service, out_of_scope_cases)`
  - 질문 추출: `[c["question"] for c in out_of_scope_cases]`
  - Acceptance: Tier 3 OOS 테스트가 fixture에서 5개 질문 사용
  - Depends on: T-1.2.1

### Section 1.3: 미사용 fixture 활용

- [ ] **T-1.3.1** general_cases fixture 활용 테스트 추가
  - Effort: S | Priority: P2
  - Tier 1: "일반 질문이 legal로 오분류되지 않는지" (False Positive 측정)
  - Acceptance: test_tier1_basic.py에 테스트 추가, 실행 통과

- [ ] **T-1.3.2** routing_edge_cases fixture 활용 테스트 추가
  - Effort: S | Priority: P2
  - Tier 1: 경계 케이스 라우팅 정확도 별도 집계 + 출력
  - Acceptance: 경계 케이스 정확도가 별도로 출력됨

### Section 1.4: 검증

- [ ] **T-1.4.1** Tier 1 전체 실행 → 무결성 확인
  - Effort: S | Priority: P0
  - Acceptance: 모든 Tier 1 테스트 PASS (24개+ 케이스)
  - Depends on: T-1.2.1, T-1.2.2

---

## Step 2: 청킹 + 재인덱싱 (T+2일)

> 목표: RecursiveCharacterTextSplitter 도입, 기존 law_vectors 재인덱싱

### Section 2.1: 청킹 구현

- [ ] **T-2.1.1** VectorStoreService에 청킹 로직 추가
  - Effort: M | Priority: P0
  - RecursiveCharacterTextSplitter(chunk_size=600, overlap=100)
  - 메타데이터에 chunk_index, total_chunks 추가
  - Acceptance: add_documents()가 1 ProcessedLawData → N Document 생성

- [ ] **T-2.1.2** 샘플 10개로 청크 결과 검증
  - Effort: S | Priority: P0
  - 기존 law_vectors 문서 10개를 청킹 후 수동 검토
  - chunk_size 조정 필요 시 파라미터 변경
  - Acceptance: 청크 경계가 의미 단위로 적절히 분리됨
  - Depends on: T-2.1.1

### Section 2.2: 재인덱싱

- [ ] **T-2.2.1** law_vectors 백업
  - Effort: S | Priority: P0
  - pg_dump 또는 COPY로 기존 벡터 백업
  - Acceptance: 백업 파일 생성, 복원 테스트 가능

- [ ] **T-2.2.2** law_vectors 삭제 + 청킹 적용 재인덱싱
  - Effort: M | Priority: P0
  - PGVector.delete_collection() → 기존 ETL 파이프라인 + 청킹으로 재적재
  - Acceptance: law_vectors에 청킹된 벡터 존재 (기존 대비 5~10배 벡터 수)
  - Depends on: T-2.1.2, T-2.2.1

### Section 2.3: 검증

- [ ] **T-2.3.1** Tier 1 실행 → 라우팅 영향 없는지 확인
  - Effort: S | Priority: P0
  - Acceptance: Tier 1 전체 PASS (청킹은 라우팅에 영향 없어야 함)
  - Depends on: T-2.2.2

- [ ] **T-2.3.2** Tier 2 실행 → Hit Rate 개선 측정
  - Effort: S | Priority: P0
  - 예상: Hit Rate 0.41 → 0.60+
  - latest_run.json 생성 + baseline 대비 비교
  - Acceptance: Hit Rate가 baseline(0.41) 대비 개선됨
  - Depends on: T-2.2.2, T-1.1.3

---

## Step 3: ActionKit 적재 (T+3일)

> 목표: ActionKit 46개 아이템을 청킹 적용하여 law_vectors에 적재

### Section 3.1: ActionKitDataSource 구현

- [ ] **T-3.1.1** ActionKitDataSource 클래스 구현 (LawDataSource ABC 확장)
  - Effort: L | Priority: P0
  - fetch_all_laws() → List[LawData]
  - seed 메타데이터 + 파일 파싱 결합 (옵션C)
  - PDF: pdfplumber, HWP/PPTX: seed fallback
  - Acceptance: 46개 LawData 반환, content_body에 seed + parsed_text

- [ ] **T-3.1.2** ActionKitETLBridge 구현 (LLM 우회 직접 변환)
  - Effort: M | Priority: P0
  - LawData → ProcessedLawData 직접 매핑
  - highlights → guide_text 불릿, relatedLaws → 참조 섹션
  - Acceptance: 46개 ProcessedLawData 생성, LLM 호출 0회

### Section 3.2: 적재 스크립트

- [ ] **T-3.2.1** seed_rag_vectors.py 통합 인제스트 스크립트 작성
  - Effort: M | Priority: P0
  - Step 1: LocalFileSource → ETL → 청킹 → law_vectors
  - Step 2: ActionKitDataSource → ETLBridge → 청킹 → law_vectors
  - 메타데이터 스키마 적용 (source, domain, item_id, sha256 등)
  - Acceptance: 전체 재인덱싱 1회 실행으로 완료
  - Depends on: T-3.1.1, T-3.1.2

- [ ] **T-3.2.2** ActionKit 46개 아이템 적재 실행
  - Effort: S | Priority: P0
  - Acceptance: law_vectors에 ActionKit 벡터 존재, 메타데이터 확인
  - Depends on: T-3.2.1

### Section 3.3: 검증

- [ ] **T-3.3.1** Tier 1 실행 → 회귀 없는지 확인
  - Effort: S | Priority: P0
  - Acceptance: Tier 1 전체 PASS
  - Depends on: T-3.2.2

- [ ] **T-3.3.2** Tier 2 실행 → 기존 메트릭 유지 확인
  - Effort: S | Priority: P0
  - Acceptance: 기존 법령 메트릭이 Step 2 대비 회귀하지 않음
  - Depends on: T-3.2.2

---

## Step 4: 골든 데이터셋 확장 (T+4일)

> 목표: 풍부해진 벡터 DB 기반 Q&A 자동 생성, 50개+ 데이터셋 구축

### Section 4.1: Q&A 생성 스크립트 수정

- [ ] **T-4.1.1** generate_golden_dataset.py seed 쿼리 확장 (5→13개)
  - Effort: S | Priority: P0
  - 세무/인사/공고문/행정법 도메인 추가
  - Acceptance: seed_queries 리스트 13개

- [ ] **T-4.1.2** Q&A 80개 자동 생성 실행
  - Effort: S | Priority: P0
  - `python -m scripts.eval.generate_golden_dataset --count 80`
  - Acceptance: generated_qa.json 생성, 80개 항목 포함
  - Depends on: T-4.1.1, T-3.2.2

### Section 4.2: 검수 및 병합

- [ ] **T-4.2.1** 생성된 Q&A 검수 (수동 샘플링)
  - Effort: L | Priority: P1
  - ground_truth 정확성, 중복 질문 제거, 도메인 분포 확인
  - ~50개 선별
  - Acceptance: 검수 완료, 50개+ 양질의 Q&A 확보

- [ ] **T-4.2.2** golden_dataset.json 병합
  - Effort: S | Priority: P1
  - 기존 24개 + 신규 ~26개 = 총 50개
  - ID 컨벤션: kit-tax-001, kit-hr-001, kit-grant-001
  - Acceptance: golden_dataset.json 50개+ 항목, Tier 1 무결성 통과
  - Depends on: T-4.2.1

### Section 4.3: 검증

- [ ] **T-4.3.1** Tier 1 실행 → 확장 데이터셋 무결성 확인
  - Effort: S | Priority: P0
  - Acceptance: 50개+ 케이스 Tier 1 전체 PASS
  - Depends on: T-4.2.2

---

## Step 5: 최종 평가 + baseline 갱신 (T+5일)

> 목표: 전체 Tier 2/3 평가 실행, 새 baseline 확정

### Section 5.1: 최종 평가 실행

- [ ] **T-5.1.1** Tier 2 전체 실행
  - Effort: S | Priority: P0
  - ~5분, ~$5
  - 50개+ 케이스 기반 메트릭 측정
  - Acceptance: latest_run.json 생성

- [ ] **T-5.1.2** Tier 3 전체 실행
  - Effort: S | Priority: P0
  - ~15분, ~$20
  - Legal accuracy, OOS refusal, latency 측정
  - Acceptance: legal_accuracy_full.json 생성
  - Depends on: T-5.1.1

### Section 5.2: baseline 갱신

- [ ] **T-5.2.1** --update-baseline 실행 → 새 baseline 확정
  - Effort: S | Priority: P0
  - `python -m scripts.eval.run_evaluation --update-baseline`
  - Acceptance: baseline.json 갱신, summary_report.json에 개선 폭 기록
  - Depends on: T-5.1.2

- [ ] **T-5.2.2** 최종 개선 폭 리포트 작성
  - Effort: M | Priority: P1
  - 목표 대비 달성률 정리
  - Acceptance: 리포트 문서 생성
  - Depends on: T-5.2.1

---

## 진행 상태 요약

| Step | 상태 | 완료/전체 |
|------|------|----------|
| Step 1: 구조 정비 | 대기 | 0/8 |
| Step 2: 청킹 + 재인덱싱 | 대기 | 0/6 |
| Step 3: ActionKit 적재 | 대기 | 0/6 |
| Step 4: 데이터셋 확장 | 대기 | 0/5 |
| Step 5: 최종 평가 | 대기 | 0/4 |
| **합계** | | **0/29** |

---

## 실행 팀 구성: `rag-upgrade-builder` (3인)

| 역할 | Step 1 | Step 2 | Step 3 | Step 4 | Step 5 |
|------|--------|--------|--------|--------|--------|
| **rag-engineer** | 설계 선행 | 청킹 구현 + 재인덱싱 | DataSource + ETL | - | - |
| **data-engineer** | - | 샘플 검증 | 적재 스크립트 + 파싱 | seed 쿼리 확장 + Q&A 생성 | 데이터 보정 |
| **eval-engineer** | baseline 자동화 + OOS 수정 | Tier 1~2 검증 | Tier 1~2 검증 | 검수 + 병합 | 최종 평가 + 리포트 |
