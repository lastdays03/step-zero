# Tasks: 운영 콘솔 통합 파일 관리

Last Updated: 2026-03-06

## Phase 1: 백엔드 API

### 1-0. 감사 로그 상수 추가 [Effort: S]
- [ ] `app/features/ops/application/audit_logs/constants.py` 수정
  - [ ] `AuditAction`에 `FILE_DELETED`, `FILE_BULK_DELETED` 추가
  - [ ] `AuditTargetType`에 `FILE` 추가
  - [ ] `ALLOWED_AUDIT_ACTIONS`, `ALLOWED_AUDIT_TARGET_TYPES`에 등록
- **AC:** 기존 감사 로그 테스트 통과, 새 상수 사용 가능

### 1-1. 파일 관리 서비스 [Effort: M]
- [ ] `app/features/ops/application/files/__init__.py` 생성
- [ ] `app/features/ops/application/files/service.py` 생성
  - [ ] `OpsFilesService.__init__(session)` — `self._session = session`
  - [ ] `list_files(page, page_size, sort_by, sort_dir, owner_type?, mime_group?, date_from?, date_to?, search?)` → `{ data, total, page, page_size }`
    - offset 기반 페이지네이션
    - ILIKE 검색 (original_filename)
    - owner_type 필터
    - mime_group 필터 (image/document/other → CASE WHEN)
    - 날짜 범위 필터 (uploaded_at)
    - 정렬 (created_at DESC 기본, size_bytes, original_filename)
    - `storage.get_public_url(object_key)`로 각 파일 public_url 포함
  - [ ] `get_stats()` → `{ total_files, total_bytes, by_owner_type: [...], by_mime_group: [...] }`
    - COUNT + SUM(size_bytes)
    - GROUP BY owner_type
    - CASE WHEN mime_type 분류
  - [ ] `delete_file(file_id, *, admin_id)` → `storage.delete()` 반환값(`bool`) 확인 → DB 삭제 + `flush()` → `record_admin_audit_log()`
  - [ ] `delete_files(file_ids, *, admin_id)` → 일괄 삭제:
    - storage.delete 루프에서 **성공/실패 ID 분리**
    - DB 삭제: `sa.delete().where(in_(success_ids))` — 성공분만
    - `flush()` → audit log 1건 (meta에 `deleted_count`, `failed_count` 포함)
    - 반환: `{ deleted: int, failed: int }`
- **주의:** `get_public_url()`은 동기 메서드 — `await` 금지
- **주의:** 기존 `delete_by_id()`는 내부 `flush()` 안 함 — 서비스에서 명시적 `flush()` 필요
- **AC:** 서비스 메서드 4개 구현, 스토리지 삭제 + 감사 로그 연동, 부분 실패 처리

### 1-2. 파일 관리 라우터 [Effort: M]
- [ ] `app/api/v1/ops/files.py` 생성
  - [ ] Pydantic 스키마 정의
    - `OpsFileResponse` (id, owner_type, owner_id, category, object_key, original_filename, mime_type, size_bytes, kind, uploaded_at, public_url)
    - `OpsFileListResponse` (data: list, total: int, page: int, page_size: int)
    - `OpsFileStatsResponse` (total_files, total_bytes, by_owner_type, by_mime_group)
    - `OpsFileBatchDeleteRequest` (ids: list[int])
    - `OpsFileBatchDeleteResponse` (deleted: int, failed: int)
  - [ ] `GET /ops/files` — 목록 조회
    - Query params: page, page_size, sort_by, sort_dir, owner_type, mime_group, date_from, date_to, search
  - [ ] `GET /ops/files/stats` — 통계 조회
  - [ ] `DELETE /ops/files/{file_id}` — 단건 삭제 (라우터에서 `session.commit()` 호출)
  - [ ] `DELETE /ops/files/batch` — 일괄 삭제 (body: `{ ids: list[int] }`, 라우터에서 `session.commit()`)
- **AC:** 4개 엔드포인트 동작, OpenAPI 문서 자동 생성, 삭제 시 commit 포함

### 1-3. 라우터 등록 [Effort: S]
- [ ] `app/api/v1/ops/router.py` — `from app.api.v1.ops import files` import + `router.include_router(files.router)` 추가
- **AC:** `/api/v1/ops/files/*` 경로로 접근 가능, `require_platform_admin` 의존성 자동 적용
- **Note:** 감사 상수 추가는 Task 1-0에서 완료 (중복 아님)

### 1-4. 백엔드 테스트 [Effort: M]
- [ ] `tests/api/test_ops_files.py` 생성
  - [ ] 목록 조회 테스트 (기본 페이지네이션)
  - [ ] 필터 테스트 (owner_type, mime_group)
  - [ ] 검색 테스트 (search 파라미터)
  - [ ] 통계 조회 테스트
  - [ ] 단건 삭제 테스트
  - [ ] 일괄 삭제 테스트
  - [ ] 비관리자 접근 거부 테스트 (403)
  - [ ] 일괄 삭제 부분 실패 테스트 (storage 삭제 일부 실패 시 성공분만 DB 삭제)
- **AC:** `make test` 통과, 핵심 경로 커버리지
- **⚠️ .gitignore 주의:** 루트 `.gitignore`에 `test_*.py` 패턴 존재 → `git add -f tests/api/test_ops_files.py` 필요

---

## Phase 2: 프론트엔드 UI

### 2-1. 타입 & API [Effort: S]
- [ ] `src/features/ops/files/types.ts` 생성
  - OpsFile, OpsFileStats, OpsFileListParams, OpsFileListResponse
- [ ] `src/features/ops/files/api.ts` 생성
  - fetchFiles(params) → OpsFileListResponse
  - fetchFileStats() → OpsFileStats
  - deleteFile(id) → void
  - deleteFiles(ids) → { deleted, failed }
- **AC:** 타입 안전한 API 호출 함수 4개

### 2-2. 메인 뷰 [Effort: L]
- [ ] `src/features/ops/files/view.tsx` — `OpsFilesView` 컴포넌트
  - [ ] 상단: 통계 카드 (총 파일 수, 총 용량, 이미지 비율, 문서 비율)
  - [ ] 필터 바: owner_type Select, mime_group Select, 날짜 범위, 검색 Input
  - [ ] 파일 테이블: 체크박스, 미리보기(이미지 썸네일/타입 아이콘), 파일명, 타입 뱃지, 크기, 소유 뱃지, 날짜, 삭제 버튼
  - [ ] 페이지네이션: 이전/다음 + 현재 페이지/총 페이지 표시
  - [ ] 일괄 선택 & 삭제: 전체 선택 체크박스, "선택 삭제 (N개)" 버튼, 확인 다이얼로그
  - [ ] 빈 상태, 로딩, 에러 처리
- **AC:** 목록 조회 + 필터 + 페이지네이션 + 단건/일괄 삭제 동작

### 2-3. 페이지 & 네비게이션 [Effort: S]
- [ ] `src/app/(dashboard)/ops/files/page.tsx` 생성
- [ ] `src/features/ops/files/index.ts` — re-export
- [ ] `src/features/ops/index.ts` — `export * from "./files"` 추가
- [ ] `src/features/ops/home/view.tsx` — "파일 관리" 카드 추가 (`Link href="/ops/files"`)
- **AC:** `/ops/files` 경로로 페이지 접근 가능, ops 홈에 메뉴 카드 표시

### 2-4. 프론트엔드 린트 [Effort: S]
- [ ] `pnpm lint` 통과 확인
- [ ] `pnpm build` 통과 확인
- **AC:** CI 레벨 품질 게이트 통과

---

## Phase 3: 검증 & 마무리

### 3-1. 통합 테스트 [Effort: S]
- [ ] 백엔드: `make test` 전체 통과
- [ ] 프론트엔드: `pnpm lint` 통과
- [ ] Docker 환경에서 실 데이터로 동작 확인 (수동)

### 3-2. 타입 동기화 [Effort: S]
- [ ] `pnpm types:sync` — OpenAPI → TypeScript 타입 생성
- **AC:** 프론트엔드 타입과 백엔드 스키마 일치

---

## Summary

| Phase | 태스크 수 | 총 Effort |
|-------|----------|-----------|
| Phase 1: 백엔드 | 5 | S+M+M+S+M |
| Phase 2: 프론트엔드 | 4 | S+L+S+S |
| Phase 3: 검증 | 2 | S+S |
| **합계** | **11** | — |

**의존성 순서:**
- 직렬: 1-0 → 1-1 → 1-2 → 1-3 → 1-4
- 병렬 가능: 2-1(타입/API)은 1-2(라우터 스키마) 완료 후 시작, 1-4(테스트)와 병렬 가능
- 직렬: 2-1 → 2-2 → 2-3 → 2-4 → 3-1 → 3-2
