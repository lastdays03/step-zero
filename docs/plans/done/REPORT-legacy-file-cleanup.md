# REPORT: 레거시 파일 관리 시스템 정리 분석

Last Updated: 2026-03-06

---

## 1. Executive Summary

Step Zero는 R2 스토리지 마이그레이션(PR #22) 과정에서 **통합 `files` 테이블**을 도입했다. 현재 3개 feature(ActionKit, GrowthClub, UserProfile)가 각각의 **레거시 파일 모델**과 통합 `File` 모델에 **이중 기록(Dual Write)** 하는 과도기 상태이다.

이 보고서는 레거시 파일 테이블·모델·코드를 완전히 제거하고 통합 `File` 모델로 전환하기 위한 **현황 분석, 의존성 매핑, 리스크 평가, 단계별 정리 전략**을 제공한다.

---

## 2. 현재 아키텍처: 이중 구조

### 2.1 테이블 매핑

| 레거시 테이블 | 통합 대응 | owner_type | 마이그레이션 상태 |
|--------------|----------|-----------|----------------|
| `actionkit_files` | `files` (owner_type="actionkit_item") | actionkit_item | 듀얼 라이트 적용 |
| `growthclubpostattachment` | `files` (owner_type="growth_club_post") | growth_club_post | **생성 시 미적용** (삭제 시만 File 정리) |
| `userprofile.profile_img` (VARCHAR 컬럼) | `files` (owner_type="user_profile") | user_profile | 듀얼 라이트 적용 |

### 2.2 레거시 모델 상세

#### ActionKitFile (`actionkit_files` 테이블)

**위치:** `app-backend/app/models/actionkit.py`

```
컬럼: id, item_id(FK), version, object_key, original_filename,
      mime_type, size_bytes, checksum, is_current, uploaded_at, created_at
인덱스: item_id, version, is_current
관계: ActionKitItem.files (CASCADE delete)
마이그레이션: alembic/versions/003_actionkit.py
```

#### GrowthClubPostAttachment (`growthclubpostattachment` 테이블)

**위치:** `app-backend/app/models/growth_club.py`

```
컬럼: id, post_id(FK), kind, object_key, original_filename,
      mime_type, size_bytes, created_at
인덱스: post_id, kind
관계: GrowthClubPost.attachments (CASCADE delete)
마이그레이션: alembic/versions/004_growth_club.py
```

#### UserProfile.profile_img (VARCHAR 컬럼)

**위치:** `app-backend/app/models/profile.py:12`

```
컬럼: profile_img (Optional[str], default="default.png")
저장값: "profile/{uuid}.{ext}" 형태의 경로 문자열
```

### 2.3 통합 File 모델

**위치:** `app-backend/app/models/file.py`
**테이블:** `files` (마이그레이션: `alembic/versions/014_files_table.py`)

```
컬럼: id, owner_type, owner_id, category, object_key(UNIQUE),
      original_filename, mime_type, size_bytes, checksum, version,
      is_current, kind, metadata_extra(JSON), uploaded_at, created_at
인덱스: (owner_type, owner_id), (owner_type, owner_id, is_current),
        owner_type, owner_id, version, is_current, kind
```

---

## 3. 듀얼 라이트 현황 상세

### 3.1 ActionKit — 완전 듀얼 라이트

**서비스:** `app/features/actionkit/application/service.py:183-262`

| 동작 | 레거시 (ActionKitFile) | 통합 (File) |
|------|----------------------|------------|
| 업로드 | `ActionKitRepository.create_file_record()` | `FileRepository.create()` + `set_current()` |
| 조회 | `ActionKitRepository.list_current_files()` | 미사용 (레거시 우선) |
| 삭제 | CASCADE (ActionKitItem 삭제 시) | **미연동** — File 레코드 미삭제 |

**문제점:**
- **조회는 레거시만 사용** — API 응답(`ActionKitFileUploadResponse`)이 `ActionKitFile.id` 반환
- **삭제 시 File 레코드 미정리** — ActionKitItem 삭제 시 CASCADE로 `actionkit_files`만 삭제, `files` 테이블에 고아 레코드 잔존
- FK 의존성: `roadmap_template_actions.actionkit_file_id` → `actionkit_files.id` (FK, ondelete=SET NULL)

### 3.2 GrowthClub — 부분 듀얼 라이트 (불완전)

**서비스:** `app/features/growth_club/application/post_service.py:61-186`

| 동작 | 레거시 (GrowthClubPostAttachment) | 통합 (File) |
|------|----------------------------------|------------|
| 생성 | `GrowthClubPostAttachment` 직접 생성 | **미기록** |
| 조회 | `GrowthClubPost.attachments` 관계 | 미사용 |
| 삭제 | CASCADE (GrowthClubPost 삭제 시) | `FileRepository.delete_by_owner()` 호출 |

**문제점:**
- **생성 시 File 테이블 미기록** — 마이그레이션 스크립트로만 동기화 가능
- 삭제 시에만 File 정리 → 생성된 적 없는 File 레코드를 삭제 시도 (무해하지만 불일치)
- API 응답이 `GrowthClubPostAttachment` 모델의 `object_key` 직접 사용

### 3.3 UserProfile — 듀얼 라이트 (가장 단순)

**서비스:** `app/features/profile/application/service.py:82-119`

| 동작 | 레거시 (profile_img 컬럼) | 통합 (File) |
|------|-------------------------|------------|
| 업로드 | `profile.profile_img = "profile/{filename}"` | `FileRepository.create()` (기존 레코드 delete 후) |
| 조회 | `UserProfile.profile_img` 직접 읽기 | 미사용 |
| 삭제 | 덮어쓰기 (새 이미지로 대체) | `delete_by_owner()` → `create()` |

**문제점:**
- **조회는 레거시만 사용** — API 응답(`UserProfileRead`)이 `profile_img` VARCHAR 반환
- `profile_img` 컬럼 자체를 제거하려면 프론트엔드 `resolveUploadUrl()` 체인 전체 수정 필요

---

## 4. 의존성 맵 (정리 차단 요소)

### 4.1 DB 레벨 의존성

```
roadmap_template_actions.actionkit_file_id
  → FK → actionkit_files.id (ondelete=SET NULL)
  → 위치: app/models/roadmap_template.py:77-79
  → 정리 전 반드시 files.id로 재매핑 필요
```

### 4.2 Repository 레벨 의존성

| Repository | 레거시 메서드 | 호출 위치 |
|-----------|-------------|---------|
| `ActionKitRepository` | `list_current_files(item_ids)` | `service.py` (목록 조회), `files.py` (뷰/다운로드) |
| `ActionKitRepository` | `create_file_record(...)` | `service.py` (업로드) |
| `ActionKitRepository` | `clear_current_file_flags(item_id)` | `service.py` (업로드) |
| `ActionKitRepository` | `get_next_file_version(item_id)` | `service.py` (업로드) |

### 4.3 API 라우터 레벨 의존성

| 라우터 | 레거시 모델 참조 | 영향 |
|-------|---------------|------|
| `api/v1/actionkit/files.py` | `_resolve_file()` → `ActionKitRepository.list_current_files()` | 뷰/다운로드 URL 생성 |
| `api/v1/growth_club/posts.py` | `GrowthClubPostAttachment` 직접 생성 | 게시글 생성 |
| `api/v1/profile/me.py` | `profile_img` 컬럼 갱신 | 프로필 이미지 업로드 |

### 4.4 프론트엔드 의존성

| 프론트엔드 파일 | 레거시 의존 | 설명 |
|---------------|-----------|------|
| `features/actionkit/components/ActionKitLibraryView.tsx` | `resolveActionKitUrl(path)` | ActionKitFile의 object_key 기반 URL 해석 |
| `features/growth-club/components/PostCard.tsx` | `attachment.object_key` | GrowthClubPostAttachment 응답 직접 사용 |
| `features/growth-club/components/CreatePostForm.tsx` | FormData `images[]`, `files[]` | 서버에서 Attachment 생성 |
| `app/(dashboard)/profile/page.tsx` | `profile.profile_img` | UserProfile 응답의 profile_img 사용 |
| `features/shared/file/utils/url.ts` | `resolveUploadUrl(value)` | object_key → 전체 URL 변환 (Local/R2) |

### 4.5 마이그레이션 스크립트

| 스크립트 | 역할 | 상태 |
|---------|------|------|
| `scripts/migrate_files_table.py` | 레거시 → files 데이터 복사 + FK 재매핑 + 검증 | 구현 완료, 실행 여부 미확인 |
| `scripts/migrate_to_r2.py` | Local → R2 스토리지 마이그레이션 | 완료 |

---

## 5. 데이터 정합성 리스크

### 5.1 현재 불일치 시나리오

| # | 시나리오 | 결과 | 심각도 |
|---|---------|------|--------|
| 1 | ActionKitItem 삭제 시 | `actionkit_files` CASCADE 삭제, `files` 고아 레코드 잔존 | **높음** |
| 2 | GrowthClub 게시글 생성 | `growthclubpostattachment`만 생성, `files` 미기록 | **높음** |
| 3 | GrowthClub 게시글 삭제 | 존재하지 않는 File 레코드 삭제 시도 (무해) | 낮음 |
| 4 | 마이그레이션 스크립트 미실행 시 | `files` 테이블에 과거 데이터 누락 | **높음** |
| 5 | 동시 업로드 + 서버 크래시 | 레거시만 기록되고 File 미기록 (트랜잭션 내이므로 이론상 안전) | 낮음 |

### 5.2 Ops 파일 관리 콘솔 영향

`OpsFilesService`는 `files` 테이블만 조회하므로:
- GrowthClub 생성 시 File 미기록 → **Ops 콘솔에 GrowthClub 파일 미표시**
- ActionKitItem 삭제 후 고아 레코드 → **삭제된 파일이 Ops 콘솔에 잔존**

---

## 6. 단계별 정리 전략

### Phase A: 데이터 정합성 확보 (선행 필수)

> **목표:** `files` 테이블이 모든 파일의 Single Source of Truth가 되도록 보장

#### A-1. 마이그레이션 스크립트 실행 및 검증

```bash
# 1. 현황 확인 (dry-run)
docker compose exec app-backend uv run python scripts/migrate_files_table.py --dry-run

# 2. 실행
docker compose exec app-backend uv run python scripts/migrate_files_table.py

# 3. 검증
docker compose exec app-backend uv run python scripts/migrate_files_table.py --verify
```

**AC:** ActionKit, GrowthClub, Profile 각각의 레거시 레코드 수 == files 테이블 레코드 수

#### A-2. GrowthClub 듀얼 라이트 추가

`post_service.py:create_post()` 수정 — `GrowthClubPostAttachment` 생성 직후 `File` 레코드도 생성:

```python
# attachment_rows 생성 루프 이후, db_post.attachments 할당 후 flush 이후
file_repo = FileRepository(self.session)
for att in attachment_rows:
    await file_repo.create(file=File(
        owner_type="growth_club_post",
        owner_id=post_id,
        category="image" if att.kind == "image" else "file",
        object_key=att.object_key,
        original_filename=att.original_filename,
        mime_type=att.mime_type,
        size_bytes=att.size_bytes,
        kind=att.kind,
    ))
```

**AC:** GrowthClub 게시글 생성 시 `files` 테이블에도 기록 확인

#### A-3. ActionKit 삭제 시 File 정리 추가

ActionKitItem 삭제 로직에 `FileRepository.delete_by_owner()` 호출 추가:

```python
file_repo = FileRepository(session)
await file_repo.delete_by_owner(owner_type="actionkit_item", owner_id=item_id)
```

**AC:** ActionKitItem 삭제 시 `files` 테이블 고아 레코드 0건

---

### Phase B: FK 재매핑

> **목표:** `roadmap_template_actions.actionkit_file_id`가 `files.id`를 참조하도록 변경

#### B-1. FK 재매핑 실행

마이그레이션 스크립트의 `build_id_mapping()` + `remap_fk()` 함수 활용:
- `_file_id_mapping` 임시 테이블 생성 (actionkit_files.id → files.id)
- `roadmap_template_actions.actionkit_file_id` UPDATE

#### B-2. Alembic 마이그레이션 — FK 대상 변경

```python
# 새 마이그레이션 파일
def upgrade():
    # 1. 기존 FK 제거
    op.drop_constraint(
        "roadmap_template_actions_actionkit_file_id_fkey",
        "roadmap_template_actions",
        type_="foreignkey"
    )
    # 2. 새 FK 추가 (files 테이블 참조)
    op.create_foreign_key(
        "roadmap_template_actions_actionkit_file_id_fkey",
        "roadmap_template_actions",
        "files",
        ["actionkit_file_id"],
        ["id"],
        ondelete="SET NULL"
    )

def downgrade():
    # 역순
    ...
```

#### B-3. 모델 수정

`app/models/roadmap_template.py:77-79`:

```python
# Before:
actionkit_file_id: Optional[int] = Field(
    default=None, foreign_key="actionkit_files.id", ondelete="SET NULL"
)

# After:
actionkit_file_id: Optional[int] = Field(
    default=None, foreign_key="files.id", ondelete="SET NULL"
)
```

**AC:** `alembic check` → diff 없음, FK orphan 검증 통과

---

### Phase C: 애플리케이션 코드 전환

> **목표:** 모든 파일 조회/생성/삭제가 `File` 모델 + `FileRepository`만 사용

#### C-1. ActionKit 서비스 전환

| 레거시 호출 | 전환 대상 | 파일 |
|-----------|---------|------|
| `ActionKitRepository.create_file_record()` | `FileRepository.create(File(...))` | `service.py` |
| `ActionKitRepository.clear_current_file_flags()` | `FileRepository.set_current()` (이미 기존 로직에서 사용) | `service.py` |
| `ActionKitRepository.get_next_file_version()` | `FileRepository.get_next_version()` | `service.py` |
| `ActionKitRepository.list_current_files()` | `FileRepository.get_current_files()` | `service.py`, `files.py` |

**ActionKit 라우터 (`api/v1/actionkit/files.py`) 수정:**
- `_resolve_file()` 함수: `ActionKitRepository.list_current_files()` → `FileRepository.get_current_files()`
- 응답 스키마: `file_id`를 `File.id`로 변경 (API 호환성 주의)

**제거 대상 메서드 (ActionKitRepository):**
- `list_current_files()`
- `create_file_record()`
- `clear_current_file_flags()`
- `get_next_file_version()`

#### C-2. GrowthClub 서비스 전환

| 레거시 호출 | 전환 대상 | 파일 |
|-----------|---------|------|
| `GrowthClubPostAttachment(...)` 직접 생성 | `FileRepository.create(File(...))` | `post_service.py` |
| `db_post.attachments` 관계 조회 | `FileRepository.get_by_owner()` | `post_service.py` |

**GrowthClub 게시글 응답 스키마 수정:**
- `GrowthClubPostRead.attachments` 타입을 `GrowthClubPostAttachment` → `File` 기반 DTO로 변경
- 프론트엔드 `PostCard.tsx`의 `attachment.object_key`, `attachment.kind` 필드명 유지 필요 (또는 동시 수정)

**제거 대상:**
- `GrowthClubPostAttachment` 모델 클래스
- `GrowthClubPost.attachments` relationship

#### C-3. UserProfile 전환

| 레거시 필드 | 전환 대상 | 파일 |
|-----------|---------|------|
| `UserProfile.profile_img` 직접 읽기 | `FileRepository.get_by_owner("user_profile", user_id)` | `service.py`, `me.py` |
| `profile.profile_img = "profile/..."` 갱신 | File 레코드만 관리 | `service.py` |

**주의사항:**
- `UserProfileRead` 응답에 `profile_img` 필드가 그대로 있어야 프론트엔드 호환
- 선택지 1: `profile_img`를 computed property로 변환 (`File.object_key`에서 도출)
- 선택지 2: `profile_img` 컬럼 유지하되 File과 동기화 (현재 방식 유지)
- **권장:** 선택지 1 — 컬럼 제거, API 직렬화 시 File 테이블에서 조회

---

### Phase D: 레거시 테이블 제거

> **목표:** 레거시 테이블 DROP + 모델 클래스 삭제

#### D-1. Alembic 마이그레이션 — 테이블 DROP

```python
def upgrade():
    # 1. _file_id_mapping 임시 테이블 정리
    op.execute("DROP TABLE IF EXISTS _file_id_mapping")

    # 2. GrowthClubPostAttachment 테이블 DROP
    op.drop_table("growthclubpostattachment")

    # 3. ActionKitFile 테이블 DROP
    # (FK가 이미 Phase B에서 files로 재매핑됨)
    op.drop_table("actionkit_files")

    # 4. UserProfile.profile_img 컬럼 DROP (선택)
    op.drop_column("userprofile", "profile_img")

def downgrade():
    # 역순 재생성
    ...
```

#### D-2. 코드 정리

| 삭제 대상 | 위치 |
|----------|------|
| `ActionKitFile` 모델 클래스 | `app/models/actionkit.py` |
| `GrowthClubPostAttachment` 모델 클래스 | `app/models/growth_club.py` |
| `ActionKitItem.files` relationship | `app/models/actionkit.py` |
| `GrowthClubPost.attachments` relationship | `app/models/growth_club.py` |
| `UserProfile.profile_img` 필드 (선택) | `app/models/profile.py` |
| `models/__init__.py` 에서 import 제거 | `app/models/__init__.py` |
| `alembic/env.py` 에서 import 제거 | `alembic/env.py` |
| `scripts/migrate_files_table.py` | 마이그레이션 완료 후 불필요 |
| `ActionKitRepository` 파일 관련 메서드 4개 | `app/repositories/actionkit_repository.py` |

#### D-3. 프론트엔드 정리

| 변경 | 파일 | 설명 |
|------|------|------|
| API 응답 타입 업데이트 | `pnpm types:sync` 실행 | OpenAPI → TypeScript 자동 생성 |
| 첨부파일 타입 수정 | GrowthClub 관련 타입 | `attachment` → File 기반 DTO |
| profile_img 처리 | Profile 관련 컴포넌트 | API 응답 변경 시 대응 |

---

## 7. 리스크 평가

| # | 리스크 | 영향도 | 발생확률 | 완화 전략 |
|---|--------|--------|---------|----------|
| 1 | FK 재매핑 실패 — orphan 발생 | 높음 | 낮음 | `--verify` 검증, 트랜잭션 내 실행 |
| 2 | API 응답 스키마 변경 — 프론트 깨짐 | 높음 | 중간 | 프론트/백 동시 배포, `types:sync` 필수 |
| 3 | 마이그레이션 스크립트 미실행 상태에서 테이블 DROP | 치명 | 낮음 | Phase A 완료 검증 → Phase D 진입 게이트 |
| 4 | GrowthClub 듀얼 라이트 추가 후 기존 데이터 누락 | 중간 | 높음 | Phase A-1 스크립트로 과거 데이터 보정 |
| 5 | profile_img 컬럼 제거 시 default.png 폴백 깨짐 | 중간 | 중간 | File 미존재 시 default 반환 로직 추가 |
| 6 | CASCADE 삭제 경로 변경 — 게시글/아이템 삭제 시 파일 잔존 | 높음 | 중간 | File 삭제 로직 명시적 추가 (Phase A-3) |

---

## 8. 실행 순서 및 의존성

```
Phase A: 데이터 정합성 확보
  A-1 마이그레이션 스크립트 실행/검증
  A-2 GrowthClub 듀얼 라이트 추가         ← A-1 완료 후
  A-3 ActionKit 삭제 시 File 정리 추가     ← 독립 실행 가능
  ─── 검증 게이트: files 테이블 == 레거시 테이블 수량 일치 ───

Phase B: FK 재매핑
  B-1 FK 데이터 재매핑 (스크립트)           ← A-1 완료 필수
  B-2 Alembic FK 대상 변경 마이그레이션      ← B-1 완료 후
  B-3 모델 FK 선언 수정                    ← B-2와 동시
  ─── 검증 게이트: alembic check clean, orphan 0건 ───

Phase C: 애플리케이션 코드 전환
  C-1 ActionKit 서비스/라우터 전환          ← B 완료 필수
  C-2 GrowthClub 서비스/라우터 전환         ← A-2 완료 후
  C-3 UserProfile 전환                    ← 독립 실행 가능
  ─── 검증 게이트: make test + pnpm lint 통과 ───

Phase D: 레거시 테이블 제거
  D-1 Alembic DROP 마이그레이션             ← C 전체 완료 필수
  D-2 코드 정리 (모델/repo/스크립트 삭제)    ← D-1과 동시
  D-3 프론트엔드 타입 동기화                 ← D-2 완료 후
  ─── 검증 게이트: make test + pnpm lint + pnpm build 통과 ───
```

---

## 9. 영향받는 파일 전체 목록

### 백엔드 — 수정

| 파일 | Phase | 변경 내용 |
|------|-------|----------|
| `app/features/growth_club/application/post_service.py` | A-2, C-2 | 듀얼 라이트 추가 → File 전용 전환 |
| `app/features/actionkit/application/service.py` | A-3, C-1 | File 삭제 추가 → 레거시 제거 |
| `app/api/v1/actionkit/files.py` | C-1 | `_resolve_file()` → FileRepository 사용 |
| `app/api/v1/growth_club/posts.py` | C-2 | 응답 스키마 변경 |
| `app/features/profile/application/service.py` | C-3 | profile_img 컬럼 의존 제거 |
| `app/api/v1/profile/me.py` | C-3 | 응답 직렬화 변경 |
| `app/repositories/actionkit_repository.py` | C-1, D-2 | 파일 메서드 4개 제거 |
| `app/models/roadmap_template.py` | B-3 | FK 선언 변경 |

### 백엔드 — 수정 (모델/마이그레이션)

| 파일 | Phase | 변경 내용 |
|------|-------|----------|
| `app/models/actionkit.py` | D-2 | ActionKitFile 클래스 + relationship 삭제 |
| `app/models/growth_club.py` | D-2 | GrowthClubPostAttachment 클래스 + relationship 삭제 |
| `app/models/profile.py` | D-2 | profile_img 필드 제거 (선택) |
| `app/models/__init__.py` | D-2 | import/export 정리 |
| `alembic/env.py` | D-2 | import 정리 |
| 새 마이그레이션 파일 (B-2) | B-2 | FK 재매핑 |
| 새 마이그레이션 파일 (D-1) | D-1 | 테이블 DROP |

### 백엔드 — 삭제

| 파일 | Phase | 사유 |
|------|-------|------|
| `scripts/migrate_files_table.py` | D-2 | 마이그레이션 완료 후 불필요 |

### 프론트엔드 — 수정

| 파일 | Phase | 변경 내용 |
|------|-------|----------|
| `features/growth-club/components/PostCard.tsx` | C-2 | attachment 타입 변경 대응 |
| `features/growth-club/components/CreatePostForm.tsx` | C-2 | 필요시 타입 수정 |
| `app/(dashboard)/profile/page.tsx` | C-3 | profile_img 필드 변경 대응 |
| `lib/api-types.ts` | D-3 | `pnpm types:sync` 자동 생성 |

---

## 10. 권장 사항

### 즉시 실행 (ops-file-manager 작업과 병행 가능)

1. **A-1: 마이그레이션 스크립트 `--verify` 실행** — 현재 데이터 정합성 상태 파악
2. **A-2: GrowthClub 듀얼 라이트 추가** — Ops 파일 관리 콘솔의 GrowthClub 파일 가시성 확보
3. **A-3: ActionKit 삭제 시 File 정리** — 고아 레코드 방지

### 중기 실행 (ops-file-manager 완료 후)

4. **Phase B 전체** — FK 재매핑은 Alembic 마이그레이션 포함이므로 별도 브랜치/PR 권장
5. **Phase C 전체** — 코드 전환은 테스트 커버리지 확보 후 진행

### 장기 실행

6. **Phase D** — 레거시 테이블 DROP은 Phase A~C 전체 검증 후 최종 단계

### profile_img 컬럼에 대한 결정

`profile_img` VARCHAR 컬럼 제거는 **선택 사항**이다:
- **제거 시:** File 테이블에서 조회하는 로직 필요 + API 응답 호환성 처리
- **유지 시:** 듀얼 라이트 지속, 코드 복잡도 약간 증가하지만 안전
- **권장:** Phase D에서 다른 테이블과 함께 정리 (단, 강제하지 않음)

---

## 부록: 관련 TODO 마커

```
app/features/actionkit/application/service.py:265
  TODO(4B-6): ActionKitFile → File 모델 완전 전환 (별도 리팩터 단계)
    - ActionKitRepository.list_current_files → FileRepository.get_current_files
    - ActionKitRepository.create_file_record → FileRepository.create
    - delete 로직에 FileRepository.delete_by_owner 추가
    - 선행 조건: 4B-4 데이터 마이그레이션 + 4B-5 FK 재매핑 완료
```
