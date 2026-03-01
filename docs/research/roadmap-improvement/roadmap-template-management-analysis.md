# 로드맵 템플릿 관리 시스템 — 상세 분석 보고서

> 작성일: 2026-03-01
> 목적: 유형별(업종/지역) 공통 로드맵을 템플릿화하여 LLM 반복 생성을 방지하고, 운영자가 품질 검수/수정/관리할 수 있는 시스템의 설계를 위한 현황 분석 및 요구사항 정의
> 방법: 로드맵 생성 파이프라인, 관리자 콘솔, 데이터 모델, 시드 데이터 총 4개 영역 병렬 코드 분석

---

## 1. 현재 로드맵 생성 파이프라인 분석

### 1.1 전체 흐름도

```
사용자 입력 (6필드)
  ├── business_type: 업종 (ex: 휴게음식점)
  ├── location: 지역 (ex: 서울시 강남구)
  ├── startup_type: 창업형태 (신규/양수양도/프랜차이즈)
  ├── open_timeline: 오픈 목표 시기
  ├── budget_range: 예산 범위
  └── description: 추가 설명

    ↓ POST /api/v1/roadmaps/jobs

Step 1: ActionKitMatcher.match()
  ├── 업종별 멀티 쿼리 생성 (BUSINESS_QUERY_TEMPLATES)
  ├── PGVector 벡터 유사도 검색 (k_per_query=6)
  ├── 결과 병합 + 중복 제거 + 점수 매핑
  └── 최소 점수 필터 (_MIN_RELEVANCE_SCORE=0.2)
    ↓ matched_items: list[MatchedActionKit]

Step 2: 분기 결정
  ├── matched >= 1 → ACTIONKIT_RAG 모드
  │   └── LLMPersonalizer.personalize() → 개인화된 단계 생성
  └── matched < 1 → RAG 폴백 모드
      └── LLM 직접 생성 (MasterRoadmap → StepDetail)
    ↓ steps_payload: list[dict]

Step 3: RoadmapRepository.create_steps_with_details()
  └── DB 저장 (Roadmap → Step → StepDetail → StepAction)
```

### 1.2 생성 결과 구조 (DB 스키마)

```
Roadmap (UUID)
  ├── team_id, business_type, location, startup_type, open_timeline, budget_range
  └── RoadmapStep[] (1:N, 보통 4-8개 단계)
        ├── step_order, title, status (PENDING/IN_PROGRESS/COMPLETED)
        ├── RoadmapStepDetail (1:1)
        │     ├── phase, objective, estimated_days, risk_notes[]
        │     ├── generation_mode: "ACTIONKIT_RAG" | "RAG"
        │     └── mapping_source: "actionkit_direct" | "rag" | "fallback"
        └── RoadmapStepAction[] (1:N)
              ├── action_type: CHECKLIST | LEGAL_BASIS | DOCUMENT
              ├── title, description, source_url
              └── metadata_json: { actionkit_item_id, mapping_source, ... }
```

### 1.3 비결정성 분석 — 동일 입력이 동일 결과를 생성하는가?

**결론: 비결정적 (Non-deterministic)**

| 단계 | 결정성 | 설명 |
|------|:------:|------|
| ActionKitMatcher | **준결정적** | 벡터 검색 점수 기반이라 거의 동일하나, 임베딩 모델 업데이트나 벡터 스토어 변경 시 달라질 수 있음 |
| LLMPersonalizer | **비결정적** | LLM(gpt-4o-mini) 출력이 매번 다름 — 체크리스트 순서, 문구, estimated_days 등 변동 |
| RAG 폴백 | **비결정적** | LLM 직접 생성이므로 완전히 다른 결과 가능 |

**핵심 관찰**: 동일 업종+지역 조합으로 요청하면 ActionKit 매칭 결과(법령, 파일, 하이라이트)는 거의 동일하지만, LLM이 생성하는 **체크리스트 문구, 순서, 일수, 리스크 노트, 목표 문구**가 매번 달라짐.

→ **이것이 바로 템플릿이 필요한 이유**: 공통 부분(법령, 서류, 기본 체크리스트)을 고정하고, 개인화 부분만 LLM에 위임

---

## 2. 공통 vs 개인화 — 무엇을 템플릿화할 수 있는가

### 2.1 공통 컴포넌트 (템플릿화 가능)

| 컴포넌트 | 설명 | 소스 | 템플릿 적합도 |
|----------|------|------|:----------:|
| **법적근거 (LEGAL_BASIS)** | 업종별 필수 법령 목록 | ActionKit DB → MatchedActionKit.related_laws | **★★★★★** |
| **필수서류 (DOCUMENT)** | 업종별 제출 서류 목록 | ActionKit DB → MatchedActionKit.files | **★★★★★** |
| **단계 구성 (phases)** | 업종별 필수 절차 순서 | CATEGORY_TO_PHASE 매핑 | **★★★★☆** |
| **기본 체크리스트** | 법령 기반 필수 확인 항목 | ActionKit DB → MatchedActionKit.highlights | **★★★★☆** |
| **기본 리스크 노트** | 업종별 공통 위험 사항 | LLM 생성 → 검수 후 고정 | **★★★☆☆** |

### 2.2 개인화 컴포넌트 (동적 생성 유지)

| 컴포넌트 | 설명 | 개인화 요소 | 템플릿화 불가 이유 |
|----------|------|-----------|:---------------:|
| **체크리스트 순서/필터링** | 사용자 상황에 맞는 재정렬 | startup_type, experience_level | 조합 경우의 수 과다 |
| **estimated_days** | 개인 일정 기반 산정 | open_timeline | 연속형 변수 |
| **objective** | 업종+지역 특화 목표 문구 | location, description | 자유 텍스트 |
| **추가 체크리스트** | 사용자 상황별 보충 항목 | description, additional_notes | 예측 불가 |

### 2.3 분리 전략

```
로드맵 = 템플릿(공통 골격) + 개인화(LLM 보충)

템플릿 (운영자 관리):
  ├── 단계 구성: ["입지 검토", "영업 인허가", "안전·소방", "영업 준수사항", ...]
  ├── 각 단계별:
  │     ├── 기본 체크리스트 (ActionKit highlights 기반)
  │     ├── 법적근거 목록 (ActionKit related_laws 기반)
  │     ├── 필수서류 목록 (ActionKit files 기반)
  │     └── 기본 리스크 노트
  └── 메타데이터: 업종, 적용 지역, 버전, 검수 상태

개인화 (LLM 생성):
  ├── 체크리스트 순서 조정 + 사용자 맥락 항목 보충
  ├── 사용자 일정 기반 estimated_days 산정
  ├── 지역/상황 특화 objective 문구
  └── 사용자 맥락 기반 추가 risk_notes
```

---

## 3. 현재 ActionKit 시드 데이터 — 템플릿 기반 데이터

### 3.1 업종별 매핑 현황

현재 `BUSINESS_QUERY_TEMPLATES`에 정의된 11개 업종:

| # | 업종 | 전용 키워드 | ActionKit 매칭 예상 |
|---|------|-----------|:------------------:|
| 1 | 휴게음식점 | 위생 허가, 식품 안전, 영업 신고 | 21법령 + 25키트 (전체) |
| 2 | 카페 | 위생 허가, 식품 안전, 영업 신고 | 휴게음식점과 동일 |
| 3 | 일반음식점 | 위생 허가, 식품 안전, 영업 허가 | 21법령 + 25키트 (전체) |
| 4 | 식품제조가공업 | 식품 제조 허가, HACCP, 위생 관리, 식품위생법 | 부분 매칭 |
| 5 | 통신판매업 | 통신판매업 신고, 전자상거래, 소비자 보호, 청약철회 | 부분 매칭 |
| 6 | 미용실/미용업 | 공중위생 신고, 미용업 면허, 위생 관리 | 부분 매칭 |
| 7 | 학원 | 학원 등록, 교육청 신고, 소방 안전 | 부분 매칭 |
| 8 | 숙박업 | 숙박업 허가, 소방 안전, 위생 관리 | 부분 매칭 |
| 9 | 소매업/일반소매업 | 영업 신고, 통신판매업, 사업자 등록 | 부분 매칭 |
| 10 | (기타 업종) | 창업 인허가, 영업 신고, 사업자 등록 (DEFAULT) | 범용 매칭 |

### 3.2 ActionKit 시드 데이터 구조

```
LAW_DATA (domain=laws): 6개 챕터, 21개 아이템
├── Ⅰ. 입지 적법성 (5개 법령)
├── Ⅱ. 영업 성립 요건 (3개 법령)
├── Ⅲ. 안전소방 요건 (3개 법령)
├── Ⅳ. 영업 준수사항 (4개 법령)
├── Ⅴ. 위반 대응 (3개 법령)
└── Ⅵ. 행정처분 구제 (3개 법령)

ACTION_KIT_DATA (domain=kits): 4개 카테고리, 25개 아이템
├── legal (법률 준비): 5개 키트
├── tax (세무 설정): 7개 키트
├── hr (인사·노무): 8개 키트
└── grant (정책자금 신청): 5개 키트

파일: PDF 39개, HWP 6개, PPTX 1개 (총 46개)
```

### 3.3 템플릿 커버리지 분석

**현재 시드 데이터는 주로 음식점(일반/휴게) 업종에 최적화되어 있음.**

| 업종 | 법령 커버리지 | 키트 커버리지 | 템플릿 생성 가능성 |
|------|:----------:|:----------:|:---------------:|
| 일반음식점/휴게음식점/카페 | **95%** | **90%** | **즉시 가능** |
| 식품제조가공업 | 60% | 70% | 보충 필요 |
| 통신판매업 | 20% | 50% | 상당 보충 필요 |
| 미용업 | 20% | 50% | 상당 보충 필요 |
| 학원업/숙박업/소매업 | 10-15% | 40% | 업종별 시드 데이터 추가 필요 |

---

## 4. 템플릿 유형 차원 분석 — 무엇으로 구분할 것인가

### 4.1 사용자 입력 6개 필드의 로드맵 구조 영향 분석

| 차원 | 현재 입력값 | 입력 방식 | 로드맵 **구조** 변경 | 로드맵 **텍스트** 변경 | 분석 |
|------|-----------|:--------:|:------------------:|:------------------:|------|
| **business_type** | 8개 정규화 업종 | 자유텍스트 → LLM 정규화 | **YES** | YES | 적용 법령, 인허가 종류, 필수서류가 **완전히** 다름 |
| **startup_type** | 개인사업자/법인/미정 | 자유텍스트 + 제안칩 | **YES** | YES | 법인 설립 등기, 세무 구조가 구조적으로 다름 |
| **location** | 시군구 단위 | 자유텍스트 → LLM 정규화 | **부분적** | YES | 핵심 법령은 전국 동일, 조례/관할기관만 다름 |
| **open_timeline** | 3개월/6개월/1년 | 자유텍스트 + 제안칩 | NO | YES | estimated_days만 영향 |
| **budget_range** | 3천만/1억/1억+ | 자유텍스트 + 제안칩 | NO | YES | 정책자금 적격성 정도만 영향 |
| **experience_level** | BEGINNER 하드코딩 | 사용자 입력 없음 | NO | 미사용 | 현재 항상 BEGINNER |

> **구조 변경** = 단계(phase) 자체가 다르거나, 적용 법령/서류 목록이 달라짐
> **텍스트 변경** = 같은 구조 위에 문구, 순서, 일수 등만 달라짐

### 4.2 발견된 문제: startup_type 정의 불일치 ⚠️

**프론트엔드 (사용자가 실제 입력하는 값):**
```
제안칩: "개인사업자", "법인", "미정"
→ 법인 형태 (Legal Entity Type) 축
```

**백엔드 LLM 프롬프트 (시스템 프롬프트가 기대하는 값):**
```
"## 창업 형태별 차이
 - 신규: 전 과정 진행
 - 양수양도: 기존 인허가 승계 절차 포함
 - 프랜차이즈: 본사 지원 항목 구분"
→ 창업 방식 (Startup Method) 축
```

**이 두 축은 완전히 다른 개념:**

| 축 | 값 | 로드맵 구조 영향 | 예시 |
|---|---|---|---|
| **법인 형태** | 개인사업자 / 법인 | 세무 신고 방식, 법인 설립 등기 절차, 4대보험 | 법인은 "법인 설립 등기" 단계 추가, 개인은 생략 |
| **창업 방식** | 신규 / 양수양도 / 프랜차이즈 | 인허가 승계 여부, 기존 시설 인수 절차, 본사 지원 | 양수양도는 "기존 인허가 승계" 단계로 대체, 프랜차이즈는 본사 지원 항목 분리 |

**현재 상태**: 사용자가 "개인사업자"를 입력하면 LLM이 "신규/양수양도/프랜차이즈" 규칙 중에서 해석하려 하므로, **두 축 모두 제대로 반영 안 됨**.

**개선 방향**: 입력을 2개 필드로 분리하거나, 최소한 프론트엔드 제안칩을 LLM 프롬프트와 일치시켜야 함.

### 4.3 각 차원의 구조적 차이 상세

#### business_type — 구조 차이 ★★★★★ (가장 큼)

```
[일반음식점]                    [통신판매업]
├── 입지 검토 (건축법)          ├── 사업자 등록
├── 영업 인허가 (식품위생법)     ├── 통신판매업 신고 (전자상거래법)
├── 안전·소방 (소방시설법)       ├── 개인정보 처리방침
├── 위생교육 이수               ├── 청약철회 정책 수립
├── 세무 설정                   ├── 세무 설정
├── 인사·노무                   ├── 인사·노무
└── 정책자금 신청               └── 정책자금 신청
```
→ 상위 4개 단계가 **완전히** 다름. 하위 3개(세무/노무/정책자금)만 공통.

#### startup_type (창업 방식) — 구조 차이 ★★★★☆

```
[신규 창업]                    [양수양도]                    [프랜차이즈]
├── 입지 검토 (신규)           ├── 양수 대상 조사             ├── 가맹점 계약 검토
├── 시설 기준 확인             ├── 기존 인허가 승계 신고       ├── 본사 제공 시설 확인
├── 영업 인허가 신규 신청       ├── 시설 변경사항 점검          ├── 영업 인허가 (본사 지원)
├── 안전·소방 검사             ├── 명의 변경                  ├── 안전·소방 (본사 매뉴얼)
└── ...                       └── ...                       └── ...
```
→ 인허가 관련 단계의 **절차 자체**가 다름 (신규 신청 vs 승계 vs 본사 지원)

#### 법인 형태 (개인/법인) — 구조 차이 ★★★☆☆

```
[개인사업자]                   [법인]
├── (인허가 단계 동일)          ├── (인허가 단계 동일)
├── 세무서 사업자등록            ├── 법인 설립 등기 ← 추가 단계
├── 간이/일반 과세 선택          ├── 법인 사업자등록
├── 종합소득세 신고 준비         ├── 법인세 신고 체계 구축
└── ...                        ├── 주주명부/이사회 관리
                               └── ...
```
→ 세무/법률 단계에서 **분기**가 발생하지만, 인허가 핵심은 동일

#### location — 구조 차이 ★★☆☆☆

```
[서울시]                       [경기도 시흥시]
├── (단계 동일)                 ├── (단계 동일)
├── 서울시 위생과 → 온라인 신청  ├── 시흥시 보건소 → 방문 신청
├── 서울시 소방서               ├── 시흥소방서
├── 서울시 조례 (심야영업 규제)   ├── 경기도 조례 (상이)
└── ...                        └── ...
```
→ **같은 단계** 내에서 관할기관/조례 차이만 존재. 구조 변경은 거의 없음.

### 4.4 조합 경우의 수 분석

| 매칭 키 조합 | 경우의 수 | 운영자 관리 부담 | 품질 관리 |
|-------------|:--------:|:-------------:|:--------:|
| business_type만 | **8개** | 매우 낮음 | 집중 가능 |
| × 창업방식 (신규/양수양도/프랜차이즈) | **24개** | 낮음 | 가능 |
| × 법인형태 (개인/법인) 추가 | **48개** | 중간 | 부담 시작 |
| × 지역 (시도 17+전국) | **864개** | **비현실적** | 불가능 |

### 4.5 추천: 단계별 확장 전략

```
┌──────────────────────────────────────────────────────────────────┐
│ Phase 1 (MVP): business_type만 → 8개 템플릿                      │
│                                                                  │
│   매칭 키: business_type                                          │
│   나머지 차원: LLM 개인화에 위임                                    │
│                                                                  │
│   장점: 즉시 시작 가능, 운영자 부담 최소                             │
│   한계: 양수양도/프랜차이즈 차이 미반영                              │
│                                                                  │
│   ※ 이 단계에서 startup_type 프론트/백엔드 불일치 먼저 수정          │
├──────────────────────────────────────────────────────────────────┤
│ Phase 2 (안정화 후): + startup_method → 최대 24개                  │
│                                                                  │
│   매칭 키: business_type × startup_method(신규/양수양도/프랜차이즈) │
│   입력 분리: startup_type → entity_type(개인/법인) + method(신규/양수/FC) │
│                                                                  │
│   장점: 실제 프로세스 차이 반영, 가맹점 창업자 대응                   │
│   한계: 48개 조합 중 유효한 것만 선별 필요                           │
│         (예: 식품제조가공업 + 프랜차이즈는 드물어서 생략 가능)         │
├──────────────────────────────────────────────────────────────────┤
│ Phase 3 (선택): + 지역 변형 (데이터 축적 후 필요시만)               │
│                                                                  │
│   방식: 전국 공통 템플릿 + 지역 override (상속 패턴)                │
│         지역 단위: 서울/수도권/비수도권 (3단계)                      │
│                                                                  │
│   ※ 지역 전체를 분리하는 게 아니라,                                 │
│     "관할기관 안내" 섹션만 지역별 override하는 패턴                  │
└──────────────────────────────────────────────────────────────────┘
```

### 4.6 Phase 1에서 해결해야 할 선행 이슈

| # | 이슈 | 현재 상태 | 필요 조치 |
|---|------|----------|----------|
| 1 | **startup_type 불일치** | FE: 개인/법인/미정, BE: 신규/양수양도/FC | Phase 1에서는 FE 제안칩을 BE와 일치시키거나, Phase 2에서 2축 분리 |
| 2 | **업종 정규화 목록** | 8개 고정 + LLM 정규화 | 템플릿 매칭 시 정규화된 값 기준으로 조회 (validate_generation_input 결과 활용) |
| 3 | **기타 업종 처리** | DEFAULT_QUERY_KEYWORDS 사용 | 매칭 실패 → 기존 파이프라인 사용 (템플릿 없이) |
| 4 | **entity_type(개인/법인) 반영** | Phase 1에서는 LLM 개인화에 위임 | 세무 단계 체크리스트에서 LLM이 분기 처리 |

---

## 5. 제안 데이터 모델 — RoadmapTemplate (Section 4 반영)

### 4.1 새 테이블 설계

```
RoadmapTemplate (새 테이블)
  ├── id: int (PK)
  ├── business_type: str (업종 키, 인덱스) ← Phase 1 매칭 키
  ├── startup_method: str | null (신규/양수양도/프랜차이즈, Phase 2에서 사용)
  ├── location_scope: str | null (지역 범위, null=전국 공통, Phase 3에서 사용)
  ├── title: str (템플릿 제목)
  ├── description: str (템플릿 설명)
  ├── version: int (버전 관리, 기본 1)
  ├── status: str (DRAFT | REVIEW | APPROVED | ARCHIVED)
  ├── source_roadmap_id: UUID | null (원본 로드맵 참조, FK → Roadmap)
  ├── created_by: int (FK → User)
  ├── reviewed_by: int | null (검수자, FK → User)
  ├── reviewed_at: datetime | null
  ├── created_at: datetime
  └── updated_at: datetime

RoadmapTemplateStep (새 테이블)
  ├── id: int (PK)
  ├── template_id: int (FK → RoadmapTemplate)
  ├── step_order: int
  ├── phase: str
  ├── title: str
  ├── objective: str
  ├── estimated_days: int (기본 일수)
  ├── risk_notes: JSON (list[str])
  └── created_at: datetime

RoadmapTemplateAction (새 테이블)
  ├── id: int (PK)
  ├── template_step_id: int (FK → RoadmapTemplateStep)
  ├── action_type: str (CHECKLIST | LEGAL_BASIS | DOCUMENT)
  ├── title: str
  ├── description: str
  ├── source_url: str | null
  ├── actionkit_item_id: int | null (FK → ActionKitItem, 역추적)
  ├── actionkit_file_id: int | null (FK → ActionKitFile)
  ├── sort_order: int
  └── created_at: datetime
```

### 4.2 상태 워크플로우

```
[최초 생성]
  │
  ▼
DRAFT ──(운영자 검토 시작)──▶ REVIEW ──(검수 승인)──▶ APPROVED
  ▲                            │                        │
  │                            │                        │
  └────(수정 요청)──────────────┘     (새 버전 생성)────────┘
                                                        │
                                             ARCHIVED ◀──┘ (이전 버전)
```

### 4.3 기존 테이블과의 관계

```
RoadmapTemplate ──(source_roadmap_id)──▶ Roadmap (원본 추적)
RoadmapTemplateAction ──(actionkit_item_id)──▶ ActionKitItem (팩트 데이터 연결)
RoadmapTemplateAction ──(actionkit_file_id)──▶ ActionKitFile (서류 파일 연결)

※ 생성 시 참조:
Roadmap 생성 → RoadmapTemplate 조회(business_type 매칭) → 템플릿 골격 사용 + LLM 개인화
```

---

## 6. 생성 파이프라인 변경 설계

### 5.1 현재 vs 개선 비교

```
[현재 파이프라인]
요청 → ActionKitMatcher → LLMPersonalizer → DB 저장
       (벡터 검색)         (LLM 전체 생성)

[개선 파이프라인]
요청 → TemplateResolver → 매칭 결과
       │
       ├── 승인 템플릿 있음 (APPROVED)
       │     └── 템플릿 골격 로드 → LLMPersonalizer (개인화만) → DB 저장
       │         - 법적근거/서류: 템플릿 그대로 사용 (LLM 불필요)
       │         - 체크리스트: 템플릿 기반 + LLM 순서/보충
       │         - objective/risk_notes: LLM 개인화
       │
       └── 승인 템플릿 없음
             └── [기존 파이프라인] ActionKitMatcher → LLMPersonalizer → DB 저장
                 + 결과를 DRAFT 템플릿으로 자동 등록
```

### 5.2 LLM 비용 절감 효과 추정

| 항목 | 현재 (매번 생성) | 개선 (템플릿 + 개인화) | 절감 |
|------|:-------------:|:------------------:|:----:|
| ActionKitMatcher 벡터 검색 | 매번 실행 | 템플릿 있으면 **스킵** | -100% |
| LLM 프롬프트 입력 토큰 | ~2,000 토큰 | ~800 토큰 (개인화만) | -60% |
| LLM 출력 토큰 | ~1,500 토큰 | ~600 토큰 | -60% |
| 법적근거/서류 정확도 | LLM 의존 (오류 가능) | 검수된 데이터 | **정확도 향상** |
| 전체 응답 시간 | 15-25초 | 5-10초 | -50~60% |

### 5.3 TemplateResolver 설계

```python
class TemplateResolver:
    """업종+지역으로 적합한 승인 템플릿을 조회"""

    async def resolve(
        self,
        business_type: str,
        location: str | None = None,
    ) -> RoadmapTemplate | None:
        """
        매칭 우선순위:
        1. business_type + location_scope 정확 일치
        2. business_type + location_scope=null (전국 공통)
        3. None (템플릿 없음 → 기존 파이프라인)

        status=APPROVED인 템플릿만 반환.
        여러 버전 있으면 최신 version 반환.
        """
```

---

## 7. 관리자 UI 설계 — 기존 Ops 콘솔 확장

### 6.1 현재 Ops 콘솔 구조

```
/api/v1/ops/ (require_platform_admin)
├── /home          → 대시보드 통계
├── /reports       → 리포트
├── /users         → 사용자 관리
├── /growth-club   → 커뮤니티 관리
├── /actionkit     → 액션키트 CRUD (30+ 엔드포인트)
├── /announcements → 공지사항 관리
└── /audit-logs    → 감사 로그 조회
```

**기존 패턴 참고: `/ops/actionkit`**
- 카테고리 CRUD + 정렬 (drag-drop)
- 아이템 CRUD + 파일 업로드/다운로드
- 관련 법령/하이라이트/체크리스트 관리
- 모든 변경에 audit log 기록

### 6.2 추가할 Ops 라우트

```
/api/v1/ops/roadmap-templates
├── GET    /                          → 템플릿 목록 (필터: status, business_type)
├── POST   /                          → 수동 템플릿 생성
├── GET    /{template_id}             → 템플릿 상세 (단계 + 액션 포함)
├── PATCH  /{template_id}             → 템플릿 메타 수정 (title, description, status)
├── DELETE /{template_id}             → 템플릿 삭제
│
├── POST   /{template_id}/steps              → 단계 추가
├── PATCH  /{template_id}/steps/{step_id}    → 단계 수정
├── DELETE /{template_id}/steps/{step_id}    → 단계 삭제
├── PATCH  /{template_id}/steps/reorder      → 단계 순서 변경
│
├── POST   /{template_id}/steps/{step_id}/actions           → 액션 추가
├── PATCH  /{template_id}/steps/{step_id}/actions/{action_id} → 액션 수정
├── DELETE /{template_id}/steps/{step_id}/actions/{action_id} → 액션 삭제
│
├── POST   /{template_id}/approve    → 검수 승인 (status: REVIEW → APPROVED)
├── POST   /{template_id}/reject     → 검수 반려 (status: REVIEW → DRAFT)
├── POST   /{template_id}/archive    → 보관 처리 (APPROVED → ARCHIVED)
│
├── POST   /generate-from-roadmap    → 기존 로드맵에서 템플릿 역생성
└── GET    /stats                    → 템플릿 사용 통계
```

### 6.3 프론트엔드 관리 화면 구성

```
[로드맵 템플릿 관리]
┌─────────────────────────────────────────────────────┐
│ 📋 로드맵 템플릿 관리                                  │
│                                                     │
│ [필터: 업종 ▼] [상태 ▼] [+ 새 템플릿] [자동생성에서 가져오기] │
│                                                     │
│ ┌───────────────────────────────────────────────┐   │
│ │ 🍴 일반음식점 (서울) — v3    ✅ APPROVED        │   │
│ │    검수: 홍길동 (2026-02-28)  사용 횟수: 47회    │   │
│ ├───────────────────────────────────────────────┤   │
│ │ ☕ 휴게음식점 (전국) — v2    ✅ APPROVED         │   │
│ │    검수: 김관리 (2026-02-25)  사용 횟수: 32회    │   │
│ ├───────────────────────────────────────────────┤   │
│ │ 💻 통신판매업 (전국) — v1    📝 DRAFT           │   │
│ │    자동 생성됨 (2026-03-01)  미검수              │   │
│ ├───────────────────────────────────────────────┤   │
│ │ 💇 미용업 (전국) — v1        🔍 REVIEW          │   │
│ │    검수 중: 박관리 (2026-02-27)                  │   │
│ └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

```
[템플릿 상세 편집]
┌─────────────────────────────────────────────────────┐
│ 📋 일반음식점 (서울) 템플릿 — v3                        │
│ 상태: APPROVED → [수정하려면 새 버전 생성]              │
│                                                     │
│ ┌─── 단계 1: 입지 검토 (drag handle) ───────────┐   │
│ │ 목표: 음식점 입지의 법적 적합성을 확인합니다       │   │
│ │ 예상 일수: 7일                                  │   │
│ │                                                │   │
│ │ ✅ 체크리스트 (3):                               │   │
│ │   ☐ 용도지역 확인 (상업/준주거 유리)              │   │
│ │   ☐ 건축물 용도 분류 확인                        │   │
│ │   ☐ 학교보건법 교육환경 보호구역 확인             │   │
│ │   [+ 항목 추가]                                 │   │
│ │                                                │   │
│ │ 📖 법적근거 (2):                                │   │
│ │   • 건축법 제2조 (용도 분류) → [actionkit #42]   │   │
│ │   • 국토이용법 제36조 (용도지역) → [actionkit #43] │   │
│ │   [+ 법적근거 추가]                              │   │
│ │                                                │   │
│ │ 📄 필수서류 (1):                                │   │
│ │   • 건축물대장 등본 → [다운로드 링크]             │   │
│ │   [+ 서류 추가]                                 │   │
│ │                                                │   │
│ │ ⚠️ 리스크 (1):                                  │   │
│ │   • 전용주거지역 내 음식점 설치 불가              │   │
│ │   [+ 리스크 추가]                               │   │
│ └────────────────────────────────────────────────┘   │
│                                                     │
│ ┌─── 단계 2: 영업 인허가 (drag handle) ──────────┐   │
│ │ ...                                            │   │
│ └────────────────────────────────────────────────┘   │
│                                                     │
│ [+ 단계 추가] [검수 요청] [미리보기]                   │
└─────────────────────────────────────────────────────┘
```

---

## 8. 자동 템플릿 등록 — 최초 생성 시 플로우

### 7.1 로직

```python
# roadmap_generation_service.py — process_job() 내부, Step 3 이후 추가

# Step 4: 템플릿 자동 등록 (ACTIONKIT_RAG 모드일 때만)
if generation_mode == "ACTIONKIT_RAG":
    existing_template = await template_repo.find_approved(
        business_type=payload.business_type,
        location=payload.location,
    )
    if not existing_template:
        # 승인 템플릿 없음 → DRAFT로 자동 등록
        await template_repo.create_from_roadmap(
            roadmap_id=roadmap.id,
            business_type=payload.business_type,
            location=payload.location,
            steps_payload=steps_payload,
            status="DRAFT",
            created_by=job.user_id,
        )
        logger.info(
            "Auto-created DRAFT template for business_type=%s",
            payload.business_type,
        )
```

### 7.2 기존 로드맵에서 역생성

```
운영자가 관리 화면에서 "기존 로드맵에서 템플릿 생성" 클릭
  ↓
로드맵 목록 조회 (ACTIONKIT_RAG 모드만 필터)
  ↓
선택한 로드맵의 Step/StepDetail/StepAction 데이터 복제
  ↓
RoadmapTemplate (status=DRAFT) + TemplateStep + TemplateAction 생성
  ↓
source_roadmap_id에 원본 로드맵 ID 기록 (역추적)
  ↓
운영자가 내용 검토 후 수정 → 검수 승인 (APPROVED)
```

---

## 9. 기존 아키텍처 영향 분석

### 8.1 변경 필요 파일

| 파일 | 변경 유형 | 내용 |
|------|:--------:|------|
| `app/models/` | **신규** | `roadmap_template.py` (3 테이블: Template, TemplateStep, TemplateAction) |
| `alembic/versions/` | **신규** | 마이그레이션 파일 (테이블 3개 + 인덱스) |
| `app/repositories/` | **신규** | `roadmap_template_repository.py` (CRUD + 매칭 조회) |
| `app/features/roadmaps/application/` | **신규** | `template_resolver.py` (업종/지역 매칭 로직) |
| `app/features/roadmaps/application/roadmap_generation_service.py` | **수정** | 템플릿 조회 → 골격 사용 분기 + 자동 DRAFT 등록 |
| `app/features/roadmaps/application/llm_personalizer.py` | **수정** | 템플릿 모드용 경량 프롬프트 추가 (개인화만) |
| `app/api/v1/ops/` | **신규** | `roadmap_templates.py` (관리 API 20+ 엔드포인트) |
| `app/api/v1/ops/router.py` | **수정** | 새 라우터 등록 |
| `app/features/ops/application/` | **신규** | `roadmap_templates/service.py` (비즈니스 로직) |
| `app-frontend/src/features/ops/` | **신규** | 템플릿 관리 UI 컴포넌트 |

### 8.2 변경하지 않는 파일

| 파일 | 이유 |
|------|------|
| `app/models/roadmap.py` | 기존 Roadmap 스키마 변경 없음 |
| `app/repositories/roadmap_repository.py` | 기존 로직 유지 |
| `app/features/roadmaps/application/actionkit_matcher.py` | 템플릿 없는 경우 기존 경로 유지 |
| `app/api/v1/roadmaps/` | 사용자 API 변경 없음 (내부 생성 로직만 변경) |

### 8.3 기존 로드맵과의 호환성

- **하위 호환 100%**: 템플릿 없으면 기존 파이프라인 그대로 동작
- 기존 Roadmap 테이블에 `template_id` 컬럼 추가 가능 (optional FK) → 어떤 템플릿으로 생성했는지 추적
- 기존 데이터 마이그레이션 불필요

---

## 10. 구현 전 확인 사항 체크리스트

### 10.1 설계 결정 필요 항목

| # | 결정 항목 | 선택지 | 추천 | 이유 |
|---|----------|--------|:----:|------|
| 1 | **Phase 1 템플릿 매칭 키** | A) business_type만 / B) business_type + startup_method | **A** | Phase 1에서는 8개 템플릿으로 시작, startup_method는 Phase 2 (Section 4.5 참고) |
| 2 | **startup_type 불일치 해결** | A) FE 제안칩을 BE와 일치 / B) 2축 분리(entity_type+method) / C) Phase 2까지 보류 | **A (단기) → B (Phase 2)** | 단기: FE 제안칩을 "신규/양수양도/프랜차이즈"로 변경. 장기: 개인/법인 축 추가 |
| 3 | **지역 범위** | A) Phase 1에서 무시(null 고정) / B) 시도 단위 / C) 3단계(서울/수도권/비수도권) | **A** | Phase 1에서는 전국 공통 템플릿만, Phase 3에서 지역 override |
| 4 | **자동 DRAFT 생성 시점** | A) 매 생성시 / B) 업종 최초 생성시만 / C) 수동만 | **B** | 동일 업종 중복 DRAFT 방지, 최초 1회만 |
| 5 | **버전 관리** | A) 동일 레코드 수정 / B) 새 버전 레코드 생성 | **B** | 이전 버전 복원 가능, 감사 추적 |
| 6 | **APPROVED 템플릿 수정** | A) 직접 수정 / B) 새 버전으로만 / C) DRAFT로 복제 | **B** | 운영 중인 템플릿 실수 방지 |
| 7 | **템플릿 사용 통계** | A) 별도 테이블 / B) Roadmap에 template_id FK | **B** | 간단한 COUNT로 충분, 별도 테이블 과잉 |
| 8 | **LLM 개인화 범위** | A) 템플릿 있으면 LLM 완전 스킵 / B) 개인화만 LLM | **B** | 사용자 맥락 반영 유지, 비용은 60% 절감 |

### 10.2 기술 구현 확인 항목

| # | 확인 항목 | 현재 상태 | 필요 조치 |
|---|----------|----------|----------|
| 1 | Alembic 마이그레이션 9번째 파일 추가 가능? | 8개 존재, 충돌 없음 | 가능 |
| 2 | Ops 라우터에 새 모듈 추가 패턴? | `router.include_router()` 패턴 확인 | 동일 패턴 사용 |
| 3 | ActionKitItem FK 참조? | `ActionKitItem.id: int` (PK) | RoadmapTemplateAction에서 FK 가능 |
| 4 | 감사 로그 확장? | `AuditTargetType` enum 존재 | `ROADMAP_TEMPLATE` 추가 |
| 5 | 프론트엔드 Ops 페이지 구조? | `src/features/ops/` 존재 | `OpsTemplateView` 컴포넌트 추가 |
| 6 | OpenAPI 타입 자동 생성? | `npm run types:sync` 존재 | 새 API 추가 후 실행 |

### 10.3 데이터 관련 확인 항목

| # | 확인 항목 | 현재 상태 | 필요 조치 |
|---|----------|----------|----------|
| 1 | 음식점 업종 초기 템플릿 시드 가능? | ActionKit 시드 데이터 완비 (21법령+25키트) | 시드 스크립트로 초기 DRAFT 생성 가능 |
| 2 | 비음식점 업종 데이터 충분? | 공통 키트(세무/노무/정책자금)만 존재 | 업종별 법령 데이터 추가 필요 (별도 작업) |
| 3 | 기존 생성 로드맵에서 역생성 대상? | DB에 ACTIONKIT_RAG 모드 로드맵 존재 여부 확인 필요 | 운영 후 데이터 있으면 활용 |

---

## 11. 구현 계획 — 우선순위별

### Phase A: 데이터 모델 + 기반 (예상 3일)

```
[A-1] DB 모델 정의 (1일)
  └── RoadmapTemplate, RoadmapTemplateStep, RoadmapTemplateAction 모델
      Roadmap 테이블에 template_id (Optional FK) 추가

[A-2] Alembic 마이그레이션 (0.5일)
  └── 테이블 3개 + 인덱스 + Roadmap.template_id 컬럼

[A-3] Repository 구현 (1.5일)
  └── RoadmapTemplateRepository (CRUD + 매칭 조회 + 역생성)
```

### Phase B: 파이프라인 통합 (예상 4일)

```
[B-1] TemplateResolver 구현 (1일)
  └── 업종+지역 매칭 로직, 버전 우선순위

[B-2] RoadmapGenerationService 수정 (2일)
  └── 템플릿 조회 → 골격 사용 분기
      개인화용 경량 프롬프트 추가
      자동 DRAFT 등록 로직

[B-3] LLMPersonalizer 템플릿 모드 (1일)
  └── 기존 템플릿 골격 + 사용자 맥락으로 개인화만 실행
      법적근거/서류는 그대로 전달, 체크리스트/일수/목표만 LLM
```

### Phase C: 관리자 API (예상 5일)

```
[C-1] Ops 템플릿 CRUD API (2일)
  └── 목록/상세/생성/수정/삭제 + 단계/액션 관리

[C-2] 검수 워크플로우 API (1일)
  └── approve/reject/archive + 버전 생성

[C-3] 기존 로드맵 역생성 API (1일)
  └── POST /generate-from-roadmap

[C-4] 감사 로그 + 통계 (1일)
  └── AuditTargetType.ROADMAP_TEMPLATE 추가, 사용 통계
```

### Phase D: 프론트엔드 관리 화면 (예상 5일)

```
[D-1] 템플릿 목록 페이지 (1.5일)
  └── 필터 (업종/상태), 카드형 목록, 상태 배지

[D-2] 템플릿 상세 편집 페이지 (2.5일)
  └── 단계 추가/수정/삭제/정렬 (drag-drop)
      액션 추가/수정/삭제 (인라인 편집)
      ActionKit 연결 (검색 → 선택)

[D-3] 검수 워크플로우 UI (0.5일)
  └── 승인/반려 버튼, 검수 이력

[D-4] 역생성 + 통계 (0.5일)
  └── 로드맵 선택 → 템플릿 변환, 사용 횟수 표시
```

### Phase E: 테스트 + QA (예상 2일)

```
[E-1] 백엔드 테스트 (1일)
  └── Repository 단위 테스트, 파이프라인 통합 테스트

[E-2] 프론트엔드 테스트 + QA (1일)
  └── 관리 화면 기능 테스트, 실제 로드맵 생성 테스트
```

**총 예상 공수: ~19일 (약 4주)**

---

## 12. 리스크 분석

| 리스크 | 영향 | 대응 |
|--------|------|------|
| **비음식점 업종 데이터 부족** | 템플릿 생성해도 법적근거가 빈약 | Phase 1은 음식점 업종만 집중, 이후 업종별 ActionKit 시드 확장 |
| **자동 DRAFT 품질** | LLM 생성 결과가 템플릿 기반이라 품질 불균등 | 운영자 검수 필수, APPROVED 전까지 사용 안 됨 |
| **템플릿 vs 개인화 경계** | 너무 많이 고정하면 개인화 의미 없음 | 법적근거/서류만 고정, 나머지는 LLM 개인화 유지 |
| **버전 관리 복잡도** | 이전 버전 로드맵 사용자 영향 | 생성된 로드맵은 독립 데이터 (template_id만 참조), 템플릿 변경해도 기존 로드맵 불변 |
| **Ops UI 개발 공수** | 프론트엔드 5일은 빡빡 | 기존 OpsActionKitView 컴포넌트 패턴 최대 재활용 |

---

## 13. 핵심 결론

### 실현 가능성

**기술적으로 완전히 실현 가능하며, 기존 아키텍처에 잘 맞는 확장.**

1. **기존 Ops 패턴 재활용**: ActionKit CRUD + 감사 로그 패턴 → 템플릿 관리에 그대로 적용 (코드 구조, UI 패턴 모두)
2. **파이프라인 영향 최소화**: 기존 경로 100% 호환, 템플릿 있을 때만 분기
3. **ActionKit 데이터 활용**: 이미 구축된 46개 법령/키트 데이터가 템플릿 초기 시드로 바로 활용 가능

### 기대 효과

| 항목 | Before | After |
|------|--------|-------|
| 동일 업종 로드맵 생성 시간 | 15-25초 | 5-10초 |
| LLM API 비용 (동일 업종) | 100% | ~40% |
| 법적근거/서류 정확도 | LLM 의존 (비결정적) | 검수된 데이터 (확정) |
| 링크 오류 발생률 | 높음 (LLM item_id 누락) | 매우 낮음 (템플릿에 고정) |
| 품질 관리 | 불가 (매번 새로 생성) | 운영자 검수 후 배포 |

### 선행 작업 의존성

```
[P0] 링크 오류 수정 (chatbot-enhancement-analysis.md Part 2)
  ↓ (링크가 제대로 동작해야 템플릿의 source_url도 의미 있음)
[이 보고서] 템플릿 관리 시스템 구현 (~4주)
  ↓ (템플릿이 있어야 AI 코치가 정확한 컨텍스트를 가짐)
[AI 코치 챗봇] 개선 (chatbot-enhancement-analysis.md Part 1)
```

### 즉시 시작 가능한 작업

1. **DB 모델 설계 확정** (외부 의존성 없음)
2. **기존 ActionKit 시드 데이터 → 초기 템플릿 변환 스크립트** 작성
3. **Ops 관리 API 스켈레톤** 구현 (기존 ActionKit API 패턴 참고)
