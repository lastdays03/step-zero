# R2 스토리지 실전 통합 - 태스크 체크리스트

> Last Updated: 2026-03-06

---

## Phase 1: 인프라 연결 완성

- [ ] **1-1** `config.py`에 R2 환경변수 추가 `[S]`
  - `STORAGE_BACKEND: str = "local"`
  - `R2_ACCOUNT_ID: str = ""`
  - `R2_ACCESS_KEY_ID: str = ""`
  - `R2_SECRET_ACCESS_KEY: str = ""`
  - `R2_BUCKET_NAME: str = "stepzero-uploads"`
  - `R2_PUBLIC_URL: str = ""`
- [ ] **1-2** `api.py`에 storage 라우터 등록 `[S]`
  - `from app.api.v1.storage import router as storage_router`
  - `api_router.include_router(storage_router, prefix="/storage", tags=["storage"])`
- [ ] **1-3** `app-backend/.env.example`에 R2 변수 추가 `[S]`
  - `STORAGE_BACKEND=local`, `R2_ACCOUNT_ID=`, `R2_ACCESS_KEY_ID=`, ...
- [ ] **1-4** `app-frontend/.env.example`에 `NEXT_PUBLIC_STORAGE_URL=` 추가 `[S]`
- [ ] **1-5** `factory.py` — `getattr(settings, "STORAGE_BACKEND", "local")` → `settings.STORAGE_BACKEND` `[S]`

---

## Phase 2: 백엔드 서비스 → StorageBackend 전환

- [ ] **2-1** ActionKit `service.py` — `storage.put()` 전환 `[M]`
  - `save_upload_to_path()` → `storage.put(f"actionkit/{object_key}", data, mime_type)`
  - `get_storage_backend()` import
  - `file_checksum()` → `result.checksum` 사용 (StorageResult에서 반환)
  - 듀얼 라이트 유지 (File 레코드)
- [ ] **2-2** ActionKit `file_pipeline.py` 리팩터 `[S]`
  - `save_upload_to_path()` 사용처 제거 (2-1에서 대체)
  - `file_checksum()` 유지 (다른 곳에서 사용 여부 확인)
  - `build_object_key()`, `normalize_filename()`, `detect_mime_type()` 유지
- [ ] **2-3** GrowthClub `post_service.py` — 파일 저장 전환 `[M]`
  - `_build_upload_path()` → `_build_object_key()` (상대 경로만 반환, 절대 경로 제거)
  - `file_path.write_bytes(data)` → `await storage.put(object_key, data, content_type)`
  - `file_path.parent.mkdir()` 제거 (StorageBackend가 처리)
  - `settings.STORAGE_ROOT_PATH` 직접 참조 제거
- [ ] **2-4** GrowthClub `post_service.py` — 파일 삭제 전환 `[S]`
  - `_remove_saved_files()` → `async def` 변경
  - `target.unlink()` → `await storage.delete(key)`
  - `create_post()` 롤백 호출부 `await` 추가 (line 155)
  - `delete_post()` 호출부 `await` 추가 (line 182)
- [ ] **2-5** Profile `service.py` — 파일 저장 전환 `[S]`
  - `open(filepath, "wb")` + `buffer.write()` → `await storage.put(object_key, content, content_type)`
  - `self.upload_dir` 초기화 제거 (StorageBackend가 관리)
  - `__init__`에서 `mkdir` 제거
- [ ] **2-6** `main.py` — StaticFiles 조건부 마운트 `[S]`
  - `if settings.STORAGE_BACKEND != "r2":` 으로 감싸기
  - uploads 마운트 + actionkit-files 마운트 모두
- [ ] **2-7** 테스트 통과 확인 `[S]`
  - `cd app-backend && uv run pytest -q`
  - 기존 테스트가 로컬 모드에서 통과하는지 확인

---

## Phase 3: ActionKit 뷰어/다운로드 R2 대응

- [ ] **3-1** `_resolve_file()` → StorageBackend 사용 `[M]`
  - `os.path.join()` + `os.path.exists()` 제거
  - R2: `storage_key = f"actionkit/{current_file.object_key}"`
  - Local: `storage.get_local_path(f"actionkit/{key}")` 사용
  - 반환값 변경: `(storage_key, current_file, storage)`
- [ ] **3-2** `/view` 엔드포인트 R2 대응 `[M]`
  - PDF → `RedirectResponse(storage.get_public_url(key), status_code=307)`
  - Markdown → `content = await storage.get(key)` → HTML 변환
  - 기타 → `Response(content=await storage.get(key), media_type=...)`
- [ ] **3-3** `/download` 엔드포인트 R2 대응 `[S]`
  - R2: `RedirectResponse(storage.get_public_url(key), status_code=307)`
  - Local: 기존 `FileResponse(path=...)` 유지
- [ ] **3-4** `_to_public_path()` R2 대응 `[S]`
  - R2: `storage.get_public_url(f"actionkit/{object_key}")`
  - Local: 기존 `actionkits/files/{object_key}` 유지

---

## Phase 4: 프론트엔드 공통 모듈 적용

- [ ] **4-1** `PostCard.tsx` import 변경 `[S]`
  - `from '../utils/upload-url'` → `from '@/features/shared/file'`
- [ ] **4-2** `CommentSection.tsx` import 변경 `[S]`
  - 동일 패턴
- [ ] **4-3** `profile/page.tsx` URL 생성 통일 `[S]`
  - `${apiHost}/api/uploads/${profile.profile_img}` → `resolveUploadUrl(profile.profile_img)`
  - `apiHost` 변수 제거 (더 이상 불필요할 경우)
  - `import { resolveUploadUrl } from '@/features/shared/file'`
- [ ] **4-4** `ActionKitLibraryView.tsx` 다운로드 URL R2 분기 `[M]`
  - `NEXT_PUBLIC_STORAGE_URL` 존재 시 → R2 URL 사용
  - 단일 다운로드: `resolveActionKitUrl(path)` 헬퍼 생성 또는 인라인
  - 일괄 다운로드: 동일 분기 적용
  - 레거시 `library/resources/` 변환 유지
- [ ] **4-5** `LawGuideView.tsx` 다운로드 URL R2 분기 `[S]`
  - 4-4와 동일 패턴 적용
- [ ] **4-6** `growth-club/utils/upload-url.ts` re-export `[S]`
  - `export { resolveUploadUrl } from '@/features/shared/file'`
  - (기존 import 호환성 유지)
- [ ] **4-7** ESLint 통과 확인 `[S]`
  - `cd app-frontend && pnpm lint`

---

## Phase 5: R2 업로드 흐름 전환 (Presigned URL)

- [ ] **5-1** `CreatePostForm.tsx` R2 모드 업로드 `[M]`
  - `isR2Mode = !!process.env.NEXT_PUBLIC_STORAGE_URL`
  - R2: `useFileUpload` → presigned upload → `growthClubApi.createPostR2({attachment_keys})`
  - Local: 기존 FormData 흐름 유지
  - 진행률 표시 (progress state)
- [ ] **5-2** `actionkit-edit-modal.tsx` R2 모드 업로드 `[M]`
  - R2: `useFileUpload` → presigned upload → 메타데이터 API
  - Local: 기존 FormData 유지
- [ ] **5-3** `profile/page.tsx` R2 모드 업로드 `[M]`
  - R2: `useFileUpload({ kind: 'profile' })` → presigned upload → 메타데이터 API
  - Local: 기존 FormData 유지
- [ ] **5-4** presign 엔드포인트 `actionkit` kind 추가 `[S]`
  - `ALLOWED_KINDS`에 `"actionkit"` 추가
  - `_build_key()` actionkit 분기 추가
- [ ] **5-5** Profile R2 메타데이터 API `[M]`
  - `POST /api/v1/profile/me/image/r2` — `{key: string}` body
  - DB에 `profile_img = key` 업데이트 + File 레코드 생성

---

## Phase 6: 마이그레이션 실행 + E2E 검증

- [ ] **6-1** Docker Compose R2 환경변수 설정 `[S]`
  - `docker-compose.dev.yml`에 R2 변수 전달
- [ ] **6-2** R2 마이그레이션 스크립트 실행 `[M]`
  - `STORAGE_BACKEND=r2 uv run python scripts/migrate_to_r2.py --dry-run`
  - `STORAGE_BACKEND=r2 uv run python scripts/migrate_to_r2.py`
- [ ] **6-3** 마이그레이션 검증 `[S]`
  - `STORAGE_BACKEND=r2 uv run python scripts/migrate_to_r2.py --verify`
- [ ] **6-4** E2E: ActionKit 전체 흐름 `[M]`
  - 업로드 → 뷰어(PDF) → 뷰어(MD) → 다운로드
- [ ] **6-5** E2E: Growth Club 전체 흐름 `[M]`
  - 게시글 생성(이미지+파일) → PostCard 표시 → 삭제
- [ ] **6-6** E2E: Profile 전체 흐름 `[S]`
  - 이미지 업로드 → 프로필 페이지 표시
- [ ] **6-7** E2E: 로컬 모드 검증 `[M]`
  - `STORAGE_BACKEND=local`로 전체 Feature 동작 확인
- [ ] **6-8** 롤백 절차 문서화 `[S]`
  - 환경변수 전환 절차
  - StaticFiles 복원 확인
  - 데이터 일관성 검증 방법

---

## Quality Gates

- [ ] `cd app-backend && uv run pytest -q` — 전체 통과
- [ ] `cd app-frontend && pnpm lint` — 0 errors
- [ ] `STORAGE_BACKEND=local` 기존 동작 100% 유지
- [ ] `STORAGE_BACKEND=r2` 전환 시 전체 Feature 정상
- [ ] 로컬 파일 직접 접근 코드 0곳 (Path.write_bytes, open, unlink, FileResponse(path=))

---

## 태스크 요약

| Phase | 태스크 수 | 완료 | 잔여 |
|-------|----------|------|------|
| Phase 1 | 5 | 0 | 5 |
| Phase 2 | 7 | 0 | 7 |
| Phase 3 | 4 | 0 | 4 |
| Phase 4 | 7 | 0 | 7 |
| Phase 5 | 5 | 0 | 5 |
| Phase 6 | 8 | 0 | 8 |
| **총합** | **36** | **0** | **36** |
