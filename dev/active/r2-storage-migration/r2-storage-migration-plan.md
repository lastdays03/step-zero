# Cloudflare R2 파일 저장소 마이그레이션 - 종합 계획서

> Last Updated: 2026-03-04

---

## Executive Summary

StepZero 플랫폼의 파일 저장 방식을 **로컬 파일시스템**에서 **Cloudflare R2 오브젝트 스토리지**로 마이그레이션한다. 현재 3개 Feature(ActionKit, Growth Club, Profile)가 서버 로컬 디스크(`uploads/` 디렉토리)에 파일을 직접 쓰고 있으며, FastAPI `StaticFiles`로 정적 서빙하는 구조다. 이를 S3-호환 API를 사용하는 Cloudflare R2로 전환하여 **수평 확장성**, **데이터 내구성**, **CDN 통합**을 확보한다.

**핵심 설계 원칙:**
- `StorageBackend` 추상화 계층 도입으로 로컬/R2 전환 가능 (환경변수 기반)
- 기존 API 계약(엔드포인트, 응답 형식) 변경 없음
- boto3(S3 호환 SDK) 사용, Cloudflare 전용 SDK 불필요
- 프론트엔드는 URL 리졸버만 수정 (R2 Public URL 또는 Presigned URL 지원)

---

## 1. Current State Analysis

### 1.1 파일 저장 아키텍처 개요

```
app-backend/
├── uploads/                    ← STORAGE_ROOT_PATH (기본: app-backend/uploads/)
│   ├── actionkit/              ← ActionKit 파일 (PDF, Markdown 등)
│   │   └── {domain}/{category}/{item_id}/v{version}/{filename}
│   ├── growth-club/            ← Growth Club 첨부파일
│   │   ├── image/{year}/{month}/{uuid_image.ext}
│   │   └── file/{year}/{month}/{uuid_file.ext}
│   └── profile/                ← 프로필 이미지
│       └── {uuid}.{ext}
```

### 1.2 환경변수 설정 (현재)

| 변수 | 파일 | 설명 |
|------|------|------|
| `STORAGE_LOCAL_ROOT` | `app-backend/.env` | 스토리지 루트 경로 (빈값 → `app-backend/uploads/`) |
| `GROWTH_CLUB_MAX_IMAGE_MB` | `app-backend/.env` | 이미지 최대 크기 (20MB) |
| `GROWTH_CLUB_MAX_FILE_MB` | `app-backend/.env` | 파일 최대 크기 (50MB) |
| `GROWTH_CLUB_MAX_TOTAL_MB` | `app-backend/.env` | 총 첨부 크기 (200MB) |

### 1.3 StaticFiles 마운트 (현재)

`app-backend/app/main.py`에서 두 개의 정적 파일 경로를 마운트:

```python
# 1. 전체 uploads 디렉토리 서빙 (Growth Club, Profile)
app.mount("/api/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

# 2. ActionKit 전용 (DecodingStaticFiles - 한국어 파일명 이중 인코딩 처리)
app.mount(
    "/api/v1/actionkits/files",
    DecodingStaticFiles(directory=str(actionkit_storage_dir)),
    name="actionkit-files",
)
```

### 1.4 Feature별 상세 분석

#### Feature 1: ActionKit (법률/행정 키트 파일)

| 구성 요소 | 파일 경로 | 역할 |
|-----------|----------|------|
| 서비스 | `app-backend/app/features/actionkit/application/service.py` | 파일 업로드, object_key 생성, DB 레코드 관리 |
| 파이프라인 | `app-backend/app/features/actionkit/application/file_pipeline.py` | 파일 저장, 체크섬 계산, MIME 타입 감지 |
| 라우터 | `app-backend/app/api/v1/actionkit/files.py` | 업로드/뷰어/다운로드 엔드포인트 |

**파일 저장 흐름:**
1. `build_object_key()` → `{domain}/{category_slug}/{item_id}/v{version}/{filename}`
2. `save_upload_to_path()` → `ACTIONKIT_STORAGE_PATH / object_key` 경로에 파일 저장
3. `file_checksum()` → SHA-256 체크섬 계산
4. DB에 `ActionKitFile` 레코드 생성 (object_key, checksum, size_bytes 등)

**파일 접근 패턴:**
- 정적 서빙: `/api/v1/actionkits/files/{object_key}` → `DecodingStaticFiles`
- 뷰어: `GET /api/v1/actionkits/items/{item_id}/view` → 파일 읽어서 Response 반환
- 다운로드: `GET /api/v1/actionkits/items/{item_id}/download` → `FileResponse`
- 공개 경로: `_to_public_path()` → `"actionkits/files/{object_key}"`

**핵심 코드 (service.py:203-206):**
```python
destination = Path(settings.ACTIONKIT_STORAGE_PATH) / object_key
size_bytes, checksum = await save_upload_to_path(upload_file, destination=destination)
```

**핵심 코드 (file_pipeline.py:42-49):**
```python
async def save_upload_to_path(upload_file: UploadFile, *, destination: Path) -> tuple[int, str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = await upload_file.read()
    destination.write_bytes(data)
    checksum = file_checksum(destination)
    return len(data), checksum
```

#### Feature 2: Growth Club (커뮤니티 첨부파일)

| 구성 요소 | 파일 경로 | 역할 |
|-----------|----------|------|
| 서비스 | `app-backend/app/features/growth_club/application/post_service.py` | 게시글 생성/삭제, 첨부파일 저장/삭제 |

**파일 저장 흐름:**
1. `_build_upload_path(kind, filename)` → `growth-club/{kind}/{year}/{month}/{uuid}_{kind}{ext}`
2. `file_path.write_bytes(data)` → 직접 바이트 쓰기
3. `GrowthClubPostAttachment` DB 레코드 생성

**파일 삭제:**
- `_remove_saved_files(object_keys)` → `settings.STORAGE_ROOT_PATH / object_key` 경로의 파일 삭제
- 게시글 삭제 시 첨부파일도 함께 삭제

**핵심 코드 (post_service.py:39-45):**
```python
def _build_upload_path(kind: str, filename: Optional[str]) -> tuple[Path, str]:
    now = datetime.now(timezone.utc)
    relative_dir = Path("growth-club") / kind / f"{now.year}" / f"{now.month:02d}"
    generated_name = _generate_upload_name(kind, filename)
    relative_path = relative_dir / generated_name
    absolute_path = settings.STORAGE_ROOT_PATH / relative_path
    return absolute_path, relative_path.as_posix()
```

#### Feature 3: Profile (프로필 이미지)

| 구성 요소 | 파일 경로 | 역할 |
|-----------|----------|------|
| 서비스 | `app-backend/app/features/profile/application/service.py` | 프로필 이미지 저장, DB 경로 업데이트 |

**파일 저장 흐름:**
1. UUID 기반 파일명 생성: `{uuid}{ext}`
2. `self.upload_dir / filename` → `STORAGE_ROOT_PATH/profile/{uuid}.ext` 경로에 저장
3. `profile.profile_img = f"profile/{filename}"` → DB에 상대 경로 저장

**프론트엔드 URL 구성:**
- `profile/page.tsx`: `${apiHost}/api/uploads/${profile.profile_img}`
- `upload-url.ts`: `resolveUploadUrl()` → `${apiHost}/api/uploads/${normalized}`

**핵심 코드 (service.py:84-104):**
```python
async def save_profile_image(self, user_id: int, file: UploadFile) -> str:
    ext = Path(file.filename or "").suffix or ".png"
    filename = f"{uuid.uuid4()}{ext}"
    filepath = self.upload_dir / filename
    with open(filepath, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    profile.profile_img = f"profile/{filename}"
```

### 1.5 프론트엔드 URL 해석

| Feature | URL 패턴 | 해석 방식 |
|---------|---------|----------|
| ActionKit | `/api/v1/actionkits/files/{object_key}` | `_to_public_path()` → 백엔드 상대 경로 |
| Growth Club | `/api/uploads/growth-club/{kind}/{year}/{month}/{file}` | `resolveUploadUrl()` 유틸 |
| Profile | `/api/uploads/profile/{uuid}.ext` | 직접 문자열 조합 (`${apiHost}/api/uploads/...`) |

---

## 2. Proposed Future State

### 2.1 R2 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (Next.js)                                              │
│   resolveUploadUrl() → R2 Public URL 또는 Presigned URL 반환   │
└───────────┬─────────────────────────────────────────────────────┘
            │ 이미지/파일 요청
            ▼
┌───────────────────────┐     ┌─────────────────────────────────┐
│ Cloudflare R2         │     │ Backend (FastAPI)                │
│ Bucket: stepzero-*    │◄────│ StorageBackend.put() / get()    │
│                       │     │ boto3 S3Client                  │
│ /actionkit/...        │     └─────────────────────────────────┘
│ /growth-club/...      │
│ /profile/...          │
└───────────────────────┘
```

### 2.2 StorageBackend 추상화

```python
# app-backend/app/services/storage/base.py
class StorageBackend(ABC):
    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str) -> StorageResult: ...

    @abstractmethod
    async def get(self, key: str) -> bytes: ...

    @abstractmethod
    async def delete(self, key: str) -> bool: ...

    @abstractmethod
    def get_public_url(self, key: str) -> str: ...

# app-backend/app/services/storage/local.py
class LocalStorageBackend(StorageBackend): ...  # 기존 로직 래핑

# app-backend/app/services/storage/r2.py
class R2StorageBackend(StorageBackend): ...  # boto3 S3Client 사용
```

### 2.3 환경변수 기반 전환

```python
# config.py 추가 필드
STORAGE_BACKEND: str = "local"  # "local" | "r2"
R2_ACCOUNT_ID: str | None = None
R2_ACCESS_KEY_ID: str | None = None
R2_SECRET_ACCESS_KEY: str | None = None
R2_BUCKET_NAME: str = "stepzero-uploads"
R2_PUBLIC_URL: str | None = None  # e.g., "https://cdn.stepzero.dev"
```

### 2.4 R2 버킷 구조

```
stepzero-uploads/
├── actionkit/                  # ActionKit 파일 (기존 object_key 유지)
│   └── {domain}/{category}/{item_id}/v{version}/{filename}
├── growth-club/                # Growth Club 첨부
│   ├── image/{year}/{month}/{uuid_image.ext}
│   └── file/{year}/{month}/{uuid_file.ext}
└── profile/                    # 프로필 이미지
    └── {uuid}.{ext}
```

### 2.5 프론트엔드 URL 변경

```typescript
// 변경 전
const url = `${apiHost}/api/uploads/${path}`;

// 변경 후 (R2 모드)
const url = `${R2_PUBLIC_URL}/${path}`;
// 또는 백엔드 Presigned URL 엔드포인트 사용
```

`NEXT_PUBLIC_STORAGE_URL` 환경변수 추가로, 프론트엔드에서 이미지/파일 URL의 base를 동적 결정.

---

## 3. Implementation Phases

### Phase 1: StorageBackend 추상화 계층 구축

**목표:** 기존 로컬 저장 로직을 `LocalStorageBackend`로 래핑하고, `StorageBackend` 인터페이스를 정의한다. 이 단계에서는 동작 변경 없이 리팩터링만 수행.

| 태스크 | 내용 | Effort |
|--------|------|--------|
| 1-1 | `StorageBackend` ABC 정의 (`base.py`) | S |
| 1-2 | `StorageResult` 데이터 클래스 정의 | S |
| 1-3 | `LocalStorageBackend` 구현 (기존 로직 이전) | M |
| 1-4 | `get_storage_backend()` 팩토리 함수 | S |
| 1-5 | `Settings`에 `STORAGE_BACKEND` 필드 추가 | S |
| 1-6 | ActionKit `service.py`, `file_pipeline.py` → `StorageBackend` 사용으로 리팩터 | M |
| 1-7 | Growth Club `post_service.py` → `StorageBackend` 사용으로 리팩터 | M |
| 1-8 | Profile `service.py` → `StorageBackend` 사용으로 리팩터 | M |
| 1-9 | 기존 테스트 통과 확인 | S |

**완료 기준:** `STORAGE_BACKEND=local` 설정으로 기존과 동일하게 동작. 모든 pytest 통과.

### Phase 2: R2StorageBackend 구현

**목표:** boto3 기반 R2 연동 백엔드를 구현하고, 단위 테스트를 작성한다.

| 태스크 | 내용 | Effort |
|--------|------|--------|
| 2-1 | `boto3` 의존성 추가 (`pyproject.toml`) | S |
| 2-2 | `R2StorageBackend` 구현 (`put`, `get`, `delete`, `get_public_url`) | L |
| 2-3 | `Settings`에 R2 관련 환경변수 추가 | S |
| 2-4 | `get_storage_backend()` 팩토리에 R2 분기 추가 | S |
| 2-5 | R2 연동 단위 테스트 (mocked boto3) | M |
| 2-6 | `.env`, `.env.example` 템플릿 업데이트 | S |

**완료 기준:** mocked 테스트로 R2 put/get/delete 동작 검증. 환경변수 전환 시 R2Backend 인스턴스 생성 확인.

### Phase 3: ActionKit 파일 뷰어/다운로드 R2 대응

**목표:** ActionKit의 파일 뷰어(`/view`)와 다운로드(`/download`) 엔드포인트가 R2에서 파일을 읽도록 수정한다. StaticFiles 마운트를 조건부로 변경.

| 태스크 | 내용 | Effort |
|--------|------|--------|
| 3-1 | `files.py`의 `_resolve_file()` → `StorageBackend.get()` 사용으로 변경 | M |
| 3-2 | `main.py`의 StaticFiles 마운트 조건부 처리 (로컬일 때만) | S |
| 3-3 | ActionKit 뷰어에서 R2 public URL 리다이렉트 옵션 추가 | M |
| 3-4 | 통합 테스트 (ActionKit 업로드 → 뷰어 → 다운로드 전체 흐름) | M |

**완료 기준:** R2 모드에서 ActionKit 파일 업로드/뷰어/다운로드 전체 흐름 동작.

### Phase 4: 프론트엔드 URL 리졸버 수정

**목표:** 프론트엔드에서 파일/이미지 URL을 R2 Public URL 기반으로 해석하도록 수정한다.

| 태스크 | 내용 | Effort |
|--------|------|--------|
| 4-1 | `NEXT_PUBLIC_STORAGE_URL` 환경변수 추가 | S |
| 4-2 | `resolveUploadUrl()` 수정 (R2 Public URL 우선 사용) | S |
| 4-3 | `profile/page.tsx` 이미지 URL 수정 (resolveUploadUrl 공통 사용) | S |
| 4-4 | Growth Club `PostCard.tsx` 이미지 URL 확인 | S |
| 4-5 | `.env`, `.env.example` 템플릿 업데이트 | S |
| 4-6 | 모든 Feature에서 이미지/파일 URL 정상 표시 확인 | M |

**완료 기준:** R2 Public URL로 이미지/파일이 정상 로딩됨. 로컬 모드에서도 기존 URL 유지.

### Phase 5: 마이그레이션 및 검증

**목표:** 기존 로컬 파일을 R2로 마이그레이션하고, 프로덕션 전환 전 최종 검증을 수행한다.

| 태스크 | 내용 | Effort |
|--------|------|--------|
| 5-1 | 마이그레이션 스크립트 작성 (로컬 → R2 일괄 업로드) | L |
| 5-2 | Docker Compose에 R2 환경변수 추가 | S |
| 5-3 | `main.py` StaticFiles 마운트 분기 최종 정리 | S |
| 5-4 | End-to-End 검증 (ActionKit, Growth Club, Profile 전체) | L |
| 5-5 | 성능 테스트 (업로드/다운로드 응답 시간 비교) | M |
| 5-6 | 롤백 절차 문서화 | S |

**완료 기준:** 프로덕션 환경에서 R2 모드로 전체 파일 서빙 동작. 롤백 절차 검증 완료.

---

## 4. Risk Assessment

| 리스크 | 영향도 | 발생 확률 | 대응 방안 |
|--------|--------|----------|----------|
| R2 장애 시 파일 접근 불가 | 높음 | 낮음 | `STORAGE_BACKEND=local` 폴백 설정 + 로컬 캐시 계층 검토 |
| 한국어 파일명 인코딩 이슈 | 중간 | 중간 | `DecodingStaticFiles` 로직을 R2 key 생성에도 적용. R2는 UTF-8 key를 네이티브 지원하므로 이중 인코딩 불필요 |
| 대용량 파일 업로드 타임아웃 | 중간 | 중간 | R2 Multipart Upload 사용 (boto3 `upload_fileobj`), 프론트엔드 타임아웃 조정 |
| 기존 파일 마이그레이션 누락 | 높음 | 낮음 | DB의 `object_key` 목록 기반 검증 스크립트로 누락 체크 |
| 프론트엔드 CORS 이슈 | 중간 | 중간 | R2 버킷 CORS 설정에 프론트엔드 도메인 추가 |
| Presigned URL 만료 | 낮음 | 낮음 | Public URL 우선 사용. Presigned URL은 private 파일에만 적용, 만료 시간 충분히 설정 (1시간) |
| boto3 의존성 크기 증가 | 낮음 | 확정 | Docker 이미지 크기 ~10MB 증가. 허용 범위 |
| 로컬 개발 환경에서 R2 접근 불가 | 중간 | 확정 | `STORAGE_BACKEND=local` 기본값 유지. R2 테스트는 Docker 환경 또는 CI에서만 |

---

## 5. Success Metrics

### 기능 정합성
1. **ActionKit**: 파일 업로드 → 뷰어 → 다운로드 전체 흐름이 R2 모드에서 동작
2. **Growth Club**: 이미지/파일 첨부 게시글 생성/삭제 시 R2 파일 정상 관리
3. **Profile**: 프로필 이미지 업로드/표시가 R2 모드에서 동작
4. **로컬 호환**: `STORAGE_BACKEND=local` 설정 시 기존과 동일하게 동작

### 성능 목표
5. **파일 업로드**: 10MB 이하 파일 업로드 응답 시간 3초 이내
6. **이미지 로딩**: R2 Public URL로 이미지 로딩 시 TTFB 500ms 이내
7. **CDN 캐시 적중률**: 정적 파일 캐시 히트 80% 이상 (R2 Custom Domain 설정 후)

### 안정성 목표
8. **기존 테스트 통과**: pytest 전체 통과, ESLint 0 error
9. **마이그레이션 완전성**: 기존 파일 100% R2 이전 확인 (DB 레코드 기반 검증)
10. **롤백 가능**: 환경변수 변경만으로 로컬 모드 즉시 전환 가능

---

## 6. Required Resources

### Cloudflare R2 설정 (사용자 수행)
- Cloudflare 계정 + R2 구독 활성화
- R2 버킷 생성 (`stepzero-uploads`)
- API Token 발급 (S3 호환 API 자격 증명)
- Custom Domain 설정 (선택, CDN 활용 시)
- CORS 정책 설정

### 환경변수 (사용자 설정 필요)
| 변수 | 위치 | 설명 |
|------|------|------|
| `STORAGE_BACKEND` | `.env` / `.env.local` | `"local"` 또는 `"r2"` |
| `R2_ACCOUNT_ID` | `.env.local` (비밀) | Cloudflare 계정 ID |
| `R2_ACCESS_KEY_ID` | `.env.local` (비밀) | R2 S3 API Access Key |
| `R2_SECRET_ACCESS_KEY` | `.env.local` (비밀) | R2 S3 API Secret Key |
| `R2_BUCKET_NAME` | `.env` | 버킷 이름 (기본: `stepzero-uploads`) |
| `R2_PUBLIC_URL` | `.env` | R2 Public URL 또는 Custom Domain |
| `NEXT_PUBLIC_STORAGE_URL` | `app-frontend/.env` | 프론트엔드 파일 URL 베이스 |

### 의존성
| 패키지 | 버전 | 용도 |
|--------|------|------|
| `boto3` | `>=1.34.0` | S3 호환 API 클라이언트 (R2 연동) |

### 예상 소요 시간
| Phase | Effort | 예상 시간 |
|-------|--------|----------|
| Phase 1: StorageBackend 추상화 | M-L | 4-6시간 |
| Phase 2: R2StorageBackend 구현 | M | 3-4시간 |
| Phase 3: ActionKit R2 대응 | M | 2-3시간 |
| Phase 4: 프론트엔드 URL 수정 | S-M | 1-2시간 |
| Phase 5: 마이그레이션 및 검증 | L | 4-6시간 |
| **총합** | | **14-21시간** |
