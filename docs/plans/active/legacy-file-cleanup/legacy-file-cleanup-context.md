# Context: 레거시 파일 테이블/모델 정리

Last Updated: 2026-03-06 (Phase A~C 완료, Phase D 미착수)

## Key Files

### 레거시 모델 (Phase D에서 제거 대상)

| 파일 | 모델/필드 | 테이블 |
|------|----------|--------|
| `app-backend/app/models/actionkit.py` | `ActionKitFile` 클래스 + `ActionKitItem.files` relationship | `actionkit_files` |
| `app-backend/app/models/growth_club.py` | `GrowthClubPostAttachment` 클래스 + `GrowthClubPost.attachments` relationship | `growthclubpostattachment` |
| `app-backend/app/models/profile.py` | `UserProfile.profile_img` VARCHAR 필드 | `userprofile` 컬럼 |

### 통합 모델 (유지 — 현재 유일한 파일 소스)

| 파일 | 역할 |
|------|------|
| `app-backend/app/models/file.py` | `File` 통합 모델 (owner_type + owner_id 폴리모픽) |
| `app-backend/app/repositories/file_repository.py` | `FileRepository` — CRUD 10개 메서드 |

### Phase C 완료 상태

| 파일 | 현재 상태 |
|------|----------|
| `app-backend/app/features/actionkit/application/service.py` | ✅ File만 사용 (레거시 ActionKitFile 생성 제거됨) |
| `app-backend/app/features/growth_club/application/post_service.py` | ✅ File만 사용 (Attachment 생성 제거됨) |
| `app-backend/app/features/profile/application/service.py` | ✅ File primary + profile_img 컬럼 동기화 유지 |
| `app-backend/app/api/v1/actionkit/files.py` | ✅ FileRepository.get_current_files() 사용 |
| `app-backend/app/api/v1/growth_club/posts.py` | ✅ File 기반 attachment 조회 |
| `app-backend/app/repositories/actionkit_repository.py` | ✅ 파일 메서드 4개 제거 완료 |

### Phase D에서 수정할 파일

| 파일 | 변경 내용 |
|------|----------|
| `app-backend/app/models/actionkit.py` | `ActionKitFile` 클래스 삭제, `ActionKitItem.files` relationship 삭제 |
| `app-backend/app/models/growth_club.py` | `GrowthClubPostAttachment` 클래스 삭제, `GrowthClubPost.attachments` relationship 삭제 |
| `app-backend/app/models/profile.py` | `profile_img` 필드 제거 (선택) |
| `app-backend/app/models/__init__.py` | `ActionKitFile`, `GrowthClubPostAttachment` import/export 제거 |
| `app-backend/alembic/env.py` | 해당 모델 import 제거 |
| `app-backend/scripts/migrate_files_table.py` | 삭제 |

---

## 주요 기술 결정

| 결정 | 선택 | 근거 |
|------|------|------|
| 정리 순서 | 데이터 정합 → FK 재매핑 → 코드 전환 → 테이블 DROP | 각 단계가 다음 단계의 선행 조건 |
| profile_img 컬럼 | Phase C에서 동기화 유지, Phase D에서 제거 (선택) | AuthorRead가 profile_img 컬럼을 직접 참조하므로 즉시 제거 불가 |
| GrowthClub 조회 전환 | selectinload 제거 + File IN 쿼리 | attachments relationship 유지하면서도 File 기반 조회 |
| FK 재매핑 방식 | object_key JOIN으로 매핑 | actionkit_files.object_key == files.object_key (UNIQUE) |
| API 응답 호환성 | 필드명 유지, 소스만 변경 | 프론트엔드 수정 최소화 |

---

## Phase C → D 게이트 (진입 조건)
```bash
cd app-backend && make test              # 전체 통과 ✅
cd app-frontend && pnpm lint             # 전체 통과 ✅
# 레거시 모델 참조 확인:
grep -r "ActionKitFile\|GrowthClubPostAttachment" app-backend/app/ --include="*.py"
# → actionkit.py, growth_club.py (모델 정의만 남아야 함)
```
