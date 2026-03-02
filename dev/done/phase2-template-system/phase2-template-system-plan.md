# Phase 2: 로드맵 템플릿 관리 시스템 — 구현 계획

> Last Updated: 2026-03-02
> Branch: `feature/2-template-system`
> Base: `develop`

---

## 1. Executive Summary

### 문제

현재 로드맵 생성은 **매 요청마다 LLM을 전면 호출**하여 비결정적 결과를 생성한다.
- 동일 업종(카페)으로 요청해도 체크리스트 문구, 순서, 일수, 위험사항이 매번 달라짐
- 운영자가 사전 품질 검수 불가능
- LLM API 비용 과다 ($0.02/건)
- 응답 시간 15-25초

### 해결

`business_type` 기반 **템플릿 관리 시스템**을 구축하여:
1. 승인된 템플릿(APPROVED) → LLM 호출 없이 즉시 로드맵 생성
2. 미등록 업종 → 기존 파이프라인 + **자동 DRAFT 템플릿 등록**
3. 운영자가 Ops UI에서 검수/승인/관리

### 기대 효과

| 지표 | Before | After | 개선 |
|------|--------|-------|:----:|
| 동일 업종 생성 시간 | 15-25초 | 5-10초 | -50~60% |
| LLM 비용/건 | $0.02 | $0.008 | -60% |
| 법적근거 정확도 | LLM 의존 | 검수된 데이터 | 향상 |
| 링크 오류율 | 5-10% | <1% | 대폭 감소 |

---

## 2. Current State Analysis

### 2.1 이미 완료된 선행 작업 (Phase 0)

- `startup_method` 컬럼: Roadmap 모델에 이미 추가됨 (마이그레이션 009)
- `startup_method` API 스키마: 이미 반영됨
- `RoadmapRepository.create_roadmap()`: 이미 `startup_method` 파라미터 수용
- 링크 오류 수정: source_url item_id 기반 통일 완료
- 프론트엔드 인테이크: `startup_method` 필드 이미 추가됨

### 2.2 현재 파이프라인 흐름

```
POST /api/v1/roadmaps/jobs → RoadmapGenerationService.process_job()
  ├── validate_generation_input() (LLM 정규화)
  ├── ActionKitMatcher.match() (벡터 검색)
  ├── LLMPersonalizer.personalize() (전면 LLM 호출)
  └── RoadmapRepository.create_steps_with_details() (DB 저장)
```

### 2.3 기존 Ops 패턴 (재활용 대상)

- **서비스**: `features/ops/application/actionkit/service.py` — CRUD + 감사로그
- **API**: `api/v1/ops/actionkit.py` — RESTful CRUD + 상태 변경 + 감사로그
- **라우터 등록**: `api/v1/ops/router.py` — `router.include_router(module.router)`
- **감사로그**: `AuditAction`, `AuditTargetType` 상수 + `record_admin_audit_log()`
- **인증**: `require_platform_admin` dependency (ops router 전체 적용)

---

## 3. Proposed Future State

### 3.1 수정된 파이프라인 흐름

```
POST /api/v1/roadmaps/jobs → RoadmapGenerationService.process_job()
  ├── validate_generation_input() (LLM 정규화)
  ├── ★ TemplateResolver.resolve(business_type, startup_method)
  │
  ├─[APPROVED 템플릿 있음]──→ template_to_steps_payload()
  │                              → 법적근거/서류 그대로 사용
  │                              → LLM 개인화: 체크리스트/일수/목표만
  │                              → create_steps(generation_mode="TEMPLATE")
  │                              → Roadmap.template_id 기록
  │
  └─[템플릿 없음]──→ 기존 파이프라인
                       → ActionKitMatcher + LLMPersonalizer
                       → create_steps(generation_mode="ACTIONKIT_RAG")
                       → ★ 자동 DRAFT 템플릿 등록
```

### 3.2 DB 스키마 확장

```
[기존]                           [신규]
Roadmap ◀──template_id──────── RoadmapTemplate
  └── RoadmapStep                 └── RoadmapTemplateStep
        └── RoadmapStepDetail           └── RoadmapTemplateAction
              └── RoadmapStepAction
```

### 3.3 Ops 관리 UI

```
/ops 홈 (7번째 카드 추가)
  └── /ops/roadmap-templates (목록)
        ├── 통계 카드 (전체/DRAFT/REVIEW/APPROVED)
        ├── 필터 (status, business_type)
        ├── 테이블 (목록)
        └── /ops/roadmap-templates/[id] (상세)
              ├── 메타 편집 (title, business_type)
              ├── 상태 변경 (DRAFT→REVIEW→APPROVED)
              ├── 스텝 아코디언 (phase, title, objective, days, risks)
              └── 액션 CRUD (action_type별)
```

---

## 4. Implementation Phases

### Phase 2 전체 구성: 7개 Group, 4개 Section

| Section | Group | 내용 | 예상 공수 | 의존성 |
|:-------:|:-----:|------|:--------:|:------:|
| A | G1 | DB 스키마 + 마이그레이션 | 1일 | 없음 |
| A | G4 | 감사로그 상수 추가 | 0.5일 | 없음 |
| B | G2 | 백엔드 CRUD 서비스 + API | 3일 | G1, G4 |
| B | G3 | 파이프라인 통합 (TemplateResolver) | 3일 | G1 |
| C | G5 | 프론트엔드 관리자 UI | 3일 | G2 API |
| D | G6 | 테스트 | 1.5일 | G2, G3 |
| D | G7 | 문서 업데이트 | 0.5일 | 전체 |

**총 예상 공수: ~12.5일 (약 2.5주)**

---

## 5. Section A: DB + 감사로그 상수 (1.5일)

### 5.1 Group 1: DB 스키마 + 마이그레이션

#### Task 1-1: 템플릿 모델 3개 생성

**파일**: `app-backend/app/models/roadmap_template.py` (신규)

```python
class RoadmapTemplate(SQLModel, table=True):
    __tablename__ = "roadmap_templates"

    id: int (PK, auto)
    business_type: str (index)          # Phase 1 매칭 키
    startup_method: str | None (index)  # Phase 2 확장용 (null = 공통)
    title: str
    status: str = "DRAFT"               # DRAFT → REVIEW → APPROVED → ARCHIVED
    version: int = 1
    source_roadmap_id: UUID | None (FK → roadmap.id)
    created_by: int (FK → user.id)
    approved_by: int | None (FK → user.id)
    approved_at: datetime | None
    created_at, updated_at: datetime

class RoadmapTemplateStep(SQLModel, table=True):
    __tablename__ = "roadmap_template_steps"

    id: int (PK, auto)
    template_id: int (FK → roadmap_templates.id, index, cascade)
    step_order: int
    phase: str
    title: str
    objective: str = ""
    estimated_days: int = 0
    risk_notes: list[str] = [] (JSON)
    created_at: datetime

class RoadmapTemplateAction(SQLModel, table=True):
    __tablename__ = "roadmap_template_actions"

    id: int (PK, auto)
    template_step_id: int (FK → roadmap_template_steps.id, index, cascade)
    action_type: str (index)            # CHECKLIST | LEGAL_BASIS | DOCUMENT
    title: str
    description: str = ""
    source_url: str | None
    actionkit_item_id: int | None (FK → actionkititem.id)
    actionkit_file_id: int | None (FK → actionkitfile.id)
    sort_order: int = 0
    metadata_json: dict = {} (JSON)
    created_at: datetime
```

**수용 기준**:
- SQLModel + table=True 패턴 준수
- datetime 패턴: `datetime.now(timezone.utc).replace(tzinfo=None)`
- JSON 필드: `sa.Column(sa.JSON, nullable=False)`
- FK cascade: ondelete="CASCADE"

#### Task 1-2: Roadmap 모델에 template_id FK 추가

**파일**: `app-backend/app/models/roadmap.py` (수정)

```python
# Roadmap 클래스에 추가
template_id: int | None = Field(default=None, foreign_key="roadmap_templates.id", index=True)
```

#### Task 1-3: __init__.py 모델 등록

**파일**: `app-backend/app/models/__init__.py` (수정)

- `RoadmapTemplate`, `RoadmapTemplateStep`, `RoadmapTemplateAction` import + __all__ 추가

#### Task 1-4: Alembic 마이그레이션

**파일**: `app-backend/alembic/versions/010_roadmap_templates.py` (신규)

```python
revision = "010_roadmap_templates"
down_revision = "009_startup_method"  # 정확한 revision ID 확인 필요

def upgrade():
    # 1. roadmap_templates 테이블 생성
    # 2. roadmap_template_steps 테이블 생성 (FK CASCADE)
    # 3. roadmap_template_actions 테이블 생성 (FK CASCADE)
    # 4. roadmap 테이블에 template_id 컬럼 추가 (nullable)
    # 5. 복합 인덱스: (business_type, startup_method, status)

def downgrade():
    # 역순 삭제
```

**수용 기준**:
- `make migrate-up` 성공
- `make migrate-verify` 모델 ↔ DB 스키마 diff 없음
- `make test` 통과 (SQLite 호환 확인)

### 5.2 Group 4: 감사로그 상수 추가

**파일**: `app-backend/app/features/ops/application/audit_logs/constants.py` (수정)

```python
# AuditAction에 추가:
TEMPLATE_CREATED = "template.created"
TEMPLATE_UPDATED = "template.updated"
TEMPLATE_STATUS_CHANGED = "template.status.changed"
TEMPLATE_APPROVED = "template.approved"
TEMPLATE_ARCHIVED = "template.archived"
TEMPLATE_DELETED = "template.deleted"

# AuditTargetType에 추가:
ROADMAP_TEMPLATE = "roadmap_template"

# ALLOWED_AUDIT_ACTIONS, ALLOWED_AUDIT_TARGET_TYPES 셋에 추가
```

**수용 기준**: 기존 테스트 통과, 상수 값 중복 없음

---

## 6. Section B: 백엔드 서비스 + 파이프라인 (6일)

### 6.1 Group 2: CRUD 서비스 + API (3일)

#### Task 2-1: 서비스 레이어

**파일**: `app-backend/app/features/ops/application/roadmap_templates/service.py` (신규)

8개 핵심 함수:
1. `get_template_summary(session)` → dict (통계)
2. `list_templates(session, *, status, business_type)` → list
3. `get_template_detail(session, template_id)` → RoadmapTemplate + steps + actions
4. `create_template_from_roadmap(session, *, roadmap_id, user_id)` → RoadmapTemplate
5. `update_template(session, template_id, data)` → RoadmapTemplate
6. `update_template_status(session, template_id, *, new_status, admin_id, reason)` → RoadmapTemplate
7. `create_template_action(session, step_id, data)` → RoadmapTemplateAction
8. `update_template_action(session, action_id, data)` → RoadmapTemplateAction
9. `delete_template_action(session, action_id)` → bool
10. `delete_template(session, template_id)` → bool

**핵심 로직 — `create_template_from_roadmap()`**:
```python
# 1. Roadmap + Steps + Details + Actions 조회
# 2. RoadmapTemplate 생성 (status=DRAFT, source_roadmap_id=roadmap.id)
# 3. 각 Step → RoadmapTemplateStep 복사 (phase, title, objective, estimated_days, risk_notes)
# 4. 각 Action → RoadmapTemplateAction 복사 (action_type, title, description, source_url, metadata)
# 5. 감사로그 기록 (TEMPLATE_CREATED)
```

**핵심 로직 — `update_template_status()`**:
```python
# 상태 전이 규칙:
# DRAFT → REVIEW → APPROVED → ARCHIVED
# REVIEW → DRAFT (반려)
# APPROVED → ARCHIVED만 허용 (수정 불가, 새 버전 생성 필요)
# ARCHIVED → (종료 상태)
```

**패턴**: `features/ops/application/actionkit/service.py` 그대로 재현
- AsyncSession 직접 사용 (DI 패턴)
- `session.add()` → `session.commit()` → `session.refresh()`

#### Task 2-2: API 스키마 정의

**파일**: `app-backend/app/api/v1/ops/schemas/roadmap_templates.py` (신규) 또는 기존 `schemas.py` 확장

요청/응답 스키마:
- `RoadmapTemplateResponse` (목록/상세용)
- `RoadmapTemplateDetailResponse` (steps + actions 포함)
- `RoadmapTemplateStatusUpdateRequest` (new_status, reason)
- `RoadmapTemplateActionCreateRequest` / `UpdateRequest`
- `RoadmapTemplateSummaryResponse`

#### Task 2-3: API 라우터

**파일**: `app-backend/app/api/v1/ops/roadmap_templates.py` (신규)

10개 엔드포인트:
```
router = APIRouter(prefix="/roadmap-templates", tags=["ops-roadmap-templates"])

GET    /summary                              → 통계
GET    /                                     → 목록 (필터: status, business_type)
GET    /{template_id}                        → 상세 (steps + actions)
POST   /from-roadmap                         → 기존 로드맵에서 생성
PATCH  /{template_id}                        → 메타 수정
PATCH  /{template_id}/status                 → 상태 변경 (감사로그)
DELETE /{template_id}                        → 삭제
POST   /{template_id}/steps/{step_id}/actions    → 액션 추가
PATCH  /{template_id}/steps/{step_id}/actions/{action_id} → 액션 수정
DELETE /{template_id}/steps/{step_id}/actions/{action_id} → 액션 삭제
```

#### Task 2-4: 라우터 등록

**파일**: `app-backend/app/api/v1/ops/router.py` (수정)

```python
from app.api.v1.ops import roadmap_templates
router.include_router(roadmap_templates.router)
```

**수용 기준**:
- `make test` 통과
- Swagger UI에서 10개 엔드포인트 확인
- 비관리자 접근 시 403

### 6.2 Group 3: 파이프라인 통합 (3일)

#### Task 3-1: TemplateResolver 구현

**파일**: `app-backend/app/features/roadmaps/application/template_resolver.py` (신규)

```python
class TemplateResolver:
    """APPROVED 템플릿 매칭 + payload 변환"""

    @staticmethod
    async def resolve(
        session: AsyncSession,
        *,
        business_type: str,
        startup_method: str | None = None,
    ) -> RoadmapTemplate | None:
        """
        매칭 우선순위:
        1. business_type + startup_method 정확 일치 (APPROVED)
        2. business_type + startup_method=null 공통 (APPROVED)
        3. None (기존 파이프라인)
        """

    @staticmethod
    async def template_to_steps_payload(
        session: AsyncSession,
        template: RoadmapTemplate,
    ) -> list[dict]:
        """
        RoadmapTemplate → RoadmapRepository.create_steps_with_details() 호환 형식.

        steps_payload 구조:
        [
          {
            "title": "입지 검토",
            "phase": "준비",
            "objective": "...",
            "estimated_days": 7,
            "risk_notes": ["위험1"],
            "mapping_source": "template",
            "checklist": [{"title": "...", "actionkit_item_id": 1, "mapping_source": "template"}],
            "legal_basis": [...],
            "documents": [...],
          }
        ]
        """
```

#### Task 3-2: RoadmapGenerationService 수정

**파일**: `app-backend/app/features/roadmaps/application/roadmap_generation_service.py` (수정)

변경 사항:
1. `process_job()`에 `TemplateResolver.resolve()` 호출 추가
2. 템플릿 있으면 → `template_to_steps_payload()` 사용
3. 템플릿 없으면 → 기존 파이프라인 + `create_template_from_roadmap()` 호출
4. `Roadmap.template_id` 설정
5. `generation_mode` → "TEMPLATE" 또는 "ACTIONKIT_RAG"

**중요 원칙**:
- 템플릿 미발견 시 기존 파이프라인 100% 호환 유지
- 자동 DRAFT: 동일 `business_type`에 기존 DRAFT/REVIEW/APPROVED 없을 때만

#### Task 3-3: LLMPersonalizer 경량 모드 (선택)

**파일**: `app-backend/app/features/roadmaps/application/llm_personalizer.py` (수정)

템플릿 모드일 때:
- 법적근거/서류: LLM 스킵 (템플릿 데이터 그대로)
- 체크리스트 순서/필터링 + estimated_days + objective만 LLM 호출
- 프롬프트 크기 60% 축소

**참고**: Phase 2 MVP에서는 이 단계를 생략하고, 템플릿 데이터를 그대로 사용해도 된다.
LLM 개인화는 Phase 2.5에서 추가 구현 가능.

#### Task 3-4: RoadmapRepository 수정

**파일**: `app-backend/app/repositories/roadmap_repository.py` (수정)

- `create_roadmap()`: `template_id` 파라미터 이미 존재하지만 모델에 반영 필요
- `create_steps_with_details()`: `generation_mode="TEMPLATE"` 지원 확인

**수용 기준**:
- 템플릿 없는 기존 경로 100% 호환
- `make test` 통과
- 자동 DRAFT 중복 등록 방지 확인

---

## 7. Section C: 프론트엔드 관리자 UI (3일)

### 7.1 Group 5: Ops 템플릿 관리 UI

#### Task 5-1: 디렉토리 구조 + 타입 + API

**파일 구조**:
```
app-frontend/src/features/ops/roadmap-templates/
├── index.ts                          # Public export
├── view.tsx                          # 목록 뷰
├── template-detail-view.tsx          # 상세/편집 뷰
├── api.ts                            # API 호출 함수
├── types.ts                          # 타입 정의
└── components/
    ├── template-list-table.tsx       # 목록 테이블
    ├── template-status-badge.tsx     # 상태 뱃지 (DRAFT/REVIEW/APPROVED/ARCHIVED)
    ├── template-step-editor.tsx      # 스텝 편집기 (아코디언)
    └── template-action-editor.tsx    # 액션 편집기
```

#### Task 5-2: Ops 홈 카드 추가

**파일**: `app-frontend/src/features/ops/home/view.tsx` (수정)

```tsx
// 7번째 카드:
{
  title: "로드맵 템플릿 관리",
  description: "업종별 로드맵 템플릿 검수 및 승인",
  href: "/ops/roadmap-templates",
  icon: FileStack,  // lucide-react
}
```

#### Task 5-3: 라우트 페이지

- `app/(dashboard)/ops/roadmap-templates/page.tsx` (신규)
- `app/(dashboard)/ops/roadmap-templates/[templateId]/page.tsx` (신규)

#### Task 5-4: 목록 뷰

- 통계 카드 (전체/DRAFT/REVIEW/APPROVED 수)
- 필터 (status 드롭다운, business_type 드롭다운)
- 테이블: 업종, 제목, 상태 배지, 버전, 사용 횟수, 생성일, 액션 버튼

#### Task 5-5: 상세/편집 뷰

- 템플릿 메타 편집 (title, business_type)
- 상태 변경 버튼 (DRAFT→REVIEW→APPROVED 워크플로우)
- 스텝 아코디언: phase, title, objective, estimated_days, risk_notes
- 각 스텝 내 액션 CRUD (action_type별 정렬)

#### Task 5-6: ops/index.ts 등록

**파일**: `app-frontend/src/features/ops/index.ts` (수정)

```tsx
export { default as OpsRoadmapTemplatesView } from "./roadmap-templates";
```

**수용 기준**:
- `npm run lint` 통과
- `npm run build` 성공
- Ops 콘솔에서 CRUD 동작 확인

---

## 8. Section D: 테스트 + 문서 (2일)

### 8.1 Group 6: 테스트

#### 백엔드 테스트

**파일**: `app-backend/tests/api/test_ops_roadmap_templates.py` (신규)

테스트 시나리오:
- 템플릿 CRUD (생성, 조회, 수정, 상태변경, 삭제)
- 권한 검증 (비관리자 접근 → 403)
- 상태 전이 규칙 검증 (유효/무효 전이)

**파일**: `app-backend/tests/services/test_template_resolver.py` (신규)

테스트 시나리오:
- 정확 매치 (business_type + startup_method)
- 공통 폴백 (startup_method=null)
- 미매치 → None 반환
- 자동 DRAFT 중복 방지

#### 프론트엔드 테스트

**파일**: `app-frontend/src/features/ops/roadmap-templates/__tests__/` (신규)

- 목록 뷰 렌더링 테스트
- 상태 배지 렌더링 테스트

### 8.2 Group 7: 문서 업데이트

- `docs/context/dev-status.md` — Phase 2 완료 상태 반영
- `docs/context/handoff.md` — 세션 핸드오프 요약

---

## 9. 설계 결정 사항

### 9.1 확정 결정

| # | 항목 | 결정 | 근거 |
|---|------|:----:|------|
| 1 | Phase 1 매칭 키 | `business_type`만 | 8개 업종 충분, `startup_method`는 Phase 2.5 |
| 2 | 자동 DRAFT 조건 | 업종 최초 생성 시만 | 동일 업종 중복 DRAFT 방지 |
| 3 | 버전 관리 | 새 버전 레코드 생성 | 이전 버전 보존 |
| 4 | APPROVED 수정 | 새 버전으로만 | 운영 중 템플릿 보호 |
| 5 | TemplateResolver 위치 | `features/roadmaps/application/` | 파이프라인의 일부 |
| 6 | 서비스 위치 | `features/ops/application/roadmap_templates/` | Ops 도메인 |
| 7 | 감사로그 | 상태 변경만 기록 | 기존 패턴 준수 |
| 8 | LLM 개인화 범위 (MVP) | 템플릿 있으면 LLM 스킵 | 단순성 우선, 2.5에서 확장 |

### 9.2 미결정 (구현 중 결정)

| # | 항목 | 선택지 | 권장 |
|---|------|--------|:----:|
| 1 | 템플릿 목록 페이지네이션 | 무한스크롤 vs 페이지 | 페이지 (최대 24개) |
| 2 | 스텝 편집 시 액션 벌크 수정 | 개별 vs 벌크 API | 개별 (MVP) |
| 3 | 시드 데이터 | 부트스트랩 스크립트 vs 수동 | 수동 (Ops UI 사용) |

---

## 10. Risk Assessment

| 리스크 | 영향 | 확률 | 완화 전략 |
|--------|:----:|:----:|----------|
| 마이그레이션 SQLite 테스트 호환 | ★★★ | 중 | JSON 필드 SQLite 호환 확인, conftest 수정 필요 시 |
| 기존 파이프라인 regression | ★★★★ | 낮 | 템플릿=None일 때 기존 경로 100% 호환 테스트 |
| Ops UI 공수 초과 | ★★ | 중 | ActionKit UI 패턴 최대 재활용, MVP 범위 유지 |
| startup_method 정규화 불일치 | ★★ | 낮 | Phase 0에서 이미 추가됨, 기존 데이터 null 허용 |
| 자동 DRAFT 무한 증식 | ★★★ | 중 | 중복 체크 로직 필수 (business_type 기준) |

---

## 11. 구현 순서 요약

```
Day 1-2:   Section A (G1: DB + G4: 감사로그)
Day 2-4:   Section B-1 (G2: CRUD 서비스 + API)
Day 4-6:   Section B-2 (G3: 파이프라인 통합)
Day 7-9:   Section C (G5: 프론트엔드 UI)
Day 10-11: Section D (G6: 테스트 + G7: 문서)
Day 12:    QA + 커밋 + PR
```

**병렬화**: G2(BE CRUD)와 G3(파이프라인)은 G1(DB) 완료 후 병렬 가능

---

## 12. Quality Gates

```bash
# 백엔드
cd app-backend && make migrate-up        # 010 마이그레이션 적용
cd app-backend && make migrate-verify    # 모델 ↔ DB diff 없음
cd app-backend && .venv/bin/pytest -q    # 전체 테스트 통과

# 프론트엔드
cd app-frontend && npm run lint          # ESLint 통과
cd app-frontend && npm run build         # 빌드 성공
cd app-frontend && npm test              # Jest 통과

# 통합
# Ops 콘솔에서 템플릿 CRUD 동작 확인
# 로드맵 생성 → 자동 DRAFT 등록 확인
# APPROVED 템플릿 → 템플릿 기반 생성 확인
```
