# Context: 레거시 파일 테이블/모델 정리

Last Updated: 2026-03-06 (Phase B+C 완료)

## Key Files

### 레거시 모델 (제거 대상)

| 파일 | 모델/필드 | 테이블 |
|------|----------|--------|
| `app-backend/app/models/actionkit.py` | `ActionKitFile` 클래스 + `ActionKitItem.files` relationship | `actionkit_files` |
| `app-backend/app/models/growth_club.py` | `GrowthClubPostAttachment` 클래스 + `GrowthClubPost.attachments` relationship | `growthclubpostattachment` |
| `app-backend/app/models/profile.py` | `UserProfile.profile_img` VARCHAR 필드 | `userprofile` 컬럼 |

### 통합 모델 (유지)

| 파일 | 역할 |
|------|------|
| `app-backend/app/models/file.py` | `File` 통합 모델 (owner_type + owner_id 폴리모픽) |
| `app-backend/app/repositories/file_repository.py` | `FileRepository` — CRUD 10개 메서드 |

### 듀얼 라이트 구현 위치 (수정 대상)

| 파일 | 현재 동작 | 목표 |
|------|----------|------|
| `app-backend/app/features/actionkit/application/service.py` | ~~ActionKitFile + File 듀얼 라이트~~ → **File만 사용 (Phase C 완료)** | ✅ 완료 |
| `app-backend/app/features/growth_club/application/post_service.py` | ~~Attachment + File 듀얼 라이트~~ → **File만 사용 (Phase C 완료)** | ✅ 완료 |
| `app-backend/app/features/ops/application/actionkit/service.py` | File 삭제 추가 완료 (커밋 `3d3b718`, PR #25) | ✅ 완료 |
| `app-backend/app/features/profile/application/service.py` | File primary, profile_img 컬럼 동기화 유지 (Phase C) | ✅ 완료 (컬럼 제거는 Phase D) |

### Ops 파일 관리 서비스 (ops-file-manager에서 구현 완료)

| 파일 | 역할 | legacy-file-cleanup 영향 |
|------|------|-------------------------|
| `app-backend/app/features/ops/application/files/service.py` | 파일 목록/통계/삭제 (`files` 테이블 전용, 178-253줄) | ⚠️ **Phase C 완료 전 삭제 시 레거시 테이블 고아 레코드 발생 + 레거시 경로 404** |
| `app-backend/app/api/v1/ops/files.py` | REST API (4개 엔드포인트) | Phase C 이후에는 안전하게 사용 가능 |

### API 라우터 (수정 대상)

| 파일 | 레거시 의존 |
|------|-----------|
| `app-backend/app/api/v1/actionkit/files.py` | `_resolve_file()` → `ActionKitRepository.list_current_files()` |
| `app-backend/app/api/v1/growth_club/posts.py` | `GrowthClubPostAttachment` 직접 생성 |
| `app-backend/app/api/v1/profile/me.py` | `profile_img` 컬럼 갱신 |

### Repository (수정 대상)

| 파일 | 제거 대상 메서드 |
|------|---------------|
| `app-backend/app/repositories/actionkit_repository.py` | `list_current_files()`, `create_file_record()`, `clear_current_file_flags()`, `get_next_file_version()` |

### FK 의존성

| 파일 | FK 선언 | 현재 참조 | 목표 참조 |
|------|---------|----------|----------|
| `app-backend/app/models/roadmap_template.py:77-79` | `actionkit_file_id` | `actionkit_files.id` | `files.id` |

### 마이그레이션 스크립트

| 파일 | 역할 | Phase |
|------|------|-------|
| `app-backend/scripts/migrate_files_table.py` | 레거시 → files 데이터 복사 + FK 재매핑 + 검증 (`--dry-run`, `--verify`, `--migrate-only` 모두 구현 완료, PR #25) | A-1, B-1 |
| `app-backend/alembic/versions/003_actionkit.py` | ActionKit 테이블 생성 (actionkit_files 포함) | D-1 역참조 |
| `app-backend/alembic/versions/004_growth_club.py` | GrowthClub 테이블 생성 (attachment 포함) | D-1 역참조 |
| `app-backend/alembic/versions/014_files_table.py` | 통합 files 테이블 생성 | 참조만 |

### 프론트엔드 (수정 대상)

| 파일 | 레거시 의존 |
|------|-----------|
| `app-frontend/src/features/actionkit/components/ActionKitLibraryView.tsx` | ActionKitFile 기반 URL 해석 |
| `app-frontend/src/features/growth-club/components/PostCard.tsx` | `attachment.object_key` (Attachment 응답) |
| `app-frontend/src/features/growth-club/components/CreatePostForm.tsx` | FormData → Attachment 생성 |
| `app-frontend/src/app/(dashboard)/profile/page.tsx` | `profile.profile_img` 직접 사용 |
| `app-frontend/src/features/shared/file/utils/url.ts` | `resolveUploadUrl()` — object_key → URL 변환 |

### 모델 등록

| 파일 | 변경 내용 |
|------|----------|
| `app-backend/app/models/__init__.py` | `ActionKitFile`, `GrowthClubPostAttachment` import/export 제거 |
| `app-backend/alembic/env.py` | 해당 모델 import 제거 |

---

## 레거시 모델 컬럼 비교

### ActionKitFile → File 매핑

| ActionKitFile 컬럼 | File 컬럼 | 비고 |
|-------------------|-----------|------|
| `id` | `id` | PK 변경 (FK 재매핑 필요) |
| `item_id` | `owner_id` | + `owner_type="actionkit_item"` |
| `version` | `version` | 그대로 |
| `object_key` | `object_key` | 그대로 (UNIQUE) |
| `original_filename` | `original_filename` | 그대로 |
| `mime_type` | `mime_type` | 그대로 |
| `size_bytes` | `size_bytes` | 그대로 |
| `checksum` | `checksum` | 그대로 |
| `is_current` | `is_current` | 그대로 |
| — | `category` | "document" 고정 |
| — | `kind` | NULL |

### GrowthClubPostAttachment → File 매핑

| Attachment 컬럼 | File 컬럼 | 비고 |
|----------------|-----------|------|
| `id` | `id` | PK 변경 (FK 없어 재매핑 불필요) |
| `post_id` | `owner_id` | + `owner_type="growth_club_post"` |
| `kind` | `kind` | "image" \| "file" |
| `object_key` | `object_key` | 그대로 |
| `original_filename` | `original_filename` | 그대로 |
| `mime_type` | `mime_type` | 그대로 |
| `size_bytes` | `size_bytes` | 그대로 |
| — | `category` | kind → category 변환 |

### UserProfile.profile_img → File 매핑

| Profile 필드 | File 컬럼 | 비고 |
|-------------|-----------|------|
| `profile_img` (VARCHAR) | `object_key` | 경로 문자열 그대로 |
| `user_id` | `owner_id` | + `owner_type="user_profile"` |
| — | `category` | "profile_image" 고정 |

---

## 기존 TODO 마커

```python
# app/features/actionkit/application/service.py:265 (검증 완료 2026-03-06)
# TODO(4B-6): ActionKitFile → File 모델 완전 전환 (별도 리팩터 단계)
# - ActionKitRepository.list_current_files → FileRepository.get_current_files(owner_type="actionkit_item")
# - ActionKitRepository.create_file_record → FileRepository.create(File(...))
# - delete 로직에 FileRepository.delete_by_owner("actionkit_item", item_id) 추가
# - 선행 조건: 4B-4 데이터 마이그레이션 + 4B-5 FK 재매핑 완료
```

---

## 주요 기술 결정

| 결정 | 선택 | 근거 |
|------|------|------|
| 정리 순서 | 데이터 정합 → FK 재매핑 → 코드 전환 → 테이블 DROP | 각 단계가 다음 단계의 선행 조건 |
| profile_img 컬럼 | Phase D에서 제거 (선택) | API 호환성 vs 코드 단순화 트레이드오프 |
| GrowthClub 듀얼 라이트 | Phase A에서 즉시 추가 | Ops 파일 콘솔 가시성 확보 급선무 |
| FK 재매핑 방식 | object_key JOIN으로 매핑 | actionkit_files.object_key == files.object_key (UNIQUE) |
| API 응답 호환성 | 필드명 유지, 소스만 변경 | 프론트엔드 수정 최소화 |
| CASCADE 대체 | 명시적 FileRepository.delete_by_owner() | File 테이블에는 FK CASCADE 없음 |

---

## 검증 체크리스트 (Phase 간 게이트)

### Phase A → B 게이트
```bash
docker compose exec app-backend uv run python scripts/migrate_files_table.py --verify
# [OK] ActionKit: N -> N
# [OK] GrowthClub: N -> N
# [OK] Profile: N -> N
```

### Phase B → C 게이트
```bash
cd app-backend && uv run alembic check   # diff 없음
# FK orphan 검증:
# SELECT COUNT(*) FROM roadmap_template_actions
# WHERE actionkit_file_id IS NOT NULL
#   AND NOT EXISTS (SELECT 1 FROM files WHERE id = actionkit_file_id)
# → 0건
```

### Phase C → D 게이트
```bash
cd app-backend && make test              # 전체 통과
cd app-frontend && pnpm lint && pnpm build  # 전체 통과
# 레거시 모델 참조 0건 확인:
# grep -r "ActionKitFile\|GrowthClubPostAttachment" app-backend/app/ --include="*.py"
# → actionkit.py, growth_club.py (모델 정의만 남아야 함)
```
