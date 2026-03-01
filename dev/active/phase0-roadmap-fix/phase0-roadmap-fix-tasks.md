# Phase 0 로드맵 파이프라인 수정 - Tasks

> Last Updated: 2026-03-01 (Session 2)

---

## Phase A: 링크 오류 수정

- [x] **0-A-4** 다중 파일 매핑 수정 (BE, S)
  - [x] `item_file_urls` 타입 `dict[int, str]` → `dict[int, list[str]]` 변경
  - [x] `break` 제거, 리스트 컴프리헨션으로 모든 파일 수집
  - [x] 소비처 3곳에서 `[0]` 인덱스 접근으로 하위 호환 유지
  - [x] `all_file_urls` 키 additive 추가

- [x] **0-A-3** LLM 참조 자동 복구 로직 (BE, L)
  - [x] `_build_repair_indexes()` 신규 추가
  - [x] `_validate_references()` → `_validate_and_repair_references()` 교체
  - [x] 3단계 복구 전략 구현 (item_id → 역매핑 → 퍼지 → 제거)
  - [x] `_collect_originals()` 삭제
  - [x] `personalize()` 호출부 수정
  - [x] 빈 리스트 방어 로직 적용

- [x] **0-A-1** DOCUMENT 폴백 표시 (FE, S)
  - [x] DOCUMENT 타입에 "서류 정보 준비 중" 메시지 추가

- [x] **0-A-2** `actionkit_item_id` 대안 링크 (FE, M)
  - [x] IIFE 패턴으로 중첩 삼항 교체
  - [x] `metadata_json.actionkit_item_id` 기반 대안 링크 추가
  - [x] 연한 파란색(`text-[#36a4f2]/70`)으로 시각 구분

---

## Phase B: source_url 통일 + 퍼지 매칭

- [x] **0-B-1** source_url item_id 기반 통일 (BE, M)
  - [x] `_actionkit_item_url()` 헬퍼 추가
  - [x] legal_basis source_url: item_id → `_actionkit_item_url()` 사용
  - [x] document source_url: item_id 우선, file_url은 다운로드용 유지
  - [x] `_resolve_document_source_url()`: item_id 우선 체크 추가

- [x] **0-B-2** DB 기존 데이터 source_url 마이그레이션 (DB, M)
  - [x] 009 마이그레이션 파일 생성
  - [x] `UPDATE roadmap_step_actions SET source_url = ...` SQL 작성
  - [x] PostgreSQL `->>`(JSON 텍스트 추출) 연산자 사용
  - [x] downgrade 시 source_url 원복 불가 (기존 값 비정상이므로 허용)
  - [x] 로컬 DB에 마이그레이션 적용 확인 (396건 file→item 변환 완료)

- [x] **0-B-3** 퍼지 매칭 모드 (BE, L)
  - [x] `_fuzzy_match_law_name()`: Jaccard 유사도 + substring 보너스
  - [x] `_fuzzy_match_file_key()`: basename 일치 또는 substring 포함
  - [x] `_validate_and_repair_references()` 내 Strategy 2.5로 통합

---

## Phase C: startup_method 어휘 추가

- [x] **0-C-3** DB 모델 + 마이그레이션 (DB, S)
  - [x] `models/roadmap.py`에 `startup_method: str | None = None` 추가
  - [x] 009 마이그레이션에 `startup_method` 컬럼 포함

- [x] **0-C-2** BE 파이프라인 전파 (BE, M)
  - [x] `GenerationPayload`에 `startup_method` 추가
  - [x] `_payload_to_dict()`에 `startup_method` 추가
  - [x] `process_job()` → `create_roadmap()` 호출에 전달
  - [x] `roadmap_repository.py` `create_roadmap()` 파라미터 추가
  - [x] `schemas.py` 두 Request 클래스에 `startup_method` 추가
  - [x] `_USER_PROMPT_TEMPLATE`에 `- 창업 방식: {startup_method}` 추가
  - [x] `personalize()` format() 호출에 `startup_method` 추가

- [x] **0-C-1** FE 인테이크 폼 startup_method 추가 (FE, M)
  - [x] `roadmap-constants.ts`: 제안 칩 추가
  - [x] `RoadmapChatIntake.tsx`: `FieldKey` 타입 추가 + 질문/검증/패널
  - [x] `RoadmapGenerationPanel.tsx`: payload + summary 수정
  - [x] `useRoadmapJob.ts`: `RoadmapIntakePayload` 타입 확장

---

## Phase D: 파일 URL 접근성 개선 (Session 2에서 추가)

- [x] **0-D-1** 이중 인코딩 StaticFiles 수정 (BE, S)
  - [x] `DecodingStaticFiles` 커스텀 클래스 (`main.py`)
  - [x] 리버스 프록시 이중 인코딩 한국어 URL 지원

- [x] **0-D-2** FE 링크 BE 도메인 prefix (FE, S)
  - [x] `TimelineStepItem.tsx`에 `API_URL` 상수 추가
  - [x] `source_url` 상대경로에 `NEXT_PUBLIC_API_URL` prefix
  - [x] `actionkitItemId` fallback 링크에도 동일 적용

- [x] **0-D-3** 아이템 뷰어 엔드포인트 (BE, M)
  - [x] `/items/{id}` → 307 redirect → `/items/{id}/view`
  - [x] `/items/{id}/view`: .md → marked.js HTML 뷰어, .pdf → inline 표시
  - [x] `/items/{id}/download`: 기존 다운로드 유지
  - [x] `_resolve_file()` 공통 헬퍼로 추출
  - [x] `Content-Disposition` 한국어 파일명 `filename*=UTF-8''` 인코딩

- [x] **0-D-4** 테스트 수정 (BE, S)
  - [x] `test_roadmap_generation_service.py`: tuple 언패킹 수정 (`detail, is_fallback = ...`)

---

## 검증 및 배포

- [x] **테스트 작성**
  - [x] `TestValidateAndRepairReferences`: 7개 테스트
  - [x] `TestFuzzyMatching`: 11개 테스트
  - [x] `TestBuildRepairIndexes`: 2개 테스트

- [x] **Backend pytest (Docker)** — 177 passed, 1 skipped

- [x] **Frontend 검증 (Docker)**
  - [x] `npm run lint` 통과
  - [x] `npm run build` 성공 (Next.js 16.1.6 Turbopack)
  - [ ] `npm run types:sync` 실행 (배포 전 확인 필요)

- [ ] **코드 포맷** (배포 전 수행)
  - [ ] `black .` 실행
  - [ ] `isort . --profile black` 실행

- [ ] **Git 커밋 & PR**
  - [ ] 변경사항 커밋 (13 modified + 4 untracked)
  - [ ] `.gitignore`의 `test_*.py` 규칙 때문에 테스트 파일은 `git add -f` 필요
  - [ ] develop 브랜치로 PR 생성

- [ ] **배포 순서**
  - [ ] BE 배포 + 마이그레이션 (`alembic upgrade head`)
  - [ ] FE 배포

- [ ] **수동 검증**
  - [x] 기존 로드맵 링크 클릭 → item 기반 URL로 변환 확인
  - [x] 파일 뷰어 (.md → HTML 렌더링, .pdf → 인라인) 동작 확인
  - [ ] 새 로드맵 생성 → source_url 패턴 확인
  - [ ] 인테이크 폼 "창업 방식" 질문 + 제안 칩 동작

---

## Summary

| 카테고리 | 완료 | 전체 | 진행률 |
|----------|:----:|:----:|:------:|
| Phase A (링크 수정) | 4 | 4 | 100% |
| Phase B (통일+퍼지) | 3 | 3 | 100% |
| Phase C (startup_method) | 3 | 3 | 100% |
| Phase D (URL 접근성) | 4 | 4 | 100% |
| 테스트 | 2 | 2 | 100% |
| FE/포맷/배포 검증 | 2 | 5 | 40% |
| **합계** | **18** | **21** | **86%** |
