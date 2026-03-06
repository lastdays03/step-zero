# REPORT: ActionKit 통계 추적 기능 구현 방안

**작성일:** 2026-03-06
**브랜치:** `feature/0-hardcode-cleanup`
**범위:** ActionKit 통계 대시보드 하드코딩 데이터 → 실제 데이터 전환

---

## 1. 현황 분석

### 1.1 하드코딩 현황 (stats-dashboard.tsx)

| # | 항목 | 하드코딩 값 | 백엔드 지원 |
|---|------|------------|------------|
| 1 | 총 다운로드 수 | 4,520건 (+15%) | 없음 |
| 2 | 총 활성 유저 (조회) | 1,284명 (+8%) | 없음 |
| 3 | 스타터 팩 다운로드율 | 42% (-3%) | 없음 |
| 4 | 인기 서류 TOP 5 | 5개 항목 (다운로드/찜/트렌드) | 없음 |
| 5 | 실시간 검색어 | 6개 키워드 | 없음 |
| 6 | 인사이트 텍스트 | 고정 문구 | 없음 |
| 7 | 기간 필터 (주/월/년) | UI만 존재, 데이터 미연동 | 없음 |

### 1.2 이미 존재하는 데이터

**백엔드 `GET /api/v1/ops/actionkit/summary` 응답:**

```python
ActionKitOpsSummary = {
    "total_items": int,        # 전체 항목 수
    "items_with_files": int,   # 파일 첨부 항목 수
    "inactive_items": int,     # 미공개 항목 수
    "total_related_laws": int, # 관련 법령 수
    "total_highlights": int,   # 하이라이트 수
}
```

**프론트엔드 동적 로직 (이미 구현):**
- 노후 항목 감지: `updated_at` 기준 365일 초과 필터링
- `fetchSummary()` 함수 정의됨 (api.ts) — 단, stats-dashboard.tsx에서 미사용

### 1.3 사용자 뷰 기존 기능

| 기능 | 구현 상태 | 추적 여부 |
|------|----------|----------|
| 파일 다운로드 (`/items/{id}/download`) | 구현됨 | 추적 안됨 |
| 파일 뷰어 (`/items/{id}/view`) | 구현됨 | 추적 안됨 |
| Zip 일괄 다운로드 (JSZip) | 구현됨 | 추적 안됨 |
| 북마크/찜 | localStorage 기반 | 서버에 없음 |
| 클라이언트 검색 | 메모리 필터링 | 로그 없음 |
| 최근 본 항목 | localStorage (최대 5개) | 서버에 없음 |
| 체크리스트 체크 상태 | localStorage | 서버에 없음 |

**핵심 문제:** 사용자 행동 데이터가 모두 클라이언트(localStorage)에만 있고, 서버로 전송되지 않음.

---

## 2. 구현 방안

### 2.1 아키텍처 개요

```
사용자 행동          프론트엔드              백엔드                  저장소
──────────          ──────────             ────────                ──────

다운로드 클릭  ──→  POST /track  ─────→  TrackingService  ────→  PostgreSQL
파일 뷰어 열기 ──→  POST /track  ─────→       │                  (actionkit_events)
검색어 입력    ──→  POST /track  ─────→       │
                    (debounce)               │
                                             ↓
통계 대시보드  ←──  GET /stats   ←─────  StatsService   ←────  집계 쿼리
                                         ├─ 기간별 집계
                                         ├─ 델타 계산
                                         └─ 인기 순위
```

### 2.2 Option A: PostgreSQL 단독 (권장)

이벤트 로그를 PostgreSQL 테이블에 직접 저장. 집계는 SQL 쿼리로 처리.

**장점:**
- 기존 인프라만 사용 (새 의존성 없음)
- 트랜잭션 보장, 데이터 유실 없음
- Alembic 마이그레이션으로 관리
- OpsReportsService 패턴 그대로 재사용

**단점:**
- 트래픽 급증 시 INSERT 부하 (현재 규모에서는 문제 없음)
- 실시간 검색어 순위 계산에 GROUP BY 쿼리 필요

**적합 시나리오:** 현재 사용자 규모 (수백~수천명), 이벤트 빈도 낮음

### 2.3 Option B: PostgreSQL + Redis 하이브리드

이벤트 카운터는 Redis INCR, 주기적으로 PostgreSQL에 flush.

**장점:**
- 실시간 카운터 성능 우수
- 검색어 ZSET으로 실시간 순위 가능

**단점:**
- Redis 장애 시 카운터 유실 가능
- flush 로직 추가 복잡도 (ARQ cron job 필요)
- 현재 규모 대비 오버엔지니어링

**적합 시나리오:** 사용자 수만명 이상, 초당 수백건 이벤트

**결론: Option A 권장.** 현재 규모에서 Redis 하이브리드는 불필요한 복잡도.

---

## 3. 상세 구현 설계

### 3.1 Phase 1: 이벤트 수집 모델 (백엔드)

#### 새 모델: `ActionKitEvent`

```python
# app/models/actionkit_event.py

class ActionKitEvent(SQLModel, table=True):
    __tablename__ = "actionkit_events"

    id: int = Field(primary_key=True)
    event_type: str = Field(index=True)
    # "view" | "download" | "bulk_download" | "search"

    item_id: int | None = Field(default=None, foreign_key="actionkit_items.id", index=True)
    user_id: int | None = Field(default=None, foreign_key="user.id", index=True)
    # user_id nullable: 비로그인 사용자도 추적

    search_query: str | None = Field(default=None)
    # event_type="search"일 때만 사용

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True,
    )

    __table_args__ = (
        Index("ix_actionkit_events_type_created", "event_type", "created_at"),
        Index("ix_actionkit_events_item_created", "item_id", "created_at"),
    )
```

**설계 근거:**
- 단일 테이블로 모든 이벤트 타입 통합 (view/download/search)
- `item_id` nullable → search 이벤트는 특정 아이템과 무관
- `user_id` nullable → 비로그인 다운로드도 추적 (현재 다운로드 API는 인증 불필요)
- 복합 인덱스로 기간별 집계 쿼리 최적화

#### 이벤트 타입 정의

```python
class ActionKitEventType:
    VIEW = "view"               # 파일 뷰어 열기
    DOWNLOAD = "download"       # 단일 파일 다운로드
    BULK_DOWNLOAD = "bulk_download"  # Zip 일괄 다운로드
    SEARCH = "search"           # 검색어 입력
```

### 3.2 Phase 2: 이벤트 수집 API (백엔드)

#### 트래킹 엔드포인트

```python
# app/api/v1/actionkit/tracking.py

@router.post("/track", status_code=204)
async def track_event(
    payload: ActionKitTrackRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    """ActionKit 사용자 이벤트 기록 (fire-and-forget)"""
    event = ActionKitEvent(
        event_type=payload.event_type,
        item_id=payload.item_id,
        user_id=current_user.id if current_user else None,
        search_query=payload.search_query,
    )
    session.add(event)
    await session.commit()

# Request schema
class ActionKitTrackRequest(BaseModel):
    event_type: Literal["view", "download", "bulk_download", "search"]
    item_id: int | None = None
    search_query: str | None = None
```

#### 기존 다운로드 엔드포인트에 추적 삽입

```python
# app/api/v1/actionkit/files.py — 기존 view/download 엔드포인트 수정

@router.get("/items/{item_id}/download")
async def download_item_file(item_id: int, ...):
    # 기존 로직 유지 + 이벤트 기록 추가
    event = ActionKitEvent(
        event_type="download", item_id=item_id, user_id=...
    )
    session.add(event)
    await session.commit()
    return file_response

@router.get("/items/{item_id}/view")
async def view_item_file(item_id: int, ...):
    # 기존 로직 유지 + 이벤트 기록 추가
    event = ActionKitEvent(
        event_type="view", item_id=item_id, user_id=...
    )
    session.add(event)
    await session.commit()
    return file_response
```

**양쪽 접근 (Belt-and-Suspenders):**
- 서버 사이드: download/view 엔드포인트에서 자동 기록 (누락 없음)
- 클라이언트 사이드: `POST /track`으로 search, bulk_download 등 서버가 감지 못하는 이벤트 기록

### 3.3 Phase 3: 통계 집계 서비스 (백엔드)

#### ActionKitStatsService

```python
# app/features/ops/application/actionkit/stats_service.py

class ActionKitStatsService:
    """OpsReportsService 패턴 기반"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stats(self, range_days: int = 30) -> ActionKitStatsResponse:
        now = datetime.now(timezone.utc)
        current_start = now - timedelta(days=range_days)
        previous_start = current_start - timedelta(days=range_days)

        return {
            "kpi": await self._get_kpi(current_start, previous_start, now),
            "popular_items": await self._get_popular_items(current_start, now, limit=5),
            "search_keywords": await self._get_search_keywords(current_start, now, limit=10),
            "range_days": range_days,
            "generated_at": now.isoformat(),
        }

    async def _get_kpi(self, current_start, previous_start, now) -> dict:
        """상단 3개 KPI 카드 데이터"""

        # 현재 기간 다운로드 수
        curr_downloads = await self._count_events(
            "download", current_start, now
        )
        prev_downloads = await self._count_events(
            "download", previous_start, current_start
        )

        # 현재 기간 고유 사용자 수 (조회)
        curr_users = await self._count_unique_users(current_start, now)
        prev_users = await self._count_unique_users(previous_start, current_start)

        # 스타터 팩 다운로드율 (= 다운로드 수 / 조회 수)
        curr_views = await self._count_events("view", current_start, now)
        prev_views = await self._count_events("view", previous_start, current_start)
        curr_rate = round(curr_downloads / curr_views * 100, 1) if curr_views else 0
        prev_rate = round(prev_downloads / prev_views * 100, 1) if prev_views else 0

        return {
            "total_downloads": curr_downloads,
            "total_downloads_delta": self._delta(curr_downloads, prev_downloads),
            "active_users": curr_users,
            "active_users_delta": self._delta(curr_users, prev_users),
            "download_rate": curr_rate,
            "download_rate_delta": self._delta(curr_rate, prev_rate),
        }

    async def _get_popular_items(self, start, end, limit=5) -> list[dict]:
        """인기 서류 TOP N"""
        stmt = (
            select(
                ActionKitEvent.item_id,
                ActionKitItem.name,
                func.count().filter(
                    ActionKitEvent.event_type == "download"
                ).label("downloads"),
                func.count().filter(
                    ActionKitEvent.event_type == "view"
                ).label("views"),
            )
            .join(ActionKitItem, ActionKitEvent.item_id == ActionKitItem.id)
            .where(
                ActionKitEvent.event_type.in_(["download", "view"]),
                ActionKitEvent.item_id.isnot(None),
                ActionKitEvent.created_at.between(start, end),
            )
            .group_by(ActionKitEvent.item_id, ActionKitItem.name)
            .order_by(func.count().desc())
            .limit(limit)
        )
        # ...

    async def _get_search_keywords(self, start, end, limit=10) -> list[dict]:
        """인기 검색어 TOP N"""
        stmt = (
            select(
                ActionKitEvent.search_query,
                func.count().label("volume"),
            )
            .where(
                ActionKitEvent.event_type == "search",
                ActionKitEvent.search_query.isnot(None),
                ActionKitEvent.created_at.between(start, end),
            )
            .group_by(ActionKitEvent.search_query)
            .order_by(func.count().desc())
            .limit(limit)
        )
        # ...

    @staticmethod
    def _delta(current: float, previous: float) -> float | None:
        """이전 기간 대비 변화율 (OpsReportsService 패턴)"""
        if previous == 0:
            return None
        return round((current - previous) / previous, 3)
```

#### 통계 API 엔드포인트

```python
# app/api/v1/ops/actionkit.py에 추가

@router.get("/stats")
async def get_actionkit_stats(
    range_days: int = Query(default=30, ge=7, le=365),
    session: AsyncSession = Depends(get_session),
    admin_user: User = Depends(require_platform_admin),
):
    service = ActionKitStatsService(session)
    return await service.get_stats(range_days)
```

#### 응답 스키마

```python
class ActionKitStatsResponse(BaseModel):
    kpi: ActionKitKPI
    popular_items: list[PopularItem]
    search_keywords: list[SearchKeyword]
    range_days: int
    generated_at: str

class ActionKitKPI(BaseModel):
    total_downloads: int
    total_downloads_delta: float | None   # e.g. 0.15 = +15%
    active_users: int
    active_users_delta: float | None
    download_rate: float                  # e.g. 42.0 (%)
    download_rate_delta: float | None

class PopularItem(BaseModel):
    item_id: int
    name: str
    downloads: int
    views: int
    trend: float | None   # 이전 기간 대비 변화율

class SearchKeyword(BaseModel):
    keyword: str
    rank: int
    volume: int
```

### 3.4 Phase 4: 프론트엔드 연동

#### API 함수 추가 (api.ts)

```typescript
// app-frontend/src/features/ops/actionkit/api.ts

export const fetchStats = async (rangeDays: number = 30) => {
    const { data } = await apiClient.get('/ops/actionkit/stats', {
        params: { range_days: rangeDays },
    });
    return data;
};
```

#### 사용자 뷰에 트래킹 삽입 (ActionKitLibraryView.tsx)

```typescript
// 검색어 트래킹 (debounce 적용)
const trackSearch = useMemo(
    () => debounce((query: string) => {
        if (query.length >= 2) {
            apiClient.post('/actionkits/track', {
                event_type: 'search',
                search_query: query,
            }).catch(() => {}); // fire-and-forget
        }
    }, 1000),
    []
);

// Zip 다운로드 트래킹
const handleBulkDownload = async () => {
    // 기존 로직 + 트래킹
    for (const item of bookmarkedItems) {
        apiClient.post('/actionkits/track', {
            event_type: 'bulk_download',
            item_id: item.id,
        }).catch(() => {});
    }
};
```

#### stats-dashboard.tsx 교체

```typescript
// props 변경
interface OpsActionKitStatsDashboardProps {
    items: StatsItem[];
    stats: ActionKitStatsResponse | null;
}

// 기간 필터 → 실제 API 호출 연동
const [timeRange, setTimeRange] = useState<number>(30);
useEffect(() => {
    fetchStats(timeRange).then(setStats);
}, [timeRange]);

// 기간 필터 매핑
// "최근 1주일" → range_days=7
// "최근 1개월" → range_days=30
// "올해"       → range_days=365
```

---

## 4. 데이터베이스 마이그레이션

### 4.1 새 마이그레이션 파일

```python
# alembic/versions/018_actionkit_events.py

def upgrade() -> None:
    op.create_table(
        "actionkit_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(20), nullable=False, index=True),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("actionkit_items.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("search_query", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
    )
    op.create_index(
        "ix_actionkit_events_type_created",
        "actionkit_events",
        ["event_type", "created_at"],
    )
    op.create_index(
        "ix_actionkit_events_item_created",
        "actionkit_events",
        ["item_id", "created_at"],
    )

def downgrade() -> None:
    op.drop_table("actionkit_events")
```

### 4.2 인덱스 전략

| 인덱스 | 컬럼 | 용도 |
|--------|------|------|
| `ix_event_type` | `event_type` | 이벤트 타입별 필터 |
| `ix_created_at` | `created_at` | 기간별 범위 쿼리 |
| `ix_type_created` | `(event_type, created_at)` | KPI 집계 (타입 + 기간) |
| `ix_item_created` | `(item_id, created_at)` | 아이템별 인기 순위 |
| `ix_user_id` | `user_id` | 고유 사용자 수 집계 |

### 4.3 데이터 보존 정책

이벤트 로그는 무한 증가하므로 보존 기간 설정 필요:

```python
# ARQ cron job으로 90일 이전 데이터 삭제
async def cleanup_old_actionkit_events(ctx):
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    await session.execute(
        delete(ActionKitEvent).where(ActionKitEvent.created_at < cutoff)
    )
```

---

## 5. 인사이트 텍스트 처리

### 5.1 현재 하드코딩

> "주주간계약서" 및 "투자계약" 검색량이 저번달 대비 24% 급증했습니다.

### 5.2 구현 방안

**Option A: 규칙 기반 자동 생성 (권장)**

```python
async def generate_insight(self, stats: ActionKitStatsResponse) -> str:
    """통계 데이터에서 주목할 만한 변화를 텍스트로 생성"""
    insights = []

    # 가장 급성장한 아이템
    top_trending = max(stats.popular_items, key=lambda x: x.trend or 0)
    if top_trending.trend and top_trending.trend > 0.1:
        insights.append(
            f'"{top_trending.name}" 다운로드가 전월 대비 '
            f'{int(top_trending.trend * 100)}% 증가했습니다.'
        )

    # 가장 많이 검색된 키워드
    if stats.search_keywords:
        top_kw = stats.search_keywords[0]
        insights.append(
            f'가장 많이 검색된 키워드는 "{top_kw.keyword}" '
            f'({top_kw.volume}회)입니다.'
        )

    return " ".join(insights) if insights else None
```

**Option B: LLM 기반 (향후 확장)**

통계 데이터를 LLM에 넘겨 자연어 인사이트 생성. 현재는 과도한 복잡도.

---

## 6. 구현 페이즈 및 작업량

### Phase 1: 이벤트 수집 인프라 (BE)

| 작업 | 파일 | 예상 규모 |
|------|------|----------|
| ActionKitEvent 모델 생성 | `app/models/actionkit_event.py` | 신규 ~40줄 |
| `__init__.py`에 import 추가 | `app/models/__init__.py` | 1줄 |
| Alembic 마이그레이션 | `alembic/versions/018_*.py` | 신규 ~30줄 |
| `alembic/env.py`에 import | `alembic/env.py` | 1줄 |
| 트래킹 API 엔드포인트 | `app/api/v1/actionkit/tracking.py` | 신규 ~30줄 |
| 라우터 등록 | `app/api/v1/actionkit/router.py` | 2줄 |
| 기존 download/view에 추적 삽입 | `app/api/v1/actionkit/files.py` | ~10줄 수정 |

### Phase 2: 통계 집계 서비스 (BE)

| 작업 | 파일 | 예상 규모 |
|------|------|----------|
| ActionKitStatsService | `app/features/ops/application/actionkit/stats_service.py` | 신규 ~150줄 |
| 응답 스키마 정의 | `app/api/v1/ops/schemas.py` | ~40줄 추가 |
| Stats API 엔드포인트 | `app/api/v1/ops/actionkit.py` | ~15줄 추가 |
| 인사이트 생성 로직 | stats_service.py 내 | ~30줄 |
| 데이터 정리 cron job | `app/workers/roadmap_worker.py` | ~10줄 |

### Phase 3: 프론트엔드 연동

| 작업 | 파일 | 예상 규모 |
|------|------|----------|
| fetchStats API 함수 | `ops/actionkit/api.ts` | ~10줄 |
| 트래킹 호출 삽입 | `actionkit/components/ActionKitLibraryView.tsx` | ~20줄 |
| stats-dashboard.tsx 전면 교체 | `ops/actionkit/components/stats-dashboard.tsx` | ~200줄 (기존과 비슷) |
| view.tsx에서 stats 연동 | `ops/actionkit/view.tsx` | ~15줄 수정 |
| TypeScript 타입 정의 | `ops/actionkit/api.ts` | ~30줄 |

### Phase 4: 테스트

| 작업 | 파일 | 예상 규모 |
|------|------|----------|
| 이벤트 기록 API 테스트 | `tests/api/test_actionkit_tracking.py` | 신규 ~80줄 |
| 통계 집계 서비스 테스트 | `tests/services/test_actionkit_stats.py` | 신규 ~120줄 |
| 마이그레이션 검증 | `alembic check` | - |

### 총 작업량 요약

| Phase | 신규 파일 | 수정 파일 | 코드량 |
|-------|----------|----------|--------|
| 1. 이벤트 수집 | 3개 | 4개 | ~110줄 |
| 2. 집계 서비스 | 1개 | 2개 | ~235줄 |
| 3. FE 연동 | 0개 | 4개 | ~275줄 |
| 4. 테스트 | 2개 | 0개 | ~200줄 |
| **합계** | **6개** | **10개** | **~820줄** |

---

## 7. 데이터 수집 시작 시점 문제

통계 대시보드는 이벤트 데이터가 쌓여야 의미가 있음. 구현 직후에는 데이터가 0건.

### 해결 방안

1. **빈 상태 UI**: "아직 충분한 데이터가 수집되지 않았습니다" 표시
2. **기간 필터 최소값**: `range_days >= 7` — 최소 1주일 데이터 필요
3. **점진 전환**: Phase 1~2 배포 후 1~2주 데이터 수집 → Phase 3(FE) 배포

---

## 8. 상단 카드 vs 통계 탭 중복 문제

현재 view.tsx에 상단 summary 카드(5개)와 stats 탭이 공존. 실데이터 전환 시:

### 권장 구조

```
┌─────────────────────────────────────────────┐
│ 상단 카드 (항상 표시)                          │
│ → summary API 데이터: 전체항목/파일/미공개/법령/하이라이트 │
│ → 콘텐츠 현황 (정적 집계)                       │
├─────────────────────────────────────────────┤
│ [액션 키트] [법령 가이드] [이용 통계]             │
├─────────────────────────────────────────────┤
│ "이용 통계" 탭 선택 시:                         │
│ → stats API 데이터: KPI/인기순위/검색어/인사이트    │
│ → 사용자 행동 통계 (동적, 기간별)                 │
└─────────────────────────────────────────────┘
```

- **상단 카드**: 콘텐츠 관리 현황 (기존 summary API) — 관리자가 항상 봐야 할 정보
- **통계 탭**: 사용자 행동 분석 (새 stats API) — 별도 탭에서 상세 분석

이렇게 하면 **역할이 다르므로 중복이 아님**.

---

## 9. 리스크 및 고려사항

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 이벤트 테이블 무한 증가 | 디스크/쿼리 성능 | 90일 보존 cron + 파티셔닝 고려 |
| 비로그인 사용자 추적 | user_id=NULL 다수 | 집계에 영향 없음 (COUNT 기반) |
| 봇/크롤러 트래픽 | 통계 왜곡 | User-Agent 필터 또는 rate limit |
| 검색 debounce 누락 | 과다 이벤트 | FE에서 1초 debounce 필수 |
| 기존 다운로드 API 수정 | 기능 영향 | 추적 실패해도 다운로드는 정상 진행 (try/except) |

---

## 10. 참고 파일

### 백엔드 모델/서비스
- `app-backend/app/models/actionkit.py` — ActionKit 모델
- `app-backend/app/models/file.py` — File 모델
- `app-backend/app/features/ops/application/actionkit/service.py` — summary 서비스
- `app-backend/app/features/ops/application/reports/service.py` — 리포트 서비스 (패턴 참조)
- `app-backend/app/features/ops/application/files/service.py` — 파일 통계 (패턴 참조)

### 백엔드 API
- `app-backend/app/api/v1/ops/actionkit.py` — Ops API
- `app-backend/app/api/v1/actionkit/files.py` — 사용자 다운로드 API
- `app-backend/app/api/v1/actionkit/router.py` — 라우터 등록

### 프론트엔드
- `app-frontend/src/features/ops/actionkit/components/stats-dashboard.tsx` — 통계 대시보드
- `app-frontend/src/features/ops/actionkit/view.tsx` — Ops 뷰
- `app-frontend/src/features/ops/actionkit/api.ts` — API 함수
- `app-frontend/src/features/actionkit/components/ActionKitLibraryView.tsx` — 사용자 뷰

### 마이그레이션
- `app-backend/alembic/versions/` — 기존 017번까지 완료
