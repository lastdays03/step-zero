# Phase 2: 로드맵 템플릿 관리 시스템 — 컨텍스트

> Last Updated: 2026-03-02 (세션 2)

---

## 0. 세션 3 핵심 기록

### 0.1 완료된 작업 (세션 2~3 누적)
- **Section A 완료 (A-1~A-9)**: 모델 3개 + 마이그레이션 + DB 적용 + pytest 통과 + 감사로그 상수 6개
- **Section B 완료 (B-1~B-11)**: CRUD 서비스 10개 함수 + API 스키마 10개 + 라우터 10개 엔드포인트 + TemplateResolver 3개 함수 + 파이프라인 통합
- **Section D 일부 (D-1~D-2)**: 백엔드 API 테스트 9개 + TemplateResolver 테스트 6개 — 모두 통과
- **pytest 전체 통과**: 174 passed, 19 skipped

### 0.2 신규 파일 (세션 2~3 생성)

| 파일 | 용도 |
|------|------|
| `app/models/roadmap_template.py` | RoadmapTemplate, RoadmapTemplateStep, RoadmapTemplateAction 모델 |
| `alembic/versions/010_roadmap_templates.py` | 마이그레이션 |
| `app/features/ops/application/roadmap_templates/__init__.py` | 서비스 패키지 export |
| `app/features/ops/application/roadmap_templates/service.py` | CRUD 서비스 (10개 함수) |
| `app/api/v1/ops/roadmap_template_schemas.py` | API 요청/응답 스키마 (10개 클래스) |
| `app/api/v1/ops/roadmap_templates.py` | API 라우터 (10개 엔드포인트) |
| `app/features/roadmaps/application/template_resolver.py` | TemplateResolver (resolve, template_to_steps_payload, should_create_auto_draft) |
| `tests/api/test_ops_roadmap_templates.py` | API 테스트 (9 tests) |
| `tests/services/test_template_resolver.py` | TemplateResolver 테스트 (6 tests) |

### 0.3 세션 2에서 발견 & 수정한 버그 3건

| 버그 | 원인 | 수정 파일 |
|------|------|----------|
| `alembic check`가 템플릿 테이블을 NullType으로 인식 | `alembic/env.py`에 `roadmap_template` import 누락 | `alembic/env.py` |
| FK ondelete 불일치 (alembic이 FK 재생성 시도) | 모델에서 `ondelete` 미선언 (마이그레이션에만 있음) | `app/models/roadmap_template.py`, `app/models/roadmap.py` |
| 복합 인덱스 삭제 시도 | 모델에 `__table_args__` 미정의 | `app/models/roadmap_template.py` |

### 0.4 핵심 교훈: 마이그레이션 실행 주의

- **호스트 alembic**: `.env`의 `DATABASE_URL=...@193.122.102.216:5432` → 외부 DB에 적용
- **Docker 백엔드**: `.env.docker.local`의 `DATABASE_URL=...@app-db:5432` → Docker 내부 DB 사용
- **마이그레이션은 반드시 Docker 컨테이너 안에서 실행**: `docker compose -f docker-compose.dev.yml exec app-backend python -m alembic upgrade head`

### 0.5 남은 작업
- **Section C (FE UI)**: 프론트엔드 관리자 UI 9개 항목 — Phase 3에서 진행중
- **Section D (D-3~D-6)**: FE 테스트 + 문서 업데이트 — Phase 3 완료 후 진행

---

## 1. Key Files — 수정 대상

### 1.1 백엔드 신규 파일

| 파일 | 용도 | Group |
|------|------|:-----:|
| `app/models/roadmap_template.py` | 3개 모델 (Template, Step, Action) | G1 |
| `alembic/versions/010_roadmap_templates.py` | DB 마이그레이션 | G1 |
| `app/features/ops/application/roadmap_templates/__init__.py` | 패키지 초기화 | G2 |
| `app/features/ops/application/roadmap_templates/service.py` | CRUD 서비스 (10개 함수) | G2 |
| `app/api/v1/ops/roadmap_templates.py` | API 라우터 (10개 엔드포인트) | G2 |
| `app/features/roadmaps/application/template_resolver.py` | 템플릿 매칭 + 변환 | G3 |
| `tests/api/test_ops_roadmap_templates.py` | API 테스트 | G6 |
| `tests/services/test_template_resolver.py` | TemplateResolver 테스트 | G6 |

### 1.2 백엔드 수정 파일

| 파일 | 변경 내용 | Group |
|------|----------|:-----:|
| `app/models/roadmap.py` | `template_id` FK 추가 (1줄) | G1 |
| `app/models/__init__.py` | 3개 모델 import + __all__ 추가 | G1 |
| `app/features/ops/application/audit_logs/constants.py` | 6개 상수 + 1개 타입 추가 | G4 |
| `app/api/v1/ops/router.py` | `roadmap_templates.router` 등록 (2줄) | G2 |
| `app/features/roadmaps/application/roadmap_generation_service.py` | TemplateResolver 통합 | G3 |
| `app/repositories/roadmap_repository.py` | `template_id` 반영 확인 | G3 |

### 1.3 프론트엔드 신규 파일

| 파일 | 용도 | Group |
|------|------|:-----:|
| `src/features/ops/roadmap-templates/index.ts` | Public export | G5 |
| `src/features/ops/roadmap-templates/view.tsx` | 목록 뷰 | G5 |
| `src/features/ops/roadmap-templates/template-detail-view.tsx` | 상세/편집 뷰 | G5 |
| `src/features/ops/roadmap-templates/api.ts` | API 호출 함수 | G5 |
| `src/features/ops/roadmap-templates/types.ts` | 타입 정의 | G5 |
| `src/features/ops/roadmap-templates/components/*.tsx` | UI 컴포넌트 4개 | G5 |
| `src/app/(dashboard)/ops/roadmap-templates/page.tsx` | 라우트 (목록) | G5 |
| `src/app/(dashboard)/ops/roadmap-templates/[templateId]/page.tsx` | 라우트 (상세) | G5 |

### 1.4 프론트엔드 수정 파일

| 파일 | 변경 내용 | Group |
|------|----------|:-----:|
| `src/features/ops/home/view.tsx` | 7번째 카드 추가 | G5 |
| `src/features/ops/index.ts` | export 추가 | G5 |

---

## 2. Key Files — 참고 (패턴 재활용)

### 2.1 백엔드 패턴 소스

| 파일 | 참고 포인트 |
|------|------------|
| `app/features/ops/application/actionkit/service.py` | CRUD 서비스 패턴 (get_all, create, update, delete + commit) |
| `app/api/v1/ops/actionkit.py` | API 라우터 패턴 (prefix, tags, Depends, HTTPException) |
| `app/features/ops/application/audit_logs/constants.py` | 감사로그 상수 패턴 (AuditAction, AuditTargetType) |
| `app/features/ops/application/audit_logs/service.py` | `record_admin_audit_log()` 호출 패턴 |
| `app/models/actionkit.py` | SQLModel 모델 패턴 (FK, cascade, JSON, index) |
| `alembic/versions/008_feature_merge_all.py` | 대규모 마이그레이션 패턴 |
| `app/repositories/roadmap_repository.py` | `create_steps_with_details()` payload 구조 |
| `app/features/roadmaps/application/roadmap_generation_service.py` | 파이프라인 통합 지점 |

### 2.2 프론트엔드 패턴 소스

| 파일 | 참고 포인트 |
|------|------------|
| `src/features/ops/home/view.tsx` | Ops 홈 카드 그리드 패턴 |
| `src/features/ops/actionkit/view.tsx` | 목록 뷰 패턴 (탭 + 테이블 + 모달 + DnD) |
| `src/features/ops/actionkit/components/` | 상태 배지, 편집 모달, 통계 카드 패턴 |
| `src/features/ops/announcements/view.tsx` | 간단한 CRUD 목록 패턴 |

---

## 3. Architecture Decisions

### 3.1 Phase 2에서 확정된 결정

| 결정 | 근거 |
|------|------|
| MVP에서 매칭 키는 `business_type`만 | 최대 8개 업종, startup_method는 null 허용 |
| 자동 DRAFT는 업종 최초 생성 시만 | 동일 업종 중복 DRAFT 무한 증식 방지 |
| 템플릿 있으면 LLM 호출 스킵 (MVP) | 복잡도 최소화, 검수된 데이터 그대로 사용 |
| APPROVED 템플릿 직접 수정 불가 | 새 버전 레코드 생성 방식으로 보호 |
| TemplateResolver는 `features/roadmaps/application/` | 파이프라인 서비스의 의존성 |
| CRUD 서비스는 `features/ops/application/roadmap_templates/` | Ops 도메인 범위 |
| 감사로그: 상태 변경만 기록 | 기존 패턴과 일관 (CRUD 개별은 미기록) |

### 3.2 기존 decisions.md와의 정합성

| 기존 결정 | Phase 2 적용 | 정합 |
|----------|-------------|:----:|
| API는 `api/v1/<feature>/` | `/api/v1/ops/roadmap-templates` | ✅ |
| 비즈니스 계층은 `features/<feature>/` | `features/ops/application/roadmap_templates/` | ✅ |
| 운영콘솔은 `ops`로 통일 | `/ops/roadmap-templates` | ✅ |
| FE 피처는 public entry + index.ts | `ops/roadmap-templates/index.ts` | ✅ |
| `/ops` 접근 = `is_superuser=true` | `require_platform_admin` dependency | ✅ |

---

## 4. Dependencies

### 4.1 작업 간 의존성

```
G1 (DB) ───────────┬──→ G2 (CRUD 서비스)
                    │       └──→ G5 (FE UI) ──→ G6 (테스트)
                    └──→ G3 (파이프라인) ──────→ G6 (테스트)
G4 (감사로그 상수) ──→ G2 (CRUD 서비스)
                                               → G7 (문서)
```

### 4.2 외부 의존성

| 의존성 | 상태 | 비고 |
|--------|:----:|------|
| Phase 0 완료 (develop 머지) | ✅ | startup_method, source_url 수정 포함 |
| Phase 1 커밋/머지 | ⚠️ 미완료 | 코드 충돌 위험 낮음 (Ops 영역 미접촉) |
| ActionKit 시드 데이터 | ✅ | 음식점 업종 충분히 존재 |
| 법률 자문 (변호사법/AI기본법) | 미착수 | Phase 4 (AI 코치) 전 필요, Phase 2와 무관 |

---

## 5. 기존 코드 핵심 구조 요약

### 5.1 Roadmap 모델 현재 필드 (Phase 2 적용 완료)

```python
class Roadmap(SQLModel, table=True):
    id: UUID (PK)
    team_id: UUID (FK → team.id)
    title: str
    business_type: str
    location: str
    description: str = ""
    startup_type: str | None
    startup_method: str | None
    open_timeline: str | None
    budget_range: str | None
    additional_notes: str = ""
    created_at, updated_at: datetime
    deleted_at: datetime | None
    template_id: int | None (FK → roadmap_templates.id, ondelete=SET NULL)  # ★ Phase 2 추가 완료
    created_by, updated_by: int | None (FK → user.id)
```

### 5.2 RoadmapStepAction.metadata_json 구조

```json
{
  "actionkit_item_id": 5,
  "actionkit_file_id": 12,
  "actionkit_highlight_id": 3,
  "actionkit_domain": "laws",
  "actionkit_category": "food-safety",
  "mapping_source": "actionkit_direct"  // or "rag", "llm_generated", "template"
}
```

### 5.3 감사로그 기록 패턴

```python
await record_admin_audit_log(
    session,
    admin_id=admin_user.id,
    action=AuditAction.TEMPLATE_STATUS_CHANGED,
    target_type=AuditTargetType.ROADMAP_TEMPLATE,
    target_id=str(template.id),
    reason=payload.reason,
    meta={"before": {"status": "DRAFT"}, "after": {"status": "REVIEW"}},
)
```

### 5.4 Alembic 마이그레이션 규칙

- Revision ID: `010_roadmap_templates`
- Down revision: `009_startup_method` (확인 완료)
- 패턴: `create_table()` → `create_index()` → `add_column()` → downgrade 역순
- FK: `sa.ForeignKeyConstraint(...)` with `ondelete="CASCADE"`
- JSON: `sa.Column(sa.JSON, nullable=False)`
- **중요**: 모델의 `Field(foreign_key=...)` 에도 반드시 `ondelete=` 명시 (growth_club.py 패턴)
- **중요**: 복합 인덱스는 `__table_args__`에도 선언 필요 (alembic check 통과용)
- **중요**: `alembic/env.py`에 새 모델 모듈 import 필수

### 5.5 Ops API 라우터 등록 패턴

```python
# api/v1/ops/router.py
from app.api.v1.ops import roadmap_templates

router = APIRouter(dependencies=[Depends(deps.require_platform_admin)])
router.include_router(roadmap_templates.router)
```

---

## 6. 상태 전이 규칙

```
         ┌──────────┐
         │  DRAFT   │ ←── 자동 생성 (파이프라인) 또는 수동 생성
         └────┬─────┘
              │ submit_for_review
              ▼
         ┌──────────┐
         │  REVIEW  │ ←── 운영자가 검수 중
         └────┬─────┘
              │ approve        │ reject
              ▼                ▼
         ┌──────────┐    ┌──────────┐
         │ APPROVED │    │  DRAFT   │ (반려 → DRAFT로 복귀)
         └────┬─────┘    └──────────┘
              │ archive
              ▼
         ┌──────────┐
         │ ARCHIVED │ (종료 상태)
         └──────────┘
```

**규칙**:
- APPROVED 직접 수정 불가 → 새 버전 레코드 생성 필요
- ARCHIVED는 최종 상태 (복원 불가)
- DRAFT/REVIEW만 편집 가능

---

## 7. 기획 문서 참조

| 문서 | 위치 | 핵심 섹션 |
|------|------|----------|
| 템플릿 관리 분석 | `docs/planning/completed/roadmap-improvement/REPORT-roadmap-template-management-analysis.md` | Section 6-8 (테이블), Section 10 (미결정) |
| 템플릿 구현 계획 | `docs/planning/completed/roadmap-improvement/REPORT-roadmap-template-implementation-plan.md` | Group 1-7 전체 |
| 통합 구현 순서 | `docs/planning/completed/roadmap-improvement/REPORT-implementation-order.md` | Phase 2 (Section 4) |
| 마스터 플랜 | `docs/planning/completed/roadmap-improvement/REPORT-01-master-plan.md` | 전체 로드맵 |
