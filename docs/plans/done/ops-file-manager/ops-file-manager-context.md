# Context: 운영 콘솔 통합 파일 관리

Last Updated: 2026-03-06

## Key Files

### 백엔드 — 기존 인프라 (변경 없이 재활용)

| 파일 | 역할 |
|------|------|
| `app-backend/app/models/file.py` | `File` 통합 모델 (폴리모픽 owner_type/owner_id) |
| `app-backend/app/repositories/file_repository.py` | File CRUD 레포지토리 (확장 예정) |
| `app-backend/app/services/storage/base.py` | StorageBackend ABC |
| `app-backend/app/services/storage/factory.py` | `get_storage_backend()` 팩토리 |
| `app-backend/app/services/storage/local.py` | 로컬 파일시스템 백엔드 |
| `app-backend/app/services/storage/r2.py` | Cloudflare R2 백엔드 |
| `app-backend/app/api/v1/ops/router.py` | ops 라우터 허브 (files 라우터 등록 위치) |
| `app-backend/app/api/v1/ops/schemas.py` | ops 공통 스키마 (참조) |
| `app-backend/app/features/ops/application/audit_logs/constants.py` | 감사 로그 action/target_type 상수 (파일 관련 상수 추가 필요) |
| `app-backend/app/features/ops/application/audit_logs/service.py` | `record_admin_audit_log()` 함수 (삭제 시 호출) |

### 백엔드 — 새로 생성할 파일

| 파일 | 역할 |
|------|------|
| `app-backend/app/features/ops/application/files/__init__.py` | 모듈 init (OpsFilesService export) |
| `app-backend/app/features/ops/application/files/service.py` | 파일 목록/통계/삭제 서비스 |
| `app-backend/app/api/v1/ops/files.py` | REST 라우터 (GET /files, GET /stats, DELETE) |

### 프론트엔드 — 새로 생성할 파일

| 파일 | 역할 |
|------|------|
| `app-frontend/src/features/ops/files/index.ts` | 모듈 re-export |
| `app-frontend/src/features/ops/files/api.ts` | API 호출 (fetchFiles, fetchStats, deleteFile, deleteFiles) |
| `app-frontend/src/features/ops/files/types.ts` | 타입 (OpsFile, OpsFileStats, OpsFileListParams) |
| `app-frontend/src/features/ops/files/view.tsx` | 메인 뷰 컴포넌트 (OpsFilesView) |
| `app-frontend/src/app/(dashboard)/ops/files/page.tsx` | Next.js 페이지 |

### 프론트엔드 — 수정할 파일

| 파일 | 변경 내용 |
|------|-----------|
| `app-frontend/src/features/ops/index.ts` | `files` 모듈 re-export 추가 (`export * from "./files"`) |
| `app-frontend/src/features/ops/home/view.tsx` | "파일 관리" 카드 추가 (ops 홈 = 운영 콘솔 메뉴 허브, Link → `/ops/files`) |

---

## 기존 File 모델 스키마 요약

```python
class File(SQLModel, table=True):
    id: Optional[int]                  # PK
    owner_type: str                    # "actionkit_item" | "growth_club_post" | "user_profile"
    owner_id: int                      # 소유 엔티티 ID
    category: str                      # "document" | "image" | "file" | "profile_image" (default="document")
    object_key: str                    # 스토리지 경로 (UNIQUE)
    original_filename: Optional[str]   # 원본 파일명
    mime_type: Optional[str]           # MIME 타입
    size_bytes: Optional[int]          # 바이트 크기
    checksum: Optional[str]            # SHA256 (ActionKit용)
    version: Optional[int]             # 버전 (ActionKit용)
    is_current: Optional[bool]         # 현재 버전 여부 (ActionKit용)
    kind: Optional[str]                # "image" | "file" (GrowthClub용)
    metadata_extra: dict               # JSON 확장 필드 (server_default="{}")
    uploaded_at: datetime
    created_at: datetime
```

**인덱스:** `(owner_type, owner_id)`, `(owner_type, owner_id, is_current)`, `owner_type`, `owner_id`, `version`, `is_current`, `kind`

---

## 기존 FileRepository 메서드

| 메서드 | 용도 | 이번 작업에서 사용 |
|--------|------|--------------------|
| `create()` | 파일 레코드 생성 | X |
| `get_by_id()` | ID로 단건 조회 | O (삭제 전 조회 — SELECT → session.delete 2단계) |
| `get_by_key()` | object_key로 조회 | X |
| `get_by_owner()` | 소유자별 파일 목록 | X |
| `get_current_files()` | ActionKit is_current=True 조회 | X |
| `delete_by_id()` | ID로 삭제 (SELECT → session.delete) | O (단건 삭제) |
| `delete_by_owner()` | 소유자별 일괄 삭제 (bulk sa.delete) | X |
| `set_current()` | ActionKit 현재 버전 설정 | X |
| `get_next_version()` | ActionKit 다음 버전 번호 | X |
| `commit()` | session.commit() 래퍼 | △ (라우터에서 직접 commit 시 불필요) |

**추가 필요 메서드 (서비스 레이어에서 직접 쿼리):**
- `list_files()` — 페이지네이션 + 필터 + 정렬 + total count (SELECT + COUNT)
- `get_stats()` — 집계 쿼리 (COUNT, SUM, GROUP BY, CASE WHEN)
- 일괄 삭제 — 스토리지 삭제는 파일별 루프 필수 (성공/실패 ID 분리), DB 삭제는 `sa.delete().where(File.id.in_(success_ids))` 성공분만 bulk 삭제

→ 기존 repo 패턴(단순 CRUD)과 달리 복합 쿼리이므로 서비스에서 직접 쿼리
→ ⚠️ 기존 `delete_by_id()`는 내부에서 `flush()` 호출하지 않음 — 서비스에서 명시적 `flush()` 필요

---

## 참조 패턴 (기존 ops 모듈)

### 서비스 패턴 (`OpsReportsService` 참조)
```python
from app.services.storage import get_storage_backend
from app.features.ops.application.audit_logs import record_admin_audit_log

class OpsFilesService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_files(...) -> dict:
        storage = get_storage_backend()
        # ... 쿼리 후 각 파일에 public_url 추가
        # ⚠️ get_public_url()은 동기 메서드 — await 금지
        # url = storage.get_public_url(file.object_key)
        ...
    async def get_stats() -> dict:
        ...
    async def delete_file(file_id: int, *, admin_id: int) -> bool:
        storage = get_storage_backend()
        # 1) storage.delete(object_key) → bool 반환, False면 raise/에러 처리
        # 2) session.delete(file) + flush()  ← repo의 delete_by_id는 flush 안 하므로 직접 flush 필요
        # 3) record_admin_audit_log(session, admin_id=..., action=..., reason=..., ...)
        ...
    async def delete_files(file_ids: list[int], *, admin_id: int) -> dict:
        # loop: storage.delete per file → 성공/실패 ID 분리
        # DB 삭제: sa.delete(File).where(File.id.in_(success_ids)) ← 성공분만
        # flush()
        # audit log 1건 (bulk) — meta에 deleted_count, failed_count, failed_ids 포함
        # return { "deleted": len(success_ids), "failed": len(failed_ids) }
        ...
```

### 라우터 패턴 (`ops/reports.py` 참조)
```python
router = APIRouter(prefix="/files")

@router.get("/", ...)
async def list_files(..., session = Depends(get_session)):
    service = OpsFilesService(session)
    return await service.list_files(...)

@router.delete("/{file_id}", ...)
async def delete_file(
    file_id: int,
    session = Depends(get_session),
    admin = Depends(deps.get_current_user),
):
    service = OpsFilesService(session)
    result = await service.delete_file(file_id, admin_id=admin.id)
    await session.commit()  # 트랜잭션 커밋은 라우터에서
    return result
```

### 프론트엔드 뷰 패턴 (`OpsReportsView` 참조)
- `useOpsAccessGuard()` — 관리자 접근 제어 (`@/features/ops/shared/use-ops-access-guard`)
- `OpsAccessPlaceholder` — 비관리자 표시 (`@/features/ops/shared/ops-access-placeholder`)
- `useCallback` + `useEffect` — 데이터 로딩
- `Card`, `CardContent` — shadcn/ui 컴포넌트

### ops 홈 메뉴 허브 패턴 (`OpsHomeView`)
- `src/features/ops/home/view.tsx` — 모든 ops 하위 페이지를 카드 형태로 나열
- 각 카드: `<article>` + `<h2>` + 설명 + `<Link href="/ops/{slug}">`
- 새 모듈 추가 시 이 파일에 카드 1개 추가 (별도 사이드바/네비게이션 없음)

---

## MIME 그룹 분류 로직

```python
MIME_GROUPS = {
    "image": ["image/"],
    "document": ["application/pdf", "application/msword",
                 "application/vnd.openxmlformats", "text/"],
    "other": [],  # fallback
}
```

SQL CASE WHEN으로 그룹 집계:
```sql
CASE
  WHEN mime_type LIKE 'image/%' THEN 'image'
  WHEN mime_type LIKE 'application/pdf%'
    OR mime_type LIKE 'application/msword%'
    OR mime_type LIKE 'application/vnd.openxmlformats%'
    OR mime_type LIKE 'text/%' THEN 'document'
  ELSE 'other'
END
```

---

## 감사 로그 연동 상세

### 추가 필요 상수 (`audit_logs/constants.py`)

```python
# AuditAction에 추가
FILE_DELETED: Final[str] = "file.deleted"
FILE_BULK_DELETED: Final[str] = "file.bulk_deleted"

# AuditTargetType에 추가
FILE: Final[str] = "file"

# ALLOWED_AUDIT_ACTIONS, ALLOWED_AUDIT_TARGET_TYPES에도 추가
```

### `record_admin_audit_log()` 호출 시그니처

```python
# 실제 시그니처 (audit_logs/service.py):
# record_admin_audit_log(session, *, admin_id, action, target_type, target_id=None, reason=None, meta=None)
# ⚠️ action/target_type이 ALLOWED_* 화이트리스트에 없으면 ValueError raise

await record_admin_audit_log(
    session,
    admin_id=admin.id,
    action=AuditAction.FILE_DELETED,      # 또는 FILE_BULK_DELETED
    target_type=AuditTargetType.FILE,
    target_id=str(file.id),               # 단건: file_id, 일괄: None
    reason=None,                          # 선택: 삭제 사유
    meta={
        "filename": file.original_filename,
        "object_key": file.object_key,
        "size_bytes": file.size_bytes,
        # 일괄 삭제 시: "deleted_count": N, "failed_count": M, "file_ids": [...]
    },
)
```

---

## StorageBackend 사용 패턴 (기존 코드 참조)

```python
from app.services.storage import get_storage_backend

# 메서드 내부에서 호출 (DI 아님, 팩토리 직접 호출)
storage = get_storage_backend()
ok = await storage.delete(file.object_key)       # 파일 삭제 → bool 반환 (실패 시 False)
url = storage.get_public_url(file.object_key)    # 공개 URL 생성 (⚠️ 동기 메서드, await 금지)
```

---

## 주요 기술 결정

| 결정 | 선택 | 근거 |
|------|------|------|
| 페이지네이션 | offset 기반 | 관리자가 N페이지 점프 필요, 데이터량 10만 이하 |
| 뷰 모드 | 테이블 뷰만 | 기존 ops 페이지 일관성 (users, audit-logs 등) |
| 삭제 방식 | 하드 딜리트 | 기존 동작 유지, 소프트 딜리트는 향후 Phase |
| 이미지 미리보기 | 원본 URL 32x32 축소 | 별도 썸네일 생성 불필요 |
| DB 변경 | 없음 | files 테이블 그대로 사용 |
| 레포지토리 확장 | 서비스에서 직접 쿼리 | 복합 쿼리(필터+페이지네이션+집계)는 repo 패턴에 안 맞음 |
| 트랜잭션 관리 | 라우터에서 commit | 서비스는 flush만, commit은 라우터 레벨 (기존 ops 패턴) |
| 스토리지 의존성 | 팩토리 직접 호출 | `get_storage_backend()` — DI 아닌 메서드 내 호출 (기존 패턴 통일) |
| 감사 로그 | `record_admin_audit_log()` | 기존 함수 재사용 + constants.py에 상수 2개 추가 |
