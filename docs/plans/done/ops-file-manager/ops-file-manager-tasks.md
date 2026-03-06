# Tasks: 운영 콘솔 통합 파일 관리

Last Updated: 2026-03-06

## Phase 1: 백엔드 API

### 1-0. 감사 로그 상수 추가 [Effort: S] -- DONE
- [x] `app/features/ops/application/audit_logs/constants.py` 수정
  - [x] `AuditAction`에 `FILE_DELETED`, `FILE_BULK_DELETED` 추가
  - [x] `AuditTargetType`에 `FILE` 추가
  - [x] `ALLOWED_AUDIT_ACTIONS`, `ALLOWED_AUDIT_TARGET_TYPES`에 등록

### 1-1. 파일 관리 서비스 [Effort: M] -- DONE
- [x] `app/features/ops/application/files/__init__.py` 생성
- [x] `app/features/ops/application/files/service.py` 생성
  - [x] `list_files()` 페이지네이션 + 필터 + 정렬
  - [x] `get_stats()` 집계 쿼리
  - [x] `delete_file()` 단건 삭제 + 감사 로그
  - [x] `delete_files()` 일괄 삭제 + 부분 실패 처리

### 1-2. 파일 관리 라우터 [Effort: M] -- DONE
- [x] `app/api/v1/ops/files.py` 생성
  - [x] Pydantic 스키마 정의
  - [x] `GET /ops/files` 목록 조회
  - [x] `GET /ops/files/stats` 통계 조회
  - [x] `DELETE /ops/files/{file_id}` 단건 삭제
  - [x] `DELETE /ops/files/batch` 일괄 삭제

### 1-3. 라우터 등록 [Effort: S] -- DONE
- [x] `app/api/v1/ops/router.py` — files 라우터 등록

### 1-4. 백엔드 테스트 [Effort: M] -- DONE
- [x] `tests/api/test_ops_files.py` 생성 (306줄)
  - [x] 목록 조회, 필터, 검색, 통계, 단건/일괄 삭제, 비관리자 거부, 부분 실패

---

## Phase 2: 프론트엔드 UI

### 2-1. 타입 & API [Effort: S] -- DONE
- [x] `src/features/ops/files/types.ts` 생성
- [x] `src/features/ops/files/api.ts` 생성

### 2-2. 메인 뷰 [Effort: L] -- DONE
- [x] `src/features/ops/files/view.tsx` — OpsFilesView (543줄)

### 2-3. 페이지 & 네비게이션 [Effort: S] -- DONE
- [x] `src/app/(dashboard)/ops/files/page.tsx` 생성
- [x] `src/features/ops/files/index.ts` re-export
- [x] `src/features/ops/index.ts` export 추가
- [x] `src/features/ops/home/view.tsx` "파일 관리" 카드 추가

### 2-4. 프론트엔드 린트 [Effort: S] -- DONE
- [x] `pnpm lint` 통과 (warning 1건: img element)
- [x] 빌드 통과

---

## Phase 3: 검증 & 마무리

### 3-1. 통합 테스트 [Effort: S] -- DONE
- [x] 백엔드: `make test` 421 passed
- [x] 프론트엔드: `pnpm lint` 통과

### 3-2. 타입 동기화 [Effort: S] -- DONE
- [x] `api-types.ts` 갱신 완료

---

## Completion
- **PR**: #24 (merged to develop)
- **Commits**: f9d7ac8, f4ba776
- **All phases complete**: 2026-03-06
