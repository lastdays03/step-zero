# Phase 2: 로드맵 템플릿 관리 시스템 — Task Checklist

> Last Updated: 2026-03-02
> Branch: `feature/2-template-system`

---

## Section A: DB 스키마 + 감사로그 상수 (1.5일)

### Group 1: DB 스키마 + 마이그레이션

- [ ] **A-1** 템플릿 모델 파일 생성 (`app/models/roadmap_template.py`)
  - [ ] `RoadmapTemplate` 모델 (id, business_type, startup_method, title, status, version, source_roadmap_id, created_by, approved_by, approved_at, timestamps)
  - [ ] `RoadmapTemplateStep` 모델 (id, template_id FK CASCADE, step_order, phase, title, objective, estimated_days, risk_notes JSON, created_at)
  - [ ] `RoadmapTemplateAction` 모델 (id, template_step_id FK CASCADE, action_type, title, description, source_url, actionkit_item_id FK, actionkit_file_id FK, sort_order, metadata_json JSON, created_at)
- [ ] **A-2** Roadmap 모델에 `template_id` FK 추가 (`app/models/roadmap.py`)
- [ ] **A-3** `__init__.py`에 3개 모델 import + `__all__` 추가 (`app/models/__init__.py`)
- [ ] **A-4** Alembic 마이그레이션 생성 (`alembic/versions/010_roadmap_templates.py`)
  - [ ] `roadmap_templates` 테이블 CREATE
  - [ ] `roadmap_template_steps` 테이블 CREATE (FK CASCADE)
  - [ ] `roadmap_template_actions` 테이블 CREATE (FK CASCADE)
  - [ ] `roadmap` 테이블 ALTER — `template_id` 컬럼 추가
  - [ ] 복합 인덱스 `(business_type, startup_method, status)` 생성
  - [ ] downgrade 함수 구현 (역순 삭제)
- [ ] **A-5** `make migrate-up` 성공 확인
- [ ] **A-6** `make test` 통과 확인 (SQLite 호환)

### Group 4: 감사로그 상수

- [ ] **A-7** `AuditAction` 상수 6개 추가 (`constants.py`)
  - `TEMPLATE_CREATED`, `TEMPLATE_UPDATED`, `TEMPLATE_STATUS_CHANGED`
  - `TEMPLATE_APPROVED`, `TEMPLATE_ARCHIVED`, `TEMPLATE_DELETED`
- [ ] **A-8** `AuditTargetType.ROADMAP_TEMPLATE` 추가
- [ ] **A-9** `ALLOWED_AUDIT_ACTIONS` + `ALLOWED_AUDIT_TARGET_TYPES` 셋 업데이트

---

## Section B: 백엔드 서비스 + 파이프라인 (6일)

### Group 2: CRUD 서비스 + API (3일)

- [ ] **B-1** 서비스 패키지 생성 (`features/ops/application/roadmap_templates/__init__.py`)
- [ ] **B-2** 서비스 함수 구현 (`features/ops/application/roadmap_templates/service.py`)
  - [ ] `get_template_summary()` — 전체/DRAFT/REVIEW/APPROVED 카운트
  - [ ] `list_templates()` — 필터 (status, business_type) + 정렬
  - [ ] `get_template_detail()` — 템플릿 + steps + actions 조회
  - [ ] `create_template_from_roadmap()` — 기존 로드맵 → 템플릿 복사
  - [ ] `update_template()` — 메타 수정 (title, business_type 등)
  - [ ] `update_template_status()` — 상태 변경 + 감사로그
  - [ ] `create_template_action()` — 액션 추가
  - [ ] `update_template_action()` — 액션 수정
  - [ ] `delete_template_action()` — 액션 삭제
  - [ ] `delete_template()` — 템플릿 삭제 (DRAFT/REVIEW만)
- [ ] **B-3** API 스키마 정의 (요청/응답)
  - [ ] `RoadmapTemplateSummaryResponse`
  - [ ] `RoadmapTemplateResponse` (목록용)
  - [ ] `RoadmapTemplateDetailResponse` (steps + actions 포함)
  - [ ] `RoadmapTemplateCreateFromRoadmapRequest`
  - [ ] `RoadmapTemplateUpdateRequest`
  - [ ] `RoadmapTemplateStatusUpdateRequest`
  - [ ] `RoadmapTemplateActionCreateRequest` / `UpdateRequest`
- [ ] **B-4** API 라우터 구현 (`api/v1/ops/roadmap_templates.py`)
  - [ ] `GET /summary` — 통계
  - [ ] `GET /` — 목록 (쿼리 파라미터: status, business_type)
  - [ ] `GET /{template_id}` — 상세
  - [ ] `POST /from-roadmap` — 로드맵 → 템플릿 생성
  - [ ] `PATCH /{template_id}` — 메타 수정
  - [ ] `PATCH /{template_id}/status` — 상태 변경 + 감사로그
  - [ ] `DELETE /{template_id}` — 삭제
  - [ ] `POST /{template_id}/steps/{step_id}/actions` — 액션 추가
  - [ ] `PATCH /{template_id}/steps/{step_id}/actions/{action_id}` — 액션 수정
  - [ ] `DELETE /{template_id}/steps/{step_id}/actions/{action_id}` — 액션 삭제
- [ ] **B-5** 라우터 등록 (`api/v1/ops/router.py`)
- [ ] **B-6** `make test` 통과 확인
- [ ] **B-7** Swagger UI에서 10개 엔드포인트 확인

### Group 3: 파이프라인 통합 (3일)

- [ ] **B-8** `TemplateResolver` 구현 (`features/roadmaps/application/template_resolver.py`)
  - [ ] `resolve()` — 매칭 (business_type + startup_method, 3단계 폴백)
  - [ ] `template_to_steps_payload()` — 템플릿 → steps_payload 변환
  - [ ] `should_create_auto_draft()` — 자동 DRAFT 조건 확인
- [ ] **B-9** `RoadmapGenerationService.process_job()` 수정
  - [ ] TemplateResolver.resolve() 호출 추가
  - [ ] 템플릿 있으면 → template_to_steps_payload() 경로
  - [ ] 템플릿 없으면 → 기존 파이프라인 + 자동 DRAFT 등록
  - [ ] Roadmap.template_id 설정
  - [ ] generation_mode = "TEMPLATE" / "ACTIONKIT_RAG" 분기
- [ ] **B-10** 기존 파이프라인 호환성 확인
  - [ ] 템플릿 없는 기존 업종 → 기존 결과와 동일
  - [ ] 자동 DRAFT 중복 등록 방지 확인
- [ ] **B-11** `make test` 통과 확인

---

## Section C: 프론트엔드 관리자 UI (3일)

### Group 5: Ops 템플릿 관리

- [ ] **C-1** 디렉토리 구조 + 타입 + API 함수 생성
  - [ ] `features/ops/roadmap-templates/types.ts` — 타입 정의
  - [ ] `features/ops/roadmap-templates/api.ts` — API 호출 함수
  - [ ] `features/ops/roadmap-templates/index.ts` — Public export
- [ ] **C-2** Ops 홈 카드 추가 (`features/ops/home/view.tsx`)
  - [ ] 7번째 카드: "로드맵 템플릿 관리"
- [ ] **C-3** 라우트 페이지 2개 생성
  - [ ] `app/(dashboard)/ops/roadmap-templates/page.tsx`
  - [ ] `app/(dashboard)/ops/roadmap-templates/[templateId]/page.tsx`
- [ ] **C-4** 목록 뷰 (`roadmap-templates/view.tsx`)
  - [ ] 통계 카드 (전체/DRAFT/REVIEW/APPROVED)
  - [ ] 필터 드롭다운 (status, business_type)
  - [ ] 테이블 (업종, 제목, 상태 배지, 버전, 사용 횟수, 생성일, 액션)
- [ ] **C-5** 상세/편집 뷰 (`roadmap-templates/template-detail-view.tsx`)
  - [ ] 템플릿 메타 편집 (title, business_type)
  - [ ] 상태 변경 버튼 (DRAFT→REVIEW→APPROVED)
  - [ ] 스텝 아코디언 (phase, title, objective, days, risk_notes)
  - [ ] 각 스텝 내 액션 목록 (action_type별 CRUD)
- [ ] **C-6** UI 컴포넌트 4개
  - [ ] `template-list-table.tsx` — 목록 테이블
  - [ ] `template-status-badge.tsx` — 상태 배지
  - [ ] `template-step-editor.tsx` — 스텝 편집기
  - [ ] `template-action-editor.tsx` — 액션 편집기
- [ ] **C-7** ops/index.ts에 export 추가
- [ ] **C-8** `npm run lint` 통과
- [ ] **C-9** `npm run build` 성공

---

## Section D: 테스트 + 문서 (2일)

### Group 6: 테스트

- [ ] **D-1** 백엔드 API 테스트 (`tests/api/test_ops_roadmap_templates.py`)
  - [ ] 템플릿 생성 (from-roadmap) 테스트
  - [ ] 목록 조회 + 필터 테스트
  - [ ] 상세 조회 테스트
  - [ ] 메타 수정 테스트
  - [ ] 상태 변경 테스트 (유효 전이)
  - [ ] 상태 변경 실패 테스트 (무효 전이)
  - [ ] 삭제 테스트
  - [ ] 권한 검증 (비관리자 → 403)
- [ ] **D-2** TemplateResolver 테스트 (`tests/services/test_template_resolver.py`)
  - [ ] 정확 매치 (business_type + startup_method)
  - [ ] 공통 폴백 (startup_method=null)
  - [ ] 미매치 → None 반환
  - [ ] should_create_auto_draft() — 중복 체크
- [ ] **D-3** 프론트엔드 테스트 (`features/ops/roadmap-templates/__tests__/`)
  - [ ] 목록 뷰 렌더링 테스트
  - [ ] 상태 배지 렌더링 테스트

### Group 7: 문서 업데이트

- [ ] **D-4** `docs/context/dev-status.md` 업데이트
- [ ] **D-5** `docs/context/handoff.md` 업데이트
- [ ] **D-6** `docs/context/decisions.md` — Phase 2 결정 사항 추가

---

## Final Quality Gates

- [ ] `cd app-backend && make migrate-up` — 010 마이그레이션 적용
- [ ] `cd app-backend && make migrate-verify` — 모델 ↔ DB diff 없음
- [ ] `cd app-backend && .venv/bin/pytest -q` — 전체 테스트 통과
- [ ] `cd app-frontend && npm run lint` — ESLint 통과
- [ ] `cd app-frontend && npm run build` — 빌드 성공
- [ ] `cd app-frontend && npm test` — Jest 통과
- [ ] 커밋 + PR 생성 (`feature/2-template-system` → `develop`)

---

## Progress Summary

| Section | 전체 | 완료 | 진행률 |
|:-------:|:----:|:----:|:------:|
| A (DB + 상수) | 9 | 0 | 0% |
| B (BE 서비스 + 파이프라인) | 11 | 0 | 0% |
| C (FE UI) | 9 | 0 | 0% |
| D (테스트 + 문서) | 6 | 0 | 0% |
| Quality Gates | 7 | 0 | 0% |
| **합계** | **42** | **0** | **0%** |
