# R2 스토리지 실전 통합 - 종합 계획서

> Last Updated: 2026-03-06
> 선행 작업: `docs/dev/done/r2-storage-migration/` (인프라 계층 구축 완료)

---

## Executive Summary

이전 단계에서 `StorageBackend` 추상화, `R2StorageBackend`, `File` 모델, `FileRepository`, 프론트엔드 공통 모듈(`useFileUpload`, `useFileDownload`, `resolveUploadUrl`)을 **구현했지만, 실제 Feature 코드에 연결하지 않았다.** 본 계획은 이 "마지막 1마일"을 완성한다.

**현재 상태:** 인프라 계층만 존재, Feature 코드는 여전히 로컬 파일시스템 직접 접근(12곳)
**목표:** 모든 파일 I/O를 `StorageBackend` 추상화를 통해 처리, `STORAGE_BACKEND=r2` 전환 시 즉시 동작

---

## 1. Current State — 무엇이 안 되어 있는가

### 1.1 백엔드 미완성 항목

| # | 문제 | 파일 | 라인 |
|---|------|------|------|
| 1 | **`config.py`에 R2 환경변수 미정의** | `app/core/config.py` | 53-59 |
| 2 | **storage 라우터 미등록** — presign 엔드포인트 호출 불가 | `app/api/v1/api.py` | 전체 |
| 3 | **`.env.example`에 R2 변수 없음** | `.env.example` | 33-39 |
| 4 | ActionKit `upload_item_file()` — 로컬 저장 | `actionkit/service.py` | 205-208 |
| 5 | ActionKit `_resolve_file()` — 로컬 읽기 | `actionkit/files.py` | 93-107 |
| 6 | ActionKit `view` — `open(file_path)` | `actionkit/files.py` | 128, 144 |
| 7 | ActionKit `download` — `FileResponse(path=)` | `actionkit/files.py` | 163 |
| 8 | GrowthClub `create_post()` — `write_bytes()` | `post_service.py` | 85, 100 |
| 9 | GrowthClub `_remove_saved_files()` — `unlink()` | `post_service.py` | 49-60 |
| 10 | Profile `save_profile_image()` — `open(filepath, "wb")` | `profile/service.py` | 95-97 |
| 11 | `main.py` StaticFiles — 항상 마운트 | `main.py` | 74-77, 132-139 |
| 12 | `file_pipeline.py` — `save_upload_to_path()` 로컬 전용 | `file_pipeline.py` | 42-49 |

### 1.2 프론트엔드 미완성 항목

| # | 문제 | 파일 |
|---|------|------|
| 1 | `PostCard` — 구 `growth-club/utils/upload-url` import | `PostCard.tsx` |
| 2 | `CommentSection` — 구 import | `CommentSection.tsx` |
| 3 | `profile/page.tsx` — URL 직접 조합 (`${apiHost}/api/uploads/...`) | `profile/page.tsx:233` |
| 4 | `ActionKitLibraryView` — `NEXT_PUBLIC_API_BASE_URL` 하드코딩 다운로드 | `ActionKitLibraryView.tsx` |
| 5 | `LawGuideView` — 동일 패턴 | `LawGuideView.tsx` |
| 6 | `CreatePostForm` — FormData 직접 업로드 (R2 미대응) | `CreatePostForm.tsx` |
| 7 | `actionkit-edit-modal` — FormData 직접 업로드 | `actionkit-edit-modal.tsx` |
| 8 | `.env.example` — `NEXT_PUBLIC_STORAGE_URL` 없음 | `.env.example` |

### 1.3 만들었지만 연결 안 된 것

| 모듈 | 실제 사용 |
|------|----------|
| `StorageBackend` ABC + `LocalStorageBackend` + `R2StorageBackend` | **0곳** |
| `get_storage_backend()` 팩토리 | **storage.py** 1곳뿐 |
| `FileRepository` | **쓰기만** (듀얼 라이트) — 읽기 경로는 여전히 구 Repository |
| `useFileUpload` hook | **0곳** |
| `useFileDownload` hook | **0곳** |
| `shared/file/utils/url.ts` `resolveUploadUrl` | **0곳** — 여전히 growth-club 버전 사용 |
| `shared/file/utils/validation.ts` | **0곳** |

---

## 2. Proposed Architecture

### 2.1 파일 업로드 흐름 (R2 모드)

```
[Frontend]                    [Backend]                    [R2]
    │                             │                          │
    ├──POST /storage/presign──────►│ key 생성 + presign URL   │
    │◄────{upload_url, key}───────│                          │
    │                             │                          │
    ├──PUT upload_url─────────────┼──────────────────────────►│ 파일 저장
    │                             │                          │
    ├──POST /posts (JSON body)────►│ DB 레코드 생성           │
    │  {title, keys: [key1,..]}   │ (key만 저장, 파일 X)     │
```

### 2.2 파일 업로드 흐름 (로컬 모드 — 기존 유지)

```
[Frontend]                    [Backend]
    │                             │
    ├──POST /posts (FormData)─────►│ 파일 수신 + 로컬 저장
    │  multipart files            │ storage.put(key, data)
```

### 2.3 파일 표시/다운로드 (R2 모드)

```
[Frontend]                    [R2]
    │                          │
    ├──resolveUploadUrl()──────►│  NEXT_PUBLIC_STORAGE_URL/{key}
    │  (이미지 <img src=...>)   │
    │                          │
    ├──useFileDownload({ url }) │  직접 fetch
```

### 2.4 ActionKit 뷰어/다운로드 (R2 모드 — 특수)

```
[Frontend]                    [Backend]                    [R2]
    │                             │                          │
    ├──GET /items/{id}/view───────►│                          │
    │                             ├──storage.get(key)────────►│
    │                             │◄─bytes───────────────────│
    │◄──HTML (MD) / Response──────│  (PDF: 307 redirect)     │
    │                             │                          │
    ├──GET /items/{id}/download───►│  (307 → R2 public URL)  │
```

---

## 3. Implementation Phases

### Phase 1: 인프라 연결 완성

**목표:** 현재 끊어진 설정/라우팅을 완성하여 presign 엔드포인트가 실제로 동작하게 만든다.

| 태스크 | 내용 | Effort | 의존 |
|--------|------|--------|------|
| **1-1** | `config.py`에 R2 환경변수 추가 (`STORAGE_BACKEND`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL`) | S | - |
| **1-2** | `api.py`에 storage 라우터 등록 | S | - |
| **1-3** | `app-backend/.env.example` R2 변수 추가 | S | 1-1 |
| **1-4** | `app-frontend/.env.example`에 `NEXT_PUBLIC_STORAGE_URL` 추가 | S | - |
| **1-5** | `factory.py`에서 `getattr` 제거, `settings.STORAGE_BACKEND` 직접 사용 | S | 1-1 |

**완료 기준:** `POST /api/v1/storage/presign`이 R2 모드에서 200 응답, 로컬 모드에서 422 응답.

---

### Phase 2: 백엔드 서비스 → StorageBackend 전환

**목표:** 3개 Feature 서비스의 파일 I/O를 `get_storage_backend()` 호출로 교체한다. 로컬 모드에서 기존과 동일하게 동작해야 한다.

| 태스크 | 내용 | Effort | 의존 |
|--------|------|--------|------|
| **2-1** | ActionKit `service.py` — `save_upload_to_path()` → `storage.put()` | M | 1-1 |
| **2-2** | ActionKit `file_pipeline.py` — `save_upload_to_path()` 리팩터 (StorageBackend 위임) | S | 2-1 |
| **2-3** | GrowthClub `post_service.py` — `create_post()` 파일 저장 → `storage.put()` | M | 1-1 |
| **2-4** | GrowthClub `post_service.py` — `_remove_saved_files()` → `storage.delete()` | S | 2-3 |
| **2-5** | Profile `service.py` — `save_profile_image()` → `storage.put()` | S | 1-1 |
| **2-6** | `main.py` StaticFiles 조건부 마운트 (로컬일 때만) | S | 1-1 |
| **2-7** | 기존 테스트 통과 확인 (`uv run pytest -q`) | S | 2-1~2-6 |

**완료 기준:** `STORAGE_BACKEND=local`로 pytest 전체 통과. `Path.write_bytes()`, `open()`, `unlink()` 직접 호출 0곳.

**상세 변경:**

```python
# 2-1: actionkit/service.py (before)
destination = Path(settings.ACTIONKIT_STORAGE_PATH) / object_key
size_bytes, checksum = await save_upload_to_path(upload_file, destination=destination)

# 2-1: actionkit/service.py (after)
storage = get_storage_backend()
data = await upload_file.read()
result = await storage.put(f"actionkit/{object_key}", data, content_type=mime_type)
size_bytes, checksum = result.size_bytes, result.checksum
```

```python
# 2-3: post_service.py (before)
file_path, object_key = _build_upload_path("image", upload.filename)
file_path.parent.mkdir(parents=True, exist_ok=True)
file_path.write_bytes(data)

# 2-3: post_service.py (after)
object_key = _build_object_key("image", upload.filename)  # 상대 경로만
storage = get_storage_backend()
await storage.put(object_key, data, content_type=upload.content_type or "application/octet-stream")
```

```python
# 2-4: post_service.py (before)
def _remove_saved_files(object_keys: list[str]) -> None:
    for key in object_keys:
        target = settings.STORAGE_ROOT_PATH / key
        target.unlink()

# 2-4: post_service.py (after)
async def _remove_saved_files(object_keys: list[str]) -> None:
    storage = get_storage_backend()
    for key in object_keys:
        await storage.delete(key)
```

```python
# 2-5: profile/service.py (before)
with open(filepath, "wb") as buffer:
    content = await file.read()
    buffer.write(content)

# 2-5: profile/service.py (after)
storage = get_storage_backend()
content = await file.read()
object_key = f"profile/{filename}"
await storage.put(object_key, content, content_type=file.content_type or "image/png")
```

---

### Phase 3: ActionKit 뷰어/다운로드 R2 대응

**목표:** ActionKit 파일 뷰어(`/view`), 다운로드(`/download`), StaticFiles 정적 경로가 R2에서도 동작하게 한다.

| 태스크 | 내용 | Effort | 의존 |
|--------|------|--------|------|
| **3-1** | `_resolve_file()` → StorageBackend 사용 (R2: `storage.get()`, Local: 기존 경로) | M | 2-1 |
| **3-2** | `/view` 엔드포인트 — R2에서 bytes 가져와 렌더링 (MD→HTML, PDF→redirect) | M | 3-1 |
| **3-3** | `/download` 엔드포인트 — R2 모드: 307 redirect to public URL | S | 3-1 |
| **3-4** | ActionKit `_to_public_path()` — R2 모드에서 public URL 반환 | S | 1-1 |

**완료 기준:** R2 모드에서 ActionKit PDF 뷰어/다운로드/Markdown 렌더링 정상 동작.

**상세 변경:**

```python
# 3-1: files.py _resolve_file() (before)
repo = ActionKitRepository(session)
files = await repo.list_current_files(item_ids=[item_id])
file_path = os.path.join(settings.ACTIONKIT_STORAGE_PATH, current_file.object_key)
if not os.path.exists(file_path):
    raise HTTPException(404)

# 3-1: files.py _resolve_file() (after)
storage = get_storage_backend()
repo = ActionKitRepository(session)
files = await repo.list_current_files(item_ids=[item_id])
current_file = files[0]
# R2 key에 "actionkit/" prefix 추가
storage_key = f"actionkit/{current_file.object_key}"
return storage_key, current_file, storage

# 3-2: /view (R2 모드)
if ext == ".pdf":
    # PDF → R2 public URL로 redirect
    return RedirectResponse(storage.get_public_url(storage_key), status_code=307)
elif ext in (".md", ".markdown"):
    # Markdown → R2에서 fetch 후 HTML 변환
    content = await storage.get(storage_key)
    md_text = content.decode("utf-8")
    ...

# 3-3: /download (R2 모드)
return RedirectResponse(storage.get_public_url(storage_key), status_code=307)
```

---

### Phase 4: 프론트엔드 공통 모듈 적용

**목표:** 모든 컴포넌트가 `shared/file/` 공통 모듈을 사용하도록 전환한다.

| 태스크 | 내용 | Effort | 의존 |
|--------|------|--------|------|
| **4-1** | `PostCard.tsx` — import를 `@/features/shared/file`로 변경 | S | - |
| **4-2** | `CommentSection.tsx` — import 변경 | S | - |
| **4-3** | `profile/page.tsx` — `apiHost` URL 직접 조합 → `resolveUploadUrl()` 사용 | S | - |
| **4-4** | `ActionKitLibraryView.tsx` — 다운로드 URL에 `NEXT_PUBLIC_STORAGE_URL` 분기 추가 | M | - |
| **4-5** | `LawGuideView.tsx` — 다운로드 URL R2 분기 추가 | S | 4-4 |
| **4-6** | `growth-club/utils/upload-url.ts` → `shared/file` re-export로 변경 | S | 4-1 |
| **4-7** | ESLint 통과 확인 (`pnpm lint`) | S | 4-1~4-6 |

**완료 기준:** 모든 파일 URL이 `resolveUploadUrl()` 또는 `useFileDownload`를 통해 생성됨. `NEXT_PUBLIC_STORAGE_URL` 설정 시 R2 URL 반환.

---

### Phase 5: R2 업로드 흐름 전환 (Presigned URL)

**목표:** R2 모드에서 프론트엔드가 Presigned URL로 직접 R2에 업로드하고, 백엔드에는 key만 전달한다.

| 태스크 | 내용 | Effort | 의존 |
|--------|------|--------|------|
| **5-1** | `CreatePostForm.tsx` — R2 모드: `useFileUpload` → presigned upload → `createPostR2()` | M | 1-2, Phase 4 |
| **5-2** | `actionkit-edit-modal.tsx` — R2 모드: `useFileUpload` → presigned upload | M | 1-2 |
| **5-3** | `profile/page.tsx` — R2 모드: `useFileUpload` → presigned upload → 메타데이터 API | M | 1-2 |
| **5-4** | presign 엔드포인트에 `actionkit` kind 추가 | S | 5-2 |
| **5-5** | Profile 메타데이터 등록 API (R2 모드용 — key만 받아 DB 업데이트) | M | 5-3 |

**완료 기준:** R2 모드에서 Growth Club 게시글 작성, ActionKit 파일 업로드, 프로필 이미지 변경이 Presigned URL로 동작.

**주의:** 로컬 모드에서는 기존 FormData 업로드 유지 (분기 처리).

---

### Phase 6: 마이그레이션 실행 + E2E 검증

**목표:** 기존 로컬 파일을 R2로 마이그레이션하고, 전체 Feature 정상 동작을 검증한다.

| 태스크 | 내용 | Effort | 의존 |
|--------|------|--------|------|
| **6-1** | Docker Compose R2 환경변수 설정 | S | 1-1 |
| **6-2** | R2 마이그레이션 스크립트 실행 (`scripts/migrate_to_r2.py`) | M | Phase 2-3 |
| **6-3** | R2 마이그레이션 검증 (`--verify`) | S | 6-2 |
| **6-4** | E2E: ActionKit 업로드 → 뷰어 → 다운로드 | M | Phase 3 |
| **6-5** | E2E: Growth Club 게시글 생성(이미지+파일) → 표시 → 삭제 | M | Phase 5 |
| **6-6** | E2E: 프로필 이미지 업로드 → 표시 | S | Phase 5 |
| **6-7** | E2E: 로컬 모드 기존 동작 100% 유지 검증 | M | Phase 2 |
| **6-8** | 롤백 절차 문서화 | S | - |

**완료 기준:** R2 모드 + 로컬 모드 양쪽에서 전체 Feature 정상 동작.

---

## 4. Risk Assessment

| 리스크 | 심각도 | 대응 |
|--------|--------|------|
| `_remove_saved_files()` 동기→비동기 전환 시 호출부 수정 누락 | 높음 | 2-4에서 모든 호출부 확인 (delete_post 내 try/except 구조 유지) |
| ActionKit `actionkit/` prefix 불일치 | 높음 | object_key에 prefix 추가 시 기존 DB 레코드와 일치 여부 검증 |
| presign 엔드포인트 인증 없이 호출 가능한 보안 이슈 | 중간 | 이미 `get_current_user` 의존성 적용됨 — 확인만 |
| R2 업로드 실패 시 DB 트랜잭션 불일치 | 중간 | presigned URL 방식은 프론트에서 업로드 → 백엔드 DB만 기록이므로 안전 |
| `DecodingStaticFiles` 한국어 인코딩 R2 전환 시 깨짐 | 낮음 | R2는 UTF-8 key 네이티브 지원, 인코딩 처리 불필요 |

---

## 5. Success Metrics

1. **로컬 직접 접근 0곳**: `Path.write_bytes()`, `open(file, "wb")`, `unlink()`, `FileResponse(path=)` 사용 0건
2. **pytest 통과**: 로컬 모드에서 기존 테스트 전체 통과
3. **ESLint 통과**: 프론트엔드 0 errors
4. **R2 E2E**: ActionKit + Growth Club + Profile 전체 흐름 동작
5. **로컬 호환**: `STORAGE_BACKEND=local`에서 기존과 100% 동일 동작
6. **환경변수 전환**: config 변경만으로 local ↔ r2 즉시 전환 가능

---

## 6. Dependencies

### 이미 완료된 선행 작업

- `app/services/storage/` 패키지 (base, local, r2, factory)
- `app/models/file.py` + `app/repositories/file_repository.py`
- `alembic/versions/014_files_table.py` (files 테이블)
- 데이터 마이그레이션 완료 (67건)
- `app/api/v1/storage.py` (presign 엔드포인트 코드)
- `app-frontend/src/features/shared/file/` (hooks, utils)
- Growth Club `POST /posts/r2` 엔드포인트 + `createPostR2()` API

### 추가 필요 패키지

없음 — `boto3`는 이미 설치됨

---

## 7. 태스크 요약

| Phase | 태스크 수 | Effort |
|-------|----------|--------|
| Phase 1: 인프라 연결 | 5 | S×5 |
| Phase 2: 백엔드 전환 | 7 | M×3 + S×4 |
| Phase 3: ActionKit R2 | 4 | M×2 + S×2 |
| Phase 4: 프론트엔드 전환 | 7 | M×1 + S×6 |
| Phase 5: R2 업로드 | 5 | M×4 + S×1 |
| Phase 6: 마이그레이션+E2E | 8 | M×4 + S×4 |
| **총합** | **36** | |
