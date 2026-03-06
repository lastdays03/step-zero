# Cloudflare R2 파일 저장소 마이그레이션 - 컨텍스트 & 의존성

> Last Updated: 2026-03-04

---

## 변경 대상 파일 목록

### 백엔드 - 수정 대상

| 순서 | 파일 경로 | 변경 내용 |
|------|----------|----------|
| 1 | `app-backend/app/core/config.py` | `STORAGE_BACKEND`, R2 관련 환경변수 6개 추가 |
| 2 | `app-backend/app/features/actionkit/application/service.py` | `StorageBackend` 주입, `save_upload_to_path()` → `storage.put()` 전환 |
| 3 | `app-backend/app/features/actionkit/application/file_pipeline.py` | `save_upload_to_path()` 제거 또는 `StorageBackend` 위임으로 변경 |
| 4 | `app-backend/app/api/v1/actionkit/files.py` | `_resolve_file()` → `StorageBackend.get()` 사용, 파일 뷰어/다운로드 수정 |
| 5 | `app-backend/app/features/growth_club/application/post_service.py` | `_build_upload_path()`, `_remove_saved_files()` → `StorageBackend` 위임 |
| 6 | `app-backend/app/features/profile/application/service.py` | `save_profile_image()` → `StorageBackend.put()` 사용 |
| 7 | `app-backend/app/main.py` | `StaticFiles` 마운트 조건부 처리 (로컬일 때만) |
| 8 | `app-backend/pyproject.toml` | `boto3>=1.34.0` 의존성 추가 |
| 9 | `app-backend/.env` | R2 환경변수 템플릿 추가 (빈 값) |
| 10 | `app-backend/.env.example` | R2 환경변수 설명 추가 |

### 백엔드 - 새로 생성

| 순서 | 파일 경로 | 역할 |
|------|----------|------|
| 1 | `app-backend/app/services/storage/__init__.py` | 패키지 init + export |
| 2 | `app-backend/app/services/storage/base.py` | `StorageBackend` ABC, `StorageResult` 데이터 클래스 |
| 3 | `app-backend/app/services/storage/local.py` | `LocalStorageBackend` (기존 로컬 저장 로직 래핑) |
| 4 | `app-backend/app/services/storage/r2.py` | `R2StorageBackend` (boto3 S3 Client) |
| 5 | `app-backend/app/services/storage/factory.py` | `get_storage_backend()` 팩토리 함수 |
| 6 | `app-backend/scripts/migrate_to_r2.py` | 로컬 → R2 마이그레이션 스크립트 |
| 7 | `app-backend/tests/services/test_storage_backend.py` | StorageBackend 단위 테스트 |

### 프론트엔드 - 수정 대상

| 순서 | 파일 경로 | 변경 내용 |
|------|----------|----------|
| 1 | `app-frontend/src/features/growth-club/utils/upload-url.ts` | `NEXT_PUBLIC_STORAGE_URL` 기반 URL 리졸빙 추가 |
| 2 | `app-frontend/src/app/(dashboard)/profile/page.tsx` | `apiHost` 대신 `resolveUploadUrl()` 공통 유틸 사용 |
| 3 | `app-frontend/.env` | `NEXT_PUBLIC_STORAGE_URL` 추가 |
| 4 | `app-frontend/.env.local` | `NEXT_PUBLIC_STORAGE_URL` 로컬 값 설정 |

### Docker

| 순서 | 파일 경로 | 변경 내용 |
|------|----------|----------|
| 1 | `docker-compose.dev.yml` | R2 환경변수 전달 확인 (기존 env_file 사용으로 자동 적용) |
| 2 | `docker-compose.prod.yml` | 프로덕션 R2 환경변수 설정 |

---

## 기술 결정 사항

### 1. S3 호환 SDK 선택: boto3

**결정:** `boto3` (AWS S3 SDK)를 사용하여 Cloudflare R2에 연동한다.

**근거:**
- R2는 S3 호환 API를 완벽 지원
- boto3는 Python 생태계에서 가장 성숙한 S3 클라이언트
- `endpoint_url`을 R2 엔드포인트로 지정하면 그대로 동작
- Cloudflare 전용 SDK 불필요 → 벤더 종속성 최소화

**R2 엔드포인트 형식:**
```
https://{ACCOUNT_ID}.r2.cloudflarestorage.com
```

**boto3 클라이언트 초기화 예시:**
```python
import boto3

s3_client = boto3.client(
    "s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    region_name="auto",
)
```

### 2. 추상화 패턴: Strategy Pattern

**결정:** `StorageBackend` ABC를 정의하고, `LocalStorageBackend`와 `R2StorageBackend`를 구현한다. 팩토리 함수로 환경변수 기반 인스턴스를 생성.

**근거:**
- 로컬 개발 환경에서 R2 없이 개발 가능
- 테스트에서 `LocalStorageBackend` 사용 (SQLite in-memory 패턴과 동일)
- 환경변수 변경만으로 즉시 롤백 가능
- 향후 AWS S3, GCS 등 다른 스토리지로 전환 시 새 Backend만 추가

### 3. 파일 접근 방식: Public URL 우선

**결정:** R2 Public URL(또는 Custom Domain)을 통한 직접 접근을 기본으로 한다. Private 파일이 필요한 경우 Presigned URL을 사용.

**근거:**
- StepZero의 파일은 대부분 공개 접근 가능 (ActionKit PDF, 프로필 이미지, 커뮤니티 첨부)
- Public URL은 프론트엔드에서 직접 접근 → 백엔드 프록시 부하 제거
- Cloudflare CDN 자동 적용 (Custom Domain 사용 시)
- Presigned URL은 복잡도가 높고 만료 관리 필요 → 현재 불필요

### 4. ActionKit 뷰어/다운로드 처리

**결정:** R2 모드에서 뷰어(`/view`)와 다운로드(`/download`)는 R2에서 파일을 가져와 응답하거나, Public URL로 리다이렉트한다.

**근거:**
- 현재 뷰어는 Markdown → HTML 변환, PDF inline 표시 등 서버사이드 처리가 필요
- 단순 리다이렉트로는 Markdown 뷰어 기능 유지 불가
- 따라서: PDF/이미지 → R2 Public URL 리다이렉트, Markdown → R2에서 fetch 후 HTML 변환

### 5. 프론트엔드 URL 전략

**결정:** `NEXT_PUBLIC_STORAGE_URL` 환경변수를 추가하고, 기존 `resolveUploadUrl()` 유틸에 통합한다.

**변경 후 동작:**
```typescript
// upload-url.ts 변경
const storageBase = process.env.NEXT_PUBLIC_STORAGE_URL;  // R2 Public URL
const apiHost = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const resolveUploadUrl = (value?: string): string => {
    if (!value) return "";
    if (value.startsWith("http://") || value.startsWith("https://")) return value;
    const normalized = value.replace(/^\/+/, "").replace(/^api\/(?:v1\/)?uploads\/?/, "");

    // R2 모드: NEXT_PUBLIC_STORAGE_URL이 설정되어 있으면 사용
    if (storageBase) {
        return `${storageBase}/${normalized}`;
    }
    // 로컬 모드: 기존 방식
    return `${apiHost}/api/uploads/${normalized}`;
};
```

### 6. 체크섬 처리

**결정:** R2 업로드 시에도 SHA-256 체크섬을 계산하여 DB에 저장한다. R2의 ETag(MD5)와는 별도로 관리.

**근거:**
- 기존 ActionKit은 `file_checksum()` (SHA-256)을 DB에 저장
- R2 ETag는 MD5 기반이므로 기존 체크섬과 호환 불가
- 업로드 전 메모리에서 체크섬 계산 → R2 put 후 DB 저장

### 7. 파일 삭제 처리

**결정:** Growth Club 게시글 삭제 시 R2 오브젝트도 함께 삭제한다. 삭제 실패 시 로깅만 수행 (기존 패턴 유지).

**근거:**
- 현재 `_remove_saved_files()`는 삭제 실패 시 `logger.error()`만 호출
- R2 삭제도 동일 패턴: 삭제 실패 시 로깅, 트랜잭션 영향 없음
- 향후 R2 Lifecycle Rule로 고아 파일 정리 가능

---

## 환경변수 목록

### 백엔드 (`app-backend/.env`)

| 변수 | 기본값 | 필수 | 설명 |
|------|--------|------|------|
| `STORAGE_BACKEND` | `"local"` | N | 스토리지 백엔드 (`"local"` 또는 `"r2"`) |
| `STORAGE_LOCAL_ROOT` | `""` (→ `app-backend/uploads/`) | N | 로컬 스토리지 루트 (기존) |
| `R2_ACCOUNT_ID` | `""` | R2 시 Y | Cloudflare 계정 ID |
| `R2_ACCESS_KEY_ID` | `""` | R2 시 Y | R2 S3 API Access Key |
| `R2_SECRET_ACCESS_KEY` | `""` | R2 시 Y | R2 S3 API Secret Key |
| `R2_BUCKET_NAME` | `"stepzero-uploads"` | N | R2 버킷 이름 |
| `R2_PUBLIC_URL` | `""` | R2 시 Y | R2 Public URL 또는 Custom Domain |

### 프론트엔드 (`app-frontend/.env`)

| 변수 | 기본값 | 필수 | 설명 |
|------|--------|------|------|
| `NEXT_PUBLIC_STORAGE_URL` | `""` (→ 백엔드 fallback) | N | 파일 URL 베이스 (R2 Public URL) |

---

## 의존성

### 새로 추가되는 패키지

| 패키지 | 최소 버전 | 파일 | 용도 |
|--------|----------|------|------|
| `boto3` | `>=1.34.0` | `app-backend/pyproject.toml` | S3 호환 API 클라이언트 |

**참고:** `boto3`는 `botocore`와 `s3transfer`를 전이 의존성으로 가져옴. Docker 이미지 크기 약 10MB 증가 예상.

### 기존 의존성 (변경 없음)

- `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg` - 프레임워크
- `pydantic-settings` - 환경변수 설정
- `python-multipart` - 파일 업로드

### 프론트엔드 (새 패키지 없음)

- 기존 `axios`, `lucide-react`, `tailwindcss` 유지
- URL 리졸버 로직만 수정

---

## 핵심 코드 패턴 참조

### StorageBackend ABC 설계

```python
# app-backend/app/services/storage/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class StorageResult:
    key: str
    size_bytes: int
    checksum: str  # SHA-256
    content_type: str

class StorageBackend(ABC):
    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> StorageResult:
        """파일 업로드. key는 버킷 내 경로."""
        ...

    @abstractmethod
    async def get(self, key: str) -> bytes:
        """파일 다운로드. 파일이 없으면 FileNotFoundError."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """파일 삭제. 성공 시 True, 파일 미존재 시 False."""
        ...

    @abstractmethod
    def get_public_url(self, key: str) -> str:
        """파일의 공개 접근 URL 반환."""
        ...
```

### LocalStorageBackend 구현 핵심

```python
# app-backend/app/services/storage/local.py
class LocalStorageBackend(StorageBackend):
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.root_path.mkdir(parents=True, exist_ok=True)

    async def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> StorageResult:
        dest = self.root_path / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        checksum = hashlib.sha256(data).hexdigest()
        return StorageResult(key=key, size_bytes=len(data), checksum=checksum, content_type=content_type)

    async def get(self, key: str) -> bytes:
        path = self.root_path / key
        if not path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return path.read_bytes()

    async def delete(self, key: str) -> bool:
        path = self.root_path / key
        if path.exists():
            path.unlink()
            return True
        return False

    def get_public_url(self, key: str) -> str:
        return f"/api/uploads/{key}"
```

### R2StorageBackend 구현 핵심

```python
# app-backend/app/services/storage/r2.py
import boto3
from botocore.config import Config

class R2StorageBackend(StorageBackend):
    def __init__(self, account_id: str, access_key: str, secret_key: str,
                 bucket_name: str, public_url: str):
        self.bucket_name = bucket_name
        self.public_url = public_url.rstrip("/")
        self.client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
            config=Config(retries={"max_attempts": 3, "mode": "standard"}),
        )

    async def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> StorageResult:
        checksum = hashlib.sha256(data).hexdigest()
        # boto3는 동기이므로 run_in_threadpool 사용
        await run_in_threadpool(
            self.client.put_object,
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return StorageResult(key=key, size_bytes=len(data), checksum=checksum, content_type=content_type)

    async def get(self, key: str) -> bytes:
        response = await run_in_threadpool(
            self.client.get_object,
            Bucket=self.bucket_name,
            Key=key,
        )
        return response["Body"].read()

    async def delete(self, key: str) -> bool:
        try:
            await run_in_threadpool(
                self.client.delete_object,
                Bucket=self.bucket_name,
                Key=key,
            )
            return True
        except Exception:
            return False

    def get_public_url(self, key: str) -> str:
        return f"{self.public_url}/{key}"
```

### 팩토리 함수

```python
# app-backend/app/services/storage/factory.py
from functools import lru_cache
from app.core.config import get_settings

@lru_cache(maxsize=1)
def get_storage_backend() -> StorageBackend:
    settings = get_settings()
    if settings.STORAGE_BACKEND == "r2":
        return R2StorageBackend(
            account_id=settings.R2_ACCOUNT_ID,
            access_key=settings.R2_ACCESS_KEY_ID,
            secret_key=settings.R2_SECRET_ACCESS_KEY,
            bucket_name=settings.R2_BUCKET_NAME,
            public_url=settings.R2_PUBLIC_URL,
        )
    return LocalStorageBackend(root_path=settings.STORAGE_ROOT_PATH)
```

### ActionKit 서비스 리팩터 예시

```python
# 변경 전 (service.py:203-206)
destination = Path(settings.ACTIONKIT_STORAGE_PATH) / object_key
size_bytes, checksum = await save_upload_to_path(upload_file, destination=destination)

# 변경 후
storage = get_storage_backend()
data = await upload_file.read()
mime_type = detect_mime_type(filename, fallback=upload_file.content_type)
# ActionKit 파일의 key prefix는 "actionkit/" 추가
result = await storage.put(f"actionkit/{object_key}", data, content_type=mime_type)
size_bytes, checksum = result.size_bytes, result.checksum
```

### Growth Club 리팩터 예시

```python
# 변경 전 (post_service.py:82-84)
file_path, object_key = _build_upload_path("image", upload.filename)
file_path.parent.mkdir(parents=True, exist_ok=True)
file_path.write_bytes(data)

# 변경 후
object_key = _build_object_key("image", upload.filename)  # 상대 경로만 반환
storage = get_storage_backend()
result = await storage.put(object_key, data, content_type=upload.content_type or "application/octet-stream")
```

### 프론트엔드 URL 리졸버 변경

```typescript
// 변경 전 (upload-url.ts)
const apiHost = (
    process.env.NEXT_PUBLIC_API_URL
    || process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/api\/v1\/?$/, "")
    || "http://localhost:8000"
).replace(/\/$/, "");

export const resolveUploadUrl = (value?: string): string => {
    if (!value) return "";
    if (value.startsWith("http://") || value.startsWith("https://")) return value;
    const normalized = value.replace(/^\/+/, "").replace(/^api\/(?:v1\/)?uploads\/?/, "");
    return `${apiHost}/api/uploads/${normalized}`;
};

// 변경 후
const storageBase = (process.env.NEXT_PUBLIC_STORAGE_URL || "").replace(/\/$/, "");
const apiHost = (
    process.env.NEXT_PUBLIC_API_URL
    || process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/api\/v1\/?$/, "")
    || "http://localhost:8000"
).replace(/\/$/, "");

export const resolveUploadUrl = (value?: string): string => {
    if (!value) return "";
    if (value.startsWith("http://") || value.startsWith("https://")) return value;
    const normalized = value
        .replace(/^\/+/, "")
        .replace(/^api\/(?:v1\/)?uploads\/?/, "");
    if (storageBase) {
        return `${storageBase}/${normalized}`;
    }
    return `${apiHost}/api/uploads/${normalized}`;
};
```

---

## API 계약 (변경 없음)

마이그레이션 후에도 모든 API 엔드포인트의 요청/응답 형식은 변경되지 않는다.

### ActionKit

| 엔드포인트 | 변경 | 비고 |
|-----------|------|------|
| `POST /api/v1/actionkits/items/{item_id}/files` | 없음 | 응답의 `download_url` 형식 유지 |
| `GET /api/v1/actionkits/items/{item_id}/view` | 내부만 | 파일 소스만 로컬→R2 전환 |
| `GET /api/v1/actionkits/items/{item_id}/download` | 내부만 | 파일 소스만 로컬→R2 전환 |

### Profile

| 엔드포인트 | 변경 | 비고 |
|-----------|------|------|
| `POST /api/v1/profile/me/image` | 없음 | 응답의 `profile_img` 경로 형식 유지 |

### Growth Club

| 엔드포인트 | 변경 | 비고 |
|-----------|------|------|
| `POST /api/v1/growth-club/posts` | 없음 | 첨부 파일 `object_key` 형식 유지 |
| `DELETE /api/v1/growth-club/posts/{id}` | 없음 | R2 파일 삭제 추가 |

---

## R2 버킷 설정 가이드 (사용자 참조)

### 1. R2 버킷 생성
```bash
# Cloudflare Dashboard → R2 → Create Bucket
# 이름: stepzero-uploads
# 위치: APAC (한국 사용자 기준)
```

### 2. S3 API Token 발급
```
Cloudflare Dashboard → R2 → Manage R2 API Tokens → Create API Token
- Permissions: Object Read & Write
- Specify bucket: stepzero-uploads
- TTL: 적절한 만료 설정
```

### 3. Public Access 설정
```
R2 버킷 → Settings → Public Access → Enable
- Custom Domain: cdn.stepzero.dev (선택)
- 또는 R2.dev subdomain 사용
```

### 4. CORS 정책
```json
[
  {
    "AllowedOrigins": [
      "http://localhost:3000",
      "https://step-zero.lastdays03.com",
      "https://code-frontend.lastdays03.com"
    ],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 86400
  }
]
```
