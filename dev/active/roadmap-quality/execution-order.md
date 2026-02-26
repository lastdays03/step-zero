# 실행 순서 가이드 - 로드맵 품질 개선 + 법률 데이터 수집

> Last Updated: 2026-02-26 (세션 4 — ActionKitFile 자동 생성, Wave 2 수집 완료 확인)
> 이 문서는 두 트랙의 최적 병렬 실행 순서를 정리한 빠른 참조 문서이다.

---

## 환경 현황 (2026-02-26 세션 2 완료 후)

### 인프라 상태

| 항목 | 상태 | 비고 |
|---|---|---|
| PostgreSQL (stepzero-db) | **Running** | `localhost:5432`, healthy |
| Redis (stepzero-redis) | **Running** | `localhost:6379`, healthy |
| Worker (stepzero-worker) | **Running** | arq 기반 백그라운드 워커 |
| Python venv | **Ready** | `.venv/bin/python` (cpython-3.11.14) |
| httpx | **Ready** | v0.28.1 (`pyproject.toml` dev deps에 포함) |

### API 키 / 인증

| 항목 | 상태 | 위치 |
|---|---|---|
| OpenAI API Key | **설정 완료** | `.env.local` |
| 국가법령정보센터 OC | **설정 완료** | `.env.local` (`LAW_API_OC=lastdays03`) |
| law.go.kr API 테스트 | **성공** | 식품위생법 검색 → 6법령 수집 완료 |

### DB 데이터 현황 (세션 4 업데이트)

| 항목 | 수치 |
|---|---|
| 로드맵 | 7건 (휴게음식점 6, 일반음식점 1) |
| 벡터 총 수 | **371건** (기존 329 + Wave 1 법률 42) |
| 고유 문서 수 | **53건** (기존 47 + 큐레이션 법률 6) |
| Alembic head | `ea3b65f32267` (품질 메타 컬럼 추가) |
| ActionKitItem | **52건** (기존 시드 46 + Wave 1 보강 6) |
| ActionKitFile | **52건** (기존 시드 46 + Wave 1 보강 **6건 신규**) |
| 지원 업종 | 휴게음식점, 일반음식점 + **식품제조가공업, 통신판매업** (Wave 1) |
| Wave 2 수집 | 미용업(공중위생관리법×3) + 일반소매업(유통산업발전법×3) — 큐레이션/적재 대기 |

### DB 스키마 - `roadmap_step_details` 컬럼 (업데이트됨)

```
id, roadmap_step_id, phase, objective, estimated_days,
risk_notes(json), generation_mode, created_at, updated_at,
source_count(int), has_fallback(bool), mapping_source(str)  ← P0-2에서 추가 완료
```

⚠️ `alembic upgrade head` 실제 DB 적용은 아직 필요 (Docker DB 실행 후)

### 원본 파일 위치 (업데이트됨)

| 데이터 | 경로 | 파일 수 |
|---|---|---|
| 법률 원본 (PDF) | `uploads/actionkit/laws/chapter-1~6/` | 21건 |
| 킷 원본 (PDF/HWP/PPTX) | `uploads/actionkit/kits/{legal,tax,hr,grant}/` | 25건 |
| Wave 1 수집 법률 | `.temp/rag/식품제조가공업/`, `.temp/rag/통신판매업/` | **12건** (6 md + 6 meta.json) |
| Wave 1 큐레이션 | `.temp/rag/*/\*_curated.md` | **6건** |
| Wave 2 수집 법률 | `.temp/rag/미용업/`, `.temp/rag/일반소매업/` | **12건** (6 md + 6 meta.json) |
| Wave 1 ActionKitFile | `uploads/actionkit/laws/chapter-7/`, `chapter-8/` | **6건** (.md) |

### 주요 코드 경로 (업데이트됨)

```
# Backend - 로드맵 생성 (구간 2에서 개선됨)
app/features/roadmaps/application/
├── actionkit_matcher.py      # 다중 쿼리 전략 (BUSINESS_QUERY_TEMPLATES, asyncio.gather)
├── llm_personalizer.py       # 7 phase 전문 fallback 템플릿
├── roadmap_generation_service.py  # ACTIONKIT_RAG 임계값 3→1, 메타데이터 기록
└── deps.py                   # DI 싱글톤

# Backend - RAG
app/features/rag/application/
├── rag_service.py            # 벡터 스토어 + 검색
├── chat_service.py           # 하이브리드 (RAG + LLM)
└── semantic_router.py        # 임베딩 기반 분류

# Backend - 서비스 (업데이트됨)
app/services/
├── law_api_client.py         # ✅ 신규: LawApiClient (httpx, Pydantic 모델, rate limit)
├── law_fetcher.py            # LawDataSource ABC + LocalFileSource + ✅ MolegApiSource
├── law_etl.py                # LawETLProcessor (GPT-4 가이드 변환)
├── vector_store.py           # VectorStoreService (청킹 600/100)
└── actionkit_data_source.py  # ActionKit 데이터 소스

# Backend - API (업데이트됨)
app/api/v1/
├── schemas.py                # ✅ RoadmapStepDetailResponse에 메타 필드 추가
└── roadmaps/get.py           # ✅ 메타데이터 API 노출

# Backend - 모델 (업데이트됨)
app/models/roadmap.py         # ✅ source_count, has_fallback, mapping_source 추가

# Frontend - 로드맵 (업데이트됨)
app-frontend/src/features/roadmap/
├── components/
│   ├── TimelinePhaseCard.tsx  # ✅ COMPLETED 기본 축소
│   ├── TimelineStepItem.tsx   # ✅ MappingSourceBadge (법령기반/AI분석/일반안내)
│   └── ...
├── roadmap-constants.ts       # ✅ 신규: 공유 상수 (SUGGESTIONS, validate 메시지)
├── hooks/
├── types/
│   └── roadmap-utils.ts       # ✅ MappingSource 타입 추가
└── api/

# 스크립트 (업데이트됨)
scripts/
├── eval_roadmap_quality.py    # ✅ 신규: 품질 baseline 측정 (5개 지표 JSON)
├── fetch_laws.py              # ✅ 신규: 법률 수집 CLI (--wave, --list, --dry-run)
├── fetch_laws_config.py       # ✅ 신규: WAVE_CONFIG (3 Wave, 6 업종)
├── seed_rag_vectors.py        # ✅ --curated + --sync-actionkit 옵션 추가
├── eval/                      # 평가 (tier 2/4)
└── seeds/                     # 시드 데이터
```

---

## 진행 현황

### 완료된 태스크

| 태스크 | 완료일 | 비고 |
|---|---|---|
| B-P0-1: open.law.go.kr 회원가입 + OC 발급 | 2026-02-26 | OC=lastdays03 |
| B-P0-2: 환경변수 및 설정 추가 | 2026-02-26 | .env.local, .env, .env.example, config.py |
| B-P0-3: API 연결 테스트 | 2026-02-26 | curl로 식품위생법 검색 성공 |
| B-P0-4: httpx 의존성 확인 | 2026-02-26 | 이미 설치됨 (v0.28.1) |
| **P0-1: Baseline 스크립트** | **2026-02-26** | `eval_roadmap_quality.py` (5개 지표, --json/--output) |
| **P0-2: Alembic Migration** | **2026-02-26** | `ea3b65f32267` (source_count, has_fallback, mapping_source) |
| **P1-QW: FE Quick Win 3건** | **2026-02-26** | TimelinePhaseCard 축소, SUGGESTIONS 통합, validate 통합 |
| **B-P1-1: API 클라이언트** | **2026-02-26** | `law_api_client.py` (24 tests), API 버그 2건 수정 |
| **B-P1-3~4: WAVE_CONFIG + CLI** | **2026-02-26** | `fetch_laws.py` + `fetch_laws_config.py` + MolegApiSource |
| **P1-1: fallback 개선** | **2026-02-26** | 7 phase 전문 템플릿, 메타데이터 자동 기록 |
| **P1-2: 쿼리 개선** | **2026-02-26** | 다중 쿼리 + asyncio.gather (10개 업종 매핑) |
| **P1-5: ACTIONKIT_RAG 해소** | **2026-02-26** | 임계값 3→1, 점수 필터링 0.2 추가 |
| **P3-2: Fallback UX** | **2026-02-26** | BE 스키마 노출 + FE 배지 3종 (법령기반/AI분석/일반안내) |
| **B-P2-1: Wave 1 수집** | **2026-02-26** | 6법령 (식품위생법×3 + 전자상거래법×3), API 버그 2건 수정 |
| **B-P2-2: Wave 1 큐레이션** | **2026-02-26** | 6개 _curated.md (업종별 핵심 조문 선별) |
| **B-P2-3: Wave 1 벡터 적재** | **2026-02-26** | 42청크 적재, 검색 테스트 통과 |
| **P2A: Wave 1 업종 확장** | **2026-02-26** | 품질 게이트 통과 (155 tests), SOFT FAIL 1건 (통신판매업 2매치) |
| **B-P2-4: ActionKitItem 보강** | **2026-02-26** | seed_rag_vectors.py에 `_ensure_actionkit_items()` 추가, Wave 1 업종 +6건 (총 52건) |
| **ActionKitFile 자동 생성** | **2026-02-26** | `_ensure_actionkit_items()`에 파일 복사 + ActionKitFile 레코드 생성 추가. 기존 Item 파일 보강 (멱등) |
| **B-P3-1: Wave 2 수집** | **2026-02-26** | 미용업(공중위생관리법×3) + 일반소매업(유통산업발전법×3) — 총 6법령 수집 완료 |

### 다음 착수 대상

| 태스크 | 트랙 | 내용 | 명령어/비고 |
|---|---|---|---|
| **law_api_client 파싱 버그 수정** | B-BE | `_build_article_content()`에서 list 타입 item_text.strip() 에러 | Wave 3 수집 차단 중 |
| Wave 2 큐레이션 | B-BE | 미용업/일반소매업 법률 핵심 조문 추출 | _curated.md 생성 |
| Wave 2 벡터 적재 + ActionKitItem + File | B-BE | 큐레이션 → 벡터 + Item + File 자동 생성 | `python -m scripts.seed_rag_vectors --curated` |
| Wave 3 수집 | B-BE | 학원업 + 숙박업 법률 수집 | `python -m scripts.fetch_laws --wave 3` (버그 수정 후) |
| Wave 3 큐레이션 + 적재 | B-BE | Wave 2와 동일 파이프라인 | _curated.md → --curated |
| 서버 재시작 후 매칭 재테스트 | A+B | 통신판매업 ActionKitMatcher 재검증 | 서버 캐시 초기화 후 확인 |

### 구간 4 (Wave 2/3과 병렬 가능)

| 태스크 | 의존 | 내용 |
|---|---|---|
| P3-1: 업종 선택 가이드 FE | P2A ✅ | 2-tier SUGGESTIONS |
| P3-3: 품질 대시보드 | P0-2 ✅ | `/ops/roadmap-quality` |
| P3-4: 골든 데이터셋 확장 | Wave 적재 완료 | 업종당 3건+ |

### 알려진 이슈

| 이슈 | 심각도 | 비고 |
|---|---|---|
| ~~ActionKitItem 누락으로 매칭 0건~~ | **해결됨** | `_ensure_actionkit_items()` 추가, `--sync-actionkit` 옵션으로 기존 보강 가능 |
| ~~ActionKitFile 미생성으로 다운로드 불가~~ | **해결됨** | `_ensure_actionkit_items()`에서 ActionKitFile 자동 생성, 기존 Item 파일 보강 |
| **law_api_client.py 파싱 버그** | **높음** | `_build_article_content()`에서 list 타입 item_text.strip() → AttributeError. Wave 3 수집 차단 |
| 통신판매업 로드맵: mapping_source=None | 중간 | ActionKitItem은 DB에 있으나 매칭이 RAG fallback으로 동작. 서버 캐시 문제 가능성 |
| `alembic upgrade head` 미실행 | 중간 | Docker DB 실행 후 적용 필요 |
| 행정규칙 수집 미완료 | 낮음 | 식품제조가공업/통신판매업 행정규칙 검색 결과 없음. 키워드 조정 필요 |

---

## 병렬 트랙 구조

| 트랙 | 목표 | 상세 계획 |
|---|---|---|
| **Track A: 로드맵 품질 개선** | 기존 음식점 fallback 제거 + ACTIONKIT_RAG 활성화 | `roadmap-quality-plan-v2.md` |
| **Track B: 법률 데이터 수집** | 6개 업종 법률 문서 수집 + 벡터 적재 | `../law-data-collection/law-data-collection-plan.md` |

---

## 최적 진행 순서

```
시간 -->

[Track A: 로드맵 품질 개선]              [Track B: 법률 데이터 수집]
================================        ================================

구간 1 (2~3일) - 독립 병렬, 즉시 시작
--------------------------------        --------------------------------
P0-1: Baseline 스크립트                  API 등록 + 환경설정 (P0-1~4)
P0-2: 품질 메타 Migration               수집 스크립트 개발
P1-QW: FE Quick Win 3건                 (law_api_client.py, fetch_laws.py)
        |                                       |
        v                                       v

구간 2 (3~5일) - 핵심 개선 + 데이터 수집 병렬
--------------------------------        --------------------------------
P1-1: 비법률 fallback 개선               Wave 1 법률 수집
P1-2: ActionKit 쿼리 개선               (식품제조가공업 + 통신판매업)
P1-5: ACTIONKIT_RAG 해소                 수집 + 큐레이션 + 검증
P3-2: Fallback UX 개선                          |
        |                                       |
        v                                       v
============= 여기서 합류 ============================
        |
        v

구간 3 (5일/Wave) - 업종 확장 순차
--------------------------------
P2A: Wave 1 업종 확장
     벡터 적재 + 매핑 + Validate
        |
        v (품질 게이트 통과)
Wave 2 수집 --> P2B (미용업 + 소매업) --> 게이트
        |
        v
Wave 3 수집 --> P2C (학원업 + 숙박업) --> 게이트
```

---

## 구간별 상세

### 구간 1: 독립 병렬 (2~3일)

모든 작업이 상호 의존성 없으며, 즉시 시작 가능하다.

**Track A**
| 태스크 | 내용 | 크기 |
|---|---|---|
| P0-1 | 품질 평가 스크립트 + Baseline 측정 | S |
| P0-2 | 품질 메타데이터 태깅 + DB Migration (Alembic) | S |
| P1-QW | FE Quick Win 3건 (TimelinePhaseCard, SUGGESTIONS 통합, validate 에러) | XS |

**Track B**
| 태스크 | 내용 | 크기 |
|---|---|---|
| B-P0 | open.law.go.kr 회원가입, OC 발급, 환경변수 설정, httpx 추가 | XS |
| B-P1-1 | `law_api_client.py` API 클라이언트 래퍼 | M |
| B-P1-2~4 | `fetch_laws.py` CLI 스크립트 + 유닛 테스트 + 설정 | L |
| B-P1-5 | `MolegApiSource` 구현체 | M |

---

### 구간 2: 핵심 개선 + 데이터 수집 병렬 (3~5일)

Track A는 **기존 음식점 데이터만으로 충분**하며, 새 법률 데이터가 불필요하다.
Track B는 수집 스크립트 완성 후 Wave 1 실행 단계이다.

**Track A**
| 태스크 | 의존 | 내용 |
|---|---|---|
| P1-1 | P0-2 | 비법률 단계 fallback 로직 개선 (`_fallback_detail()` 외 3곳) |
| P1-2 | P0-1 | ActionKit 쿼리 개선 (다중 쿼리 전략, `asyncio.gather`) |
| P1-5 | P1-2 | ACTIONKIT_RAG 미활성 원인 분석 + 해소 |
| P3-2 | P0-2, P1-1 | Fallback UX 개선 (FE, P1-1과 동시 진행 가능) |

**Track B**
| 태스크 | 내용 |
|---|---|
| B-P2-1 | Wave 1 법률 수집 실행 (`fetch_laws --wave 1`) |
| B-P2-2 | 관련 조문 큐레이션 (LLM 1차 + 수동 2차) -- 핵심 병목 |
| B-P2-3 | Wave 1 벡터 적재 + ActionKitItem 자동 생성 (`seed_rag_vectors --curated`) |

---

### 구간 3: 합류 - 업종 확장 (Wave당 5일)

Track B의 수집 결과물이 Track A의 업종 확장에 직접 입력된다.

**Wave 파이프라인 (v3 — ActionKitFile 포함)**
```
법률 수집 → 큐레이션(_curated.md) → seed_rag_vectors --curated
  └→ 벡터 적재 (law_vectors 컬렉션)
  └→ ActionKitItem/Category/Highlight 자동 생성 (멱등)
  └→ ActionKitFile 자동 생성 (curated .md → uploads/actionkit/ 복사)
  └→ 라이브러리 UI에서 다운로드 가능

보강 전용: seed_rag_vectors --sync-actionkit (벡터 적재 없이 Item+File만 생성/보강)
```

**Wave 1 (식품제조가공업 + 통신판매업)**
| 태스크 | 내용 |
|---|---|
| P2A-2 | Wave 1 벡터 적재 + ActionKitItem 자동 생성 (수집된 법률 문서 필요) |
| P2A-3 | 매핑/Validate/쿼리 확장 |
| 게이트 | fallback < 10%, ActionKit >= 3건, 기존 hit_rate >= 0.85, 교차 오염 통과 |

**Wave 2 (미용업 + 일반소매업)** -- Wave 1 게이트 통과 후
| 태스크 | 내용 |
|---|---|
| B-P3-1~3 | Wave 2 수집/큐레이션/적재 |
| P2B-1~3 | Wave 2 매핑/확장/검증 |

**Wave 3 (학원업 + 숙박업)** -- Wave 2 게이트 통과 후
| 태스크 | 내용 |
|---|---|
| B-P4-1~3 | Wave 3 수집/큐레이션/적재 |
| P2C-1~3 | Wave 3 매핑/확장/검증 |

---

### 구간 4: Phase 3 Ops (Phase 2A 완료 후 병렬 가능)

| 태스크 | 의존 | 내용 |
|---|---|---|
| P3-1 | P2A-1 (업종 목록 확정) | 업종 선택 가이드 FE (2-tier SUGGESTIONS) |
| P3-3 | P0-2 | 로드맵 품질 대시보드 (`/ops/roadmap-quality`) |
| P3-4 | P2A-2 (법률 적재) | 골든 데이터셋 확장 (업종당 3건+) |

---

## 데이터 수집 없이 먼저 할 수 있는 것

기존 DB와 코드만으로 즉시 착수 가능한 작업 목록이다.

| 태스크 | 성격 | 이유 |
|---|---|---|
| P0-1: Baseline 측정 | 백엔드 스크립트 | 기존 DB만 필요 |
| P0-2: 품질 메타 Migration | DB 스키마 | Alembic 컬럼 추가만 |
| P1-1: 비법률 fallback 개선 | 백엔드 로직 | 코드 분기 변경, 기존 데이터로 검증 |
| P1-2: ActionKit 쿼리 개선 | 백엔드 로직 | 기존 음식점 벡터로 검증 |
| P1-5: ACTIONKIT_RAG 해소 | 백엔드 로직 | 기존 데이터로 검증 |
| P1-QW: FE Quick Win 3건 | 프론트엔드 | 백엔드 의존 없음 |
| P3-2: Fallback UX 개선 | 프론트엔드 | P1-1 분류 기준만 필요 |

---

## 데이터 수집이 선행되어야 하는 것

Track B 결과물(수집된 법률 문서 + 벡터 적재)이 반드시 있어야 하는 작업이다.

| 태스크 | 필요한 데이터 |
|---|---|
| P2A-2, P2B-2, P2C-2: 업종 확장 벡터 적재 | 해당 Wave의 법률 문서 수집 완료 |
| P2A-3, P2B-3, P2C-3: 매핑/Validate 확장 | 해당 Wave의 벡터 적재 완료 |
| P3-1: 업종 선택 가이드 FE | 업종 목록 확정 (P2A-1) |
| P3-4: 골든 데이터셋 확장 | 법률 문서 적재 완료 |

---

## 일정 비교

| 방식 | 예상 기간 | 비고 |
|---|---|---|
| 순차 진행 (A 완료 후 B) | ~25일 | Track A Phase 1 (4일) + Track B 전체 (12~17일) + 업종 확장 (15일) |
| **병렬 진행 (권장)** | **~18일** | 구간 1~2에서 약 7일 단축 |

```
순차:  [--- Track A Phase 0~1 (4일) ---][--- Track B (14일) ---][--- 업종 확장 (15일) ---] = ~25일+

병렬:  [- 구간1 (3일) -][- 구간2 (5일) -][- 구간3: Wave1 (5일) -][- Wave2 (5일) -][- Wave3 (5일) -]
       A: P0 + QW        A: P1 전체        합류: P2A                 P2B               P2C
       B: P0 + P1        B: Wave1 수집      B결과 --> A에 입력
                                                                    = ~18일 (크리티컬 패스)
```

---

## 관련 문서

| 문서 | 경로 |
|---|---|
| 로드맵 품질 개선 상세 계획 | `dev/active/roadmap-quality/roadmap-quality-plan-v2.md` |
| 로드맵 품질 태스크 체크리스트 | `dev/active/roadmap-quality/roadmap-quality-tasks.md` |
| 법률 데이터 수집 상세 계획 | `dev/active/law-data-collection/law-data-collection-plan.md` |
| 법률 데이터 수집 태스크 체크리스트 | `dev/active/law-data-collection/law-data-collection-tasks.md` |
