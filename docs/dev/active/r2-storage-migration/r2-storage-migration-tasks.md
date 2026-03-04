# Cloudflare R2 파일 저장소 마이그레이션 - 태스크 체크리스트

> Last Updated: 2026-03-04

---

## Phase 0: 사전 준비 (사용자 수행)

- [ ] **0-1** Cloudflare R2 버킷 생성 `[S]`
  - 버킷명: `stepzero-uploads`, 리전: APAC
  - AC: R2 Dashboard에서 버킷 확인 가능

- [ ] **0-2** R2 S3 API Token 발급 `[S]`
  - Cloudflare Dashboard → R2 → Manage R2 API Tokens
  - Permissions: Object Read & Write, Bucket: `stepzero-uploads`
  - AC: Access Key ID + Secret Access Key 확보

- [ ] **0-3** R2 Public Access 활성화 `[S]`
  - R2 버킷 → Settings → Public Access → Enable
  - Custom Domain 설정 (선택): `cdn.stepzero.dev`
  - AC: Public URL로 버킷 접근 가능

- [ ] **0-4** R2 CORS 정책 설정 `[S]`
  - AllowedOrigins: `http://localhost:3000`, `https://step-zero.lastdays03.com`, `https://code-frontend.lastdays03.com`
  - AllowedMethods: `GET`, `HEAD`
  - AC: 프론트엔드에서 R2 URL 접근 시 CORS 에러 없음

- [ ] **0-5** 환경변수 로컬 설정 `[S]`
  - `app-backend/.env.local`에 R2 자격 증명 추가
  - AC: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_PUBLIC_URL` 설정 완료

---

## Phase 1: StorageBackend 추상화 계층 구축

- [ ] **1-1** `StorageBackend` ABC 정의 `[S]`
  - 새 파일: `app-backend/app/services/storage/base.py`
  - 메서드: `put()`, `get()`, `delete()`, `get_public_url()`
  - `StorageResult` 데이터 클래스 정의: `key`, `size_bytes`, `checksum`, `content_type`
  - AC: import 가능, mypy 타입 체크 통과

- [ ] **1-2** `StorageBackend` 패키지 초기화 `[S]`
  - 새 파일: `app-backend/app/services/storage/__init__.py`
  - export: `StorageBackend`, `StorageResult`, `LocalStorageBackend`, `get_storage_backend`
  - AC: `from app.services.storage import StorageBackend` 성공

- [ ] **1-3** `LocalStorageBackend` 구현 `[M]`
  - 새 파일: `app-backend/app/services/storage/local.py`
  - 기존 `file_pipeline.py`의 `save_upload_to_path()`, `file_checksum()` 로직 이전
  - `put()`: 디렉토리 생성 + 파일 쓰기 + SHA-256 체크섬
  - `get()`: 파일 읽기 (없으면 `FileNotFoundError`)
  - `delete()`: 파일 삭제 (없으면 `False`)
  - `get_public_url()`: `/api/uploads/{key}` 형식 반환
  - AC: 기존 로컬 저장과 동일 동작, 단위 테스트 통과

- [ ] **1-4** `get_storage_backend()` 팩토리 함수 `[S]`
  - 새 파일: `app-backend/app/services/storage/factory.py`
  - `@lru_cache(maxsize=1)` 싱글턴 패턴
  - `STORAGE_BACKEND == "local"` → `LocalStorageBackend(STORAGE_ROOT_PATH)`
  - AC: 팩토리 호출 시 `LocalStorageBackend` 인스턴스 반환
  - 의존: 1-1, 1-3

- [ ] **1-5** `Settings`에 `STORAGE_BACKEND` 필드 추가 `[S]`
  - 파일: `app-backend/app/core/config.py`
  - `STORAGE_BACKEND: str = "local"` 추가
  - AC: `.env`에 `STORAGE_BACKEND=local` 설정 시 정상 로딩

- [ ] **1-6** ActionKit 서비스 리팩터 `[M]`
  - 파일: `app-backend/app/features/actionkit/application/service.py`
  - `upload_item_file()` 내 `save_upload_to_path()` → `storage.put()` 전환
  - `get_storage_backend()` import하여 스토리지 인스턴스 사용
  - ActionKit key prefix: `actionkit/{object_key}`
  - AC: `STORAGE_BACKEND=local`에서 ActionKit 파일 업로드 기존과 동일 동작
  - 의존: 1-4

- [ ] **1-7** Growth Club 서비스 리팩터 `[M]`
  - 파일: `app-backend/app/features/growth_club/application/post_service.py`
  - `_build_upload_path()` → `_build_object_key()` (상대 경로만 반환)
  - `file_path.write_bytes(data)` → `storage.put(object_key, data)`
  - `_remove_saved_files()` → `storage.delete(key)` 전환
  - AC: 게시글 생성/삭제 시 파일 저장/삭제 정상 동작
  - 의존: 1-4

- [ ] **1-8** Profile 서비스 리팩터 `[M]`
  - 파일: `app-backend/app/features/profile/application/service.py`
  - `save_profile_image()` → `storage.put(f"profile/{filename}", content)` 전환
  - `self.upload_dir` 직접 관리 제거
  - AC: 프로필 이미지 업로드 기존과 동일 동작
  - 의존: 1-4

- [ ] **1-9** 기존 테스트 통과 확인 `[S]`
  - `cd app-backend && .venv/bin/pytest -q`
  - AC: 모든 기존 테스트 통과 (0 failures)
  - 의존: 1-6, 1-7, 1-8

---

## Phase 2: R2StorageBackend 구현

- [ ] **2-1** `boto3` 의존성 추가 `[S]`
  - 파일: `app-backend/pyproject.toml`
  - `dependencies`에 `"boto3>=1.34.0"` 추가
  - AC: `pip install -e .` 후 `import boto3` 성공

- [ ] **2-2** `R2StorageBackend` 구현 `[L]`
  - 새 파일: `app-backend/app/services/storage/r2.py`
  - boto3 S3 Client 초기화 (endpoint_url, region_name="auto")
  - `put()`: `client.put_object()` + `run_in_threadpool` (비동기 래핑)
  - `get()`: `client.get_object()` + Body.read()
  - `delete()`: `client.delete_object()`, 실패 시 False + 로깅
  - `get_public_url()`: `{R2_PUBLIC_URL}/{key}`
  - 재시도 설정: `Config(retries={"max_attempts": 3})`
  - AC: mocked 테스트로 put/get/delete 동작 확인
  - 의존: 2-1

- [ ] **2-3** `Settings`에 R2 환경변수 추가 `[S]`
  - 파일: `app-backend/app/core/config.py`
  - 추가 필드: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_PUBLIC_URL`
  - `R2_BUCKET_NAME` 기본값: `"stepzero-uploads"`
  - 나머지 기본값: `None` 또는 `""`
  - Validator: `STORAGE_BACKEND == "r2"` 시 필수값 검증
  - AC: R2 환경변수 미설정 + `STORAGE_BACKEND=local` → 정상 기동
  - 의존: 1-5

- [ ] **2-4** 팩토리에 R2 분기 추가 `[S]`
  - 파일: `app-backend/app/services/storage/factory.py`
  - `STORAGE_BACKEND == "r2"` → `R2StorageBackend(...)` 인스턴스 생성
  - AC: `STORAGE_BACKEND=r2` + R2 환경변수 설정 시 R2Backend 인스턴스 반환
  - 의존: 2-2, 2-3

- [ ] **2-5** StorageBackend 단위 테스트 `[M]`
  - 새 파일: `app-backend/tests/services/test_storage_backend.py`
  - `LocalStorageBackend`: put/get/delete 테스트 (tmp_path 사용)
  - `R2StorageBackend`: mocked boto3 client로 put/get/delete 테스트
  - `get_storage_backend()` 팩토리: 환경변수별 인스턴스 타입 확인
  - AC: `pytest tests/services/test_storage_backend.py` 전체 통과
  - 의존: 2-2, 2-4
  - **주의:** `git add -f` 필요 (루트 `.gitignore`에 `test_*.py` 패턴 존재)

- [ ] **2-6** `.env`, `.env.example` 템플릿 업데이트 `[S]`
  - 파일: `app-backend/.env`, `app-backend/.env.example`
  - R2 환경변수 추가 (빈 값, 주석 설명)
  - AC: 환경변수 설명이 포함된 템플릿 파일 업데이트
  - 의존: 2-3

---

## Phase 3: ActionKit 파일 뷰어/다운로드 R2 대응

- [ ] **3-1** `_resolve_file()` R2 대응 `[M]`
  - 파일: `app-backend/app/api/v1/actionkit/files.py`
  - 기존: `os.path.join(settings.ACTIONKIT_STORAGE_PATH, object_key)` + `os.path.exists()`
  - 변경: `storage.get(f"actionkit/{object_key}")` 사용
  - R2 모드: 바이트 데이터 반환, 로컬 모드: 파일 경로 반환 (기존 유지)
  - AC: R2 모드에서 뷰어/다운로드 엔드포인트 정상 동작
  - 의존: Phase 2 완료

- [ ] **3-2** `main.py` StaticFiles 마운트 조건부 처리 `[S]`
  - 파일: `app-backend/app/main.py`
  - 로컬 모드: 기존 `StaticFiles`, `DecodingStaticFiles` 마운트 유지
  - R2 모드: StaticFiles 마운트 스킵 (R2 Public URL로 직접 접근)
  - `if settings.STORAGE_BACKEND == "local":` 조건문으로 래핑
  - AC: R2 모드에서 `/api/uploads/` StaticFiles 마운트 없음, 에러 없이 기동

- [ ] **3-3** ActionKit 뷰어 R2 리다이렉트 옵션 `[M]`
  - 파일: `app-backend/app/api/v1/actionkit/files.py`
  - PDF/이미지: R2 Public URL로 `307 Redirect` (R2 모드)
  - Markdown: R2에서 fetch → HTML 변환 후 응답 (기존 방식 유지)
  - AC: PDF 뷰어에서 R2 URL로 리다이렉트됨, Markdown 뷰어 정상 렌더링
  - 의존: 3-1

- [ ] **3-4** ActionKit 통합 테스트 `[M]`
  - 업로드 → 뷰어 → 다운로드 전체 흐름 (로컬 모드)
  - R2 모드 테스트는 별도 환경 (수동 또는 CI)
  - AC: 로컬 모드 통합 테스트 통과
  - 의존: 3-1, 3-2, 3-3

---

## Phase 4: 프론트엔드 URL 리졸버 수정

- [ ] **4-1** `NEXT_PUBLIC_STORAGE_URL` 환경변수 추가 `[S]`
  - 파일: `app-frontend/.env`, `app-frontend/.env.local`
  - 로컬 기본값: 빈 문자열 (→ 백엔드 fallback)
  - AC: 환경변수 로딩 확인 (`process.env.NEXT_PUBLIC_STORAGE_URL`)

- [ ] **4-2** `resolveUploadUrl()` 수정 `[S]`
  - 파일: `app-frontend/src/features/growth-club/utils/upload-url.ts`
  - `NEXT_PUBLIC_STORAGE_URL` 설정 시 R2 Public URL 기반으로 URL 생성
  - 미설정 시 기존 `apiHost + /api/uploads/` fallback 유지
  - AC: R2 URL 설정 시 `resolveUploadUrl("profile/abc.png")` → `https://cdn.stepzero.dev/profile/abc.png`
  - AC: R2 URL 미설정 시 기존과 동일: `http://localhost:8000/api/uploads/profile/abc.png`
  - 의존: 4-1

- [ ] **4-3** Profile 페이지 이미지 URL 공통화 `[S]`
  - 파일: `app-frontend/src/app/(dashboard)/profile/page.tsx`
  - 기존: `${apiHost}/api/uploads/${profile.profile_img}` 직접 조합
  - 변경: `resolveUploadUrl(profile.profile_img)` 호출
  - `resolveUploadUrl` import 추가
  - AC: 프로필 이미지가 로컬/R2 모드 모두에서 정상 표시
  - 의존: 4-2

- [ ] **4-4** Growth Club PostCard 이미지 URL 확인 `[S]`
  - 파일: `app-frontend/src/features/growth-club/components/PostCard.tsx`
  - 기존 `resolveUploadUrl()` 사용 중인지 확인, 미사용 시 적용
  - AC: 게시글 첨부 이미지가 R2 URL로 정상 표시
  - 의존: 4-2

- [ ] **4-5** 프론트엔드 `.env` 템플릿 업데이트 `[S]`
  - 파일: `app-frontend/.env`
  - `NEXT_PUBLIC_STORAGE_URL=` 추가 (빈 값, 주석)
  - AC: 환경변수 템플릿에 STORAGE_URL 포함

- [ ] **4-6** 전체 Feature 이미지/파일 URL 수동 검증 `[M]`
  - ActionKit 파일 다운로드 링크 확인
  - Growth Club 게시글 이미지 표시 확인
  - Profile 이미지 표시 확인
  - AC: 3개 Feature 모두 이미지/파일 정상 로딩 (로컬 모드)
  - 의존: 4-2, 4-3, 4-4

---

## Phase 5: 마이그레이션 및 검증

- [ ] **5-1** 마이그레이션 스크립트 작성 `[L]`
  - 새 파일: `app-backend/scripts/migrate_to_r2.py`
  - 로컬 `uploads/` 디렉토리의 모든 파일을 R2 버킷으로 업로드
  - DB의 `ActionKitFile.object_key`, `GrowthClubPostAttachment.object_key`, `UserProfile.profile_img` 기반으로 대상 파일 목록 생성
  - 진행률 표시, 이미 존재하는 파일 스킵 (idempotent)
  - AC: 스크립트 실행 후 R2 버킷에 모든 파일 존재 확인

- [ ] **5-2** Docker Compose R2 환경변수 설정 `[S]`
  - 파일: `docker-compose.dev.yml`, `docker-compose.prod.yml`
  - R2 환경변수는 `.env.local` / `.env.docker.local`에서 로딩 (기존 env_file 패턴 사용)
  - AC: Docker 환경에서 `STORAGE_BACKEND=r2` 설정 시 R2 연동 동작
  - 의존: Phase 2 완료

- [ ] **5-3** `main.py` StaticFiles 마운트 최종 정리 `[S]`
  - 파일: `app-backend/app/main.py`
  - R2 모드에서 불필요한 StaticFiles 마운트 완전 제거 확인
  - 로그 메시지: "Storage backend: {r2|local}" 기동 시 출력
  - AC: R2 모드 기동 로그에 "Storage backend: r2" 표시
  - 의존: 3-2

- [ ] **5-4** End-to-End 검증 `[L]`
  - [ ] ActionKit 파일 업로드 → R2 저장 확인 (R2 Dashboard에서 객체 확인)
  - [ ] ActionKit 뷰어 (PDF): R2 URL 리다이렉트 정상
  - [ ] ActionKit 뷰어 (Markdown): HTML 변환 정상
  - [ ] ActionKit 다운로드: R2에서 파일 가져와 응답
  - [ ] Growth Club 이미지 업로드 → R2 저장 확인
  - [ ] Growth Club 게시글 삭제 → R2 파일 삭제 확인
  - [ ] Profile 이미지 업로드 → R2 저장 확인
  - [ ] 프론트엔드: 3개 Feature 이미지/파일 정상 표시
  - [ ] `STORAGE_BACKEND=local` 전환 → 기존 동작 정상 확인 (롤백)
  - AC: 모든 항목 통과

- [ ] **5-5** 성능 비교 테스트 `[M]`
  - 10MB 파일 업로드 응답 시간: 로컬 vs R2
  - 이미지 로딩 TTFB: 로컬 StaticFiles vs R2 Public URL
  - 목표: R2 업로드 3초 이내, R2 이미지 TTFB 500ms 이내
  - AC: 성능 목표 충족 또는 개선 방안 문서화

- [ ] **5-6** 롤백 절차 문서화 `[S]`
  - 롤백 단계:
    1. `STORAGE_BACKEND=local` 변경
    2. `NEXT_PUBLIC_STORAGE_URL` 제거
    3. Docker 재시작
  - AC: 롤백 절차 문서 작성 완료

---

## Quality Gates

- [ ] `cd app-backend && .venv/bin/pytest -q` — 전체 통과
- [ ] `cd app-frontend && npm run lint` — 0 errors
- [ ] `STORAGE_BACKEND=local` 기본값에서 기존 동작 100% 유지
- [ ] `STORAGE_BACKEND=r2` 전환 시 3개 Feature 파일 서빙 정상

---

## 태스크 요약

| Phase | 태스크 수 | S | M | L | 예상 시간 |
|-------|----------|---|---|---|----------|
| Phase 0 (사용자) | 5 | 5 | 0 | 0 | 1시간 |
| Phase 1 | 9 | 5 | 4 | 0 | 4-6시간 |
| Phase 2 | 6 | 4 | 1 | 1 | 3-4시간 |
| Phase 3 | 4 | 1 | 3 | 0 | 2-3시간 |
| Phase 4 | 6 | 5 | 1 | 0 | 1-2시간 |
| Phase 5 | 6 | 3 | 1 | 2 | 4-6시간 |
| **총합** | **36** | **23** | **10** | **3** | **15-22시간** |
