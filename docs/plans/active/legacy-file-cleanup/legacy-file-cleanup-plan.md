# PLAN: 레거시 파일 테이블/모델 정리 — 통합 File 모델 전환

Last Updated: 2026-03-06

## Executive Summary

R2 스토리지 마이그레이션(PR #22)으로 도입된 통합 `files` 테이블이 존재하지만, 3개 feature가 여전히 레거시 파일 모델과 이중 기록(Dual Write) 상태를 유지하고 있다. 이 계획은 레거시 테이블(`actionkit_files`, `growthclubpostattachment`)과 레거시 컬럼(`userprofile.profile_img`)을 제거하고, **`files` 테이블을 유일한 파일 메타데이터 소스**로 전환한다.

**배경 보고서:** `docs/plans/reports/REPORT-legacy-file-cleanup.md`

---

## Current State Analysis

### 이중 구조 현황 (2026-03-06 갱신 — ops-file-manager 구현 반영)

| Feature | 레거시 저장소 | 생성 듀얼 라이트 | 삭제 동기화 | 조회 소스 |
|---------|-------------|---------------|-----------|----------|
| ActionKit | `actionkit_files` 테이블 | O | **X** (고아 레코드 발생) | 레거시만 |
| GrowthClub | `growthclubpostattachment` 테이블 | **O** (커밋 `f9d7ac8`에서 추가) | **O** (`delete_by_owner` 동작 확인) | 레거시만 |
| UserProfile | `userprofile.profile_img` 컬럼 | O | O | 레거시만 |

### 핵심 문제점

1. ~~**GrowthClub 생성 시 `files` 미기록**~~ → **해결됨** (ops-file-manager 커밋 `f9d7ac8`에서 듀얼 라이트 추가)
2. **ActionKit 삭제 시 `files` 미정리** → 삭제된 파일이 Ops 콘솔에 잔존 (고아 레코드) — TODO 주석만 존재 (`service.py:265`) ⚠️ **현행 버그: 지금도 고아 레코드가 누적 중**
3. **FK 의존성:** `roadmap_template_actions.actionkit_file_id` → `actionkit_files.id`
4. **모든 조회가 레거시 모델 사용** → File 모델 전환 불가 상태
5. **[신규] Ops 콘솔 삭제 시 역방향 고아 레코드:** `OpsFilesService.delete_file()`이 `files` 테이블만 삭제, 레거시 테이블 미정리 → Phase C 전까지 주의 필요

---

## Proposed Future State

```
Before (현재):
  ActionKit 업로드 → actionkit_files + files (듀얼 라이트)
  GrowthClub 업로드 → growthclubpostattachment (files 미기록)
  Profile 업로드   → userprofile.profile_img + files (듀얼 라이트)
  모든 조회        → 레거시 테이블

After (목표):
  ActionKit 업로드 → files (단일 소스)
  GrowthClub 업로드 → files (단일 소스)
  Profile 업로드   → files (단일 소스)
  모든 조회        → files + FileRepository
  레거시 테이블    → DROP (삭제)
```

---

## Implementation Phases

### Phase A: 데이터 정합성 확보

> **목표:** `files` 테이블이 모든 파일의 Single Source of Truth가 되도록 보장

**A-1. 마이그레이션 스크립트 실행 및 검증** [Effort: S]
- ⚠️ **선행 필수:** 스크립트에 `--migrate-only` 플래그 추가 (데이터 복사만 실행, FK 재매핑 스킵)
  - 현재 `migrate_files_table.py`에는 `--dry-run`과 `--verify`만 존재, `--migrate-only`는 **미구현 상태**
  - 플래그 추가 없이 본 실행하면 **Phase B(build_id_mapping + remap_fk)까지 의도치 않게 동시 실행됨**
- `scripts/migrate_files_table.py --dry-run` → `--migrate-only` → `--verify` 순서로 실행
- 레거시 3종의 레코드 수가 files 테이블과 일치하는지 확인

**A-2. GrowthClub 듀얼 라이트 추가** [Effort: S]
- `post_service.py:create_post()` 수정
- `GrowthClubPostAttachment` 생성 후 `File` 레코드도 함께 생성
- 기존 마이그레이션 스크립트로 과거 데이터 보정

**A-3. ActionKit 삭제 시 File 정리 추가** [Effort: S] — ⚠️ **현행 버그 수정 (우선 처리 권장)**
- `service.py:delete_item()` (233-239줄)에서 ActionKitItem만 삭제, File 레코드 삭제 누락 → **지금도 고아 레코드 누적 중**
- ActionKitItem 삭제 로직에 `FileRepository.delete_by_owner("actionkit_item", item_id)` 추가

---

### Phase B: FK 재매핑

> **목표:** `roadmap_template_actions.actionkit_file_id`가 `files.id`를 참조하도록 변경

**B-1. FK 데이터 재매핑** [Effort: S]
- `migrate_files_table.py`의 `build_id_mapping()` + `remap_fk()` 활용
- `_file_id_mapping` 임시 테이블로 old_id → new_id 매핑

**B-2. Alembic 마이그레이션 — FK 대상 변경** [Effort: M]
- 기존 FK 제거 (`actionkit_files.id`) → 새 FK 생성 (`files.id`)
- `app/models/roadmap_template.py` FK 선언 수정

---

### Phase C: 애플리케이션 코드 전환

> **목표:** 모든 파일 조회/생성/삭제가 `FileRepository`만 사용

**C-1. ActionKit 서비스/라우터 전환** [Effort: L]
- `ActionKitRepository`의 파일 메서드 4개 → `FileRepository` 메서드로 전환
  - `list_current_files()` → `FileRepository.get_current_files()`
  - `create_file_record()` → `FileRepository.create()`
  - `clear_current_file_flags()` → `FileRepository.set_current()` (이미 사용 중)
  - `get_next_file_version()` → `FileRepository.get_next_version()`
- `api/v1/actionkit/files.py` `_resolve_file()` 수정
- 응답에서 `ActionKitFile.id` → `File.id` 변경 (API 호환성 주의)

**C-2. GrowthClub 서비스/라우터 전환** [Effort: M]
- `GrowthClubPostAttachment` 직접 생성 → `FileRepository.create()` 전환
- `db_post.attachments` 관계 조회 → `FileRepository.get_by_owner()` 전환
- API 응답 스키마 변경 (attachment DTO)

**C-3. UserProfile 전환** [Effort: M]
- `profile.profile_img` 직접 읽기 → `FileRepository.get_by_owner()` 전환
- API 응답에서 `profile_img` 필드는 File.object_key에서 도출 (호환성 유지)

---

### Phase D: 레거시 테이블 제거

> **목표:** 레거시 테이블 DROP + 모델 클래스 삭제

**D-1. Alembic DROP 마이그레이션** [Effort: M]
- `growthclubpostattachment` 테이블 DROP
- `actionkit_files` 테이블 DROP
- `userprofile.profile_img` 컬럼 DROP (선택)
- `_file_id_mapping` 임시 테이블 DROP
- **downgrade:** 데이터 복구 불가한 비가역 마이그레이션 → `raise NotImplementedError("irreversible")`

**D-2. 코드 정리** [Effort: M]
- `ActionKitFile` 모델 + relationship 삭제
- `GrowthClubPostAttachment` 모델 + relationship 삭제
- `models/__init__.py`, `alembic/env.py` import 정리
- `ActionKitRepository` 파일 메서드 4개 삭제
- `scripts/migrate_files_table.py` 삭제

**D-3. 프론트엔드 타입 동기화** [Effort: S]
- `pnpm types:sync` 실행
- 변경된 API 응답 타입에 대응하는 프론트엔드 수정

---

## Risk Assessment

| # | 리스크 | 영향도 | 발생확률 | 완화 전략 |
|---|--------|--------|---------|----------|
| 1 | FK 재매핑 실패 — orphan 발생 | 높음 | 낮음 | `--verify` 검증 스크립트, 트랜잭션 내 실행 |
| 2 | API 응답 스키마 변경 — 프론트 깨짐 | 높음 | 중간 | 프론트/백 동시 배포, `types:sync` 필수 |
| 3 | 미실행 상태에서 테이블 DROP | 치명 | 낮음 | Phase A 검증 게이트 → Phase D 진입 조건 |
| 4 | GrowthClub 기존 데이터 누락 | 중간 | 높음 | Phase A-1 스크립트로 과거 데이터 보정 |
| 5 | profile_img 기본값 폴백 깨짐 | 중간 | 중간 | File 미존재 시 "default.png" 반환 로직 |
| 6 | CASCADE 삭제 경로 변경 | 높음 | 중간 | Phase A-3에서 명시적 File 삭제 추가 |
| 7 | Ops 콘솔 삭제 → 레거시 고아 레코드 | 중간 | 중간 | **Phase C 완료 전까지 Ops 콘솔 파일 삭제 자제.** 삭제 시 레거시 경로에서 스토리지 404 발생. Phase C 완료 시 자동 해소 |

---

## Success Metrics

- [ ] `files` 테이블 레코드 수 == 레거시 3종 합계 (데이터 정합)
- [ ] `actionkit_files` 테이블 DROP 완료
- [ ] `growthclubpostattachment` 테이블 DROP 완료
- [ ] 모든 파일 조회/생성/삭제가 `FileRepository`만 사용
- [ ] FK orphan 0건 (`roadmap_template_actions.actionkit_file_id`)
- [ ] `make test` + `pnpm lint` + `pnpm build` 통과
- [ ] Ops 파일 관리 콘솔에서 전체 파일 정상 표시

---

## Dependencies

- **선행:** `ops-file-manager` 계획 **구현 완료** (커밋 `f9d7ac8`, feature/0-ops-file-manager 브랜치)
- **Phase A:** A-1(데이터 마이그레이션) 우선 실행 필수 — Ops 파일 콘솔이 `files` 테이블만 조회하므로, 실행 전에는 과거 파일이 콘솔에 미표시
- **Phase A-2:** ~~구현 필요~~ → **이미 완료** (ops-file-manager 커밋에서 `post_service.py:153-166`에 GrowthClub 듀얼 라이트 구현됨)
- **Phase B:** Phase A-1 완료 필수
- **Phase C:** Phase B 완료 필수 (ActionKit), C-2는 A-2 완료 후 가능 (이미 충족), C-3(UserProfile)은 A-1 이후 즉시 가능
- **Phase D:** Phase C 전체 완료 + 검증 필수

### ops-file-manager 연동 주의사항

> **역방향 고아 레코드 위험:** Ops 파일 콘솔(`OpsFilesService.delete_file/delete_files`)은 `files` 테이블 + 스토리지만 삭제하고, 레거시 테이블(`actionkit_files`, `growthclubpostattachment`)은 정리하지 않는다.
> Phase C(코드 전환) 완료 전에 Ops 콘솔에서 파일을 삭제하면 레거시 테이블에 고아 레코드가 남고, 레거시 조회 경로에서 스토리지 404가 발생할 수 있다.
> **완화:** Phase C 완료 전까지 Ops 콘솔 삭제 기능은 신중하게 사용하거나, Phase C를 가능한 빠르게 실행한다.

## DB 변경: 있음

- Phase B: FK 재매핑 마이그레이션 1건
- Phase D: 테이블 DROP 마이그레이션 1건
