# RAG-ActionKit 통합 연동 - 컨텍스트 문서

> Last Updated: 2026-02-25

---

## 1. 핵심 파일 맵

### 1.1 챗봇 시스템 (수정 대상)

| 파일 | 역할 | 변경 내용 |
|------|------|----------|
| `app-backend/app/features/rag/application/chat_service.py` | 질문 분류 + 라우팅 | LEGAL_KEYWORDS 확장(P1), SemanticRouter 교체(P2), 한국어 프롬프트(P2) |
| `app-backend/app/features/rag/application/rag_service.py` | RAG 파이프라인 | 한국어 프롬프트(P2), format_docs_with_metadata(P2), k=3→5(P2) |
| `app-backend/app/features/rag/application/deps.py` | 싱글톤 DI | SemanticRouter 싱글톤 추가(P2) |

### 1.2 로드맵 생성 시스템 (수정 대상)

| 파일 | 역할 | 변경 내용 |
|------|------|----------|
| `app-backend/app/features/roadmaps/application/roadmap_generation_service.py` | 비동기 로드맵 생성 | ActionKit 매칭(P2) → LLM 맞춤화(P2) → 저장 흐름으로 변경 |
| `app-backend/app/repositories/roadmap_repository.py` | DB 저장 | metadata_json에 actionkit_item_id 주입(P2) |

### 1.3 ActionKit 데이터 레이어 (참조/부분 수정)

| 파일 | 역할 | 변경 내용 |
|------|------|----------|
| `app-backend/app/services/actionkit_data_source.py` | ActionKit → LawData 변환 | 변경 없음 (참조) |
| `app-backend/app/services/actionkit_etl.py` | ActionKit → ProcessedLawData 변환 | 변경 없음 (참조) |
| `app-backend/app/services/vector_store.py` | 벡터 DB 적재 | 변경 없음 (참조) |
| `app-backend/app/models/actionkit.py` | ActionKit 관계형 모델 | 변경 없음 (참조) |
| `app-backend/app/models/roadmap.py` | 로드맵/Step/Action 모델 | 변경 없음 (스키마 유지) |
| `app-backend/scripts/seeds/actionkit_seed_source.py` | LAW_DATA + ACTION_KIT_DATA 원본 | 참조 (매핑 기준) |
| `app-backend/scripts/seed_rag_vectors.py` | 벡터 인제스트 | 샘플 3건 재적재 옵션 추가(P1) |

### 1.4 평가 시스템 (수정 대상)

| 파일 | 역할 | 변경 내용 |
|------|------|----------|
| `app-backend/tests/eval/data/golden_dataset.json` | 골든 데이터셋 50건 | legal-001~015 중 12건 재작성(P1) |
| `app-backend/tests/eval/results/baseline.json` | 평가 기준점 | Phase 1, 3에서 갱신 |
| `app-backend/scripts/eval/run_evaluation.py` | 평가 실행 | --tier 4 추가(P3) |
| `app-backend/tests/eval/test_tier1_basic.py` | 구조 테스트 | 재작성된 질문 반영 확인(P1) |

### 1.5 신규 생성 파일

| 파일 | 역할 | Phase |
|------|------|-------|
| `app-backend/app/features/rag/application/semantic_router.py` | 임베딩 기반 의미 분류기 | Phase 2 |
| `app-backend/app/features/roadmaps/application/actionkit_matcher.py` | 업종 기반 ActionKit 검색/매칭 (팩트 레이어) | Phase 2 |
| `app-backend/app/features/roadmaps/application/llm_personalizer.py` | ActionKit 팩트 + GenerationPayload → 개인화 맞춤화 (지능 레이어) | Phase 2 |
| `app-backend/scripts/eval/roadmap_evaluator.py` | 로드맵 품질 평가기 | Phase 3 |
| `app-backend/tests/eval/data/roadmap_golden_dataset.json` | 로드맵 평가 시나리오 | Phase 3 |
| `app-backend/tests/integration/test_roadmap_generation.py` | 로드맵 생성 통합 테스트 | Phase 2 |
| `dev/active/rag-integration/coverage-matrix.md` | legal 질문 vs ActionKit 매핑표 | Phase 1 |

---

## 2. 기술적 의사결정 기록

### 결정 1: SemanticRouter 설계 (Phase 2)

**날짜:** 2026-02-25 (계획)

**배경:** classify_query()의 키워드 13개 기반 라우팅이 80% 정확도에 그침. "4대보험", "행정심판" 등 법률 관련 질문을 놓치는 구조적 한계.

**결정:** 임베딩 코사인 유사도 기반 분류 + 키워드 fallback
**구현 방안:**
```python
class SemanticRouter:
    def __init__(self, embeddings: OpenAIEmbeddings):
        self.embeddings = embeddings
        # 카테고리별 앵커 텍스트 (초기화 시 임베딩 캐싱)
        self.anchors = {
            "legal": [
                "창업 시 필요한 인허가 절차",
                "영업신고 방법과 서류",
                "법인 설립 등록",
                "세금 신고 및 납부",
                "4대보험 가입 절차",
                "행정심판 및 행정처분",
                "근로계약서 작성 의무",
                "소방 안전 기준",
            ],
            "general": [
                "카페 인테리어 추천",
                "마케팅 전략",
                "사업계획서 작성",
                "투자 유치 방법",
            ],
        }
        self._anchor_embeddings: dict[str, list[list[float]]] = {}

    async def initialize(self):
        """앵커 임베딩 사전 계산 (앱 시작 시 1회)"""
        for category, texts in self.anchors.items():
            self._anchor_embeddings[category] = await self.embeddings.aembed_documents(texts)

    def classify(self, query_embedding: list[float], threshold: float = 0.7) -> str:
        """코사인 유사도 기반 분류"""
        # legal 앵커와의 최대 유사도 계산
        # threshold 이상이면 "legal", 아니면 LEGAL_KEYWORDS fallback
        ...
```

**트레이드오프:**
- 장점: 새 법률 도메인 추가 시 앵커 텍스트만 추가, 키워드 관리 부담 감소
- 단점: 초기화 시 임베딩 API 호출 1회 (~$0.01), 요청당 임베딩 1회 추가 (~$0.0001/건)
- 완화: 앵커 임베딩 캐싱, 요청 임베딩은 RAG retriever에도 재활용 가능

### 결정 2: 한국어 시스템 프롬프트 설계 (Phase 2)

**날짜:** 2026-02-25 (계획)

**배경:** 현재 RAG 프롬프트가 영어("You are an AI assistant for startup founders in Korea"), 모든 데이터와 사용자 질문은 한국어.

**결정:** 전면 한국어 전환

**RAG 프롬프트 (안):**
```
당신은 한국 창업 법률·행정 전문 AI 어시스턴트입니다.

[규칙]
1. 아래 제공된 컨텍스트 문서에 기반해서만 답변하세요.
2. 컨텍스트에 답변 근거가 없으면 "제공된 문서에서 해당 정보를 찾을 수 없습니다."라고 솔직히 답하세요.
3. 관련 법령이 있으면 법령명과 조항을 인용하세요.
4. 창업 초보자도 이해할 수 있는 쉬운 한국어로 설명하세요.
5. 핵심 내용은 불릿 포인트로 정리하세요.

[컨텍스트]
{context}

[질문]
{question}

[답변]
```

**General 프롬프트 (안):**
```
당신은 한국 창업자를 위한 친절한 AI 어시스턴트입니다.
명확하고 간결하게 한국어로 답변하세요.
모르는 것은 솔직히 모른다고 말하세요.
```

### 결정 3: ActionKitMatcher 검색 전략 + LLM 맞춤화 아키텍처 (Phase 2)

**날짜:** 2026-02-25 (확정)

**배경:** 로드맵 생성 시 업종/지역에 맞는 ActionKit item을 찾아야 함. 벡터 검색만으로는 카테고리 구조를 무시. 또한 LLM의 역할이 objective/risk_notes/estimated_days 3개만 생성하는 것으로 축소되면 개인화가 부족.

**결정:** 하이브리드 방식 B + LLM 맞춤화
- ActionKit = **팩트 레이어** (정확한 법령, 체크리스트, 파일 경로 제공)
- LLM = **지능 레이어** (업종/지역/형태/일정/예산에 맞춤화)

**ActionKitMatcher 검색 흐름 (Step 1: 팩트 수집):**
```
1. 업종 키워드로 벡터 검색 (k=10, law_vectors)
   → ActionKit item_id 추출 (metadata에서)

2. 관계형 DB 보강 조회
   → ActionKitItem JOIN ActionKitItemHighlight
   → ActionKitItem JOIN ActionKitRelatedLaw
   → ActionKitItem JOIN ActionKitFile

3. 카테고리별 그룹핑
   laws/chapter-1~6 → 인허가 phase
   kits/legal → 법률 phase
   kits/tax → 세무 phase
   kits/hr → 인사 phase
   kits/grant → 지원금 phase

4. 중복 제거 (sha256 기준)
5. 최종 MatchedActionKit 리스트 반환
```

**LLM 맞춤화 (Step 2: 지능 레이어):**

LLM에게 ActionKit 구조화 데이터 + GenerationPayload 전체를 전달하여 7가지 영역에서 맞춤화:

| # | 영역 | LLM 역할 |
|---|------|---------|
| 1 | checklist | highlights 원문 → 우선순위 재배열 + 불필요 항목 필터 + 보충 |
| 2 | legal_basis | 법령명/요약 → 해당 업종에 중요한 조항 강조 |
| 3 | documents | 파일 경로 → 제출 순서 + 준비 가이드 추가 |
| 4 | phases | 카테고리 기반 구성 → 순서 조정 + 병행 가능 판단 |
| 5 | objective | 업종/지역 맞춤 목표 생성 |
| 6 | risk_notes | 업종 특화 위험요소 생성 |
| 7 | estimated_days | open_timeline 기반 현실적 소요일 산출 |

**규칙:** ActionKit이 제공한 법령명, 파일경로는 수정 금지. LLM은 "판단하고 맞춤화"만 수행.

**대안 검토:**
- 벡터 검색만: 카테고리 구조 무시, 그룹핑 어려움
- 관계형 DB만: 키워드 매칭 한계, 의미 검색 불가
- LLM은 3개만 생성 (objective, risk_notes, estimated_days): 개인화 부족, 모든 업종에 동일 checklist
- 하이브리드 + LLM 맞춤화: 양쪽 장점 결합, 프롬프트 복잡도 증가 (허용 범위)

### 결정 4: GenerationPayload 전체 활용 전략 (Phase 2)

**날짜:** 2026-02-25 (확정)

**배경:** GenerationPayload에 이미 풍부한 입력(업종, 지역, 형태, 일정, 예산, 경험)이 있지만 프롬프트에 텍스트로만 넘겨주고 실질적 분기가 없음. LLM 맞춤화에서 이 입력들을 구체적으로 활용해야 함.

**결정:** GenerationPayload 전체를 LLM 맞춤화 프롬프트에 구조적으로 전달

```
GenerationPayload 필드 → LLM 맞춤화 영향:

business_type: ActionKit 매칭 키

location: 지역별 조례/임대 환경 반영

startup_type (신규/프랜차이즈/양수양도):
  → 절차가 완전히 다름
  → 신규: 사업자등록 신규 신청 강조
  → 양수양도: 영업양도 절차 추가, 신규 등록 제외
  → 프랜차이즈: 가맹사업법 관련 추가

open_timeline (3개월/6개월):
  → phase 병행 여부 결정
  → estimated_days 타이트하게 조정
  → risk_notes에 일정 차질 위험 추가

budget_range (3000만/1억):
  → 정책자금 phase 우선순위 조정
  → 소규모/대규모 인허가 기준 차이 반영

experience_level (BEGINNER/EXPERIENCED):
  → 체크리스트 세분화 수준
  → 용어 설명 유무
```

**카테고리-Phase 기본 매핑 테이블:**

```python
CATEGORY_TO_PHASE = {
    # laws 챕터 → 인허가 관련 phase
    "chapter-1": "입지 검토",
    "chapter-2": "영업 인허가",
    "chapter-3": "안전·소방",
    "chapter-4": "영업 준수사항",
    "chapter-5": "위반 대응",
    "chapter-6": "행정처분 구제",
    # kits 카테고리 → 운영 관련 phase
    "legal": "법률 준비",
    "tax": "세무 설정",
    "hr": "인사·노무",
    "grant": "정책자금 신청",
}
```

**트레이드오프:**
- 고정 매핑: 예측 가능, 일관성 보장 (phase 기본 구조)
- LLM 맞춤화: startup_type/budget/timeline에 따라 phase 순서, 병행, 필터링이 달라짐
- 완화: LLM이 고정 매핑 기반 위에서 순서 조정 + 병행 가능 판단만 수행 (phase 자체를 제거하지는 않음)

### 결정 5: 로드맵 평가 메트릭 정의 (Phase 3)

**날짜:** 2026-02-25 (계획)

**배경:** 현재 로드맵 생성 품질을 정량적으로 측정하는 체계가 없음.

**결정:** 5가지 메트릭

| 메트릭 | 정의 | 측정 방법 |
|--------|------|----------|
| ActionKit 매핑률 | legal_basis 중 actionkit_item_id가 있는 비율 | DB 쿼리 |
| legal_basis 정확도 | 매핑된 법령이 해당 업종에 실제 관련되는 비율 | LLM judge |
| documents 유효성 | file_url이 실제 파일(ActionKitFile)과 매핑되는 비율 | DB 쿼리 |
| 생성 성공률 | fallback 없이 정상 생성된 비율 | 로그 분석 |
| 개인화 수준 | 사용자 입력(startup_type, budget 등)이 결과에 반영된 비율 | LLM judge: 동일 업종 + 다른 입력 조합으로 생성한 결과 비교 |

---

## 3. 데이터 흐름도

### 3.1 챗봇 데이터 흐름 (Phase 2 후)

```
[사용자]
   |  "4대보험 가입 방법이 궁금합니다"
   v
[SemanticRouter]
   |  query → embed → cosine_similarity(legal_anchors)
   |  max_sim = 0.82 > threshold 0.7 → "legal"
   v
[RagService.query()]
   |  question → retriever.invoke(question)
   |  PGVector k=5 검색
   v
[law_vectors (314 벡터)]
   |  상위 5개 청크 반환
   |  doc.metadata: {title, category, law_reference, source, ...}
   v
[format_docs_with_metadata()]
   |  [출처 1] 4대보험 가입 절차 안내 (actionkit/kits/hr)
   |  법령 참조: 국민건강보험법
   |  {page_content}
   |  ---
   |  [출처 2] 근로계약서 작성 의무 (actionkit/kits/hr)
   |  ...
   v
[LLM (gpt-4o-mini)]
   |  한국어 시스템 프롬프트 + 메타데이터 포함 컨텍스트
   v
[사용자에게 답변]
   "4대보험 가입은 다음 절차를 따릅니다:
    1. 국민건강보험법에 따라...
    - 출처: 4대보험 가입 절차 안내"
```

### 3.2 로드맵 생성 데이터 흐름 (Phase 2 후)

```
[사용자 입력 - GenerationPayload]
   |  업종: "카페", 지역: "서울 강남구"
   |  startup_type: "신규", open_timeline: "3개월"
   |  budget_range: "3000만", experience_level: "BEGINNER"
   v
[RoadmapGenerationService.process_job()]
   |
   v

Step 1: ActionKit 매칭 (팩트 레이어)
─────────────────────────────────────────────
[ActionKitMatcher.match(business_type="카페")]
   |  1) 벡터 검색: "카페 휴게음식점 강남" → k=10
   |     → item_ids: [1, 3, 5, 8, 22, 25, 30, 35, 40, 42]
   |  2) 관계형 DB JOIN:
   |     → ActionKitItem(id=1): 건축법 용도분류
   |     → ActionKitItemHighlight(item_id=1): ["건축물 용도 확인", ...]
   |     → ActionKitRelatedLaw(item_id=1): [{law_name: "건축법 제2조", ...}]
   |     → ActionKitFile(item_id=1): {object_key: "laws/chapter-1/1/v1/건축법.pdf"}
   |  3) 카테고리별 그룹핑:
   |     phase "입지 검토": [item 1, 3]
   |     phase "영업 인허가": [item 5, 8]
   |     phase "세무 설정": [item 22, 25]
   |     phase "인사·노무": [item 30, 35]
   |     phase "정책자금 신청": [item 40, 42]
   v
   MatchedActionKit 리스트 (구조화된 팩트)

Step 2: LLM 맞춤화 (지능 레이어) ← 핵심 변경
─────────────────────────────────────────────
[LLMPersonalizer.personalize()]
   |
   |  입력 1: ActionKit 구조화 데이터 (팩트)
   |    - highlights 원문, 법령명/요약, 파일 경로
   |
   |  입력 2: GenerationPayload 전체 (사용자 상황)
   |    - startup_type="신규" → 사업자등록 신규 신청 강조
   |    - open_timeline="3개월" → phase 병행 판단, 일정 타이트
   |    - budget_range="3000만" → 소규모 인허가, 정책자금 우선
   |    - experience_level="BEGINNER" → 체크리스트 세분화, 용어 설명 추가
   |
   |  LLM 맞춤화 7가지:
   |    1. checklist: 우선순위 재배열 + 불필요 항목 필터 + 초보자용 보충
   |    2. legal_basis: 카페 업종에 특히 중요한 조항 강조
   |    3. documents: 제출 순서 + 준비 가이드 (초보자 눈높이)
   |    4. phases: 3개월 일정 → 병행 가능 phase 묶음 처리
   |    5. objective: "서울 강남구 카페 신규 창업" 맞춤 목표
   |    6. risk_notes: "3000만 예산 + 강남 임대료" 위험요소
   |    7. estimated_days: 3개월 기준 현실적 소요일
   |
   |  규칙: 법령명("건축법 제2조"), 파일경로 수정 금지
   v
   개인화된 StepDetail 리스트

Step 3: DB 저장
─────────────────────────────────────────────
[RoadmapRepository.create_steps_with_details()]
   |  RoadmapStepAction(
   |    action_type="LEGAL_BASIS",
   |    title="건축법 제2조",
   |    metadata_json={
   |      ...,
   |      "actionkit_item_id": 1,
   |      "actionkit_domain": "laws",
   |      "actionkit_category": "chapter-1",
   |      "mapping_source": "actionkit_direct"
   |    }
   |  )
   v
[DB: roadmap + steps + details + actions]
```

---

## 4. DB 스키마 관련

### 4.1 기존 스키마 (변경 없음)

본 계획은 DB 마이그레이션 없이 진행한다. `RoadmapStepAction.metadata_json` (JSON 필드)의 내용만 확장한다.

**관련 테이블:**

```sql
-- 로드맵 체계
roadmap                  -- 로드맵 메인 (team_id, business_type, location)
roadmapstep              -- 단계 (roadmap_id, step_order, title, status)
roadmap_step_details     -- 상세 (roadmap_step_id, phase, objective, estimated_days)
roadmap_step_actions     -- 액션 (roadmap_step_id, action_type, title, metadata_json)
roadmap_generation_jobs  -- 비동기 잡 (status, progress, stage)

-- ActionKit 체계
actionkit_categories     -- 카테고리 (domain, slug, title)
actionkit_items          -- 아이템 (category_id, name, summary, tag)
actionkit_item_highlights -- 핵심 포인트 (item_id, content)
actionkit_related_laws   -- 관련 법령 (item_id, law_name, law_summary)
actionkit_files          -- 파일 (item_id, object_key, original_filename)
```

### 4.2 metadata_json 확장 스키마

**action_type = "LEGAL_BASIS":**
```json
{
  "title": "식품위생법 제37조",
  "snippet": "영업허가를 받으려는 자는 시장·군수·구청장에게...",
  "source_url": null,
  "actionkit_item_id": 5,
  "actionkit_domain": "laws",
  "actionkit_category": "chapter-2",
  "mapping_source": "actionkit_direct"
}
```

**action_type = "DOCUMENT":**
```json
{
  "name": "영업허가 신청서 양식",
  "type": "FORM",
  "source_url": null,
  "download_url": null,
  "file_url": "/uploads/actionkit/laws/chapter-2/5/v1/식품위생법_시행규칙.pdf",
  "actionkit_item_id": 5,
  "actionkit_file_id": 12,
  "mapping_source": "actionkit_direct"
}
```

**action_type = "CHECKLIST":**
```json
{
  "actionkit_item_id": 5,
  "actionkit_highlight_id": 18,
  "mapping_source": "actionkit_direct"
}
```

### 4.3 벡터 DB 현황 (law_vectors 컬렉션)

```
총 벡터: 314개 (+ 샘플 3건 재적재 시 약 +24개 = ~338개)
  - ActionKit laws: 168벡터 (21 아이템)
  - ActionKit kits: 146벡터 (25 아이템)
  - 기존 법령 샘플: 0벡터 → Phase 1에서 재적재 예정

임베딩 모델: text-embedding-3-small (1536차원)
청킹: chunk_size=600, overlap=100
```

---

## 5. ActionKit 데이터 구조 참조

### 5.1 LAW_DATA 구조 (21개 아이템)

```python
LAW_DATA = {
    "1": {
        "title": "입지 적법성",
        "items": [
            {
                "name": "건축법 제2조 (용도 분류)",
                "summary": "건축물 용도 분류 체계...",
                "path": "actionkits/files/laws/chapter-1/건축법.pdf",
                "highlights": ["건축물 용도 확인", "..."],
            },
            # ... 5개 아이템
        ]
    },
    # chapter 2~6
}
```

**챕터별 분포:**
| 챕터 | 제목 | 아이템 수 |
|------|------|-----------|
| chapter-1 | 입지 적법성 | 5 |
| chapter-2 | 영업 성립 요건 | 3 |
| chapter-3 | 안전소방 요건 | 3 |
| chapter-4 | 영업 중 준수의무 | 3 |
| chapter-5 | 위반 시 대응 절차 | 1 |
| chapter-6 | 행정처분 및 구제 | 6 |

### 5.2 ACTION_KIT_DATA 구조 (25개 아이템)

```python
ACTION_KIT_DATA = {
    "legal": {
        "title": "법률 키트",
        "items": [
            {
                "name": "건축법 제2조 기반 검토 키트",
                "summary": "...",
                "tag": "[용도 확인]",
                "relatedLaws": [
                    {"name": "건축법 제2조", "summary": "..."}
                ],
                "path": "actionkits/files/kits/legal/건축법.pdf",
            },
            # ... 11개 아이템
        ]
    },
    "tax": { ... },   # 3개 아이템
    "hr": { ... },    # 8개 아이템
    "grant": { ... }, # 3개 아이템
}
```

**카테고리별 분포:**
| 카테고리 | 제목 | 아이템 수 | 특징 |
|----------|------|-----------|------|
| legal | 법률 키트 | 11 | relatedLaws 풍부 |
| tax | 세무 키트 | 3 | 세금 신고/납부 |
| hr | 인사 키트 | 8 | HWP 6개 포함 |
| grant | 공고문 키트 | 3 | 정책자금 |

---

## 6. 선행 태스크 참조

| 문서 | 경로 | 관계 |
|------|------|------|
| RAG 업그레이드 계획서 | `dev/active/rag-upgrade/rag-upgrade-plan.md` | Step 1~5 완료, P-1~P-5 본 계획에서 해결 |
| RAG 업그레이드 태스크 | `dev/active/rag-upgrade/rag-upgrade-tasks.md` | 28/28 완료, 후속 작업 P-1~P-5 본 계획으로 이관 |
| RAG 업그레이드 현황 | `dev/active/rag-upgrade/rag-upgrade-status.md` | 이슈 A/B/C 분석, 다음 세션 권장 순서 |
| RAG 업그레이드 컨텍스트 | `dev/active/rag-upgrade/rag-upgrade-context.md` | 결정 1~7, 메타데이터 스키마, 골든 데이터셋 설계 |
| 최종 평가 리포트 | `app-backend/tests/eval/results/EVALUATION_REPORT.md` | baseline 확정, 미달 메트릭 분석 |

---

## 7. 환경 의존성

### 실행 환경

| 항목 | 요구사항 | 비고 |
|------|---------|------|
| Python | >= 3.11 | pyproject.toml 확인 |
| Docker (PostgreSQL + pgvector) | 필수 | 벡터 DB + 관계형 DB |
| OPENAI_API_KEY | 필수 | 임베딩 + LLM |
| DATABASE_URL | 필수 | asyncpg + sync 양쪽 |

### 패키지 의존성

| 패키지 | 상태 | 용도 |
|--------|------|------|
| langchain_openai | 설치됨 | OpenAIEmbeddings, ChatOpenAI |
| langchain_postgres | 설치됨 | PGVector |
| langchain_text_splitters | 설치됨 | RecursiveCharacterTextSplitter |
| langchain_core | 설치됨 | Document, ChatPromptTemplate |
| pdfplumber | 설치됨 | PDF 파싱 |
| numpy | 확인 필요 | 코사인 유사도 계산 (SemanticRouter) |

**추가 의존성:** numpy (코사인 유사도 계산용, 미설치 시 추가)

---

## 8. 변경 영향 분석

### API 엔드포인트 영향

| 엔드포인트 | 영향 | 설명 |
|-----------|------|------|
| `POST /api/v1/rag/chat` | 내부 개선 | 라우팅 + 프롬프트 변경, API 계약 불변 |
| `POST /api/v1/rag/query` | 내부 개선 | 프롬프트 + format_docs 변경, API 계약 불변 |
| `POST /api/v1/roadmaps/jobs` | 내부 개선 | 생성 로직 변경, API 계약 불변 |
| `POST /api/v1/roadmaps/jobs/validate` | 변경 없음 | 검증 로직 불변 |
| `GET /api/v1/roadmaps/jobs/{id}` | 변경 없음 | 조회만 |
| `GET /api/v1/roadmaps/jobs/{id}/result` | 변경 없음 | 조회만 |

**핵심:** 모든 변경은 내부 구현에 한정. API 계약(request/response 스키마)은 불변. 프론트엔드 변경 불필요.

### 프론트엔드 영향

- 변경 없음: metadata_json 확장은 프론트엔드에서 표시하지 않는 한 영향 없음
- 후속 작업으로 ActionKit 원문 링크 표시 UI 추가 가능 (본 계획 범위 밖)
