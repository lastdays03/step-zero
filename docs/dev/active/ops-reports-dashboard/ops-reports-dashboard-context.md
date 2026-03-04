# Ops Reports Dashboard - Context

> Last Updated: 2026-03-04

---

## Key Files

### 백엔드 (수정 대상)

| 파일 | 역할 | 현재 상태 |
|------|------|----------|
| `app-backend/app/features/ops/application/reports/service.py` | KPI 집계 서비스 | Placeholder (하드코딩 0) |
| `app-backend/app/features/ops/application/reports/__init__.py` | 모듈 export | `get_summary` 함수 export |
| `app-backend/app/api/v1/ops/reports.py` | HTTP 라우트 | `GET /summary` (파라미터 없음) |

### 프론트엔드 (수정 대상)

| 파일 | 역할 | 현재 상태 |
|------|------|----------|
| `app-frontend/src/features/ops/reports/types.ts` | OpsSummary 타입 | 4필드 |
| `app-frontend/src/features/ops/reports/api.ts` | API 호출 | 파라미터 없는 GET |
| `app-frontend/src/features/ops/reports/view.tsx` | KPI 카드 UI | 3개 인라인 `<dl>` 카드 |

### 참조 파일 (읽기 전용)

| 파일 | 참조 이유 |
|------|----------|
| `app-backend/app/models/user.py` | User 모델 (last_login_at, created_at, is_active, is_suspended) |
| `app-backend/app/models/roadmap.py` | Roadmap (created_at, deleted_at, created_by), RoadmapChatThread |
| `app-backend/app/models/roadmap_chat.py` | RoadmapChatThread (created_at, is_deleted) |
| `app-backend/app/models/growth_club.py` | GrowthClubPost (created_at) |
| `app-backend/app/models/team.py` | Team (created_at, deleted_at) |
| `app-backend/app/core/db.py` | `get_session()` AsyncSession 팩토리 |
| `app-backend/app/features/dashboard/application/dashboard_service.py` | 서비스 패턴 참조 |
| `app-backend/app/repositories/roadmap_repository.py` | 쿼리 패턴 참조 (func.count, select_from, where) |
| `app-frontend/src/features/ops/shared/use-ops-access-guard.ts` | `useOpsAccessGuard()` 패턴 |
| `app-frontend/src/lib/api-client.ts` | Axios 인스턴스 + JWT 인터셉터 |

---

## Decisions Log

| # | 결정 | 근거 |
|---|------|------|
| 1 | Phase 1만 구현 (내부 DB 쿼리 기반) | 사용자 선택. 외부 서비스(Sentry/PostHog)는 별도 태스크 |
| 2 | KPI 확장 8종 + 비율 + 총계 | 사용자 선택. 기본 3종만으론 운영 판단 불충분 |
| 3 | Slack 알림 미포함 | 사용자 선택. 웹 대시보드만으로 충분 |
| 4 | 서비스에서 직접 session 쿼리 (별도 Repository 미생성) | 집계 전용 쿼리이므로 재사용 가능성 낮음, 오버엔지니어링 방지 |
| 5 | `range` 파라미터로 7d/30d 선택 | 원래 기획 문서(`PLAN-ops-reports-dashboard.md`)에 명시 |
| 6 | 응답 필드명에서 `_7d`/`_30d` 접미사 제거 | range 파라미터로 구분하므로 접미사 불필요. 단, `dau_mau_ratio`는 항상 7d/30d 비교로 고정 |

---

## DB 모델 필드 상세

### User (user.py:20)
```python
class User(UserBase, table=True):
    id: Optional[int] = Field(primary_key=True)
    is_active: bool = True               # 활성 상태
    is_suspended: bool = Field(default=False, index=True)
    last_login_at: Optional[datetime]     # nullable, indexed — 로그인 기록 없으면 None
    created_at: datetime                  # naive UTC
```

### Roadmap (roadmap.py:9)
```python
class Roadmap(SQLModel, table=True):
    id: UUID
    team_id: UUID = Field(foreign_key="team.id", index=True)
    created_at: datetime                  # indexed
    deleted_at: datetime | None = None    # soft delete
    created_by: Optional[int] = Field(foreign_key="user.id")
```

### RoadmapChatThread (roadmap_chat.py:10)
```python
class RoadmapChatThread(SQLModel, table=True):
    id: UUID
    user_id: int = Field(foreign_key="user.id")
    is_deleted: bool                      # soft delete (boolean, NOT deleted_at)
    created_at: datetime
```

### GrowthClubPost (growth_club.py:127)
```python
class GrowthClubPost(GrowthClubPostBase, table=True):
    id: Optional[int]
    author_id: int = Field(foreign_key="user.id")
    created_at: datetime
    is_blinded: bool = Field(default=False)  # 블라인드 처리
```

### Team (team.py:8)
```python
class Team(SQLModel, table=True):
    id: UUID
    created_at: datetime                  # indexed
    deleted_at: datetime | None = None    # soft delete
```

---

## Query Patterns (기존 코드에서 확인)

### COUNT 패턴 (RoadmapRepository)
```python
from sqlalchemy import func, select

stmt = select(func.count()).select_from(Model).where(...)
result = await self.session.execute(stmt)
count = result.scalar_one()
```

### Soft Delete 필터
```python
.where(Roadmap.deleted_at.is_(None))     # Roadmap, Team
.where(RoadmapChatThread.is_deleted == False)  # Chat
```

### DateTime 비교
```python
now = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC
cutoff = now - timedelta(days=7)
.where(User.last_login_at >= cutoff)
```

### Session DI (API 라우트)
```python
from app.core.db import get_session
session: AsyncSession = Depends(get_session)
```

---

## Architecture Constraints

1. **단일 세션:** Read/Write 분리 없음 — `get_session()` 하나로 통일
2. **Naive UTC:** 모든 datetime은 `tzinfo=None`으로 저장 — 비교 시 `.replace(tzinfo=None)` 필요
3. **Admin 전용:** `/ops/*` 라우트는 `require_platform_admin` dependency로 보호
4. **Feature 모듈 격리:** 크로스 feature import 금지 — 서비스에서 직접 모델 import
5. **테스트 DB:** pytest는 SQLite in-memory — `pg_stat_*` 같은 PG 전용 쿼리 불가

---

## Related Documents

- `docs/planning/PLAN-ops-reports-dashboard.md` — 원래 기획 문서
- `docs/research/REPORT-ops-monitoring-strategy.md` — 모니터링 전략 보고서
- `CLAUDE.md` — 프로젝트 전체 컨텍스트
