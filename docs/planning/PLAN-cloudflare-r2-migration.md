# Cloudflare R2 파일 저장소 마이그레이션 계획

> 작성일: 2026-03-04
> 상태: 계획 수립 (승인 대기)
> 구현 추적: `dev/active/r2-storage-migration/`

---

## 1. 현재 상태 분석

### 1.1 저장소 구조

현재 모든 파일은 **로컬 파일시스템**에 저장됩니다.

| 항목 | 값 |
|------|---|
| 저장소 루트 | `STORAGE_LOCAL_ROOT` 또는 기본값 `app-backend/uploads/` |
| ActionKit 경로 | `{루트}/actionkit/{domain}/{category}/{item_id}/v{ver}/{filename}` |
| Growth Club 이미지 | `{루트}/growth-club/image/{year}/{month}/{uuid}_image.{ext}` |
| Growth Club 파일 | `{루트}/growth-club/file/{year}/{month}/{uuid}_file.{ext}` |
| 프로필 이미지 | `{루트}/profile/{uuid}.{ext}` |
| 서빙 방식 | FastAPI `StaticFiles` 마운트 (`/api/uploads/`, `/api/v1/actionkits/files/`) |

### 1.2 파일을 사용하는 Feature (3곳)

| Feature | 업로드 | 다운로드/서빙 | 삭제 |
|---------|--------|-------------|------|
| **ActionKit** | `POST /api/v1/actionkits/items/{id}/files` | `GET .../view`, `GET .../download`, 정적 마운트 | 없음 (버전 관리) |
| **Growth Club** | `POST /api/v1/growth-club/posts` (multipart) | 정적 마운트 `/api/uploads/` | 게시글 삭제 시 파일도 삭제 |
| **Profile** | `POST /api/v1/profile/me` (multipart) | 정적 마운트 `/api/uploads/` | 없음 (덮어쓰기) |

### 1.3 DB에 저장되는 파일 경로 (3개 테이블)

| 테이블 | 컬럼 | 저장 형식 | 예시 |
|--------|------|----------|------|
| `actionkit_files` | `object_key` | 상대경로 | `laws/chapter-1/123/v1/민법.pdf` |
| `growthclubpostattachment` | `object_key` | 상대경로 | `growth-club/image/2026/03/abc_image.jpg` |
| `userprofile` | `profile_img` | 상대경로 | `profile/550e8400.png` |

### 1.4 프론트엔드 파일 URL 구성

```
프론트엔드 → {API_HOST}/api/uploads/{object_key}
ActionKit → {API_HOST}/api/v1/actionkits/files/{object_key}
```

`resolveUploadUrl()` 유틸리티가 상대경로를 절대 URL로 변환합니다.

---

## 2. Cloudflare R2 마이그레이션 설계

### 2.1 목표 아키텍처

```
[사용자 브라우저]
    │
    ├─ 파일 읽기 ──→ [R2 퍼블릭 URL / 커스텀 도메인]  ← 직접 서빙 (CDN)
    │
    └─ 파일 업로드 ─→ [FastAPI 백엔드]
                          │
                          └─→ [Cloudflare R2 버킷]  ← S3 호환 API로 업로드
```

**핵심 변경점:**
- **업로드**: 로컬 `open().write()` → `boto3` S3 호환 클라이언트로 R2에 PUT
- **서빙**: FastAPI `StaticFiles` → R2 퍼블릭 URL 직접 접근 (CDN 캐싱)
- **삭제**: `Path.unlink()` → S3 `delete_object()`
- **프론트엔드**: URL 베이스를 R2 퍼블릭 도메인으로 변경

### 2.2 R2 버킷 구조

```
stepzero-uploads/              ← 버킷명
├── actionkit/
│   └── laws/chapter-1/123/v1/민법.pdf
├── growth-club/
│   ├── image/2026/03/abc_image.jpg
│   └── file/2026/03/def_file.pdf
└── profile/
    └── 550e8400.png
```

> 기존 `object_key` 패턴을 그대로 유지하여 DB 마이그레이션 불필요

### 2.3 환경변수 설계

```env
# R2 연결 설정
R2_ACCOUNT_ID=<cloudflare-account-id>
R2_ACCESS_KEY_ID=<r2-api-token-access-key>
R2_SECRET_ACCESS_KEY=<r2-api-token-secret-key>
R2_BUCKET_NAME=stepzero-uploads
R2_PUBLIC_URL=https://uploads.stepzero.kr   # 커스텀 도메인 또는 R2 퍼블릭 URL

# 스토리지 모드 (마이그레이션 기간 동안 전환 가능)
STORAGE_BACKEND=r2   # "local" | "r2"
```

---

## 3. 구현 계획 (개발자 작업)

### Phase 1: R2 스토리지 서비스 추가

**새 파일**: `app-backend/app/services/storage.py`

```python
# 추상 인터페이스
class StorageBackend(ABC):
    async def upload(self, key: str, data: bytes, content_type: str) -> str: ...
    async def delete(self, key: str) -> None: ...
    def public_url(self, key: str) -> str: ...

# 로컬 구현 (기존 호환)
class LocalStorageBackend(StorageBackend): ...

# R2 구현
class R2StorageBackend(StorageBackend): ...

# 팩토리
def get_storage_backend() -> StorageBackend:
    if settings.STORAGE_BACKEND == "r2":
        return R2StorageBackend()
    return LocalStorageBackend()
```

### Phase 2: Feature별 서비스 수정 (3곳)

| 파일 | 변경 내용 |
|------|----------|
| `features/actionkit/application/service.py` | `save_upload_to_path()` → `storage.upload()` |
| `features/actionkit/application/file_pipeline.py` | `file_checksum()` 메모리 기반으로 변경 |
| `features/growth_club/application/post_service.py` | 파일 저장/삭제 → `storage.upload()` / `storage.delete()` |
| `features/profile/application/service.py` | 이미지 저장 → `storage.upload()` |

### Phase 3: 파일 서빙 엔드포인트 수정

| 현재 | 변경 후 |
|------|--------|
| `StaticFiles("/api/uploads/")` 마운트 | 제거 (R2 직접 서빙) |
| `DecodingStaticFiles("/api/v1/actionkits/files/")` 마운트 | 제거 |
| `GET /actionkits/items/{id}/view` 로컬 파일 읽기 | R2에서 다운로드 후 처리 또는 리다이렉트 |
| `GET /actionkits/items/{id}/download` `FileResponse` | R2 presigned URL 리다이렉트 |

### Phase 4: 프론트엔드 URL 변경

| 파일 | 변경 내용 |
|------|----------|
| `features/growth-club/utils/upload-url.ts` | `resolveUploadUrl()` → R2 퍼블릭 URL 기반 |
| `app/(dashboard)/profile/page.tsx` | 프로필 이미지 URL 변경 |
| 기타 이미지/파일 표시 컴포넌트 | URL 패턴 변경 |

### Phase 5: 기존 파일 마이그레이션

- 로컬 `uploads/` 디렉토리의 기존 파일을 R2로 일괄 업로드
- `rclone` 또는 Python 스크립트로 수행
- DB의 `object_key`는 변경 불필요 (경로 패턴 동일)

---

## 4. 사용자(당신)가 수행해야 하는 작업

### 4.1 Cloudflare R2 버킷 생성

1. **Cloudflare 대시보드 접속**: https://dash.cloudflare.com
2. **R2 Object Storage** 메뉴 진입
3. **버킷 생성**:
   - 버킷 이름: `stepzero-uploads` (원하는 이름 가능)
   - 리전: `Asia Pacific` (APAC) 권장 (한국 사용자 대상)
4. **퍼블릭 액세스 설정**:
   - 버킷 설정 → "Public access" 활성화
   - 또는 커스텀 도메인 연결 (아래 참조)

### 4.2 R2 API 토큰 생성

1. **R2** → **Manage R2 API Tokens** 클릭
2. **Create API Token** 클릭
3. 설정:
   - **Token name**: `stepzero-backend`
   - **Permissions**: `Object Read & Write`
   - **Specify bucket(s)**: `stepzero-uploads` (방금 만든 버킷만 선택)
   - **TTL**: 필요에 따라 설정 (무제한 가능)
4. **생성 완료 후 값 복사** (한 번만 표시됨!):
   - `Access Key ID` → 나에게 전달
   - `Secret Access Key` → 나에게 전달
   - `Account ID` (대시보드 URL에서 확인 가능) → 나에게 전달

### 4.3 (선택) 커스텀 도메인 연결

R2 퍼블릭 URL 대신 자체 도메인을 사용하려면:

1. **R2 버킷** → **Settings** → **Public access** → **Custom Domains**
2. **Connect Domain** 클릭
3. 도메인 입력: 예) `uploads.stepzero.kr`
4. Cloudflare DNS에서 CNAME 자동 생성됨
5. SSL 인증서 자동 발급 (몇 분 소요)

> **커스텀 도메인 미사용 시**: R2 퍼블릭 URL 형식은
> `https://pub-{hash}.r2.dev` 또는 `https://{account-id}.r2.cloudflarestorage.com/{bucket}` 입니다.

### 4.4 CORS 설정

R2 버킷에 CORS 규칙 추가 필요:

1. **R2 버킷** → **Settings** → **CORS Policy**
2. 다음 규칙 추가:

```json
[
  {
    "AllowedOrigins": [
      "http://localhost:3000",
      "https://stepzero.kr",
      "https://www.stepzero.kr"
    ],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 86400
  }
]
```

> 프론트엔드 도메인을 `AllowedOrigins`에 추가하세요.

---

## 5. 나(Claude)에게 전달해야 하는 값

구현을 시작하려면 다음 값이 필요합니다:

| 항목 | 설명 | 예시 |
|------|------|------|
| **R2_ACCOUNT_ID** | Cloudflare 계정 ID | `a1b2c3d4e5f6...` |
| **R2_ACCESS_KEY_ID** | R2 API 토큰의 Access Key | `abcdef1234567890` |
| **R2_SECRET_ACCESS_KEY** | R2 API 토큰의 Secret Key | `secret1234567890abcdef` |
| **R2_BUCKET_NAME** | 생성한 버킷 이름 | `stepzero-uploads` |
| **R2_PUBLIC_URL** | 퍼블릭 접근 URL (커스텀 도메인 또는 R2 기본 URL) | `https://uploads.stepzero.kr` |
| **프론트엔드 도메인** | CORS용 프로덕션 도메인 | `https://stepzero.kr` |

> **보안 주의**: Secret Key는 `.env.local`에만 저장하고 Git에 커밋하지 않습니다.

---

## 6. 변경되는 파일 목록

### 백엔드 (Python)

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `app/services/storage.py` | **신규** | StorageBackend 추상화 + R2/Local 구현 |
| `app/core/config.py` | 수정 | R2 관련 환경변수 추가 |
| `app/main.py` | 수정 | StaticFiles 마운트 조건부 처리 |
| `app/features/actionkit/application/service.py` | 수정 | 파일 저장 → storage 서비스 사용 |
| `app/features/actionkit/application/file_pipeline.py` | 수정 | 체크섬/저장 함수 리팩터링 |
| `app/api/v1/actionkit/files.py` | 수정 | view/download 엔드포인트 R2 지원 |
| `app/features/growth_club/application/post_service.py` | 수정 | 파일 저장/삭제 → storage 서비스 |
| `app/features/profile/application/service.py` | 수정 | 이미지 저장 → storage 서비스 |
| `.env` | 수정 | R2 환경변수 템플릿 추가 |
| `requirements.txt` | 수정 | `boto3` 의존성 추가 |

### 프론트엔드 (TypeScript)

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| `src/features/growth-club/utils/upload-url.ts` | 수정 | R2 퍼블릭 URL 지원 |
| `src/app/(dashboard)/profile/page.tsx` | 수정 | 이미지 URL 변경 |
| `.env` | 수정 | `NEXT_PUBLIC_UPLOAD_URL` 추가 |

### 마이그레이션 스크립트

| 파일 | 설명 |
|------|------|
| `scripts/migrate_files_to_r2.py` | **신규** - 기존 로컬 파일 → R2 일괄 업로드 |

---

## 7. 의존성 추가

```
# app-backend/requirements.txt에 추가
boto3>=1.35.0        # S3 호환 API 클라이언트 (R2용)
```

> Cloudflare R2는 S3 호환 API를 제공하므로 `boto3`를 그대로 사용합니다.
> R2 전용 SDK는 불필요합니다.

---

## 8. 마이그레이션 순서 (전체 타임라인)

```
[당신이 할 일]                         [Claude가 할 일]
─────────────────────────────────────────────────────────────
1. R2 버킷 생성
2. API 토큰 생성
3. (선택) 커스텀 도메인 설정
4. CORS 설정
5. 키 값 전달 ──────────────────→     6. StorageBackend 서비스 구현
                                      7. 각 Feature 서비스 수정
                                      8. 프론트엔드 URL 로직 수정
                                      9. 환경변수 설정 (.env 파일)
                                      10. 마이그레이션 스크립트 작성
─────────────────────────────────────────────────────────────
11. Docker 환경 테스트                  12. 테스트 지원
13. 기존 파일 마이그레이션 실행
14. 프로덕션 배포
```

---

## 9. 리스크 및 고려사항

### 9.1 하위 호환성

- `STORAGE_BACKEND=local` 설정 시 기존과 동일하게 동작 (롤백 가능)
- DB 스키마 변경 없음 (`object_key` 패턴 유지)

### 9.2 ActionKit 뷰어 특수 처리

- Markdown 파일 뷰어: R2에서 파일 내용을 읽어 HTML로 변환해야 함
- 대안: 프론트엔드에서 R2 URL로 직접 fetch 후 렌더링

### 9.3 파일 크기 제한

- R2 단일 PUT 제한: 5GB (현재 최대 50MB이므로 문제없음)
- Multipart upload: 50MB 이상 시 사용 (현재 불필요)

### 9.4 비용

| 항목 | R2 무료 티어 | 초과 시 |
|------|------------|--------|
| 저장 용량 | 10GB/월 | $0.015/GB |
| Class A (쓰기) | 1,000,000회/월 | $4.50/1M |
| Class B (읽기) | 10,000,000회/월 | $0.36/1M |
| 이그레스 (전송) | **무료** | **무료** |

> R2의 가장 큰 장점: **이그레스(데이터 전송) 비용 무료**

### 9.5 보안

- R2 API 토큰은 `.env.local`에만 저장 (Git 제외)
- 퍼블릭 읽기만 허용, 쓰기는 API 토큰 필수
- 프론트엔드에 Secret Key 노출 없음 (백엔드만 사용)

---

## 10. 체크리스트 요약

### 당신(사용자)의 할 일

- [ ] Cloudflare 계정에서 R2 활성화
- [ ] R2 버킷 생성 (`stepzero-uploads`, APAC 리전)
- [ ] R2 API 토큰 생성 (Object Read & Write, 해당 버킷만)
- [ ] 퍼블릭 액세스 활성화 또는 커스텀 도메인 연결
- [ ] CORS 정책 설정
- [ ] 다음 값을 전달:
  - Account ID
  - Access Key ID
  - Secret Access Key
  - 버킷 이름
  - 퍼블릭 URL
  - 프론트엔드 프로덕션 도메인

### Claude의 할 일

- [ ] `StorageBackend` 추상화 서비스 구현
- [ ] `R2StorageBackend` 구현 (boto3 S3 호환)
- [ ] `LocalStorageBackend` 구현 (기존 코드 래핑)
- [ ] `config.py`에 R2 환경변수 추가
- [ ] ActionKit 파일 서비스 수정
- [ ] Growth Club 파일 서비스 수정
- [ ] Profile 이미지 서비스 수정
- [ ] `main.py` StaticFiles 마운트 조건부 처리
- [ ] ActionKit view/download 엔드포인트 수정
- [ ] 프론트엔드 `resolveUploadUrl()` 수정
- [ ] 프론트엔드 환경변수 추가
- [ ] `.env` 템플릿 업데이트
- [ ] `requirements.txt`에 `boto3` 추가
- [ ] 기존 파일 마이그레이션 스크립트 작성
- [ ] 테스트 코드 업데이트
