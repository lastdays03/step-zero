# 로드맵 템플릿 관리 시스템 구현 계획

## Context

현재 StepZero의 로드맵 생성은 매번 LLM(gpt-4o-mini)을 호출하여 비결정적 결과를 생성한다. 동일한 업종(예: 카페)에 대해 매번 다른 품질의 로드맵이 생성되며, 운영자가 품질을 사전 검수하거나 일관성을 보장할 방법이 없다.

**목표**: `business_type × startup_method` 조합(최대 24개)으로 템플릿을 관리하여, 승인된 템플릿이 있으면 LLM 호출 없이 즉시 로드맵을 생성하고, 없으면 기존 파이프라인으로 생성 후 자동으로 DRAFT 템플릿을 등록한다.

**추가 수정**: 프론트엔드 startup_type("개인사업자/법인/미정")과 백엔드 LLM 프롬프트("신규/양수양도/프랜차이즈")의 어휘 불일치를 수정하여 `startup_method` 필드를 새로 분리한다.

---

## Group 1: DB 스키마 & 마이그레이션

### 1-1. 새 모델 3개 생성

**파일**: `app-backend/app/models/roadmap_template.py` (신규)

```python
class RoadmapTemplate(SQLModel, table=True):
    __tablename__ = "roadmap_templates"
    id: int (PK, auto)
    business_type: str (index)
    startup_method: str | None (index)  # "신규"|"양수양도"|"프랜차이즈"|None(공통)
    title: str
    status: str = "DRAFT"  # DRAFT → REVIEW → APPROVED → ARCHIVED
    version: int = 1
    source_roadmap_id: UUID | None (FK → roadmap.id)
    created_by: int | None (FK → user.id)
    approved_by: int | None (FK → user.id)
    approved_at: datetime | None
    created_at, updated_at: datetime

class RoadmapTemplateStep(SQLModel, table=True):
    __tablename__ = "roadmap_template_steps"
    id: int (PK, auto)
    template_id: int (FK → roadmap_templates.id, index)
    step_order: int
    title: str
    phase: str
    objective: str
    estimated_days: int
    risk_notes: list[str] (JSON)

class RoadmapTemplateAction(SQLModel, table=True):
    __tablename__ = "roadmap_template_actions"
    id: int (PK, auto)
    template_step_id: int (FK → roadmap_template_steps.id, index)
    action_type: str  # CHECKLIST | LEGAL_BASIS | DOCUMENT
    title: str
    description: str
    source_url: str | None
    metadata_json: dict (JSON)
```

### 1-2. 기존 Roadmap 모델 수정

**파일**: `app-backend/app/models/roadmap.py`

- `Roadmap` 테이블에 컬럼 추가:
  - `template_id: int | None = Field(default=None, foreign_key="roadmap_templates.id")`
  - `startup_method: str | None = None`

### 1-3. Alembic 마이그레이션

**파일**: `app-backend/alembic/versions/009_roadmap_templates.py` (신규)

- `down_revision = "008_feature_merge"`
- 3개 테이블 CREATE + roadmap 테이블 ALTER (template_id, startup_method 컬럼)
- `(business_type, startup_method, status)` 복합 인덱스

---

## Group 2: 백엔드 템플릿 CRUD 서비스

### 2-1. 감사로그 상수 추가

**파일**: `app-backend/app/features/ops/application/audit_logs/constants.py`

AuditAction에 추가:
- `TEMPLATE_CREATED`, `TEMPLATE_UPDATED`, `TEMPLATE_STATUS_CHANGED`
- `TEMPLATE_APPROVED`, `TEMPLATE_ARCHIVED`, `TEMPLATE_DELETED`

AuditTargetType에 추가:
- `ROADMAP_TEMPLATE = "ROADMAP_TEMPLATE"`

ALLOWED 셋에도 각각 추가.

### 2-2. 서비스 레이어

**파일**: `app-backend/app/features/ops/application/roadmap_templates.py` (신규)

기존 `app/features/ops/application/actionkit.py` 패턴 참조. 주요 함수:

```
get_template_summary(session) → dict  # 전체/DRAFT/APPROVED 통계
get_templates(session, status?, business_type?) → list  # 필터링 목록
get_template_detail(session, template_id) → dict  # steps + actions 포함
create_template_from_roadmap(session, roadmap_id, user_id) → template  # 기존 로드맵에서 복제
update_template(session, template_id, data) → template
update_template_status(session, template_id, new_status, user_id, reason?) → template
delete_template(session, template_id) → bool
update_template_step(session, step_id, data) → step
create_template_action(session, step_id, data) → action
update_template_action(session, action_id, data) → action
delete_template_action(session, action_id) → bool
```

`create_template_from_roadmap`: Roadmap + RoadmapStep + RoadmapStepDetail + RoadmapStepAction → RoadmapTemplate + TemplateStep + TemplateAction로 데이터 복사.

### 2-3. API 스키마

**파일**: `app-backend/app/api/v1/ops/schemas.py` (기존 파일에 추가)

- `RoadmapTemplateResponse`, `RoadmapTemplateListResponse`
- `RoadmapTemplateCreateFromRoadmapRequest` (roadmap_id: UUID)
- `RoadmapTemplateUpdateRequest` (title?, business_type?, startup_method?)
- `RoadmapTemplateStatusUpdateRequest` (status: str, reason?: str)
- `RoadmapTemplateStepResponse`, `RoadmapTemplateStepUpdateRequest`
- `RoadmapTemplateActionResponse`, `RoadmapTemplateActionCreateRequest`, `RoadmapTemplateActionUpdateRequest`

### 2-4. API 라우터

**파일**: `app-backend/app/api/v1/ops/roadmap_templates.py` (신규)

`router = APIRouter(prefix="/roadmap-templates", tags=["ops-roadmap-templates"])`

엔드포인트:
- `GET /summary` → 통계
- `GET /` → 목록 (query: status, business_type)
- `GET /{template_id}` → 상세 (steps + actions)
- `POST /from-roadmap` → 로드맵에서 템플릿 생성
- `PATCH /{template_id}` → 기본 정보 수정
- `PATCH /{template_id}/status` → 상태 변경 (+ 감사로그)
- `DELETE /{template_id}` → 삭제
- `PATCH /steps/{step_id}` → 스텝 수정
- `POST /steps/{step_id}/actions` → 액션 추가
- `PATCH /actions/{action_id}` → 액션 수정
- `DELETE /actions/{action_id}` → 액션 삭제

### 2-5. 라우터 등록

**파일**: `app-backend/app/api/v1/ops/router.py`

- `from app.api.v1.ops import roadmap_templates` 추가
- `router.include_router(roadmap_templates.router)` 추가

---

## Group 3: 파이프라인 통합

### 3-1. TemplateResolver

**파일**: `app-backend/app/features/roadmaps/application/template_resolver.py` (신규)

```python
class TemplateResolver:
    async def resolve(session, business_type, startup_method) -> RoadmapTemplate | None:
        # 1순위: business_type + startup_method 정확 매치 (APPROVED만)
        # 2순위: business_type + startup_method=NULL (공통 템플릿, APPROVED만)
        # 3순위: None (기존 파이프라인으로 폴백)

    async def template_to_steps_payload(template) -> list[dict]:
        # RoadmapTemplate → RoadmapRepository.create_steps_with_details()에 맞는 형식 변환
        # generation_mode = "TEMPLATE", mapping_source = f"template:{template.id}"
```

### 3-2. 자동 DRAFT 등록

**파일**: `app-backend/app/features/roadmaps/application/roadmap_generation_service.py`

`process_job()` 메서드 수정:

```
기존 흐름:
  ActionKitMatcher → LLMPersonalizer → RoadmapRepository.create

수정 흐름:
  1. TemplateResolver.resolve(business_type, startup_method)
  2-A. 템플릿 있음 → template_to_steps_payload() → RoadmapRepository.create (template_id 포함)
  2-B. 템플릿 없음 → 기존 파이프라인 실행 → RoadmapRepository.create
       → 자동 DRAFT 등록: create_template_from_roadmap(new_roadmap_id)
```

- `GenerationPayload` dataclass에 `startup_method: str | None = None` 추가
- `_build_generation_payload()`에서 `input_payload["startup_method"]` 읽기
- 템플릿 사용 시 stage를 `TEMPLATE_MATCH` → `BUILDING` → `DONE`으로 진행

### 3-3. RoadmapRepository 수정

**파일**: `app-backend/app/repositories/roadmap_repository.py`

- `create_roadmap()` 파라미터에 `template_id: int | None = None`, `startup_method: str | None = None` 추가
- Roadmap 생성 시 해당 필드 설정

---

## Group 4: startup_type / startup_method 어휘 수정

### 4-1. 프론트엔드 인테이크 폼

**파일**: `app-frontend/src/features/roadmap/components/roadmap-constants.ts`

`INTAKE_FIELD_SUGGESTIONS`에 추가:
```typescript
startup_method: ["신규 창업", "양수양도", "프랜차이즈"],
```

**파일**: `app-frontend/src/features/roadmap/components/RoadmapChatIntake.tsx`

- `FieldKey` 타입에 `"startup_method"` 추가
- `RoadmapRawInput` 인터페이스에 `startup_method: string` 추가
- `RoadmapIntakePayload` 인터페이스에 `startup_method: string` 추가
- `QUESTIONS` 배열에 startup_method 질문 추가 (기존 startup_type 질문 뒤에):
  ```
  { key: "startup_method", label: "창업 방식을 알려주세요 (신규/양수양도/프랜차이즈)" }
  ```
- `PANEL_ROWS`에 `startup_method` 항목 추가
- 기존 startup_type 질문 라벨을 명확하게 수정: "사업자 형태" 관련으로

**파일**: `app-frontend/src/features/roadmap/components/RoadmapGenerationPanel.tsx`

- `handleValidateInput()`에서 `startup_method: input.startup_method.trim()` 추가
- 요약 문자열에 startup_method 표시

**파일**: `app-frontend/src/features/roadmap/hooks/useRoadmapJob.ts`

- `RoadmapIntakePayload` 인터페이스에 `startup_method: string` 추가

### 4-2. 백엔드 페이로드

**파일**: `app-backend/app/features/roadmaps/application/roadmap_generation_service.py`

- `GenerationPayload.startup_method` 필드 (Group 3에서 이미 추가)
- `_build_generation_payload()`: `input_payload`에서 `startup_method` 읽기

**파일**: `app-backend/app/features/roadmaps/application/llm_personalizer.py`

- `_USER_PROMPT_TEMPLATE`에 `{startup_method}` 플레이스홀더 추가
- `personalize()` 호출 시 `startup_method` 전달
- `_SYSTEM_PROMPT`의 "신규/양수양도/프랜차이즈" 설명을 startup_method 기준으로 정리

---

## Group 5: 프론트엔드 관리자 UI

### 5-1. 디렉토리 구조

```
app-frontend/src/features/ops/roadmap-templates/
├── index.ts
├── view.tsx                    # 메인 목록 뷰
├── template-detail-view.tsx    # 상세/편집 뷰
├── api.ts                      # API 호출 함수
├── types.ts                    # 타입 정의
└── components/
    ├── template-list-table.tsx  # 템플릿 목록 테이블
    ├── template-status-badge.tsx # 상태 뱃지
    ├── template-step-editor.tsx  # 스텝 편집기
    └── template-action-editor.tsx # 액션 편집기
```

### 5-2. 운영 홈 카드 추가

**파일**: `app-frontend/src/features/ops/home/view.tsx`

기존 6개 카드 그리드에 7번째 카드 추가:
```
제목: "로드맵 템플릿 관리"
설명: "업종별 로드맵 템플릿 검수 및 승인 운영"
링크: /ops/roadmap-templates
```

### 5-3. 라우트 페이지

**파일**: `app-frontend/src/app/(dashboard)/ops/roadmap-templates/page.tsx` (신규)
**파일**: `app-frontend/src/app/(dashboard)/ops/roadmap-templates/[templateId]/page.tsx` (신규)

### 5-4. ops index 등록

**파일**: `app-frontend/src/features/ops/index.ts`

`export * from "./roadmap-templates"` 추가

### 5-5. 주요 UI 기능

**목록 뷰**:
- 통계 카드 (전체/DRAFT/REVIEW/APPROVED)
- 필터 (status, business_type)
- 테이블: 업종, 창업방식, 제목, 상태, 버전, 생성일, 액션버튼

**상세 뷰**:
- 템플릿 기본 정보 편집 (title, business_type, startup_method)
- 상태 변경 버튼 (DRAFT→REVIEW→APPROVED, ARCHIVED)
- 스텝 목록 (아코디언): 각 스텝의 phase, title, objective, estimated_days, risk_notes 편집
- 각 스텝 내 액션 목록: action_type별 CRUD

---

## Group 6: 테스트

### 6-1. 백엔드 테스트

**파일**: `app-backend/tests/api/test_ops_roadmap_templates.py` (신규)

- 템플릿 CRUD API 테스트 (생성, 조회, 수정, 상태변경, 삭제)
- 권한 검증 (비관리자 접근 차단)

**파일**: `app-backend/tests/services/test_template_resolver.py` (신규)

- 정확 매치 / 공통 폴백 / 미매치 시나리오
- 자동 DRAFT 등록 검증

### 6-2. 프론트엔드 테스트

**파일**: `app-frontend/src/features/ops/roadmap-templates/__tests__/` (신규)

- 목록 뷰 렌더링 테스트
- startup_method 인테이크 필드 추가 검증

---

## Group 7: 문서 업데이트

- `docs/context/dev-status.md` 업데이트
- `docs/context/handoff.md` 업데이트

---

## 구현 순서

1. **Group 1** (DB) → 나머지 모든 그룹의 선행 조건
2. **Group 4** (startup_method 수정) → Group 3 파이프라인에서 사용
3. **Group 2** (백엔드 CRUD) → Group 5 프론트엔드 UI에서 호출
4. **Group 3** (파이프라인 통합) → Group 2 서비스 함수 활용
5. **Group 5** (프론트엔드 UI) → Group 2 API 의존
6. **Group 6** (테스트) → 전체 구현 후
7. **Group 7** (문서) → 최종

## 검증 방법

1. `cd app-backend && make migrate-up` → 009 마이그레이션 적용 확인
2. `cd app-backend && make test` → 새 테스트 포함 전체 통과
3. `cd app-frontend && npm run lint` → 린트 통과
4. `cd app-frontend && npm run build` → 빌드 성공
5. Docker Compose로 전체 스택 실행 후:
   - 인테이크 폼에서 startup_method 질문 표시 확인
   - 로드맵 생성 → 자동 DRAFT 템플릿 등록 확인
   - Ops 콘솔에서 템플릿 목록/상세/상태변경/편집 확인
   - APPROVED 템플릿 존재 시 LLM 호출 없이 로드맵 생성 확인
