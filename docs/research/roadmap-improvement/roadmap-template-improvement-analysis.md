# 로드맵 템플릿 기능 개선 분석서

> 작성일: 2026-03-01
> 브랜치: `feature/0-roadmap-improvement`
> 상태: 분석 완료, 구현 대기

---

## 1. 개요

운영자가 보고한 로드맵 템플릿 기능의 수정 사항 10건을 코드 레벨에서 상세 분석한 문서이다.
현재 템플릿 시스템은 DRAFT→REVIEW→APPROVED→ARCHIVED 단방향 상태 흐름, 2가지 유형 매칭(업종+창업방식),
Step 단위 CRUD 미지원, 승인 후 수정 불가 등의 제약이 있어 운영 효율이 떨어지는 상황.

---

## 2. 요구사항별 상세 분석

### 2.1 양방향 상태변경

**요구사항:** 보관처리만이 아니라 각 단계는 앞뒤로 상태변경이 가능하도록

**현재 상태:**
```python
# app-backend/app/features/ops/application/roadmap_templates/service.py:19-24
_VALID_TRANSITIONS = {
    "DRAFT": {"REVIEW"},
    "REVIEW": {"DRAFT", "APPROVED"},
    "APPROVED": {"ARCHIVED"},        # → 보관만 가능
    "ARCHIVED": set(),                # → 전환 불가
}
```

**분석:**
- APPROVED에서 ARCHIVED로의 단방향만 존재
- ARCHIVED 상태가 되면 어떤 전환도 불가 (터미널 상태)
- APPROVED에서 수정이 필요해도 REVIEW로 되돌릴 방법 없음

**해결 방안:**
```python
_VALID_TRANSITIONS = {
    "DRAFT": {"REVIEW"},
    "REVIEW": {"DRAFT", "APPROVED"},
    "APPROVED": {"ARCHIVED", "REVIEW"},   # +REVIEW (수정을 위한 되돌리기)
    "ARCHIVED": {"APPROVED"},              # +APPROVED (복원)
}
```

**영향 파일:**
- `app-backend/app/features/ops/application/roadmap_templates/service.py` — 전환 규칙 수정
- `app-frontend/src/features/ops/roadmap-templates/template-detail-view.tsx` — 버튼 추가

---

### 2.2 보관처리된 유형의 자동 DRAFT 생성

**요구사항:** 보관처리된 템플릿에 해당하는 유형의 로드맵이 새로 생성되면 새 템플릿이 등록되야 하는데 안됨

**현재 상태:**
```python
# app-backend/app/features/roadmaps/application/template_resolver.py:157-173
@staticmethod
async def should_create_auto_draft(session, *, business_type):
    # ANY 템플릿(상태 무관)이 존재하면 False
    stmt = select(RoadmapTemplate.id).where(
        RoadmapTemplate.business_type == business_type
    ).limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is None
```

**분석:**
- ARCHIVED 상태의 템플릿이라도 존재하면 `False` 반환 → 새 DRAFT 미생성
- 이는 의도된 설계: "한번 생성된 유형은 관리자가 수동으로 관리" 의도
- 그러나 운영상 ARCHIVED만 있고 활성 템플릿이 없는 경우 자동 생성이 필요

**해결 방안:**
```python
async def should_create_auto_draft(session, *, business_type, startup_method=None, startup_type=None):
    """APPROVED/DRAFT/REVIEW 상태 중 하나라도 있으면 False, ARCHIVED만 있으면 True"""
    stmt = select(RoadmapTemplate.id).where(
        RoadmapTemplate.business_type == business_type,
        RoadmapTemplate.status.in_(["DRAFT", "REVIEW", "APPROVED"]),
    )
    if startup_method:
        stmt = stmt.where(RoadmapTemplate.startup_method == startup_method)
    if startup_type:
        stmt = stmt.where(RoadmapTemplate.startup_type == startup_type)
    stmt = stmt.limit(1)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is None
```

**영향 파일:**
- `app-backend/app/features/roadmaps/application/template_resolver.py`
- `app-backend/app/features/roadmaps/application/roadmap_generation_service.py` (호출부)

---

### 2.3 유형 = 업종 + 창업방식 + 창업형태 (3가지 조합)

**요구사항:** 유형은 업종/창업방식/창업형태 3가지로 각각 유형별 3개가 다 같을때 하나의 템플릿

**현재 상태:**
- `Roadmap` 모델: `business_type`, `startup_method`, `startup_type` 3개 필드 존재
- `RoadmapTemplate` 모델: `business_type`, `startup_method` 2개만 존재 → **startup_type 누락**
- `TemplateResolver.resolve()`: 2-tier 매칭만 수행

**분석:**
- Roadmap 생성 시 `startup_type` (개인사업/법인설립 등)을 받지만, 템플릿에는 저장하지 않음
- 같은 업종이라도 창업형태가 다르면 필요한 절차가 다를 수 있음

**해결 방안:**

1. **DB 마이그레이션:** `roadmap_templates` 테이블에 `startup_type VARCHAR NULL` 컬럼 추가
2. **모델 수정:** `RoadmapTemplate.startup_type` 필드 추가
3. **Resolver 3-tier 매칭:**
   ```
   Priority 1: business_type + startup_method + startup_type (exact match)
   Priority 2: business_type + startup_method + startup_type=NULL (fallback)
   Priority 3: business_type + startup_method=NULL + startup_type=NULL (common fallback)
   Priority 4: None (기존 파이프라인)
   ```

**영향 파일:**
- `app-backend/alembic/versions/` (신규 마이그레이션)
- `app-backend/app/models/roadmap_template.py`
- `app-backend/app/features/roadmaps/application/template_resolver.py`
- `app-backend/app/api/v1/ops/roadmap_template_schemas.py`
- `app-backend/app/api/v1/ops/roadmap_templates.py`
- `app-frontend/src/features/ops/roadmap-templates/types.ts`
- `app-frontend/src/features/ops/roadmap-templates/template-detail-view.tsx`

---

### 2.4 로드맵 생성 버튼 — 리스트 검색 형태

**요구사항:** UUID 입력이 불편하므로 리스트 형태로 보여주고 3가지 유형으로 검색 가능

**현재 상태:**
```tsx
// app-frontend/.../create-from-roadmap-dialog.tsx
// UUID 텍스트 입력 → createTemplateFromRoadmap(trimmed) 호출
<Input placeholder="예: 550e8400-e29b-41d4-a716-446655440000" />
```

**분석:**
- 관리자가 로드맵 UUID를 직접 알아야 사용 가능 → 비실용적
- ops 라우터에 로드맵 목록/검색 API가 없음

**해결 방안:**

1. **백엔드:** 로드맵 검색 API 추가
   ```
   GET /ops/roadmap-templates/roadmaps/search
   ?business_type=&startup_method=&startup_type=&q=
   ```
   반환: `[{id, title, business_type, startup_method, startup_type, created_at}]`

2. **프론트엔드:** Dialog를 검색+리스트 형태로 교체
   - 3가지 유형 드롭다운 필터 + 텍스트 검색
   - 결과 테이블에서 로드맵 선택
   - UUID 직접 입력 옵션도 유지 (폴백)

**영향 파일:**
- `app-backend/app/api/v1/ops/roadmap_templates.py` (검색 엔드포인트)
- `app-backend/app/api/v1/ops/roadmap_template_schemas.py` (응답 스키마)
- `app-frontend/.../components/create-from-roadmap-dialog.tsx` (전면 교체)
- `app-frontend/.../api.ts` (searchRoadmaps 함수 추가)
- `app-frontend/.../types.ts` (RoadmapSearchResult 타입 추가)

---

### 2.5 승인 상태 템플릿만 로드맵 생성에 적용 확인

**요구사항:** 확인 필요

**분석 결과: 정상 작동 — 변경 불필요**

```python
# template_resolver.py:37-39
RoadmapTemplate.status == "APPROVED",  # 명시적 APPROVED 조건
```

`TemplateResolver.resolve()`에서 `status == "APPROVED"` 조건으로만 조회하므로 DRAFT/REVIEW/ARCHIVED 템플릿은 사용되지 않음.

---

### 2.6 단계 추가/삭제/순서변경 기능 부재

**요구사항:** 단계 자체를 늘리고 줄이고 순서를 변경하는 기능이 필요

**현재 상태:**
- Step CRUD 엔드포인트: **존재하지 않음**
- Action CRUD만 존재 (POST/PATCH/DELETE `steps/{step_id}/actions`)
- 단계는 `create_template_from_roadmap()` 시 로드맵에서 복사 후 고정

**해결 방안:**

1. **서비스 함수 4개 추가:**
   ```python
   create_template_step(session, template_id, data)     # 단계 추가
   update_template_step(session, step_id, data)         # 단계 수정 (목표/위험 포함)
   delete_template_step(session, step_id)               # 단계 삭제 (CASCADE → 액션도 삭제)
   reorder_template_steps(session, template_id, step_ids)  # 순서 변경
   ```

2. **API 엔드포인트 4개 추가:**
   ```
   POST   /roadmap-templates/{template_id}/steps
   PATCH  /roadmap-templates/{template_id}/steps/{step_id}
   DELETE /roadmap-templates/{template_id}/steps/{step_id}
   PATCH  /roadmap-templates/{template_id}/steps/reorder
   ```

3. **프론트엔드 UI:**
   - 단계 추가 버튼 + 인라인 폼
   - 위/아래 화살표로 순서 변경
   - 단계 삭제 버튼 (확인 다이얼로그)

**영향 파일:**
- `app-backend/app/features/ops/application/roadmap_templates/service.py`
- `app-backend/app/api/v1/ops/roadmap_templates.py`
- `app-backend/app/api/v1/ops/roadmap_template_schemas.py`
- `app-frontend/.../api.ts`
- `app-frontend/.../template-detail-view.tsx`
- `app-frontend/.../components/template-step-editor.tsx`

---

### 2.7 각 단계의 목표/위험상황 수정 기능

**요구사항:** 각 단계의 목표/위험상황도 수정 가능하게 변경

**현재 상태:**
```tsx
// template-step-editor.tsx:56-72
// 목표와 위험사항은 읽기 전용 텍스트로만 표시
{step.objective && (
  <p className="mt-1 text-sm text-slate-700">{step.objective}</p>
)}
{step.risk_notes.map((note, i) => (
  <li key={i}>{note}</li>
))}
```

**분석:**
- UI에서 objective/risk_notes를 표시만 하고 편집 불가
- 백엔드에도 Step 수정 API가 없어서 프론트만 바꿔도 동작 안 함
- #2.6의 Step CRUD와 함께 해결

**해결 방안:**
- Step PATCH API (2.6에서 추가)로 objective, risk_notes 수정 가능
- 프론트엔드에서 editable 모드일 때 인라인 편집 UI 제공
  - objective: textarea → 저장 버튼
  - risk_notes: 항목별 추가/삭제/수정

**영향 파일:**
- `app-frontend/.../components/template-step-editor.tsx` (인라인 편집 UI)

---

### 2.8 맵핑스코어 문제 (템플릿 기반 생성 시 AI생성으로 표시)

**요구사항:** 등록된 템플릿 기반으로 생성시 맵핑스코어가 AI생성으로 나오는 문제 확인

**분석 결과: 코드상 정상 — 변경 불필요**

코드 추적 결과:

1. **template_to_steps_payload()** (template_resolver.py:123,131,140,152):
   - 모든 항목에 `"mapping_source": "template"` 명시적 설정

2. **create_steps_with_details()** (roadmap_repository.py:206-209):
   ```python
   generation_mode=generation_mode,        # "TEMPLATE"
   mapping_source=payload.get("mapping_source"),  # "template"
   ```

3. **process_job()** (roadmap_generation_service.py:232):
   ```python
   generation_mode = "TEMPLATE"
   ```

**결론:** 새로 템플릿 기반으로 생성된 로드맵은 `mapping_source="template"`, `generation_mode="TEMPLATE"`으로 정상 저장됨. 문제가 발생한다면 이전에 template 없이 생성된 기존 데이터가 원인일 가능성이 높음.

---

### 2.9 승인 후 템플릿 수정

**요구사항:** 승인 후에는 템플릿 수정이 안되는건 의도한건지 확인 — 운영중에 승인된 템플릿이라도 수정할 일이 있을 수 있음

**현재 상태:**
```python
# service.py:27
_EDITABLE_STATUSES = {"DRAFT", "REVIEW"}

# service.py:210
if template.status not in _EDITABLE_STATUSES:
    raise ValueError(f"Cannot edit template in {template.status} status")
```

**분석:**
- 의도된 설계: 승인 후 무분별한 수정을 방지하여 운영 중인 템플릿의 안정성 보장
- 그러나 운영상 승인된 템플릿도 수정이 필요한 경우 발생

**결정사항:** APPROVED → REVIEW 전환 후 수정 가능하도록 (#2.1 상태전환에 포함)
- 직접 수정이 아닌 "검토중으로 전환" 과정을 거치도록 하여 안전장치 유지
- `_EDITABLE_STATUSES`는 `{"DRAFT", "REVIEW"}`로 유지

---

## 3. 수정 대상 파일 총정리

### Backend (8파일)

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `alembic/versions/` (신규) | startup_type 컬럼 + 인덱스 마이그레이션 |
| 2 | `app/models/roadmap_template.py` | startup_type 필드 추가 |
| 3 | `app/features/ops/application/roadmap_templates/service.py` | 상태전환 수정 + Step CRUD 함수 |
| 4 | `app/features/roadmaps/application/template_resolver.py` | 3-tier 매칭 + auto-draft 수정 |
| 5 | `app/features/roadmaps/application/roadmap_generation_service.py` | startup_type 전달 |
| 6 | `app/api/v1/ops/roadmap_templates.py` | Step CRUD + 로드맵 검색 엔드포인트 |
| 7 | `app/api/v1/ops/roadmap_template_schemas.py` | 스키마 추가 |
| 8 | `app/features/ops/application/roadmap_templates/__init__.py` | 새 함수 export |

### Frontend (7파일)

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `types.ts` | startup_type + RoadmapSearchResult 타입 |
| 2 | `api.ts` | Step CRUD + 검색 API 함수 |
| 3 | `template-detail-view.tsx` | 상태전환 UI + 단계 추가/순서변경 |
| 4 | `components/template-step-editor.tsx` | 목표/위험 편집 + 삭제 |
| 5 | `components/create-from-roadmap-dialog.tsx` | 리스트 검색 형태 |
| 6 | `components/template-list-table.tsx` | startup_type 컬럼 |
| 7 | `view.tsx` | startup_type 필터 |

---

## 4. 구현 순서

```
Phase 1: 기반 작업
  1. DB 마이그레이션 + 모델 (startup_type)
  2. 백엔드 상태전환 로직 수정

Phase 2: 백엔드 기능 확장
  3. Template Resolver 3-tier 매칭 + auto-draft 수정
  4. 서비스/스키마에 startup_type 반영
  5. Step CRUD API 추가
  6. 로드맵 검색 API 추가

Phase 3: 프론트엔드 적용
  7. 타입/API 업데이트
  8. 상태전환 UI 수정
  9. 단계 관리 UI (추가/삭제/순서변경/목표편집)
  10. 로드맵 검색 다이얼로그
  11. startup_type UI 반영
```

---

## 5. 검증 방법

1. **백엔드 단위 테스트**: 상태전환 로직, Step CRUD, Resolver 3-tier 매칭
2. **API 수동 테스트**: curl/httpie로 새 엔드포인트 호출 확인
3. **프론트엔드 빌드**: `pnpm lint && pnpm build` 통과
4. **통합 테스트** (브라우저):
   - DRAFT → REVIEW → APPROVED → ARCHIVED → APPROVED 전체 흐름
   - APPROVED → REVIEW → 수정 → REVIEW → APPROVED 수정 흐름
   - 단계 추가/삭제/순서변경/목표수정
   - 로드맵 리스트 검색으로 템플릿 생성
   - 3가지 유형(업종+창업방식+창업형태)으로 필터링
