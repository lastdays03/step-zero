# PLAN: 운영 콘솔 통합 파일 관리

Last Updated: 2026-03-06

## Executive Summary

운영 콘솔(ops)에 **통합 파일 관리** 페이지를 추가한다. 기존 `files` 테이블(v014 마이그레이션)과 `FileRepository`를 최대한 활용하여, 관리자가 플랫폼 전체 파일을 조회·검색·삭제할 수 있는 인터페이스를 제공한다.

**새 테이블 생성 없이** 기존 인프라를 활용하는 것이 핵심.

---

## Current State Analysis

### 이미 구축된 것
1. **`File` 통합 모델** — `owner_type`/`owner_id` 폴리모픽 패턴으로 3종 엔티티 연결
   - `actionkit_item`, `growth_club_post`, `user_profile`
   - 메타데이터: `object_key`, `original_filename`, `mime_type`, `size_bytes`, `checksum`, `version`, `kind`
2. **`FileRepository`** — CRUD 10개 메서드 완비 (`create`, `get_by_id`, `get_by_key`, `get_by_owner`, `get_current_files`, `delete_by_id`, `delete_by_owner`, `set_current`, `get_next_version`, `commit`)
3. **`StorageBackend` 추상화** — Local/R2 교체 가능, `put`/`get`/`delete`/`get_public_url` 인터페이스 + 선택적 `create_presigned_put_url`
4. **`get_storage_backend()` 팩토리** — `app.services.storage`에서 import하여 사용 (기존 feature들의 공통 패턴)
5. **감사 로그** — `record_admin_audit_log()` 함수 + `AuditAction`/`AuditTargetType` 상수 체계 (`app/features/ops/application/audit_logs/`)
6. **듀얼 라이트** — 3개 feature 모두 `File` 테이블에 기록 중 (레거시 모델 병행)

### 없는 것 (= 이번에 구현할 것)
1. 전체 파일 목록 조회 API (페이지네이션, 필터, 정렬)
2. 사용량 통계 API (총 용량, 타입별 분포)
3. 관리자 파일 삭제 API (단건 + 일괄)
4. 프론트엔드 파일 관리 페이지 (목록, 필터, 통계, 삭제)

---

## Proposed Future State

### 관리자 파일 관리 페이지 (`/ops/files`)

```
┌──────────────────────────────────────────────────────────────┐
│  통합 파일 관리                                    [검색...]   │
├──────────────────────────────────────────────────────────────┤
│  [총 파일 수]  [총 용량]  [이미지]  [문서]  [기타]              │
│   1,234개      2.3 GB    45%      38%     17%               │
├──────────────────────────────────────────────────────────────┤
│  필터: [소유 타입 ▼] [파일 타입 ▼] [날짜 범위]  [초기화]       │
├──────────────────────────────────────────────────────────────┤
│  ☐ │ 미리보기 │ 파일명        │ 타입     │ 크기  │ 소유│ 날짜  │
│  ☐ │ [thumb]  │ invoice.pdf  │ PDF      │ 2.1MB │ GC │ 03/05 │
│  ☐ │ [thumb]  │ avatar.jpg   │ 이미지   │ 340KB │ PR │ 03/04 │
│  ☐ │ [icon]   │ guide.docx   │ 문서     │ 1.5MB │ AK │ 03/03 │
│  ...                                                         │
├──────────────────────────────────────────────────────────────┤
│  [선택 삭제 (N개)]           페이지 1 / 12  [< 이전] [다음 >]  │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: 백엔드 API (3개 파일 신규 + 2개 수정)

#### 1-1. 파일 관리 서비스 (`app/features/ops/application/files/service.py`)

4개 메서드: `list_files`, `get_stats`, `delete_file`, `delete_files`. 구현 상세는 context 파일 참조.

**핵심 설계 원칙:**
- `get_public_url()`은 **동기 메서드** — `await` 금지
- `storage.delete()` → `bool` 반환 — 실패 시(`False`) 해당 파일 skip 후 응답에 실패 목록 포함
- 일괄 삭제: storage 삭제 루프에서 **성공 ID / 실패 ID 분리** → DB 삭제는 성공분만 `sa.delete().where(in_(success_ids))`
- 감사 로그: `record_admin_audit_log()` 호출 시 `reason` 파라미터도 전달 가능 (선택)
- 트랜잭션: 서비스 내부 `flush()`, 라우터 레벨 `session.commit()` (기존 ops 패턴)

#### 1-2. 파일 관리 라우터 (`app/api/v1/ops/files.py`)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/ops/files` | GET | 파일 목록 (페이지네이션 + 필터) |
| `/ops/files/stats` | GET | 사용량 통계 |
| `/ops/files/{file_id}` | DELETE | 단건 삭제 |
| `/ops/files/batch` | DELETE | 일괄 삭제 (body: `{ ids: list[int] }`) |

스키마: `OpsFileListParams`, `OpsFileResponse`, `OpsFileListResponse`, `OpsFileStatsResponse`, `OpsFileBatchDeleteRequest`, `OpsFileBatchDeleteResponse`

---

### Phase 2: 프론트엔드 UI (1 페이지 + 4~5 컴포넌트)

#### 2-1. 모듈 구조

```
src/features/ops/files/
├── index.ts              # re-export
├── api.ts                # API 호출 함수
├── types.ts              # 타입 정의
└── view.tsx              # 메인 뷰 (OpsFilesView)
```

```
src/app/(dashboard)/ops/files/
└── page.tsx              # Next.js 페이지
```

#### 2-2. 뷰 컴포넌트 구성

**OpsFilesView** (메인 뷰)
- 상단: 통계 카드 4개 (총 파일, 총 용량, 이미지 비율, 문서 비율)
- 중단: 필터 바 (owner_type 드롭다운, mime_group 드롭다운, 날짜 범위, 검색어)
- 하단: 파일 테이블 + 페이지네이션

**파일 테이블 컬럼:**
| 컬럼 | 내용 |
|------|------|
| ☐ | 체크박스 (일괄 선택) |
| 미리보기 | 이미지면 32x32 썸네일, 아니면 파일 타입 아이콘 |
| 파일명 | `original_filename` (없으면 `object_key` 끝부분) |
| 타입 | MIME 그룹 뱃지 (이미지/PDF/문서/기타) |
| 크기 | 사람이 읽기 좋은 형식 (1.2 MB) |
| 소유 | owner_type 뱃지 (AK/GC/PR) |
| 업로드일 | `uploaded_at` 포맷 |
| 액션 | 삭제 버튼 |

**일괄 삭제 UX:**
- 체크박스 선택 시 하단에 "선택 삭제 (N개)" 버튼 노출
- 클릭 시 확인 다이얼로그 → 일괄 삭제 API 호출

---

### Phase 3: 통합 & 연결

- `app/api/v1/ops/router.py`에 files 라우터 import + `include_router` 추가
- `app/features/ops/application/audit_logs/constants.py`에 파일 관련 감사 상수 추가
- `src/features/ops/index.ts`에 files 모듈 re-export
- ops 홈 뷰에 "파일 관리" 카드 추가 (`src/features/ops/home/view.tsx` — 기존 운영 콘솔 메뉴 허브)

---

## Risk Assessment

| 리스크 | 영향 | 완화 |
|--------|------|------|
| 듀얼 라이트 누락 — `File` 테이블에 기록 안 된 파일 존재 가능 | 일부 파일이 목록에 안 보임 | Phase 1 범위 외 — 향후 데이터 정합성 검증 태스크에서 처리 |
| 대량 삭제 시 스토리지 삭제 실패 | DB와 스토리지 불일치 | 삭제 루프에서 성공/실패 ID 분리 → 성공분만 DB 삭제, 응답에 `failed` 수 포함 |
| 파일 수가 많을 때 COUNT(*) 성능 | 통계 API 느려짐 | 현재 규모에서는 문제 없음. 필요 시 캐시 추가 |

---

## Success Metrics

- [ ] 관리자가 `/ops/files`에서 전체 파일 목록을 조회할 수 있다
- [ ] owner_type, mime_group, 날짜, 검색어 필터가 동작한다
- [ ] 통계 카드가 총 파일 수, 용량, 타입별 비율을 표시한다
- [ ] 단건/일괄 파일 삭제가 DB + 스토리지 모두에서 수행된다
- [ ] 기존 테스트가 깨지지 않는다 (`make test` + `pnpm lint` 통과)

---

## Dependencies

- 기존 `File` 모델 (`app/models/file.py`) — 변경 없이 사용
- 기존 `FileRepository` (`app/repositories/file_repository.py`) — 확장 (목록 조회 메서드 추가)
- 기존 `StorageBackend` — delete 메서드 활용
- 기존 ops 라우터 패턴 — `require_platform_admin` 의존성

## DB 변경: 없음

기존 `files` 테이블을 그대로 사용. Alembic 마이그레이션 불필요.
