# Roadmap Quality Improvement - Context

> Last Updated: 2026-02-25

## Key Files

### Backend - 로드맵 생성 파이프라인

| 파일 | 역할 | 수정 필요 |
|---|---|---|
| `app-backend/app/features/roadmaps/application/roadmap_generation_service.py` | 로드맵 생성 메인 서비스 (validate, process_job, fallback) | Phase 1 (P1-1, P1-3) |
| `app-backend/app/features/roadmaps/application/actionkit_matcher.py` | 벡터 검색 → ActionKit 매칭 (fact layer) | Phase 1 (P1-2), Phase 2 (P2-3, P2-5) |
| `app-backend/app/features/roadmaps/application/llm_personalizer.py` | LLM 개인화 (intelligence layer) | Phase 1 (P1-1) |
| `app-backend/app/features/roadmaps/application/deps.py` | DI 싱글톤 (ActionKitMatcher, LLMPersonalizer) | 변경 없음 |
| `app-backend/app/features/rag/application/rag_service.py` | RAG 벡터 검색 서비스 | Phase 2 (P2-2) |
| `app-backend/app/features/rag/application/deps.py` | RAG DI 싱글톤 | 변경 없음 |
| `app-backend/app/repositories/roadmap_repository.py` | 로드맵 DB CRUD | Phase 1 (P1-3) |

### Backend - 테스트

| 파일 | 역할 |
|---|---|
| `app-backend/tests/services/test_roadmap_generation_service.py` | 생성 서비스 단위 테스트 |
| `app-backend/tests/api/test_roadmap_jobs_validate.py` | validate API 테스트 |
| `app-backend/tests/eval/test_tier3_full.py` | Tier 3 전체 평가 (121 passed, 5 skipped) |

### Frontend - 로드맵 UI

| 파일 | 역할 | 수정 필요 |
|---|---|---|
| `app-frontend/src/features/roadmap/components/RoadmapChatIntake.tsx` | 로드맵 생성 입력 (채팅 인터페이스) | Phase 3 (P3-1) |
| `app-frontend/src/features/roadmap/components/RoadmapExecutionView.tsx` | 로드맵 실행 뷰 | Phase 3 (P3-2) |
| `app-frontend/src/features/roadmap/components/TimelinePhaseCard.tsx` | 단계별 타임라인 카드 | Phase 3 (P3-2) |

---

## Key Decisions

### D1. 비법률 단계 처리 전략
- **결정**: 단계 성격 분류(법률필수/비법률)를 도입하여 비법률 단계에서는 LEGAL_BASIS에 "근거 보강 필요" 대신 적합한 가이드 텍스트 생성
- **근거**: 마케팅/인테리어/메뉴개발 단계에는 법적 근거가 구조적으로 없으므로, RAG 실패가 아닌 정상 케이스로 취급
- **영향**: `roadmap_generation_service.py`의 `_fallback_detail()`, `llm_personalizer.py`의 `_fallback_from_facts()`

### D2. ActionKit 매칭 쿼리 전략
- **현재**: `"{business_type} {location} 창업 인허가"` 고정 쿼리 (actionkit_matcher.py:82)
- **개선 방향**: phase별 키워드 포함 쿼리 생성
- **영향**: `actionkit_matcher.py`의 `match()` 메서드

### D3. 업종 확장 시 법률 문서 적재 방식
- **결정**: 기존 `file_pipeline` 활용하여 벡터DB에 추가 적재
- **근거**: 기존 파이프라인이 청킹(chunk_size=600, overlap=100) + 임베딩 적재를 처리
- **영향**: `rag_service.py`, 벡터DB `law_vectors` 컬렉션

### D4. generation_mode 분기 기준
- **현재**: ActionKit 매칭 3건 이상 → `ACTIONKIT_RAG`, 미만 → `RAG` (legacy LLM 생성)
- **상수**: `_MIN_ACTIONKIT_MATCHES = 3` (roadmap_generation_service.py:21)
- **Phase 2 고려**: 새 업종 법률 문서 적재 후에도 최소 매칭 기준 유지

### D5. validate 프롬프트 개선 방향
- **현재**: RAG 기반 정규화 → fallback은 카페→휴게음식점만 매핑
- **개선**: 지원 업종 화이트리스트를 프롬프트에 포함
- **영향**: `validate_generation_input()` 프롬프트, `_fallback_validation()` 매핑

---

## Dependencies

### 기술 의존성

```
Phase 1 (독립 작업 가능)
├── P1-1: 비법률 단계 fallback 로직 ← 독립
├── P1-2: ActionKit 쿼리 개선 ← 독립
├── P1-3: 품질 메타데이터 태깅 ← 독립
└── P1-4: 품질 평가 스크립트 ← 독립

Phase 2 (순차 의존)
├── P2-1: 업종 선정 + 법률 매핑 ← 독립
├── P2-2: 법률 문서 수집 + 적재 ← P2-1
├── P2-3: 카테고리→페이즈 매핑 ← P2-1
├── P2-4: Validate 프롬프트 업데이트 ← P2-2
└── P2-5: 업종별 쿼리 전략 ← P2-2, P2-3

Phase 3 (Phase 2와 일부 병렬)
├── P3-1: 프론트엔드 업종 가이드 ← P2-1 (업종 목록 확정 후)
├── P3-2: fallback UX 개선 ← P1-1 (비법률 분류 후)
├── P3-3: 품질 대시보드 ← P1-3, P1-4
└── P3-4: 골든 데이터셋 확장 ← P2-2
```

### 외부 의존성

| 의존성 | 상태 | 비고 |
|---|---|---|
| 국가법령정보센터 API/PDF | 이용 가능 | 공공데이터, CC BY 확인 필요 |
| OpenAI API (GPT-4) | 운영 중 | 비용 모니터링 필요 |
| PostgreSQL + pgvector | 운영 중 | 벡터 컬렉션 `law_vectors` |
| LangChain | v0.1.0+ | 벡터 스토어 래퍼 |

---

## Current Data Analysis (2026-02-25)

### 벡터DB 문서 분포

```
전체: 47개 고유 문서 (laws 22 + kits 25)

laws (22건):
  chapter-1 (입지/건축법): 5건
  chapter-2 (영업 인허가 - 식품위생법): 3건  ← 핵심
  chapter-3 (소방/다중이용업소): 3건
  chapter-4 (영업 준수사항): 3건
  chapter-5 (행정조사): 1건
  chapter-6 (행정구제): 8건 (가장 많음 - 과다?)

kits (25건):
  legal: 11건
  tax: 3건
  hr: 8건
  grant: 3건
```

### 로드맵 품질 현황

```
전체 로드맵: 5개 (휴게음식점 4, 일반음식점 1)
전체 LEGAL_BASIS 액션: 75건
"근거 보강 필요" 발생: 16건 (21%)

업종별:
  휴게음식점: 14/68건 fallback (20%)
  일반음식점: 2/7건 fallback (29%)

source_url 보유율:
  LEGAL_BASIS: 휴게음식점 79%, 일반음식점 71%
  DOCUMENT: 휴게음식점 92%

generation_mode: 전체 RAG (37건) - ACTIONKIT_RAG는 아직 없음
```

### Fallback 발생 단계 패턴

비법률 단계에서 집중 발생:
- 마케팅/홍보
- 인테리어/시설
- 메뉴개발
- 오픈준비

법률 단계에서는 거의 미발생 (벡터DB에 관련 문서 존재)

---

## Architecture Notes

### 로드맵 생성 플로우

```
사용자 입력 → validate_generation_input() → process_job()
                                                ↓
                                    ActionKitMatcher.match()
                                         ↓           ↓
                              매칭 ≥ 3건        매칭 < 3건
                                 ↓                  ↓
                          LLMPersonalizer     Legacy RAG 생성
                                 ↓                  ↓
                          ACTIONKIT_RAG          RAG mode
                                 ↓                  ↓
                               DB 저장 ←──────────┘
```

### DI 패턴

```python
# 싱글톤 패턴 (@lru_cache)
get_rag_service()          → RagService
get_actionkit_matcher()    → ActionKitMatcher(rag_service)
get_llm_personalizer()     → LLMPersonalizer(ChatOpenAI)
```

### 주요 상수/설정

| 상수 | 값 | 위치 |
|---|---|---|
| `_MIN_ACTIONKIT_MATCHES` | 3 | `roadmap_generation_service.py:21` |
| `chunk_size` | 600 | VectorStoreService |
| `chunk_overlap` | 100 | VectorStoreService |
| 벡터 컬렉션 | `law_vectors` | RagService |
| Semaphore (병렬 생성) | 3 | `roadmap_generation_service.py:316` |
