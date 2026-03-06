# RAG 업그레이드 현황 및 후속 분석 메모

> Last Updated: 2026-02-24
> 다음 세션에서 이어서 진행할 내용 정리

---

## 1. 완료된 작업 요약

### 팀 운영
- 팀명: `rag-upgrade-builder` (해산 완료)
- eval-engineer: 태스크 12개 (Step 1 전체 + #14, #16, #19, #20)
- rag-engineer: 태스크 8개 (Step 2 전체 + Step 3 핵심)
- 총 20개 태스크 완료

### 최종 메트릭 (50 케이스 기준)

| 메트릭 | 시작 | 최종 | 목표 | 판정 |
|--------|------|------|------|------|
| Hit Rate@3 | 41.2% | **86.1%** | 70%+ | PASS |
| Faithfulness | 0.15 | **0.73** | 0.50+ | PASS |
| Answer Correctness | 0.00 | **0.36** | 0.40+ | 91% (근접) |
| Answer Relevancy | 0.24 | **0.44** | 0.50+ | 88% (근접) |
| Routing Accuracy | 78.9% | **80.0%** | 70%+ | PASS |

### 생성/수정된 파일
- `app/services/vector_store.py` — 청킹 로직 추가
- `app/services/actionkit_data_source.py` — 신규
- `app/services/actionkit_etl.py` — 신규
- `scripts/seed_rag_vectors.py` — 통합 인제스트 스크립트
- `scripts/backup_law_vectors.py` — 백업 스크립트
- `scripts/verify_chunking.py` — 청킹 검증 스크립트
- `scripts/eval/run_evaluation.py` — --update-baseline, latest_run, 회귀 감지
- `scripts/eval/generate_golden_dataset.py` — seed 쿼리 13개로 확장
- `tests/eval/conftest.py` — fixture 유지 (변경 없음)
- `tests/eval/test_tier1_basic.py` — fixture 활용 테스트 추가
- `tests/eval/test_tier3_full.py` — OOS 하드코딩 → fixture 주입
- `tests/eval/data/golden_dataset.json` — 24→50개
- `tests/eval/results/baseline.json` — 최종 baseline
- `tests/eval/results/EVALUATION_REPORT.md` — 사람이 읽는 최종 리포트
- `pyproject.toml` — langchain-text-splitters 의존성 추가

---

## 2. 발견된 이슈 (후속 분석 필요)

### 이슈 A: 기존 법령 데이터 부재

**현상:**
- `.temp/rag/` 디렉토리가 존재하지 않음
- 백업 확인 결과 기존 법령 데이터는 **샘플 3건**만 있었음 (일반음식점, 휴게음식점, 집단급식소)
- 재인덱싱 시 ".temp/rag 디렉토리 없어 법률 ETL은 건너뜀" → ActionKit 314벡터만 적재됨

**영향:**
- golden_dataset의 legal-001~015 질문 중 12건이 "정보를 찾을 수 없습니다"로 답변 실패
- Answer Correctness 0.36 (목표 0.40 미달)의 주 원인

**분석 필요 사항:**
1. 기존 샘플 3건을 청킹 적용해서 재적재할 가치가 있는가?
   - 백업 위치: `.temp/backups/law_vectors_20260224_153755.json`
   - 3건 모두 "집단급식소_법률" 카테고리 (건축법, 폐기물관리법, 근로기준법)
2. legal-001~015 질문을 실제 데이터 커버리지에 맞게 교체해야 하는가?
   - 현재 legal 질문: 영업신고, 허가서류, 위생교육, 주류판매, 자본금, 사업자등록 등
   - 실제 적재 데이터: ActionKit (법령 21 + 키트 25) + 샘플 3건
   - 많은 legal 질문이 ActionKit 커버리지 밖
3. 아니면 추가 법령 데이터를 수집해서 적재해야 하는가?

### 이슈 B: 키워드 라우터 한계

**현상:**
- 9건 오분류 (45건 중 36건 정확 = 80%)
- 신규 도메인(행정심판, 소방, 개인정보 등) 키워드가 classify_query에 미등록

**해결 방안 (간단):**
- classify_query()에 키워드 추가: "행정심판", "행정조사", "소방", "개인정보", "근로계약"
- 예상 효과: 오분류 7건 해소 → routing_accuracy 80%→95%+

### 이슈 C: Near-Miss 메트릭 2개

**Answer Correctness 0.36 (목표 0.40):**
- 주 원인: 이슈 A (데이터 부재로 12건 답변 실패)
- 이슈 A 해결 시 목표 도달 가능

**Answer Relevancy 0.44 (목표 0.50):**
- 주 원인: 거부 응답("정보를 찾을 수 없습니다")이 많아 LLM judge 점수 낮음
- 이슈 A 해결 + 프롬프트 한국어 전환 시 개선 기대

---

## 3. 다음 세션 권장 진행 순서

1. **이슈 A 분석**: legal-001~015 질문과 실제 데이터 매핑표 작성
   - 어떤 질문이 어떤 데이터로 답변 가능한지 매트릭스 정리
   - 질문 교체 vs 데이터 추가 vs 혼합 전략 결정
2. **이슈 B 수정**: classify_query 키워드 사전 확장 (5분 작업)
3. **재평가**: 수정 후 Tier 2 재실행하여 목표 달성 여부 확인
4. **커밋**: 전체 변경사항 정리 후 커밋

---

## 4. 벡터 DB 현황

```
law_vectors 컬렉션:
  - 총 벡터: 314개
  - ActionKit laws: 168벡터 (21아이템 × ~8청크)
  - ActionKit kits: 146벡터 (25아이템 × ~6청크)
  - 기존 법령 샘플: 0벡터 (재인덱싱 시 .temp/rag 없어서 건너뜀)

백업:
  - .temp/backups/law_vectors_20260224_153755.json (기존 3건 보존)
```
