# Phase 0 로드맵 파이프라인 수정 - Context

> Last Updated: 2026-03-01 (Session 2)

---

## 1. Key Files (수정됨)

### Backend (BE)

| 파일 | 작업 ID | 변경 요약 |
|------|---------|-----------|
| `app-backend/app/features/roadmaps/application/llm_personalizer.py` | 0-A-3, 0-B-3 | `_validate_and_repair_references` 교체, `_build_repair_indexes`/`_fuzzy_match_*` 추가, 프롬프트에 `startup_method` 추가 |
| `app-backend/app/features/roadmaps/application/roadmap_generation_service.py` | 0-A-4, 0-B-1, 0-C-2 | `break` 제거 + `dict[int, list[str]]`, `_actionkit_item_url()`, source_url 통일, `startup_method` 전파 |
| `app-backend/app/repositories/roadmap_repository.py` | 0-B-1, 0-C-2 | `_resolve_document_source_url`에 item_id 우선 체크, `create_roadmap`에 `startup_method` 파라미터 |
| `app-backend/app/models/roadmap.py` | 0-C-3 | `startup_method: str \| None = None` 컬럼 추가 |
| `app-backend/app/api/v1/schemas.py` | 0-C-2 | `RoadmapJobCreateRequest`/`RoadmapCreateRequest`에 `startup_method` 필드 |
| `app-backend/alembic/versions/009_startup_method_and_source_urls.py` | 0-C-3+0-B-2 | 신규 마이그레이션 (startup_method 컬럼 + source_url 일괄 업데이트) |
| `app-backend/app/main.py` | 0-D-1 | `DecodingStaticFiles` 클래스 추가 (이중 인코딩 URL 디코딩) |
| `app-backend/app/api/v1/actionkit/files.py` | 0-D-3 | `/items/{id}/view` 뷰어 엔드포인트, `/items/{id}` 리다이렉트, `_resolve_file()` 헬퍼 |
| `app-backend/tests/services/test_roadmap_generation_service.py` | 0-D-4 | `_generate_phase_detail_with_retry` 반환 타입 tuple 언패킹 수정 |

### Frontend (FE)

| 파일 | 작업 ID | 변경 요약 |
|------|---------|-----------|
| `app-frontend/src/features/roadmap/components/TimelineStepItem.tsx` | 0-A-1, 0-A-2, 0-D-2 | IIFE 링크 패턴 + `API_URL` prefix로 BE 도메인 연결 |
| `app-frontend/src/features/roadmap/components/RoadmapChatIntake.tsx` | 0-C-1 | `startup_method` 질문/타입/검증/패널 추가, `Repeat2` 아이콘 |
| `app-frontend/src/features/roadmap/components/roadmap-constants.ts` | 0-C-1 | `startup_method` 제안 칩 추가 |
| `app-frontend/src/features/roadmap/components/RoadmapGenerationPanel.tsx` | 0-C-1 | payload/summary에 `startup_method` 반영 |
| `app-frontend/src/features/roadmap/hooks/useRoadmapJob.ts` | 0-C-1 | `RoadmapIntakePayload` 타입에 `startup_method` 추가 |

### Tests

| 파일 | 변경 요약 |
|------|-----------|
| `app-backend/tests/services/test_llm_personalizer.py` | 신규 20개 테스트 (3 클래스) — `.gitignore`에 `test_*.py` 규칙 있어 `git add -f` 필요 |
| `app-backend/tests/services/test_roadmap_generation_service.py` | tuple 언패킹 수정 |

---

## 2. Key Decisions

| 결정 | 근거 |
|------|------|
| source_url → `/api/v1/actionkits/items/{id}` 통일 | 파일 경로 기반 URL은 한국어 인코딩 문제 + LLM 변조 취약 |
| `/items/{id}` → 307 → `/items/{id}/view` 리다이렉트 | 뷰어로 바로 연결, `/download`는 별도 유지 |
| `.md` 파일은 marked.js CDN으로 렌더링 | Python markdown 패키지 의존성 추가 불필요, 클라이언트 사이드 렌더링 |
| `DecodingStaticFiles` 서브클래스 | 리버스 프록시 이중 인코딩 방어, 기존 file URL 호환 |
| FE 링크에 `NEXT_PUBLIC_API_URL` prefix | FE/BE 도메인 분리 환경에서 상대경로 404 방지 |
| `Content-Disposition: inline; filename*=UTF-8''...` | 한국어 파일명 latin-1 인코딩 에러 방지 (RFC 5987) |
| 개발서버 DB 데이터를 로컬로 복사 | 실제 데이터로 마이그레이션 검증 |
| `.env.docker.local` → `app-db:5432` (로컬) | 로컬 Docker DB 사용으로 변경 |

---

## 3. Dependencies

### 환경 설정
- `.env.docker.local`: `DATABASE_URL=...@app-db:5432/...` (로컬 Docker DB)
- `.env`: `DATABASE_URL=...@193.122.102.216:5432/...` (개발서버 — 직접 사용 X)
- 개발서버 DB 데이터가 로컬 DB로 복사됨 (actionkit, roadmap, vector 테이블)

### 배포 순서 의존성 (Critical)
```
BE 배포 + 마이그레이션(009) → FE 배포
```

### 외부 의존성
- marked.js CDN (`cdn.jsdelivr.net/npm/marked/marked.min.js`) — view 엔드포인트에서 사용
- PostgreSQL `->>`(JSON 텍스트 추출) 연산자 — 마이그레이션에서 사용

---

## 4. Architecture Notes

### 파일 접근 엔드포인트 체계 (Session 2 확정)
```
/api/v1/actionkits/items/{id}           → 307 → /items/{id}/view
/api/v1/actionkits/items/{id}/view      → .md: HTML(marked.js), .pdf: inline
/api/v1/actionkits/items/{id}/download  → FileResponse (attachment)
/api/v1/actionkits/files/{object_key}   → StaticFiles (DecodingStaticFiles, 레거시 호환)
```

### FE 링크 구성 (TimelineStepItem.tsx)
```
const API_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";

source_url 있음 → href = API_URL + source_url (상대경로면 prefix)
actionkitItemId → href = API_URL + /api/v1/actionkits/items/{id}/download
LEGAL_BASIS     → "상세 법령 정보 준비 중"
DOCUMENT        → "서류 정보 준비 중"
```

### 이중 인코딩 방어 (main.py)
```
문제: 리버스 프록시가 %EC%A0%84 → %25EC%25A0%2584 로 재인코딩
해결: DecodingStaticFiles.get_response()에서 unquote(path) 처리
```

---

## 5. 검증 결과 (Session 2)

| 검증 항목 | 결과 |
|-----------|------|
| Backend pytest (Docker) | **177 passed, 1 skipped** |
| Frontend lint (Docker) | **통과** |
| Frontend build (Docker) | **Next.js 16.1.6 빌드 성공** |
| Migration 009 (로컬 DB) | **적용 완료** — 396건 file→item URL 변환 |
| `/items/{id}/view` .md 렌더링 | **200 OK** — marked.js HTML |
| `/items/{id}/view` .pdf 인라인 | **200 OK** — application/pdf |
| 이중 인코딩 file URL | **200 OK** — DecodingStaticFiles |
| FE→BE 도메인 링크 | **API_URL prefix 적용** |

### 로컬 DB 데이터 (개발서버에서 복사됨)
| 테이블 | 로컬 = 개발서버 |
|--------|:-:|
| actionkit_items | 67 ✅ |
| actionkit_files | 67 ✅ |
| langchain_pg_embedding | 1,777 ✅ |
| roadmap_step_actions | 885 (source_url 변환됨) |

---

## 6. 발견된 버그 & 해결 (Session 2)

| 버그 | 원인 | 해결 |
|------|------|------|
| 프로덕션 파일 URL 404 | 리버스 프록시 이중 인코딩 (`%25EC`) | `DecodingStaticFiles` (main.py) |
| FE 링크 클릭 시 404 | 상대경로가 FE 도메인으로 해석 | `API_URL` prefix (TimelineStepItem.tsx) |
| `/items/{id}` 라우트 없음 | migration이 item URL로 변환하지만 라우트 부재 | 307 redirect → `/items/{id}/view` |
| `/items/{id}/view` 500 에러 | `Content-Disposition` 한국어 latin-1 인코딩 실패 | `filename*=UTF-8''` + `quote()` |
| `test_generate_phase_detail_normalizes_document_source_url` 실패 | `_generate_phase_detail_with_retry` 반환 타입이 tuple로 변경됨 | `detail, is_fallback = ...` 언패킹 |

---

## 7. 미완료 작업 / 다음 세션

### 즉시 필요
1. **Git 커밋**: 13 modified + 4 untracked 파일, `git add -f` for test files
2. **코드 포맷**: `black .` + `isort . --profile black`
3. **PR 생성**: `feature/0-roadmap-improvement` → `develop`

### 배포 시
1. **개발서버 DB에 migration 009 적용** — 아직 개발서버는 008 상태
2. BE 먼저 배포 → FE 배포
3. 수동 검증: 새 로드맵 생성 + startup_method 폼

### 참고
- `.gitignore` Line 126에 `test_*.py` 규칙 존재 — 기존 테스트는 이미 tracked, 신규는 `git add -f` 필요
- `.env.docker.local`은 `app-db:5432`로 변경됨 (커밋 대상 아님, `.gitignore`에 포함)
