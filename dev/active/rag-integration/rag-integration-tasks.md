# RAG-ActionKit 통합 연동 - 작업 체크리스트

> Last Updated: 2026-02-25
> Status: 미착수

---

## Status Legend
- [ ] Not started
- [x] In progress
- [x] Complete (checked)
- [!] Blocked
- [-] Skipped

## Progress Summary
0 / 24 tasks complete (0%)

---

## Phase 1: 데이터 정합성 + 즉시 수정 (2일)

> 목표: 골든 데이터셋과 실제 데이터 커버리지 일치, 즉시 수정 반영
> 담당: data-analyst + chat-engineer (병렬)

### Section 1.1: 커버리지 분석 (data-analyst)

- [ ] **T-1.1** legal-001~015 vs ActionKit 커버리지 매핑표 작성
  - 파일: `dev/active/rag-integration/coverage-matrix.md` (신규)
  - 상세:
    - golden_dataset의 legal-001~015 각 질문에 대해:
      - 어떤 ActionKit 아이템으로 답변 가능한지 매핑
      - 답변 불가 질문 식별 (예상 12건)
      - 답변 가능 질문의 expected_source, expected_keywords 검증
    - 출력 형식: 15행 x 5열 매트릭스 (question, answerable, matched_item_ids, gap_reason, action)
  - 수락 기준: 15건 전체 분석 완료, "교체 필요" vs "유지" 판정
  - Size: M
  - 의존성: 없음

### Section 1.2: 골든 데이터셋 교정 (data-analyst)

- [ ] **T-1.2** 커버리지 밖 질문 재작성 (예상 12건)
  - 파일: `app-backend/tests/eval/data/golden_dataset.json`
  - 상세:
    - T-1.1 결과에서 "교체 필요"로 판정된 질문을 ActionKit 커버리지 내 질문으로 교체
    - 교체 시 도메인 분포 유지: legal(chapter-1~6) + kits(legal/tax/hr/grant)
    - ground_truth를 ActionKit seed 데이터 기반으로 재작성
    - expected_law_reference를 ActionKit relatedLaws와 일치시킴
    - 교체 전 원본을 `golden_dataset_v1_backup.json`으로 백업
  - 수락 기준:
    - 50건 전체가 ActionKit 커버리지 내
    - ID 컨벤션 유지 (legal-001~015)
    - Tier 1 구조 테스트 통과
  - Size: L
  - 의존성: T-1.1

### Section 1.3: 키워드 사전 확장 (chat-engineer)

- [ ] **T-1.3** classify_query LEGAL_KEYWORDS에 키워드 7개 추가
  - 파일: `app-backend/app/features/rag/application/chat_service.py`
  - 상세:
    - 추가 키워드: "행정심판", "행정조사", "소방", "개인정보", "근로계약", "보험", "세금"
    - LEGAL_KEYWORDS frozenset 확장 (13개 → 20개)
    - rag-upgrade-status.md 이슈 B에서 식별된 오분류 7건 해소 목표
  - 수락 기준: 키워드 추가 후 golden_dataset 50건 중 routing accuracy >= 90%
  - Size: S
  - 의존성: 없음

### Section 1.4: 기존 법령 샘플 재적재 (data-analyst)

- [ ] **T-1.4** 백업 데이터 3건 청킹 적용 재적재
  - 파일: `app-backend/scripts/seed_rag_vectors.py`
  - 상세:
    - 백업 위치: `.temp/backups/law_vectors_20260224_153755.json` (3건: 일반음식점, 휴게음식점, 집단급식소)
    - seed_rag_vectors.py에 `--restore-backup` 옵션 추가
    - 청킹 적용 재적재 (chunk_size=600, overlap=100)
    - 예상 벡터 추가: ~24개 (3건 x ~8청크)
    - 적재 후 벡터 총수: ~338개
  - 수락 기준: 벡터 DB에 338개 내외 벡터 확인, 기존 314개 벡터 보존
  - Size: M
  - 의존성: 없음

### Section 1.5: Phase 1 검증 (data-analyst)

- [ ] **T-1.5** Tier 1 검증 (구조 테스트)
  - 파일: `app-backend/tests/eval/test_tier1_basic.py`
  - 상세:
    - 재작성된 golden_dataset 50건으로 Tier 1 실행
    - 모든 필수 필드 존재 확인
    - ID 유일성, category 유효값, difficulty 유효값 확인
  - 수락 기준: 29/29 PASSED (또는 테스트 추가 시 전체 PASS)
  - Size: S
  - 의존성: T-1.2

- [ ] **T-1.6** Tier 2 재실행 + baseline 비교
  - 파일: `app-backend/scripts/eval/run_evaluation.py`
  - 상세:
    - `python -m scripts.eval.run_evaluation --tier 2`
    - 결과를 latest_run.json에 자동 저장
    - baseline.json과 비교하여 회귀 여부 확인
    - 목표: Answer Correctness >= 0.45, Routing Accuracy >= 90%
    - 목표 달성 시: `--update-baseline`으로 baseline 갱신
  - 수락 기준: 회귀 없음, Answer Correctness 개선 확인
  - Size: S
  - 의존성: T-1.2, T-1.3, T-1.4, T-1.5

---

## Phase 2: 핵심 연동 구현 (5일)

> 목표: 챗봇과 로드맵 생성에서 ActionKit 데이터를 직접 활용
> 담당: chat-engineer (Section 2A) + roadmap-engineer (Section 2B) 병렬

### Section 2A: 챗봇 고도화 (chat-engineer)

- [ ] **T-2A.1** 시스템 프롬프트 한국어 전환
  - 파일:
    - `app-backend/app/features/rag/application/rag_service.py` (RAG 프롬프트)
    - `app-backend/app/features/rag/application/chat_service.py` (General 프롬프트)
  - 상세:
    - RAG 프롬프트: 영어 → 한국어 전환
      - 역할 정의: "한국 창업 법률/행정 전문 AI 어시스턴트"
      - 규칙: 컨텍스트 기반만, 모르면 솔직히, 법령 인용, 쉬운 한국어
      - 형식: 불릿 포인트, 출처 명시
    - General 프롬프트: GENERAL_SYSTEM_PROMPT 한국어 전환
    - A/B 테스트: 영어 vs 한국어 프롬프트 10건 비교
  - 수락 기준: A/B 테스트에서 한국어 프롬프트가 동등 이상 품질
  - Size: M
  - 의존성: Phase 1 완료

- [ ] **T-2A.2** format_docs → format_docs_with_metadata 교체
  - 파일: `app-backend/app/features/rag/application/rag_service.py`
  - 상세:
    - 기존: `"\n\n".join(doc.page_content for doc in docs)`
    - 신규: 각 doc에 메타데이터 헤더 추가
      ```
      [출처 1] {title} ({category})
      법령 참조: {law_reference}
      {page_content}
      ---
      ```
    - LLM이 출처를 인용할 수 있도록 구조화
  - 수락 기준: 답변에 출처 정보 포함 확인 (수동 5건 테스트)
  - Size: M
  - 의존성: T-2A.1

- [ ] **T-2A.3** retriever k=3 → k=5 상향
  - 파일: `app-backend/app/features/rag/application/rag_service.py`
  - 상세:
    - `self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})`
    - 벡터 314~338개 중 5개 검색 → 다양한 ActionKit 소스 노출
    - 토큰 예산 확인: k=5 x 600자 x 1.5토큰/자 = ~4,500토큰 (허용 범위)
  - 수락 기준: Hit Rate@5 >= Hit Rate@3 (하락 없음)
  - Size: S
  - 의존성: 없음

- [ ] **T-2A.4** SemanticRouter 구현
  - 파일: `app-backend/app/features/rag/application/semantic_router.py` (신규)
  - 상세:
    - SemanticRouter 클래스 구현
      - `__init__`: OpenAIEmbeddings 주입, 카테고리별 앵커 텍스트 정의
      - `initialize()`: 앵커 임베딩 사전 계산 (async, 앱 시작 시 1회)
      - `classify(query: str) -> Literal["legal", "general"]`: 코사인 유사도 분류
      - threshold: 0.7 (tunable)
      - fallback: LEGAL_KEYWORDS 매칭
    - 앵커 텍스트 설계:
      - legal: 8개 (인허가, 세무, 인사, 소방, 행정 등)
      - general: 4개 (마케팅, 인테리어, 사업계획 등)
    - 코사인 유사도: numpy 또는 수동 구현
  - 수락 기준:
    - golden_dataset 50건으로 테스트 시 routing accuracy >= 95%
    - 초기화 시간 < 3초
    - 분류 latency < 500ms/건
  - Size: L
  - 의존성: T-2A.1

- [ ] **T-2A.5** ChatService.classify_query를 SemanticRouter로 교체
  - 파일:
    - `app-backend/app/features/rag/application/chat_service.py`
    - `app-backend/app/features/rag/application/deps.py`
  - 상세:
    - deps.py에 `get_semantic_router()` 싱글톤 추가 (lru_cache)
    - ChatService.__init__에 SemanticRouter 주입
    - chat() 메서드에서 classify_query() → semantic_router.classify() 교체
    - classify_query() 함수는 fallback으로 보존 (SemanticRouter 실패 시)
  - 수락 기준: 기존 API 계약 불변, routing accuracy >= 95%
  - Size: M
  - 의존성: T-2A.4

- [ ] **T-2A.6** 챗봇 단위 테스트 갱신
  - 파일: `app-backend/tests/eval/test_tier1_basic.py`
  - 상세:
    - SemanticRouter 관련 테스트 추가:
      - 앵커 임베딩 초기화 테스트
      - 법률 질문 분류 테스트 (5건)
      - 일반 질문 분류 테스트 (3건)
      - fallback 동작 테스트
    - format_docs_with_metadata 출력 형식 테스트
  - 수락 기준: 신규 테스트 전체 PASS
  - Size: M
  - 의존성: T-2A.4, T-2A.5

### Section 2B: 로드맵 ActionKit 매칭 + LLM 맞춤화 (roadmap-engineer)

- [ ] **T-2B.1** ActionKitMatcher 구현
  - 파일: `app-backend/app/features/roadmaps/application/actionkit_matcher.py` (신규)
  - 상세:
    - ActionKitMatcher 클래스 구현:
      - `__init__(self, rag_service: RagService, session: AsyncSession)`
      - `async match(self, business_type: str, location: str) -> list[MatchedActionKit]`
    - 검색 전략:
      1. 벡터 유사도 검색: `"{business_type} {location} 창업"` → k=10
         - 메타데이터에서 actionkit item_id 추출
      2. 관계형 DB JOIN 보강:
         - `SELECT * FROM actionkit_items WHERE id IN (...)`
         - JOIN actionkit_item_highlights
         - JOIN actionkit_related_laws
         - JOIN actionkit_files
      3. 카테고리별 그룹핑 (CATEGORY_TO_PHASE 매핑)
      4. sha256 기반 중복 제거
    - MatchedActionKit 데이터 클래스:
      ```python
      @dataclass
      class MatchedActionKit:
          item: ActionKitItem
          highlights: list[ActionKitItemHighlight]
          related_laws: list[ActionKitRelatedLaw]
          files: list[ActionKitFile]
          phase_group: str
          relevance_score: float
      ```
  - 수락 기준:
    - "카페 서울 강남" 입력 시 최소 5개 item 매칭
    - 각 item에 highlights, related_laws 포함
    - 카테고리 그룹핑 정확
  - Size: XL
  - 의존성: Phase 1 완료

- [ ] **T-2B.2** LLMPersonalizer 구현 (ActionKit 팩트 + GenerationPayload → 7가지 영역 맞춤화)
  - 파일: `app-backend/app/features/roadmaps/application/llm_personalizer.py` (신규)
  - 상세:
    - LLMPersonalizer 클래스 구현:
      - `__init__(self, llm: ChatOpenAI)`
      - `async personalize(self, matched_items: list[MatchedActionKit], payload: GenerationPayload) -> list[StepDetail]`
    - 입력:
      - ActionKit 구조화 데이터 (팩트 레이어): highlights 원문, 법령명/요약, 파일 경로
      - GenerationPayload 전체 (사용자 상황): business_type, location, startup_type, open_timeline, budget_range, experience_level
    - LLM 맞춤화 7가지 영역:
      1. checklist: highlights 원문 → 업종에 맞게 우선순위 재배열 + 불필요 항목 필터링 + 보충
      2. legal_basis: 법령명/요약 → 해당 업종에 특히 중요한 조항 강조
      3. documents: 파일 경로 → 제출 순서 + 준비 가이드 추가
      4. phases: 카테고리 기반 구성 → 순서 조정 + 병행 가능 판단
      5. objective: 업종/지역 맞춤 목표 생성
      6. risk_notes: 업종 특화 위험요소 생성
      7. estimated_days: open_timeline 기반 현실적 소요일 산출
    - GenerationPayload 필드별 분기:
      - startup_type: 신규 → 사업자등록 강조, 양수양도 → 영업양도 절차 추가 + 신규 등록 제외, 프랜차이즈 → 가맹사업법 추가
      - open_timeline: 3개월 → phase 병행 처리, 6개월 → 순차 진행
      - budget_range: 3000만 → 소규모 인허가/정책자금 우선, 1억 → 대규모 기준
      - experience_level: BEGINNER → 세분화 + 용어 설명, EXPERIENCED → 핵심만 간결
    - CATEGORY_TO_PHASE 매핑 테이블 정의
    - 프롬프트 설계 원칙:
      - 구조 지시 → 맞춤화 지시 → 제약 조건 순서로 구성
      - **규칙:** ActionKit이 제공한 법령명, 파일경로는 수정 금지. LLM은 "판단하고 맞춤화"만 수행.
    - 후처리 검증:
      - LLM 출력에서 법령명/파일경로가 원본과 일치하는지 검증
      - 불일치 시 원본으로 복원
  - 수락 기준:
    - 5개 phase_group → 5개 StepDetail 정상 생성
    - checklist: 업종에 맞게 재배열 확인 (수동 검증 3건)
    - legal_basis: 원본 법령명 보존 확인
    - documents: 원본 파일경로 보존 확인
    - startup_type 변경 시 결과 차이 확인 (신규 vs 양수양도 비교 1건)
  - Size: XL
  - 의존성: T-2B.1

- [ ] **T-2B.3** RoadmapGenerationService 리팩토링 (ActionKit 매칭 → LLM 맞춤화 → 저장)
  - 파일: `app-backend/app/features/roadmaps/application/roadmap_generation_service.py`
  - 상세:
    - process_job() 흐름 변경:
      1. payload에서 business_type, location 및 GenerationPayload 전체 추출
      2. ActionKitMatcher.match(business_type, location) 호출 → 팩트 데이터 수집
      3. 매칭 결과가 충분하면 (>= 3 items):
         - LLMPersonalizer.personalize(matched_items, payload) 호출
         - ActionKit 팩트 + 사용자 입력 기반으로 7가지 영역 맞춤화
         - 결과: 개인화된 StepDetail 리스트
      4. 매칭 결과 불충분하면:
         - 기존 자유 생성 로직 fallback (_generate_master_with_retry)
         - mapping_source="llm_generated"로 표기
      5. DB 저장: metadata_json에 actionkit_item_id, mapping_source 포함
    - LLMPersonalizer 의존성 주입:
      - deps.py에 `get_llm_personalizer()` 싱글톤 추가
      - RoadmapGenerationService.__init__에 LLMPersonalizer 주입
    - 기존 _generate_master_with_retry, _generate_details_parallel은 fallback 전용으로 보존
  - 수락 기준:
    - ActionKit 매칭 성공 시: LLMPersonalizer 경유, fallback 미사용
    - 생성된 StepDetail에 actionkit_item_id 포함
    - startup_type/budget_range 등 사용자 입력이 결과에 반영됨 (수동 검증 3건)
    - 기존 API 계약 불변
  - Size: XL
  - 의존성: T-2B.1, T-2B.2

- [ ] **T-2B.4** metadata_json에 actionkit_item_id 주입
  - 파일: `app-backend/app/repositories/roadmap_repository.py`
  - 상세:
    - create_steps_with_details() 메서드 수정:
      - legal_basis 항목: metadata_json에 actionkit_item_id, actionkit_domain, actionkit_category, mapping_source 추가
      - documents 항목: metadata_json에 actionkit_item_id, actionkit_file_id, mapping_source 추가
      - checklist 항목: metadata_json에 actionkit_item_id, actionkit_highlight_id, mapping_source 추가
    - 기존 LLM 자유 생성 결과는 mapping_source="llm_generated"로 표기
  - 수락 기준:
    - DB에 저장된 actions의 metadata_json에 actionkit_item_id 존재
    - 기존 자유 생성 결과도 정상 저장 (하위 호환)
  - Size: M
  - 의존성: T-2B.3

- [ ] **T-2B.5** 로드맵 생성 통합 테스트
  - 파일: `app-backend/tests/integration/test_roadmap_generation.py` (신규)
  - 상세:
    - 테스트 시나리오 5건:
      1. 카페(휴게음식점) + 서울 → ActionKit 매핑 성공
      2. 일반음식점 + 경기도 → ActionKit 매핑 성공
      3. IT 스타트업 + 판교 → ActionKit 매핑 불충분 → fallback
      4. 미용실 + 부산 → 부분 매핑
      5. 빈 입력 → 검증 실패
    - 각 시나리오에서 검증:
      - 생성 성공 여부
      - StepDetail 수 >= 3
      - legal_basis에 actionkit_item_id 포함 여부
      - documents에 유효한 file_url 포함 여부
  - 수락 기준: 5건 전체 PASS
  - Size: L
  - 의존성: T-2B.3, T-2B.4

---

## Phase 3: 통합 검증 (2일)

> 목표: 전체 시스템 품질 정량 검증, baseline 갱신
> 담당: eval-engineer + data-analyst

### Section 3.1: 로드맵 평가 체계 구축 (eval-engineer)

- [ ] **T-3.1** 로드맵 품질 평가 메트릭 구현 (개인화 포함)
  - 파일: `app-backend/scripts/eval/roadmap_evaluator.py` (신규)
  - 상세:
    - RoadmapEvaluator 클래스:
      - `evaluate(self, roadmap_id: UUID) -> RoadmapEvalResult`
      - `evaluate_personalization(self, roadmap_a_id: UUID, roadmap_b_id: UUID) -> PersonalizationEvalResult`
    - 메트릭 5종:
      1. actionkit_mapping_rate: LEGAL_BASIS action 중 actionkit_item_id 보유 비율
      2. legal_basis_accuracy: LLM judge로 매핑 법령의 업종 관련성 평가
      3. document_validity: file_url이 ActionKitFile과 매핑되는 비율
      4. generation_success_rate: fallback 없이 정상 생성 비율
      5. personalization_score: 사용자 입력(startup_type, budget_range, open_timeline, experience_level)이 결과에 반영된 비율 (LLM judge)
    - 개인화 평가 방법:
      - 동일 업종 + 다른 입력 조합으로 2개 로드맵 생성
      - LLM judge가 두 결과의 차이를 분석하여 입력 반영 여부 판정
      - 예: 카페 + 신규/3000만 vs 카페 + 양수양도/1억 → checklist, phases 차이 검증
    - RoadmapEvalResult, PersonalizationEvalResult 데이터 클래스
  - 수락 기준: 평가기 구현 완료, 단위 테스트 PASS
  - Size: L
  - 의존성: Phase 2 완료

- [ ] **T-3.2** run_evaluation.py에 --tier 4 추가
  - 파일: `app-backend/scripts/eval/run_evaluation.py`
  - 상세:
    - `--tier 4` 옵션: 로드맵 E2E 평가
    - 흐름:
      1. roadmap_golden_dataset.json에서 시나리오 로드
      2. 각 시나리오에 대해 RoadmapGenerationService.process_job() 실행
      3. 생성된 로드맵에 대해 RoadmapEvaluator.evaluate() 실행
      4. 결과 집계 + roadmap_eval_results.json 저장
    - baseline 비교 로직 확장: 로드맵 메트릭도 회귀 감지
  - 수락 기준: `--tier 4` 실행 시 정상 완료 + 결과 파일 생성
  - Size: L
  - 의존성: T-3.1

### Section 3.2: 로드맵 평가 데이터 (data-analyst)

- [ ] **T-3.3** 로드맵 평가 골든 데이터셋 작성 (개인화 변형 포함)
  - 파일: `app-backend/tests/eval/data/roadmap_golden_dataset.json` (신규)
  - 상세:
    - 기본 시나리오 5건 (업종 x 지역):
      1. 휴게음식점(카페) + 서울: 기대 phase 5개, legal_basis >= 5
      2. 일반음식점 + 부산: 기대 phase 4개, legal_basis >= 4
      3. 소매업 + 대구: 기대 phase 3개 (일부 ActionKit 미매핑)
      4. 프랜차이즈 가맹점 + 인천: 기대 phase 5개
      5. 미용업 + 경기: 기대 phase 3개
    - 개인화 변형 시나리오 3건 (동일 업종, 다른 입력 조합):
      6. 카페 + 서울 + 신규/3개월/3000만/BEGINNER → 기대: 병행 phase, 초보자 체크리스트
      7. 카페 + 서울 + 양수양도/6개월/1억/EXPERIENCED → 기대: 영업양도 절차, 간결한 체크리스트
      8. 일반음식점 + 부산 + 프랜차이즈/3개월/3000만/BEGINNER → 기대: 가맹사업법 추가
    - 각 시나리오에 기대값 정의:
      - expected_phases: list[str]
      - expected_min_legal_basis: int
      - expected_min_documents: int
      - expected_actionkit_mapping_rate: float (>= 0.8)
    - 개인화 변형 시나리오에 추가 기대값:
      - expected_personalization_markers: list[str] (결과에 반영되어야 할 키워드)
      - comparison_pair_id: str (비교 대상 시나리오 ID)
  - 수락 기준: 8건 작성 완료, 기대값이 현실적, 개인화 변형 간 차이 기대 명확
  - Size: L
  - 의존성: Phase 2 완료

### Section 3.3: 최종 평가 실행 (eval-engineer)

- [ ] **T-3.4** 개인화 품질 평가 (동일 업종, 다른 입력으로 비교)
  - 파일: `app-backend/scripts/eval/roadmap_evaluator.py`
  - 상세:
    - 골든 데이터셋의 개인화 변형 시나리오(#6~#8) 활용
    - 비교 쌍별 로드맵 2개씩 생성:
      - 쌍 1: 카페 + 신규/3000만/BEGINNER vs 카페 + 양수양도/1억/EXPERIENCED
      - 쌍 2: 일반음식점 + 신규 vs 일반음식점 + 프랜차이즈
    - RoadmapEvaluator.evaluate_personalization() 실행
    - LLM judge가 차이 분석:
      - checklist 우선순위/항목 차이
      - phases 순서/병행 차이
      - risk_notes 내용 차이
      - estimated_days 차이
    - personalization_score >= 70% 목표
  - 수락 기준:
    - 비교 쌍 간 결과 차이 확인 (startup_type 변경 시 checklist/phases 변경됨)
    - personalization_score >= 70%
  - Size: M
  - 의존성: T-3.1, T-3.3

- [ ] **T-3.5** 전체 Tier 2~4 실행
  - 파일: --
  - 상세:
    - Tier 2 실행: 챗봇 품질 50건
    - Tier 3 실행: 챗봇 심화 평가
    - Tier 4 실행: 로드맵 E2E 8건 (기본 5건 + 개인화 변형 3건)
    - 결과 수집 + 이전 baseline 비교
  - 수락 기준:
    - 챗봇: Routing >= 95%, Faithfulness >= 0.80, Correctness >= 0.55
    - 로드맵: 매핑률 >= 80%, legal_basis 정확도 >= 70%
    - 로드맵: 개인화 수준 >= 70%
  - Size: M
  - 의존성: T-3.1, T-3.2, T-3.3, T-3.4

- [ ] **T-3.6** baseline 갱신 + EVALUATION_REPORT_V2.md 작성
  - 파일:
    - `app-backend/tests/eval/results/baseline.json`
    - `app-backend/tests/eval/results/EVALUATION_REPORT_V2.md` (신규)
  - 상세:
    - `python -m scripts.eval.run_evaluation --update-baseline`
    - EVALUATION_REPORT_V2.md 작성:
      - 챗봇 메트릭 추이 (rag-upgrade baseline → Phase 1 → Phase 3)
      - 로드맵 메트릭 (신규, 개인화 포함)
      - 개선 사항 요약
      - 잔여 이슈 + 후속 작업
  - 수락 기준: baseline 갱신 완료, 리포트 작성 완료
  - Size: M
  - 의존성: T-3.5

- [ ] **T-3.7** 회귀 감지 임계값 조정
  - 파일: `app-backend/scripts/eval/run_evaluation.py`
  - 상세:
    - 새 baseline 기준으로 회귀 감지 margin 재설정
    - 로드맵 메트릭 회귀 감지 추가:
      - actionkit_mapping_rate: margin 5%
      - legal_basis_accuracy: margin 10%
      - personalization_score: margin 10%
  - 수락 기준: 회귀 감지 로직 동작 확인 (의도적 열화 테스트)
  - Size: S
  - 의존성: T-3.6

---

## 진행 상태 요약

| Phase | 상태 | 완료/전체 | 담당 |
|-------|------|----------|------|
| Phase 1: 데이터 정합성 + 즉시 수정 | 미착수 | 0/6 | data-analyst, chat-engineer |
| Phase 2A: 챗봇 고도화 | 미착수 | 0/6 | chat-engineer |
| Phase 2B: 로드맵 ActionKit 매칭 + LLM 맞춤화 | 미착수 | 0/5 | roadmap-engineer |
| Phase 3: 통합 검증 | 미착수 | 0/7 | eval-engineer, data-analyst |
| **합계** | | **0/24** | |

---

## 후속 작업 (본 계획 범위 밖)

> 아래 항목은 Phase 3 완료 후 별도 계획 수립 필요

- [ ] **F-1** 리랭킹(Reranking) 도입 검토 (rag-upgrade P-5 이관)
  - cross-encoder 기반 리랭킹으로 retriever 정밀도 추가 개선
  - 비용/성능 트레이드오프 분석 필요

- [ ] **F-2** 프론트엔드 ActionKit 원문 링크 UI
  - RoadmapStepAction.metadata_json의 actionkit_item_id 활용
  - 로드맵 상세 페이지에서 "관련 법령 원문 보기" 링크 표시
  - ActionKit 파일 다운로드 기능

- [ ] **F-3** 챗봇 대화 내 ActionKit 카드 UI
  - 챗봇 답변에 관련 ActionKit 아이템을 카드 형태로 표시
  - 카드 클릭 시 ActionKit 상세 페이지로 이동

- [ ] **F-4** ActionKit 데이터 추가 적재
  - 현재 46개 아이템 외 추가 법령/가이드 데이터 수집
  - 새 도메인 확장: 지식재산, 수출입, 환경 등

- [ ] **F-5** 벡터 DB 성능 최적화
  - 벡터 수 1,000개+ 시점 인덱스 최적화 (IVFFlat → HNSW)
  - 메타데이터 필터 인덱스 추가

- [ ] **F-6** 로드맵 생성 캐싱
  - 동일 업종+지역 조합의 ActionKitMatcher 결과 캐싱
  - Redis 또는 메모리 캐시

---

## Deployment Checklist

- [ ] DB 마이그레이션: 불필요 (metadata_json 확장만)
- [ ] 환경 변수: 변경 없음
- [ ] 패키지 의존성: numpy 추가 여부 확인 (SemanticRouter용)
- [ ] 벡터 DB: 샘플 3건 재적재 (Phase 1)
- [ ] 기존 테스트: Tier 1~3 전체 PASS 확인
- [ ] 신규 테스트: 통합 테스트 + 로드맵 평가 PASS 확인
- [ ] baseline.json: Phase 3에서 최종 갱신

---

## Notes

- Phase 1과 Phase 2는 순차 (Phase 1 완료 → Phase 2 시작)
- Phase 2A(챗봇)와 Phase 2B(로드맵)는 병렬 진행 가능
- Phase 3은 Phase 2A, 2B 모두 완료 후 시작
- 모든 변경은 API 계약 불변 (프론트엔드 영향 없음)
- 커밋은 Phase별 1회 권장 (Phase 1 커밋, Phase 2 커밋, Phase 3 커밋)
