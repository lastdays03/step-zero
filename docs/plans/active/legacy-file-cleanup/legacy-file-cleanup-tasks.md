# Tasks: 레거시 파일 테이블/모델 정리

Last Updated: 2026-03-06

## Phase A: 데이터 정합성 확보 — ✅ 완료

### A-1. 마이그레이션 스크립트 실행 및 검증 [Effort: S] — ✅ 완료
- [x] `migrate_files_table.py`에 `--migrate-only` 플래그 구현 (커밋 `3d3b718`, PR #25)
- [x] `migrate_files_table.py --dry-run` 실행 → 71건 확인
- [x] `migrate_files_table.py --migrate-only` 실행 (데이터 복사)
- [x] `migrate_files_table.py --verify` 실행 → 3종 모두 OK
  - ActionKit: 67 → 67, GrowthClub: 3 → 3, Profile: 1 → 1, FK orphan: 0건
- **AC:** 달성

### A-2. GrowthClub 생성 시 듀얼 라이트 추가 [Effort: S] — ✅ 완료 (ops-file-manager에서 구현)
- [x] 구현 완료 (커밋 `f9d7ac8`)

### A-3. ActionKit 삭제 시 File 정리 추가 [Effort: S] — ✅ 완료 (PR #25)
- [x] 구현 완료 (커밋 `3d3b718`)

---

## Phase B: FK 재매핑 — ✅ 완료

### B-1. FK 데이터 재매핑 [Effort: S] — ✅ 완료
- [x] `build_id_mapping()` 실행 → 67건 매핑 생성
- [x] `remap_fk()` 실행 → FK 대상 0건 (현재 NULL만)
- [x] 검증: FK orphan 0건 확인

### B-2. Alembic FK 대상 변경 마이그레이션 [Effort: M] — ✅ 완료
- [x] `016_fk_remap_actionkit_file_to_files.py` 생성 + 적용
- [x] `_file_id_mapping` 임시 테이블 DROP 포함
- [x] `app/models/roadmap_template.py` FK 수정 (`actionkit_files.id` → `files.id`)
- [x] `alembic check` → diff 없음
- [x] `make test` → 421 passed, 10 skipped

---

## Phase C: 애플리케이션 코드 전환 — ✅ 완료

### C-1. ActionKit 서비스/라우터 전환 [Effort: L] — ✅ 완료
- [x] `service.py:upload_item_file()`: 레거시 ActionKitFile 생성 제거, File만 사용
- [x] `service.py:_build_law_payload()/_build_kit_payload()`: FileRepository.get_current_files() 사용
- [x] `files.py:_resolve_file()`: FileRepository 사용
- [x] `actionkit_repository.py`: 파일 메서드 4개 + ActionKitFile import 제거
- [x] TODO(4B-6) 주석 제거
- [x] `make test` 통과

### C-2. GrowthClub 서비스/라우터 전환 [Effort: M] — ✅ 완료
- [x] `post_service.py:create_post()`: GrowthClubPostAttachment 생성 제거, File만 생성
- [x] `post_service.py:delete_post()`: FileRepository.get_by_owner()로 attachment keys 조회
- [x] `posts.py:list_posts()`: File 기반 attachments 일괄 조회 (selectinload 제거)
- [x] `posts.py:create_post()` 응답: File 기반 GrowthClubAttachmentRead 매핑
- [x] `make test` + `pnpm lint` 통과

### C-3. UserProfile 전환 [Effort: M] — ✅ 완료
- [x] `service.py:save_profile_image()`: File primary source, profile_img 컬럼 동기화 유지
- [x] AuthorRead 호환성 유지 (profile_img 컬럼 계속 갱신)
- [x] `make test` 통과
- **Note:** profile_img 컬럼 제거는 Phase D에서 처리

---

## Phase D: 레거시 테이블 제거 — ✅ 완료

### D-1. Alembic DROP 마이그레이션 [Effort: M] — ✅ 완료
- [x] `017_drop_legacy_file_tables.py` 생성
  - [x] `op.drop_table("actionkit_files")`
  - [x] `op.drop_table("growthclubpostattachment")`
  - [x] `downgrade()`: `raise NotImplementedError("irreversible migration")`
  - [x] `userprofile.profile_img` 컬럼 유지 (AuthorRead 호환)
- **Depends:** C-1, C-2, C-3 전체 완료 ✅

### D-2. 코드 정리 [Effort: M] — ✅ 완료
- [x] `ActionKitFile` 클래스 + `ActionKitItem.files` relationship 삭제
- [x] `GrowthClubPostAttachment` 클래스 + `GrowthClubPost.attachments` relationship 삭제
- [x] `models/__init__.py` import 정리
- [x] `scripts/migrate_files_table.py` 삭제
- [x] `actionkit_matcher.py` → `File` 모델 전환
- [x] `ops/actionkit/service.py` → `File` + `FileRepository` 전환
- [x] `ops/growth_club.py` → `File` 기반 attachment 조회 전환
- [x] `seed_actionkit.py`, `seed_rag_vectors.py` → `File` 전환
- [x] `roadmap_evaluator.py` → `File` 전환
- [x] `test_roadmap_generation.py` → `File` 전환
- [x] `make test` 통과 (421 passed, 10 skipped)
- [x] 레거시 ORM 모델 참조 잔존 grep 0건

### D-3. 프론트엔드 검증 [Effort: S] — ✅ 완료
- [x] `pnpm lint` 통과 (0 errors, 1 warning — 기존)

---

## Summary

| Phase | 상태 |
|-------|------|
| Phase A: 데이터 정합성 | ✅ 완료 |
| Phase B: FK 재매핑 | ✅ 완료 |
| Phase C: 코드 전환 | ✅ 완료 |
| Phase D: 레거시 제거 | ✅ 완료 |

**권장 PR 분할:**
- ~~PR 1: Phase A~~ → PR #25 머지 완료
- ~~PR 2: Phase B+C~~ → PR #26 머지 완료
- PR 3: Phase D (레거시 제거 — 최종 정리) → 커밋 대기
