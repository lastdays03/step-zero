# Tasks: 레거시 파일 테이블/모델 정리

Last Updated: 2026-03-06

## Phase A: 데이터 정합성 확보

### A-1. 마이그레이션 스크립트 실행 및 검증 [Effort: S]
- [ ] ⚠️ **선행 필수:** `migrate_files_table.py`에 `--migrate-only` 플래그 구현 (데이터 복사만, FK 재매핑 스킵)
  - 현재 `--dry-run`과 `--verify`만 존재, `--migrate-only`는 **미구현 상태**
  - 플래그 없이 본 실행 시 Phase B(build_id_mapping + remap_fk)까지 의도치 않게 동시 실행됨
- [ ] Docker 환경에서 `migrate_files_table.py --dry-run` 실행 → 대상 건수 확인
- [ ] `migrate_files_table.py --migrate-only` 실행 (데이터 복사만)
- [ ] `migrate_files_table.py --verify` 실행 → 3종 모두 OK 확인
- **AC:** ActionKit, GrowthClub, Profile 각각의 레거시 레코드 수 == files 테이블 레코드 수

### A-2. GrowthClub 생성 시 듀얼 라이트 추가 [Effort: S] — ✅ 완료 (ops-file-manager에서 구현)
- [x] `app/features/growth_club/application/post_service.py` 수정
  - [x] `create_post()` 메서드에서 `GrowthClubPostAttachment` 생성 후 `File` 레코드도 생성 (`post_service.py:153-166`)
  - [x] `flush()` 후 `post_id` 확보 → `File(owner_type="growth_club_post", owner_id=post_id, ...)` 생성
  - [x] `FileRepository` import 추가
- [x] `delete_post()`에서도 `file_repo.delete_by_owner()` 호출 (`post_service.py:195`)
- **구현 커밋:** `f9d7ac8` (feature/0-ops-file-manager)
- **Note:** 과거 데이터는 A-1 스크립트로 보정 필요

### A-3. ActionKit 삭제 시 File 정리 추가 [Effort: S] — ⚠️ **현행 버그 수정 (우선 처리 권장)**
- [ ] `service.py:delete_item()` (233-239줄) 확인 — 현재 ActionKitItem만 삭제, File 레코드 삭제 누락 → **고아 레코드 누적 중**
- [ ] `FileRepository.delete_by_owner(owner_type="actionkit_item", owner_id=item_id)` 호출 추가
- [ ] 기존 테스트 통과 확인
- **AC:** ActionKitItem 삭제 시 `files` 테이블 고아 레코드 0건

---

## Phase B: FK 재매핑

### B-1. FK 데이터 재매핑 [Effort: S]
- [ ] `migrate_files_table.py`의 `build_id_mapping()` 실행 → `_file_id_mapping` 생성
- [ ] `remap_fk()` 실행 → `roadmap_template_actions.actionkit_file_id` 값 변환
- [ ] 검증: FK orphan 0건 확인
  ```sql
  SELECT COUNT(*) FROM roadmap_template_actions
  WHERE actionkit_file_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM files WHERE id = actionkit_file_id)
  ```
- **AC:** `roadmap_template_actions.actionkit_file_id`의 모든 값이 `files.id`에 존재

### B-2. Alembic FK 대상 변경 마이그레이션 [Effort: M]
- [ ] 새 마이그레이션 파일 생성
  - [ ] `op.drop_constraint("roadmap_template_actions_actionkit_file_id_fkey", ...)`
  - [ ] `op.create_foreign_key(... "files", ["actionkit_file_id"], ["id"], ondelete="SET NULL")`
  - [ ] `downgrade()` 역순 작성
- [ ] `app/models/roadmap_template.py:77-79` 수정
  - [ ] `foreign_key="actionkit_files.id"` → `foreign_key="files.id"`
- [ ] `alembic check` → diff 없음 확인
- [ ] `make test` 통과 확인
- **AC:** FK가 `files.id` 참조, alembic clean, 테스트 통과
- **Depends:** B-1 완료

---

## Phase C: 애플리케이션 코드 전환

### C-1. ActionKit 서비스/라우터 전환 [Effort: L]
- [ ] `app/features/actionkit/application/service.py` 수정
  - [ ] `upload_item_file()`: ActionKitFile 생성 제거, File 생성만 유지
    - `ActionKitRepository.create_file_record()` → `FileRepository.create(File(...))`
    - `ActionKitRepository.clear_current_file_flags()` → `FileRepository.set_current()` (이미 사용 중이므로 레거시 호출만 제거)
    - `ActionKitRepository.get_next_file_version()` → `FileRepository.get_next_version()`
  - [ ] TODO(4B-6) 주석 제거
- [ ] `app/api/v1/actionkit/files.py` 수정
  - [ ] `_resolve_file()`: `ActionKitRepository.list_current_files()` → `FileRepository.get_current_files()`
  - [ ] 응답 스키마: `file_id`를 `File.id`로 변경
  - [ ] 뷰/다운로드 로직: File 모델 기반으로 `object_key` 해석
- [ ] `app/repositories/actionkit_repository.py` 수정
  - [ ] `list_current_files()` 메서드 제거
  - [ ] `create_file_record()` 메서드 제거
  - [ ] `clear_current_file_flags()` 메서드 제거
  - [ ] `get_next_file_version()` 메서드 제거
  - [ ] `ActionKitFile` import 제거 (다른 곳에서 미사용 확인)
- [ ] `make test` 통과 확인
- **AC:** ActionKit 파일 업로드/조회/다운로드가 File 모델만 사용, 레거시 메서드 0개
- **Depends:** B-2 완료

### C-2. GrowthClub 서비스/라우터 전환 [Effort: M]
- [ ] `app/features/growth_club/application/post_service.py` 수정
  - [ ] `create_post()`: `GrowthClubPostAttachment` 생성 제거 → `FileRepository.create(File(...))` 전용
  - [ ] `delete_post()`: `db_post.attachments` 대신 `FileRepository.get_by_owner()` 사용
  - [ ] `db_post.attachments = attachment_rows` 관계 할당 제거
- [ ] `app/api/v1/growth_club/posts.py` 수정
  - [ ] 게시글 조회 응답에서 attachments를 File 기반 DTO로 변경
  - [ ] 기존 필드명 (`object_key`, `kind`, `original_filename` 등) 호환성 유지
- [ ] 프론트엔드 타입 대응 (필요시)
  - [ ] `PostCard.tsx` attachment 타입 확인
  - [ ] `CreatePostForm.tsx` 변경 불필요 확인 (FormData는 동일)
- [ ] `make test` + `pnpm lint` 통과 확인
- **AC:** GrowthClub 게시글 생성/삭제/조회가 File 모델만 사용
- **Depends:** A-2 완료

### C-3. UserProfile 전환 [Effort: M]
- [ ] `app/features/profile/application/service.py` 수정
  - [ ] `save_profile_image()`: `profile.profile_img = ...` 갱신 제거 → File 레코드만 관리
  - [ ] 프로필 조회 시 `profile_img` 값을 File 테이블에서 도출하는 로직 추가
- [ ] `app/api/v1/profile/me.py` 수정
  - [ ] `UserProfileRead` 응답에 `profile_img` 필드 호환 유지
  - [ ] 선택지: computed property로 `File.object_key` → `profile_img` 반환
- [ ] 프론트엔드 대응
  - [ ] `profile/page.tsx`: `profile.profile_img` 사용 패턴 확인 → 변경 불필요 확인
  - [ ] `resolveUploadUrl()`: object_key 형식 동일하므로 변경 불필요 확인
- [ ] `make test` + `pnpm lint` 통과 확인
- **AC:** 프로필 이미지 업로드/조회가 File 모델만 사용, API 응답 호환 유지

---

## Phase D: 레거시 테이블 제거

### D-1. Alembic DROP 마이그레이션 [Effort: M]
- [ ] 새 마이그레이션 파일 생성
  - [ ] `op.execute("DROP TABLE IF EXISTS _file_id_mapping")`
  - [ ] `op.drop_table("growthclubpostattachment")`
  - [ ] `op.drop_table("actionkit_files")`
  - [ ] `op.drop_column("userprofile", "profile_img")` (선택)
  - [ ] `downgrade()`: 데이터 복구 불가 → `raise NotImplementedError("irreversible migration")`
- [ ] Docker 환경에서 마이그레이션 실행 테스트
- **AC:** 레거시 테이블 DROP 완료, `alembic check` clean
- **Depends:** C-1, C-2, C-3 전체 완료

### D-2. 코드 정리 [Effort: M]
- [ ] `app/models/actionkit.py` 수정
  - [ ] `ActionKitFile` 클래스 삭제
  - [ ] `ActionKitItem.files` relationship 삭제
- [ ] `app/models/growth_club.py` 수정
  - [ ] `GrowthClubPostAttachment` 클래스 삭제
  - [ ] `GrowthClubPost.attachments` relationship 삭제
- [ ] `app/models/profile.py` 수정 (선택)
  - [ ] `profile_img` 필드 제거
- [ ] `app/models/__init__.py` 수정
  - [ ] `ActionKitFile`, `GrowthClubPostAttachment` import/export 제거
- [ ] `alembic/env.py` 수정
  - [ ] 해당 모델 import 제거 (있는 경우)
- [ ] `scripts/migrate_files_table.py` 삭제
- [ ] `make test` 통과 확인
- [ ] 레거시 참조 잔존 확인
  ```bash
  grep -r "ActionKitFile\|GrowthClubPostAttachment\|actionkit_files\|growthclubpostattachment" \
    app-backend/app/ --include="*.py" | grep -v __pycache__
  ```
  → 결과 0건
- **AC:** 레거시 모델/참조 완전 제거, 테스트 통과

### D-3. 프론트엔드 타입 동기화 및 최종 검증 [Effort: S]
- [ ] `pnpm types:sync` 실행 → `api-types.ts` 갱신
- [ ] `pnpm lint` 통과 확인
- [ ] `pnpm build` 통과 확인
- [ ] Docker 환경 통합 테스트 (수동)
  - [ ] ActionKit 파일 업로드/뷰/다운로드
  - [ ] GrowthClub 게시글 생성 (이미지+파일 첨부) / 삭제
  - [ ] 프로필 이미지 업로드
  - [ ] Ops 파일 관리 콘솔 목록/통계/삭제
- **AC:** 프론트/백 전체 빌드 통과, 수동 통합 테스트 통과

---

## Summary

| Phase | 태스크 수 | 총 Effort |
|-------|----------|-----------|
| Phase A: 데이터 정합성 | 3 | S+S+S |
| Phase B: FK 재매핑 | 2 | S+M |
| Phase C: 코드 전환 | 3 | L+M+M |
| Phase D: 레거시 제거 | 3 | M+M+S |
| **합계** | **11** | — |

**의존성 순서 (A-2 완료 반영):**
```
A-1 ─→ (A-2 완료) ─→ C-2 ──┐
  └──→ B-1 → B-2 → C-1 ─────┤
A-3 (독립) ───────────────────┤→ D-1 → D-2 → D-3
C-3 (독립, A-1 이후 가능) ────┘
```

**권장 실행 단위 (PR 분할):**
- PR 1: Phase A (A-1 + A-3만, A-2는 완료) — **우선 실행 권장** (Ops 콘솔 데이터 완전성 확보)
- PR 2: Phase B 전체 (FK 재매핑 — Alembic 마이그레이션 포함)
- PR 3: Phase C 전체 (코드 전환 — 가장 큰 변경, 이후 Ops 삭제도 안전)
- PR 4: Phase D 전체 (레거시 제거 — 최종 정리)
