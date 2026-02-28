# 로드맵 기능 상세 분석 보고서

> 작성일: 2026-02-28
> 분석 범위: `app-backend/` (FastAPI) + `app-frontend/` (Next.js 15)

---

## 목차

1. [기능 개요](#1-기능-개요)
2. [데이터베이스 스키마](#2-데이터베이스-스키마)
3. [백엔드 아키텍처](#3-백엔드-아키텍처)
4. [API 엔드포인트](#4-api-엔드포인트)
5. [로드맵 생성 파이프라인](#5-로드맵-생성-파이프라인)
6. [비동기 작업 처리](#6-비동기-작업-처리)
7. [프론트엔드 아키텍처](#7-프론트엔드-아키텍처)
8. [사용자 흐름 (User Flows)](#8-사용자-흐름)
9. [핵심 비즈니스 로직](#9-핵심-비즈니스-로직)
10. [파일 맵](#10-파일-맵)

---

## 1. 기능 개요

로드맵은 **창업 준비 과정을 단계별로 안내하는 AI 기반 가이드 시스템**이다. 사용자가 업종, 지역, 창업 형태 등을 입력하면 AI가 맞춤형 로드맵을 생성하고, 사용자는 체크리스트와 법적 근거를 따라 단계별로 창업을 준비할 수 있다.

### 핵심 특징

- **하이브리드 AI 생성**: ActionKit(법률/양식 DB) 매칭 + LLM 개인화의 2단계 파이프라인
- **단계별 실행 관리**: 순차적 진행 강제, 자동 진행(auto-advance), 되돌리기(revert)
- **3가지 액션 타입**: 체크리스트(CHECKLIST), 법적 근거(LEGAL_BASIS), 필수 서류(DOCUMENT)
- **비동기 생성**: Redis 큐 + arq 워커를 통한 백그라운드 생성, 클라이언트 폴링
- **멀티 로드맵 지원**: 사용자가 여러 로드맵을 생성·관리·전환 가능
- **팀 스코프 인가**: 모든 데이터는 team_id로 격리

---

## 2. 데이터베이스 스키마

> 마이그레이션: `app-backend/alembic/versions/002_roadmap.py`
> 모델: `app-backend/app/models/roadmap.py`

### 2.1 Roadmap (메인 엔티티)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID (PK, indexed) | 로드맵 고유 ID |
| `team_id` | UUID (FK → team.id, indexed) | 소속 팀 |
| `title` | String | 로드맵 제목 (자동생성: `{업종} 창업 로드맵`) |
| `business_type` | String | 업종 (예: "카페", "온라인 쇼핑몰") |
| `location` | String | 지역 (예: "서울특별시 강남구") |
| `description` | String (default="") | 추가 설명 |
| `startup_type` | String (nullable) | 창업 형태 (신규, 양수양도, 프랜차이즈 등) |
| `open_timeline` | String (nullable) | 목표 오픈 시기 (예: "3개월 내") |
| `budget_range` | String (nullable) | 예산 범위 (예: "1억 이하") |
| `additional_notes` | String (default="") | 추가 메모 |
| `created_at` | DateTime (indexed) | 생성일 |
| `updated_at` | DateTime | 수정일 |
| `deleted_at` | DateTime (nullable) | **소프트 삭제** 타임스탬프 |
| `created_by` | Integer (FK → user.id) | 생성자 |
| `updated_by` | Integer (FK → user.id) | 수정자 |

### 2.2 RoadmapStep (단계)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | Integer (PK, autoincrement) | 단계 ID |
| `roadmap_id` | UUID (FK → roadmap.id, indexed) | 소속 로드맵 |
| `step_order` | Integer (indexed) | 순서 (1, 2, 3...) |
| `title` | String | 단계 제목 |
| `status` | String (default="PENDING") | 상태: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `BLOCKED` |
| `created_at` | DateTime | 생성일 |
| `completed_at` | DateTime (nullable) | 완료일 |

### 2.3 RoadmapStepDetail (단계 상세 메타데이터)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | Integer (PK) | 상세 ID |
| `roadmap_step_id` | Integer (FK → roadmapstep.id, unique) | 1:1 관계 |
| `phase` | String (default="기본") | 위상 이름 (예: 입지 검토, 영업 인허가) |
| `objective` | String (default="") | 단계 목표 |
| `estimated_days` | Integer (default=0) | 예상 소요일 |
| `risk_notes` | JSON (array) | 리스크/유의사항 목록 |
| `generation_mode` | String (default="RAG") | 생성 방식: `RAG`, `ACTIONKIT_RAG` |
| `source_count` | Integer (nullable) | ActionKit 소스 수 |
| `has_fallback` | Boolean (nullable) | 폴백 사용 여부 |
| `mapping_source` | String (nullable) | 데이터 출처: `actionkit_direct`, `rag`, `fallback` |
| `created_at` | DateTime | 생성일 |
| `updated_at` | DateTime | 수정일 |

### 2.4 RoadmapStepAction (실행 항목)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | Integer (PK) | 액션 ID |
| `roadmap_step_id` | Integer (FK → roadmapstep.id, indexed) | 소속 단계 |
| `action_type` | String (indexed) | 유형: `CHECKLIST`, `LEGAL_BASIS`, `DOCUMENT` |
| `title` | String | 액션 제목 |
| `description` | String (default="") | 설명/스니펫 |
| `source_url` | String (nullable) | 출처 URL |
| `metadata_json` | JSON (object) | 확장 메타데이터 |
| `created_at` | DateTime | 생성일 |

**metadata_json 구조:**
```json
{
  "completed": false,
  "actionkit_item_id": 123,
  "actionkit_file_id": 456,
  "actionkit_highlight_id": 789,
  "actionkit_domain": "laws",
  "actionkit_category": "legal",
  "mapping_source": "actionkit_direct"
}
```

### 2.5 RoadmapGenerationJob (비동기 생성 작업)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| `id` | UUID (PK) | 작업 ID |
| `team_id` | UUID (FK → team.id) | 팀 |
| `user_id` | Integer (FK → user.id) | 요청자 |
| `status` | String (default="QUEUED") | `QUEUED`, `RUNNING`, `SUCCEEDED`, `FAILED` |
| `progress` | Integer (default=0) | 진행률 0~100 |
| `stage` | String (default="QUEUED") | 생성 단계 (아래 참조) |
| `input_payload` | JSON | 사용자 입력값 |
| `error_code` | String (nullable) | 에러 코드 |
| `error_message` | String (nullable, max 1000) | 에러 메시지 |
| `roadmap_id` | UUID (nullable, FK → roadmap.id) | 결과 로드맵 ID |
| `created_at` | DateTime | 생성일 |
| `updated_at` | DateTime | 수정일 |
| `started_at` | DateTime (nullable) | 처리 시작일 |
| `completed_at` | DateTime (nullable) | 완료/실패일 |

**생성 단계(stage) 진행 순서:**
```
QUEUED → MASTER_GENERATING → MATCHING_COMPLETE → PERSONALIZING → DETAIL_GENERATING → PERSISTING → COMPLETED
                                                                                                  → FAILED
```

### ER 다이어그램 (관계)

```
Roadmap (1) ──── (*) RoadmapStep
                       │
                       ├── (1) RoadmapStepDetail
                       │
                       └── (*) RoadmapStepAction

Roadmap (1) ──── (*) RoadmapGenerationJob
```

---

## 3. 백엔드 아키텍처

### 3.1 계층 구조

```
app-backend/app/
├── models/roadmap.py                    # SQLModel 데이터 모델
├── repositories/
│   ├── roadmap_repository.py            # 로드맵 데이터 접근 계층
│   └── roadmap_job_repository.py        # 생성 작업 데이터 접근 계층
├── features/roadmaps/application/
│   ├── roadmap_service.py               # 기본 CRUD 서비스
│   ├── roadmap_progress_service.py      # 진행 상태 관리 서비스
│   ├── roadmap_generation_service.py    # AI 생성 오케스트레이션
│   ├── actionkit_matcher.py             # ActionKit 팩트 매칭
│   ├── llm_personalizer.py              # LLM 개인화 파이프라인
│   └── worker_queue.py                  # Redis 큐 인큐
├── api/v1/roadmaps/
│   ├── router.py                        # 라우터 어그리게이터
│   ├── create.py                        # 생성/목록 엔드포인트
│   ├── get.py                           # 조회/상태 업데이트 엔드포인트
│   └── jobs.py                          # 비동기 작업 엔드포인트
└── workers/roadmap_worker.py            # arq 백그라운드 워커
```

### 3.2 Repository 주요 메서드

**RoadmapRepository:**

| 메서드 | 설명 |
|--------|------|
| `get_latest_for_team(team_id)` | 팀의 최신 비삭제 로드맵 조회 |
| `get_by_id_for_team(roadmap_id, team_id)` | 팀 권한 확인 후 로드맵 조회 |
| `list_for_team(team_id, offset, limit)` | 페이지네이션 로드맵 목록 |
| `create_roadmap(...)` | 로드맵 레코드 생성 |
| `create_steps(roadmap_id, step_titles)` | 기본 단계 생성 |
| `create_steps_with_details(roadmap_id, steps_payload, generation_mode)` | 상세 정보 포함 단계 생성 |
| `list_steps(roadmap_id)` | 단계 목록 (step_order 순) |
| `list_step_details(step_ids)` | 단계 상세 일괄 조회 |
| `list_step_actions(step_ids)` | 단계 액션 일괄 조회 |
| `soft_delete(roadmap_id, team_id)` | 소프트 삭제 (deleted_at 설정) |
| `update_title(roadmap_id, team_id, new_title)` | 제목 변경 |

**RoadmapJobRepository:**

| 메서드 | 설명 |
|--------|------|
| `create_job(team_id, user_id, payload)` | 생성 작업 레코드 생성 (QUEUED) |
| `get_for_team(job_id, team_id)` | 팀 권한 확인 후 작업 조회 |
| `mark_running(job)` | RUNNING 상태로 전환, progress=10 |
| `set_progress(job, stage, progress)` | 진행 단계/률 업데이트 |
| `mark_succeeded(job, roadmap_id)` | 성공 처리, roadmap_id 연결 |
| `mark_failed(job, code, message)` | 실패 처리, 에러 정보 기록 |

---

## 4. API 엔드포인트

> 프리픽스: `/api/v1/roadmaps`
> 인증: 모든 엔드포인트에 JWT 인증 필요 (current_user/current_team 의존성)

### 4.1 로드맵 CRUD

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/api/v1/roadmaps` | 로드맵 목록 조회 (페이지네이션) |
| `POST` | `/api/v1/roadmaps` | 로드맵 생성 (기본 3단계 포함) |
| `GET` | `/api/v1/roadmaps/{roadmap_id}` | 로드맵 기본 조회 (단계 목록) |
| `GET` | `/api/v1/roadmaps/{roadmap_id}/detail` | 로드맵 상세 조회 (단계+상세+액션) |
| `GET` | `/api/v1/roadmaps/latest/detail` | 최신 로드맵 상세 조회 |
| `PATCH` | `/api/v1/roadmaps/{roadmap_id}` | 로드맵 제목 수정 |
| `DELETE` | `/api/v1/roadmaps/{roadmap_id}` | 로드맵 소프트 삭제 (204) |

### 4.2 단계/액션 관리

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `PATCH` | `/api/v1/roadmaps/tasks/{step_id}` | 단계 상태 변경 |
| `PATCH` | `/api/v1/roadmaps/tasks/{step_id}/actions/{action_id}` | 액션 완료 상태 토글 |

### 4.3 비동기 생성 작업

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/roadmaps/jobs/validate` | 입력값 검증 (LLM 정규화) |
| `POST` | `/api/v1/roadmaps/jobs` | 생성 작업 제출 (202 Accepted) |
| `GET` | `/api/v1/roadmaps/jobs/{job_id}` | 작업 상태 조회 (폴링용) |
| `GET` | `/api/v1/roadmaps/jobs/{job_id}/result` | 생성 결과 조회 (roadmap_id) |

### 4.4 주요 요청/응답 스키마

**생성 요청 (POST /roadmaps, POST /roadmaps/jobs):**
```json
{
  "business_type": "카페",
  "location": "서울특별시 강남구",
  "description": "",
  "startup_type": "개인사업자",
  "open_timeline": "3개월 내",
  "budget_range": "1억 이하",
  "additional_notes": "",
  "goal_horizon_days": 30,
  "experience_level": "BEGINNER"
}
```

**상세 응답 (GET /roadmaps/{id}/detail):**
```json
{
  "roadmap_id": "uuid",
  "title": "카페 창업 로드맵",
  "created_at": "2026-02-28T...",
  "steps": [
    {
      "id": 1,
      "title": "카페 시장 조사",
      "status": "COMPLETED",
      "completed_at": "2026-02-28T...",
      "detail": {
        "id": 1,
        "phase": "시장 조사",
        "objective": "카페 시장 트렌드와 경쟁 환경 분석",
        "estimated_days": 7,
        "source_count": 3,
        "has_fallback": false,
        "mapping_source": "actionkit_direct",
        "actions": [
          {
            "id": 1,
            "action_type": "CHECKLIST",
            "title": "주변 상권 분석",
            "description": "반경 500m 내 경쟁 카페 조사",
            "source_url": null,
            "metadata_json": { "completed": true }
          },
          {
            "id": 2,
            "action_type": "LEGAL_BASIS",
            "title": "식품위생법 제37조",
            "description": "영업허가 관련 법적 근거",
            "source_url": "https://...",
            "metadata_json": { "actionkit_domain": "laws" }
          }
        ]
      }
    }
  ]
}
```

**작업 상태 응답 (GET /roadmaps/jobs/{id}):**
```json
{
  "job_id": "uuid",
  "status": "RUNNING",
  "stage": "PERSONALIZING",
  "progress": 60,
  "roadmap_id": null,
  "error_code": null,
  "error_message": null
}
```

---

## 5. 로드맵 생성 파이프라인

> 핵심 파일: `app-backend/app/features/roadmaps/application/roadmap_generation_service.py`

### 5.1 2단계 하이브리드 생성 전략

```
┌─────────────────────────────────────────────────────────┐
│                    사용자 입력                            │
│  (업종, 지역, 창업형태, 오픈시기, 예산, 추가설명)           │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 1: Fact Layer (ActionKit 매칭)                     │
│  ─────────────────────────────────                       │
│  • 멀티 쿼리 벡터 검색 (hybrid search)                    │
│  • 법률, 양식, 가이드 매칭                                │
│  • 관련성 점수 기반 필터링                                 │
│  • 최소 매칭 수: 1건 (_MIN_ACTIONKIT_MATCHES)             │
└─────────────────┬───────────────────────────────────────┘
                  │
          ┌───────┴───────┐
          │               │
     ≥1 매칭         <1 매칭
          │               │
          ▼               ▼
┌──────────────┐  ┌──────────────┐
│ Path A:      │  │ Path B:      │
│ ACTIONKIT_RAG│  │ RAG          │
│ (LLM 개인화) │  │ (LLM 단독)   │
└──────┬───────┘  └──────┬───────┘
       │                 │
       ▼                 ▼
┌─────────────────────────────────────────────────────────┐
│  Stage 2: Intelligence Layer (LLM 개인화)                 │
│  ─────────────────────────────────                       │
│  7가지 개인화 영역:                                       │
│  1. 체크리스트 재정렬/필터/보충                             │
│  2. 법적 근거 강조                                        │
│  3. 서류 제출 순서 + 준비 가이드                           │
│  4. 위상(phase) 재정렬/병렬 실행 결정                      │
│  5. 목표 (업종/지역 특화)                                 │
│  6. 리스크 노트 (업종별 위험 요소)                         │
│  7. 예상 일수 (오픈 타임라인 기반)                         │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│  DB 저장                                                │
│  Roadmap + RoadmapStep + RoadmapStepDetail              │
│  + RoadmapStepAction                                    │
└─────────────────────────────────────────────────────────┘
```

### 5.2 ActionKit 매칭 (actionkit_matcher.py)

**멀티 쿼리 전략:**
1. 기본 쿼리: `"{업종} {지역} 창업 인허가"`
2. 업종별 특화 쿼리: `BUSINESS_QUERY_TEMPLATES`에서 추출
3. 모든 쿼리 병렬 실행, 중복 제거 (최고 점수 기준)

**카테고리→위상 매핑 (CATEGORY_TO_PHASE):**

| 카테고리 | 위상 |
|----------|------|
| 법률 챕터 1 | 입지 검토 |
| 법률 챕터 2 | 영업 인허가 |
| 법률 챕터 3 | 안전·소방 |
| 법률 챕터 4 | 영업 준수사항 |
| 법률 챕터 5 | 위반 대응 |
| 법률 챕터 6 | 행정처분 구제 |
| 법률 챕터 7~12 | 영업 인허가 |
| ActionKit: legal | 법률 준비 |
| ActionKit: tax | 세무 설정 |
| ActionKit: hr | 인사·노무 |
| ActionKit: grant | 정책자금 신청 |

### 5.3 LLM 개인화 (llm_personalizer.py)

**절대 규칙:**
- ActionKit 법률명 + 파일 경로는 **절대 수정 불가**
- 재정렬/필터/보충만 허용

**폴백 전략:**
- LLM 실패 시 → ActionKit 팩트 기반의 기본 생성 (개인화 없이)

### 5.4 입력값 검증 (validate_generation_input)

- LLM(직접 호출, RAG 아님)으로 업종/지역 정규화
- 반환: `{valid, normalized_business_type, normalized_location, reason, confidence}`
- 폴백: 입력 2자 이상 + 지역에 시/도/군/구 포함 시 수락

---

## 6. 비동기 작업 처리

### 6.1 아키텍처

```
Frontend (폴링)
    │
    ▼
POST /roadmaps/jobs  ──→  DB에 Job 생성 (QUEUED)
    │                          │
    │                          ▼
    │                   Redis 큐에 인큐 (arq)
    │                          │
    │                          ▼
    │                   roadmap_worker.py
    │                   (process_roadmap_job)
    │                          │
    │                          ▼
    │                   RoadmapGenerationService
    │                   .process_job(job_id)
    │                          │
GET /roadmaps/jobs/{id} ◄──── 진행률 업데이트
    │
GET /roadmaps/jobs/{id}/result ◄── 완료 시 roadmap_id 반환
```

### 6.2 진행률 단계

| 단계 | stage | progress | 설명 |
|------|-------|----------|------|
| 1 | QUEUED | 0 | 대기열 진입 |
| 2 | MASTER_GENERATING | 10 | 워커가 처리 시작 |
| 3 | MATCHING_COMPLETE | 20 | ActionKit 매칭 완료 |
| 4 | PERSONALIZING | 40~60 | LLM 개인화 진행 |
| 5 | DETAIL_GENERATING | 70 | 상세 정보 생성 |
| 6 | PERSISTING | 80 | DB 저장 |
| 7 | COMPLETED | 100 | 성공 완료 |
| - | FAILED | - | 실패 |

### 6.3 에러 코드

| 코드 | 설명 |
|------|------|
| `QUEUE_UNAVAILABLE` | Redis 큐 연결 실패 |
| `VALIDATION_FAILED` | 입력값 검증 실패 |
| `GENERATION_TIMEOUT` | 생성 시간 초과 |
| `GENERATION_FAILED` | AI 생성 에러 |

---

## 7. 프론트엔드 아키텍처

### 7.1 디렉터리 구조

```
app-frontend/src/
├── app/(dashboard)/roadmap/
│   └── page.tsx                          # 메인 로드맵 페이지
└── features/roadmap/
    ├── api/
    │   └── index.ts                      # API 클라이언트
    ├── types/
    │   ├── roadmap.ts                    # 기본 타입 정의
    │   └── roadmap-utils.ts             # 상세 타입 + 유틸 함수
    ├── hooks/
    │   ├── useActiveRoadmap.ts           # 활성 로드맵 관리
    │   ├── useRoadmapList.ts            # 로드맵 목록 관리
    │   └── useRoadmapJob.ts             # 비동기 작업 관리
    ├── components/
    │   ├── RoadmapExecutionView.tsx      # 실행 뷰 (메인)
    │   ├── RoadmapGenerationPanel.tsx    # 생성 패널 (오케스트레이터)
    │   ├── RoadmapChatIntake.tsx         # 대화형 입력 폼
    │   ├── RoadmapHeader.tsx             # 헤더
    │   ├── RoadmapSwitcher.tsx           # 로드맵 전환기
    │   ├── RoadmapSidebar.tsx            # 사이드바 (진행률/마감일)
    │   ├── RoadmapEmptyHero.tsx          # 빈 상태 히어로
    │   ├── RoadmapGeneratingState.tsx    # 생성 중 상태
    │   ├── RoadmapDeleteDialog.tsx       # 삭제 확인 다이얼로그
    │   ├── RoadmapRenameDialog.tsx       # 이름 변경 다이얼로그
    │   ├── TimelinePhaseCard.tsx         # 위상별 타임라인 카드
    │   ├── TimelineStepItem.tsx          # 개별 단계 아이템
    │   └── roadmap-constants.ts         # 상수 정의
```

### 7.2 주요 컴포넌트 상세

#### page.tsx (메인 페이지)
- **페이지 모드**: `"loading"` → `"empty"` | `"viewing"` | `"creating"`
- 로드맵 목록 로드 → 활성 로드맵 선택 → 상세 로드 → 실행 뷰 렌더링
- 단계 상태 변경 및 액션 완료 처리 핸들러 포함

#### RoadmapExecutionView.tsx (실행 뷰)
- **레이아웃**: 8컬럼 타임라인 + 4컬럼 사이드바
- 현재 위상으로 자동 스크롤
- 위상별 그룹핑으로 타임라인 렌더링
- 전체 진행률 사이드바 표시

#### RoadmapChatIntake.tsx (대화형 입력)
- **6단계 Q&A 인터페이스** (봇 아바타 포함):
  1. 업종 (business_type) - 필수
  2. 지역 (location) - 필수
  3. 창업 형태 (startup_type) - 필수
  4. 오픈 시기 (open_timeline) - 필수
  5. 예산 범위 (budget_range) - 필수
  6. 추가 설명 (description) - 선택
- 필드별 제안 칩(suggestion chips) 제공
- 진행 바로 필수 필드 완료율 표시
- 생성 전 검증 요약 표시

#### TimelinePhaseCard.tsx (타임라인 카드)
- **위상 상태**: `COMPLETED`, `CURRENT`, `LOCKED`, `FUTURE`
- 완료된 위상: 접기 가능
- 현재 위상: 단계 목록 펼침
- 잠긴 위상: 미리보기만 표시
- 상태별 CSS 스타일링 (`STATE_CONFIG`)

#### TimelineStepItem.tsx (단계 아이템)
- **단계 상태**: `DONE`, `ACTIVE`, `LOCKED`
- 완료 확인: 더블 클릭 패턴 (오확인 방지)
- 되돌리기: 마지막 완료 단계만 가능
- 액션 그룹핑: CHECKLIST, DOCUMENT, LEGAL_BASIS별
- 출처 배지: actionkit_direct, rag, fallback
- 외부 링크: 법률/양식 소스 URL

#### RoadmapGenerationPanel.tsx (생성 패널)
- 생성 플로우 오케스트레이션
- localStorage에 job_id 저장하여 폴링 지속
- 에러 처리: `mapJobFailureMessage()` 사용
- 미인증 시 `SocialAuthModal` 연동

#### RoadmapSwitcher.tsx (전환기)
- 팝오버 컴포넌트 (380px 폭)
- 모든 로드맵 목록 + 진행률 바
- 드롭다운 메뉴: 이름 변경 / 삭제
- "새 로드맵" 버튼

#### RoadmapSidebar.tsx (사이드바)
- 전체 진행률 카드
- 다가오는 마감일 (다음 3개 미완료 단계)
- ActionKit 가이드북 링크 (`/actionkit`)
- estimated_days 기반 마감일 계산

### 7.3 커스텀 훅

| 훅 | 역할 | localStorage 키 |
|----|------|------------------|
| `useActiveRoadmap` | 활성 로드맵 ID 관리, 상세 로드, 404 처리 | `stepzero_active_roadmap_id` |
| `useRoadmapList` | 목록 로드, 삭제, 이름 변경 | - |
| `useRoadmapJob` | 비동기 작업 생성/폴링/결과 조회 | - |

### 7.4 프론트엔드 API 클라이언트

```typescript
// app-frontend/src/features/roadmap/api/index.ts
fetchRoadmapList(offset?, limit?)     → RoadmapListResponse
deleteRoadmap(roadmapId)              → void
updateRoadmapTitle(roadmapId, title)  → RoadmapSummary
fetchRoadmapDetail(roadmapId)         → RoadmapDetailResponse
```

### 7.5 상수 및 레이블

**제안 칩:**
```typescript
HERO_SUGGESTIONS = ["카페 프랜차이즈", "SaaS 스타트업", "온라인 의류 쇼핑몰", "샐러드 배달 전문점"]

INTAKE_FIELD_SUGGESTIONS = {
  business_type: ["카페", "온라인 쇼핑몰", "SaaS"],
  location: ["서울 마포구", "서울 강남구", "부산 해운대구"],
  startup_type: ["개인사업자", "법인", "미정"],
  open_timeline: ["3개월 내", "6개월 내", "1년 내"],
  budget_range: ["3천만 원 이하", "1억 이하", "1억 이상"],
}
```

**상태 레이블:**
```typescript
STATUS_LABEL = { PENDING: "대기", IN_PROGRESS: "진행 중", COMPLETED: "완료", BLOCKED: "보류" }
ACTION_TYPE_LABEL = { CHECKLIST: "체크리스트", LEGAL_BASIS: "법적 근거", DOCUMENT: "필수 서류" }
TOGGLE_ACTION_TYPES = Set(["CHECKLIST", "DOCUMENT"])  // LEGAL_BASIS는 토글 불가
```

### 7.6 대시보드 연동

- **RoadmapStepper** (`features/dashboard/components/RoadmapStepper.tsx`): 대시보드에 가로 타임라인 표시
- **DashboardView.tsx**: localStorage에서 활성 로드맵 로드 또는 `/roadmaps/latest/detail` 호출
- **Sidebar**: "나의 로드맵" 메뉴 → `/roadmap` 경로 (Map 아이콘)

### 7.7 스타일링

- **프레임워크**: Tailwind CSS 4
- **UI 라이브러리**: shadcn/ui (Button, Badge, Dialog, Card, Progress, Popover, Dropdown)
- **아이콘**: Lucide React
- **주요 색상**: Blue primary (#36a4f2), slate grays
- **애니메이션**: 부드러운 전환, 진행률 애니메이션, 로딩 스피너

---

## 8. 사용자 흐름

### 8.1 새 로드맵 생성

```
1. /roadmap 접속
2. 로드맵 없음 → 빈 상태 히어로 표시
3. "AI 로드맵 생성하기" 클릭
4. RoadmapChatIntake 6단계 폼:
   ├─ 업종 입력 (제안 칩 또는 직접 입력)
   ├─ 지역 입력
   ├─ 창업 형태 선택
   ├─ 오픈 시기 선택
   ├─ 예산 범위 선택
   └─ 추가 설명 (선택)
5. POST /roadmaps/jobs/validate → 입력값 검증
6. POST /roadmaps/jobs → 생성 작업 제출 (202)
7. 폴링 시작 (localStorage에 job_id 저장)
   ├─ GET /roadmaps/jobs/{id} → 진행 상태 표시
   └─ 반복...
8. 성공 → GET /roadmaps/jobs/{id}/result → roadmap_id 획득
9. GET /roadmaps/{id}/detail → 상세 로드
10. RoadmapExecutionView 렌더링
```

### 8.2 로드맵 실행 (단계 진행)

```
1. /roadmap 접속 → 활성 로드맵 로드
2. RoadmapExecutionView: 타임라인 + 사이드바
3. 현재 위상의 활성 단계 확인
4. 체크리스트/서류 항목 체크박스 토글:
   └─ PATCH /roadmaps/tasks/{stepId}/actions/{actionId}
      ├─ 모든 CHECKLIST+DOCUMENT 완료 시 → 단계 자동 완료
      └─ 체크 해제 시 → 단계 COMPLETED → IN_PROGRESS 되돌림
5. 단계 수동 완료 (더블 클릭 확인):
   └─ PATCH /roadmaps/tasks/{stepId} { status: "COMPLETED" }
      └─ 다음 PENDING/BLOCKED 단계 자동 IN_PROGRESS 전환
6. 되돌리기 (마지막 완료 단계만):
   └─ PATCH /roadmaps/tasks/{stepId} { status: "IN_PROGRESS" }
      └─ 자동 진행된 다음 단계 → PENDING으로 되돌림
```

### 8.3 로드맵 관리

```
1. RoadmapSwitcher 열기 → 전체 로드맵 목록 표시
2. 로드맵 선택 → 활성 로드맵 변경 (localStorage 저장)
3. ⋯ 드롭다운:
   ├─ 이름 변경 → RoadmapRenameDialog
   │   └─ PATCH /roadmaps/{id} { title: "..." }
   └─ 삭제 → RoadmapDeleteDialog (활성 로드맵 삭제 경고)
       └─ DELETE /roadmaps/{id} (소프트 삭제)
4. "새 로드맵" → 생성 모드 전환
```

---

## 9. 핵심 비즈니스 로직

### 9.1 순차적 단계 실행 규칙

| 규칙 | 설명 |
|------|------|
| 이전 단계 완료 필수 | 앞선 모든 단계가 COMPLETED여야 IN_PROGRESS/COMPLETED 가능 |
| 되돌리기 제한 | 마지막 COMPLETED 단계만 되돌리기 가능 (이후 완료된 단계 없어야) |
| 자동 진행 | 현재 단계 완료 시 → 다음 PENDING/BLOCKED 단계 자동 IN_PROGRESS |
| 되돌리기 시 강등 | 자동 진행된 다음 단계 → PENDING으로 복귀 |
| 상태 검증 | 허용된 상태만: PENDING, IN_PROGRESS, COMPLETED, BLOCKED |

### 9.2 액션 자동 완료 로직

- 단계의 모든 `CHECKLIST` + `DOCUMENT` 액션이 `completed: true`일 때
- 해당 단계가 자동으로 `COMPLETED`로 전환
- 하나라도 체크 해제되면 `IN_PROGRESS`로 되돌림
- `LEGAL_BASIS`는 토글 대상이 아님 (참고용)

### 9.3 팀 스코프 인가

- 모든 쿼리에 `team_id` 필터 적용
- 로드맵/단계/액션 조회 시 팀 소속 확인
- 팀 내 별도 권한 레벨 없음 (전 멤버 동일 접근)

### 9.4 기본 단계 생성 (즉시 생성)

POST `/roadmaps` 시 3개의 기본 단계 자동 생성:
1. `{업종} 시장 조사`
2. `{지역} 입지 및 규제 확인`
3. `사업자 등록 및 인허가 준비`

---

## 10. 파일 맵

### 백엔드

| 파일 | 역할 |
|------|------|
| `app-backend/app/models/roadmap.py` | SQLModel DB 모델 (5개 테이블) |
| `app-backend/app/repositories/roadmap_repository.py` | 로드맵 데이터 접근 계층 |
| `app-backend/app/repositories/roadmap_job_repository.py` | 생성 작업 데이터 접근 계층 |
| `app-backend/app/features/roadmaps/application/roadmap_service.py` | 기본 CRUD 서비스 |
| `app-backend/app/features/roadmaps/application/roadmap_progress_service.py` | 진행 상태 관리 |
| `app-backend/app/features/roadmaps/application/roadmap_generation_service.py` | AI 생성 오케스트레이션 |
| `app-backend/app/features/roadmaps/application/actionkit_matcher.py` | ActionKit 벡터 검색 매칭 |
| `app-backend/app/features/roadmaps/application/llm_personalizer.py` | LLM 개인화 파이프라인 |
| `app-backend/app/features/roadmaps/application/worker_queue.py` | Redis 큐 인큐 |
| `app-backend/app/api/v1/roadmaps/router.py` | 라우터 어그리게이터 |
| `app-backend/app/api/v1/roadmaps/create.py` | 생성/목록 엔드포인트 |
| `app-backend/app/api/v1/roadmaps/get.py` | 조회/상태 변경 엔드포인트 |
| `app-backend/app/api/v1/roadmaps/jobs.py` | 비동기 작업 엔드포인트 |
| `app-backend/app/workers/roadmap_worker.py` | arq 백그라운드 워커 |
| `app-backend/app/api/v1/schemas.py` | 요청/응답 DTO 스키마 |
| `app-backend/alembic/versions/002_roadmap.py` | DB 마이그레이션 |

### 프론트엔드

| 파일 | 역할 |
|------|------|
| `app-frontend/src/app/(dashboard)/roadmap/page.tsx` | 메인 로드맵 페이지 |
| `app-frontend/src/features/roadmap/api/index.ts` | API 클라이언트 |
| `app-frontend/src/features/roadmap/types/roadmap.ts` | 기본 타입 정의 |
| `app-frontend/src/features/roadmap/types/roadmap-utils.ts` | 상세 타입 + 유틸 함수 |
| `app-frontend/src/features/roadmap/hooks/useActiveRoadmap.ts` | 활성 로드맵 관리 훅 |
| `app-frontend/src/features/roadmap/hooks/useRoadmapList.ts` | 목록 관리 훅 |
| `app-frontend/src/features/roadmap/hooks/useRoadmapJob.ts` | 비동기 작업 훅 |
| `app-frontend/src/features/roadmap/components/RoadmapExecutionView.tsx` | 실행 뷰 (메인) |
| `app-frontend/src/features/roadmap/components/RoadmapGenerationPanel.tsx` | 생성 패널 |
| `app-frontend/src/features/roadmap/components/RoadmapChatIntake.tsx` | 대화형 입력 폼 |
| `app-frontend/src/features/roadmap/components/RoadmapHeader.tsx` | 헤더 |
| `app-frontend/src/features/roadmap/components/RoadmapSwitcher.tsx` | 로드맵 전환기 |
| `app-frontend/src/features/roadmap/components/RoadmapSidebar.tsx` | 사이드바 |
| `app-frontend/src/features/roadmap/components/RoadmapEmptyHero.tsx` | 빈 상태 히어로 |
| `app-frontend/src/features/roadmap/components/RoadmapGeneratingState.tsx` | 생성 중 상태 |
| `app-frontend/src/features/roadmap/components/roadmap-utils.ts` | 상세 타입 + 유틸 함수 (정본) |
| `app-frontend/src/features/roadmap/components/TimelinePhaseCard.tsx` | 타임라인 위상 카드 |
| `app-frontend/src/features/roadmap/components/TimelineStepItem.tsx` | 타임라인 단계 아이템 |
| `app-frontend/src/features/roadmap/components/RoadmapDeleteDialog.tsx` | 삭제 다이얼로그 |
| `app-frontend/src/features/roadmap/components/RoadmapRenameDialog.tsx` | 이름 변경 다이얼로그 |
| `app-frontend/src/features/roadmap/components/roadmap-constants.ts` | 상수/레이블 정의 |
| `app-frontend/src/features/dashboard/components/RoadmapStepper.tsx` | 대시보드 타임라인 |
| `app-frontend/src/lib/api-types.ts` (423~535) | 로드맵 API 타입 정의 |

---

*이 보고서는 프로젝트의 로드맵 기능 전체를 커버하며, 데이터베이스 스키마부터 AI 생성 파이프라인, API 설계, 프론트엔드 UI까지 모든 계층을 포함합니다.*
