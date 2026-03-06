# Cloudflare R2 파일 저장소 마이그레이션 - 태스크 체크리스트

> Last Updated: 2026-03-06

---

## Phase 0: 사전 준비 (사용자 수행)

- [x] **0-1** Cloudflare R2 버킷 생성 `[S]`
- [x] **0-2** R2 S3 API Token 발급 `[S]`
- [x] **0-3** R2 Public Access 활성화 `[S]`
- [x] **0-4** R2 CORS 정책 설정 `[S]`
- [x] **0-5** 환경변수 로컬 설정 `[S]`
- [x] **0-6** R2 연결 테스트 통과 `[S]`

---

## Phase 1: 백엔드 StorageBackend 추상화

- [x] **1-1** `StorageBackend` ABC + `StorageResult` + `LocalStorageBackend` `[M]`
- [x] **1-2** `get_storage_backend()` 팩토리 + Settings 추가 `[S]`
- [x] **1-3** ActionKit 서비스 리팩터 `[M]`
- [x] **1-4** Growth Club 서비스 리팩터 `[M]`
- [x] **1-5** Profile 서비스 리팩터 `[S]`
- [x] **1-6** 기존 테스트 통과 확인 `[S]` — 391 passed

---

## Phase 2: R2StorageBackend + Presigned URL 엔드포인트

- [x] **2-1** `boto3` 의존성 + R2 환경변수 `[S]` — 이미 설치됨, config.py 추가 완료
- [x] **2-2** `R2StorageBackend` 구현 `[L]` — r2.py 생성, asyncio.to_thread 래핑
- [x] **2-3** 팩토리에 R2 분기 추가 `[S]` — lazy import로 동작
- [x] **2-4** `POST /api/v1/storage/presign` 엔드포인트 `[M]` — storage.py + api.py 등록
- [x] **2-5** ActionKit 뷰/다운로드 R2 대응 `[M]` — _resolve_file R2 분기, 307 Redirect
- [x] **2-6** `_to_public_path()` + StaticFiles 조건부 처리 `[S]` — main.py 조건부 마운트
- [x] **2-7** StorageBackend 단위 테스트 `[M]` — 10 passed (git add -f 필요)
- [x] **2-8** `.env`, `.env.example` 업데이트 `[S]` — 이미 완료
- [x] **2-10** Presign 엔드포인트 MIME 타입 형식 검증 추가 `[S]` — field_validator + regex 검증

---

## Phase 3: 프론트엔드 공통 파일 모듈

- [x] **3-1** `shared/file/utils/validation.ts` `[M]` — validateFiles 통합 함수
- [x] **3-2** `shared/file/utils/url.ts` `[S]` — resolveUploadUrl + NEXT_PUBLIC_STORAGE_URL
- [x] **3-3** `shared/file/hooks/useFileUpload.ts` `[L]` — Presigned URL + XHR 진행률
- [x] **3-4** `shared/file/hooks/useFileDownload.ts` `[M]` — apiPath/url 분기 다운로드
- [x] **3-5** `shared/file/index.ts` + `NEXT_PUBLIC_STORAGE_URL` 환경변수 `[S]`
- [x] **3-7** useFileUpload: XHR abort cleanup + presign 재시도 로직 `[S]` — useRef + useEffect cleanup
- [x] **3-8** useFileDownload: fetch() 상태 코드 검증 (`res.ok` 체크) `[S]` — res.ok 체크 추가

---

## Phase 4: 기존 Feature 통합

- [x] **4-1** Growth Club `CreatePostForm` → 공통 모듈 적용 `[M]` — validateFiles 적용
- [x] **4-2** Growth Club R2 업로드 흐름 `[M]` — POST /posts/r2 + create_post_from_keys + CreatePostForm R2/로컬 분기
- [x] **4-3** Growth Club `PostCard` → 새 url.ts import `[S]`
- [x] **4-4** Profile 업로드 → resolveUploadUrl 적용 `[S]`
- [x] **4-5** ActionKit Library 다운로드 → useFileDownload `[M]`
- [x] **4-6** LawGuide + Ops 다운로드 → useFileDownload `[S]`
- [x] **4-7** 기존 upload-url.ts re-export `[S]`
- [x] **4-8** ESLint 통과 확인 `[S]` — 0 errors

---

## Phase 4B: File 테이블 공통화

> 기존 `ActionKitFile`, `GrowthClubPostAttachment`, `UserProfile.profile_img`를
> 단일 `files` 테이블로 통합 (polymorphic: `owner_type` + `owner_id`)
>
> **전략: 듀얼 라이트** — 기존 모델 유지 + File 모델에도 동시 기록

- [x] **4B-1** `File` SQLModel 모델 생성 `[M]` — app/models/file.py, 복합 인덱스 포함
- [x] **4B-2** `FileRepository` CRUD 구현 `[M]` — app/repositories/file_repository.py
- [x] **4B-3** Alembic 마이그레이션 — `files` 테이블 생성 `[S]` — 014_files_table.py, DB 적용 완료
- [x] **4B-4** 데이터 마이그레이션 스크립트 `[L]` — scripts/migrate_files_table.py, 67건 마이그레이션 + 검증 PASS
- [x] **4B-5** FK 재매핑 `[M]` — 마이그레이션 스크립트 내 remap_fk(), 0건 (orphan 없음)
- [x] **4B-6** ActionKit 서비스 → File 듀얼 라이트 `[M]` — upload_item_file에 File 레코드 동시 생성
- [x] **4B-7** Growth Club 서비스 → delete_by_owner 추가 `[M]` — delete_post에서 File 레코드도 삭제
- [x] **4B-8** Profile 서비스 → File 듀얼 라이트 `[S]` — save_profile_image에 File 레코드 생성
- [x] **4B-9** API 응답 스키마 호환성 확인 `[S]` — 기존 DTO 유지, 변경 없음
- [x] **4B-10** File 모델 단위 테스트 `[M]` — tests/repositories/test_file_repository.py, 12 tests passed

---

## Phase 5: 기존 파일 R2 마이그레이션 + 검증

- [x] **5-1** DB object_key 경로 형식 정규화 `[M]` — 확인 결과 이미 순수 key 형식, 정규화 불필요
- [x] **5-2** R2 마이그레이션 스크립트 작성 `[L]` — scripts/migrate_to_r2.py (files 테이블 기반)
- [ ] **5-3** R2 마이그레이션 실행 + 검증 `[M]` — STORAGE_BACKEND=r2 설정 후 실행 필요
- [ ] **5-4** Docker Compose R2 환경변수 + 모드 전환 `[S]`
- [ ] **5-5** E2E 검증 `[L]` — R2 모드에서 전체 Feature 정상 동작 확인
- [ ] **5-6** 롤백 절차 문서화 `[S]`

---

## Quality Gates

- [x] `cd app-backend && uv run pytest -q` — 396 passed, 10 skipped
- [x] `cd app-frontend && pnpm lint` — 0 errors
- [x] `files` 테이블 Alembic 마이그레이션 적용 완료
- [x] `files` 테이블 데이터 마이그레이션 67건 + 검증 PASS
- [ ] `STORAGE_BACKEND=local` 기존 동작 100% 유지
- [ ] `STORAGE_BACKEND=r2` 전환 시 전체 Feature 정상
- [ ] Cascade Delete 대체 로직 검증 (orphan 레코드 없음)

---

## 태스크 요약

| Phase | 태스크 수 | 완료 | 잔여 |
|-------|----------|------|------|
| Phase 0 | 6 | 6 | 0 |
| Phase 1 | 6 | 6 | 0 |
| Phase 2 | 9 | 9 | 0 |
| Phase 3 | 7 | 7 | 0 |
| Phase 4 | 8 | 8 | 0 |
| Phase 4B | 10 | 10 | 0 |
| Phase 5 | 6 | 2 | 4 |
| **총합** | **52** | **48** | **4** |
