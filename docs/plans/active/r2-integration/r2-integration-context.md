# R2 스토리지 실전 통합 - 컨텍스트 & 의존성

> Last Updated: 2026-03-06

---

## 변경 대상 파일 목록

### 백엔드 - 수정 대상

| # | 파일 경로 | 변경 내용 | Phase |
|---|----------|----------|-------|
| 1 | `app/core/config.py` | `STORAGE_BACKEND`, `R2_*` 환경변수 6개 추가 | 1 |
| 2 | `app/api/v1/api.py` | storage 라우터 등록 | 1 |
| 3 | `app/services/storage/factory.py` | `getattr` → `settings.STORAGE_BACKEND` 직접 참조 | 1 |
| 4 | `.env.example` | R2 환경변수 템플릿 추가 | 1 |
| 5 | `app/features/actionkit/application/service.py` | `save_upload_to_path()` → `storage.put()` | 2 |
| 6 | `app/features/actionkit/application/file_pipeline.py` | `save_upload_to_path()` 리팩터 or 삭제 | 2 |
| 7 | `app/features/growth_club/application/post_service.py` | `write_bytes()` → `storage.put()`, `unlink()` → `storage.delete()` | 2 |
| 8 | `app/features/profile/application/service.py` | `open(filepath, "wb")` → `storage.put()` | 2 |
| 9 | `app/main.py` | StaticFiles 조건부 마운트 | 2 |
| 10 | `app/api/v1/actionkit/files.py` | `_resolve_file()`, `/view`, `/download` R2 대응 | 3 |
| 11 | `app/api/v1/storage.py` | `actionkit` kind 추가 | 5 |
| 12 | `app/api/v1/profile/me.py` | R2 모드용 메타데이터 API (선택) | 5 |

### 프론트엔드 - 수정 대상

| # | 파일 경로 | 변경 내용 | Phase |
|---|----------|----------|-------|
| 1 | `.env.example` | `NEXT_PUBLIC_STORAGE_URL` 추가 | 1 |
| 2 | `growth-club/components/PostCard.tsx` | import → `@/features/shared/file` | 4 |
| 3 | `growth-club/components/CommentSection.tsx` | import 변경 | 4 |
| 4 | `(dashboard)/profile/page.tsx` | `apiHost` 직접조합 → `resolveUploadUrl()` | 4 |
| 5 | `actionkit/components/ActionKitLibraryView.tsx` | 다운로드 URL R2 분기 | 4 |
| 6 | `actionkit/components/LawGuideView.tsx` | 다운로드 URL R2 분기 | 4 |
| 7 | `growth-club/utils/upload-url.ts` | `shared/file` re-export | 4 |
| 8 | `growth-club/components/CreatePostForm.tsx` | R2: useFileUpload + createPostR2 | 5 |
| 9 | `ops/actionkit/components/actionkit-edit-modal.tsx` | R2: useFileUpload | 5 |

---

## 기술 결정 사항

### 1. object_key prefix 전략

**결정:** ActionKit 파일의 R2 key에 `actionkit/` prefix를 추가한다.

**근거:**
- DB의 `ActionKitFile.object_key`는 `laws/chapter-1/3/v1/file.pdf` 형태 (prefix 없음)
- 로컬 저장 시 `ACTIONKIT_STORAGE_PATH/` 아래에 저장되므로 prefix가 암묵적
- R2 버킷에서는 namespace 분리 필요 → `actionkit/` prefix 추가
- `migrate_to_r2.py` 스크립트에서 `to_r2_key()` 함수가 이미 이 prefix를 추가함

**영향:** 서비스 코드에서 `storage.put(f"actionkit/{object_key}", ...)` 호출, DB에는 여전히 prefix 없는 key 저장.

### 2. `_remove_saved_files()` 동기→비동기 전환

**결정:** `async def`로 변경하고, `storage.delete()`를 await한다.

**영향 범위:**
- `post_service.py:155` — `create_post()` 롤백 시 호출 → `await` 추가
- `post_service.py:182` — `delete_post()` 후 호출 → `await` 추가
- 두 곳 모두 이미 async 컨텍스트 안이므로 문제 없음

### 3. StaticFiles 조건부 마운트

**결정:** `STORAGE_BACKEND == "local"` 일 때만 StaticFiles 마운트.

```python
# main.py
if settings.STORAGE_BACKEND != "r2":
    app.mount("/api/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")
    app.mount("/api/v1/actionkits/files", DecodingStaticFiles(...), name="actionkit-files")
```

**근거:** R2 모드에서 StaticFiles가 마운트되면 로컬 파일이 없어 404 발생. R2에서는 프론트엔드가 R2 Public URL로 직접 접근.

### 4. ActionKit 뷰어 R2 처리

**결정:**
- **PDF/이미지** → R2 public URL로 307 redirect (서버 프록시 불필요)
- **Markdown** → R2에서 fetch → 서버에서 HTML 변환 후 응답 (marked.js 렌더링)

**근거:** Markdown 뷰어는 서버사이드 HTML 생성이 필요하므로 redirect 불가. PDF/이미지는 브라우저가 직접 렌더링 가능.

### 5. 프론트엔드 R2 모드 감지

**결정:** `process.env.NEXT_PUBLIC_STORAGE_URL` 존재 여부로 R2 모드 판별.

```typescript
const isR2Mode = !!process.env.NEXT_PUBLIC_STORAGE_URL;
```

**사용처:** CreatePostForm (업로드 방식 분기), resolveUploadUrl (URL base 분기)

### 6. ActionKit 다운로드 URL 처리

**결정:** ActionKitLibraryView/LawGuideView에서 다운로드 시:
- R2 모드: `NEXT_PUBLIC_STORAGE_URL + "/actionkit/" + path` 로 직접 접근
- 로컬 모드: 기존 `NEXT_PUBLIC_API_BASE_URL + "/actionkits/files/" + path` 유지

**레거시 경로 변환:** `library/resources/` → `actionkits/files/` 변환 로직은 유지 (DB에 레거시 경로 존재 가능)

---

## 환경변수 목록

### 백엔드 (`app-backend/.env.example`)

```env
# Storage
STORAGE_BACKEND=local                  # "local" | "r2"
STORAGE_LOCAL_ROOT=

# R2 (STORAGE_BACKEND=r2 시 필수)
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=stepzero-uploads
R2_PUBLIC_URL=
```

### 프론트엔드 (`app-frontend/.env.example`)

```env
# Storage (R2 사용 시 설정)
NEXT_PUBLIC_STORAGE_URL=
```

### config.py 추가 필드

```python
# Storage
STORAGE_BACKEND: str = "local"
STORAGE_LOCAL_ROOT: str | None = None

# R2 (STORAGE_BACKEND=r2 시 필수)
R2_ACCOUNT_ID: str = ""
R2_ACCESS_KEY_ID: str = ""
R2_SECRET_ACCESS_KEY: str = ""
R2_BUCKET_NAME: str = "stepzero-uploads"
R2_PUBLIC_URL: str = ""
```

---

## 핵심 코드 참조 (이미 구현됨)

### StorageBackend 인터페이스

```
app/services/storage/base.py    → StorageBackend ABC, StorageResult
app/services/storage/local.py   → LocalStorageBackend (put/get/delete/get_public_url)
app/services/storage/r2.py      → R2StorageBackend (boto3, asyncio.to_thread)
app/services/storage/factory.py → get_storage_backend() (lru_cache)
```

### File 모델 + Repository

```
app/models/file.py              → File SQLModel (owner_type, owner_id, object_key, ...)
app/repositories/file_repository.py → CRUD + delete_by_owner + set_current + get_next_version
```

### 프론트엔드 공통 모듈

```
shared/file/utils/url.ts        → resolveUploadUrl (R2/로컬 분기)
shared/file/utils/validation.ts → validateFiles (크기/개수/확장자 검증)
shared/file/hooks/useFileUpload.ts  → presigned URL + XHR PUT + 진행률
shared/file/hooks/useFileDownload.ts → apiPath/url 분기 다운로드
shared/file/index.ts            → barrel export
```

### Growth Club R2 엔드포인트 (이미 구현됨)

```
POST /api/v1/growth-club/posts/r2  → JSON body {title, content, category, attachment_keys}
→ create_post_from_keys() 서비스 메서드
→ 프론트엔드: growthClubApi.createPostR2()
```

---

## 테스트 전략

### 로컬 모드 테스트 (기존 유지)
- `uv run pytest -q` — SQLite in-memory, STORAGE_BACKEND=local (기본값)
- 파일 I/O는 `LocalStorageBackend`를 통해 실행
- `tmpdir` 또는 `tmp_path` fixture로 격리

### R2 모드 테스트 (선택적)
- `test_storage_backend.py::test_factory_r2` — R2 환경변수 필요 (CI에서만)
- E2E는 Docker + R2 환경에서 수동 검증

### 프론트엔드 테스트
- `pnpm lint` — ESLint 0 errors
- `pnpm build` — 빌드 성공 확인
