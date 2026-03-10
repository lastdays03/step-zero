# REPORT: ActionKit 통계 추적 기능 구현 방안

**작성일:** 2026-03-06
**최종 보완일:** 2026-03-10
**범위:** ActionKit 통계 대시보드 하드코딩 데이터 → 실제 데이터 전환

---

## 1. ActionKit 시스템 전체 아키텍처

### 1.1 데이터 모델 (6개 테이블)

```
actionkit_categories (domain: laws|kits)
  └─ actionkit_items
       ├─ actionkit_item_highlights (핵심 포인트)
       ├─ actionkit_checklists (체크리스트)
       ├─ actionkit_related_laws (관련 법령)
       └─ files (통합 File 테이블, owner_type="actionkit_item")
            └─ 멀티버전 지원 (version, is_current)
```

| 테이블 | 주요 필드 | 관계 |
|--------|----------|------|
| `actionkit_categories` | id, domain(laws\|kits), slug, title, sort_order, is_active | 1:N → items |
| `actionkit_items` | id, domain, category_id, name, summary, tag, ext, size_label, file_type, dday, sort_order, is_active | N:1 → category, 1:N → highlights/laws/checklists |
| `actionkit_item_highlights` | id, item_id, content, sort_order | N:1 → item (cascade delete) |
| `actionkit_checklists` | id, item_id, content, sort_order | N:1 → item (cascade delete) |
| `actionkit_related_laws` | id, item_id, law_name, law_summary, sort_order | N:1 → item (cascade delete) |
| `files` | id, owner_type, owner_id, category, object_key, original_filename, mime_type, size_bytes, version, is_current, metadata_extra | 범용 파일 테이블 |

### 1.2 이중 도메인 구조

ActionKit은 **laws**(법령 가이드)와 **kits**(액션 키트) 두 도메인을 동일한 테이블 구조로 관리한다. `domain` 필드로 구분하며, 프론트엔드에서 별도 탭/뷰로 노출.

- **Laws**: 법령별 챕터 구조 → `LawGuideView` 컴포넌트
- **Kits**: 카테고리별 문서 라이브러리 → `ActionKitLibraryView` 컴포넌트
- **상호 연결**: 법령 페이지에서 "관련 액션 키트" 제안, 키트 페이지에서 "관련 법령" 표시

### 1.3 백엔드 API 전체 맵

#### 사용자 공개 API (`/api/v1/actionkits/`)

| 엔드포인트 | 메서드 | 인증 | 설명 |
|-----------|--------|------|------|
| `/actionkits/laws` | GET | 불필요 | 전체 법령 챕터 목록 |
| `/actionkits/kits` | GET | 불필요 | 전체 키트 카테고리+아이템 |
| `/actionkits/laws/{chapter_id}` | GET | 불필요 | 특정 법령 챕터 상세 |
| `/actionkits/kits/{category_id}` | GET | 불필요 | 특정 키트 카테고리 상세 |
| `/actionkits/items/{item_id}` | GET | 불필요 | 아이템→뷰어 리다이렉트 (307) |
| `/actionkits/items/{item_id}/view` | GET | 불필요 | 파일 뷰어 (MD→HTML, PDF inline) |
| `/actionkits/items/{item_id}/download` | GET | 불필요 | 파일 다운로드 |
| `/actionkits/items/{item_id}/files` | POST | **admin** | 파일 업로드 |

**핵심 발견: view/download API는 인증 불필요** → 비로그인 사용자 행동 추적 시 user_id가 NULL이 됨

#### 관리자 API (`/api/v1/ops/actionkit/`)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/ops/actionkit/summary` | GET | 콘텐츠 현황 요약 (5개 지표) |
| `/ops/actionkit/categories` | GET/POST | 카테고리 CRUD |
| `/ops/actionkit/categories/{id}` | PATCH/DELETE | 카테고리 수정/삭제 |
| `/ops/actionkit/categories/{id}/items` | GET | 카테고리별 아이템 목록 |
| `/ops/actionkit/items` | POST | 아이템 생성 |
| `/ops/actionkit/items/{id}` | GET/PATCH/DELETE | 아이템 CRUD |
| `/ops/actionkit/items/reorder` | PATCH | 드래그 앤 드롭 정렬 |
| `/ops/actionkit/items/{id}/files` | POST | 파일 업로드 (버전 관리) |
| `/ops/actionkit/items/{id}/status` | PATCH | 활성/비활성 토글 |
| `/ops/actionkit/items/{id}/related-laws` | POST | 관련 법령 추가 |
| `/ops/actionkit/related-laws/{id}` | DELETE | 관련 법령 삭제 |
| `/ops/actionkit/items/{id}/highlights` | POST | 하이라이트 추가 |
| `/ops/actionkit/highlights/{id}` | DELETE | 하이라이트 삭제 |
| `/ops/actionkit/items/{id}/checklists` | POST | 체크리스트 추가 |
| `/ops/actionkit/checklists/{id}` | DELETE | 체크리스트 삭제 |

### 1.4 로드맵 생성 파이프라인 연동

ActionKit은 로드맵 생성 시 핵심 데이터 소스로 사용된다:

```
사용자 업종 입력
    ↓
ActionKitMatcher.match()
    ├─ 벡터 유사도 검색 (RagService → PGVector)
    ├─ 관계형 DB JOIN (item + highlights + laws + files)
    ├─ 카테고리→단계(phase) 매핑
    └─ 점수 기반 필터링 (min 0.2)
    ↓
MatchedActionKit[] (item + highlights + related_laws + files + phase_group)
    ↓
LLMPersonalizer.personalize()
    ├─ ActionKit 팩트 데이터 + 사용자 정보 결합
    ├─ LLM이 개인화된 로드맵 단계 생성
    └─ hallucination repair (ActionKit 원본 참조 보존)
    ↓
개인화된 로드맵 (각 단계에 ActionKit 아이템 연결)
```

**통계적 의미:** ActionKit 아이템의 **로드맵 매칭 빈도**도 향후 추적 가능한 유의미한 지표

### 1.5 파일 버전 관리 시스템

```
파일 업로드 → get_next_version() → 기존 is_current 전부 False
→ 새 File(version=n, is_current=True) 생성
→ item.ext/file_type/size_label 자동 갱신
→ 프론트엔드 "v{n} (최신)" 표시
```

- R2 모드: S3 호환 스토리지에 `actionkit/{object_key}` 경로로 저장
- Local 모드: `STORAGE_LOCAL_ROOT/actionkit/` 경로
- Markdown 뷰어: `marked.js`로 클라이언트 사이드 HTML 렌더링 + 인쇄/PDF 저장 툴바

---

## 2. 현황 분석 (보완)

### 2.1 통계 대시보드 하드코딩 현황 (stats-dashboard.tsx)

#### 하드코딩된 상수

```typescript
// 1. 인기 서류 TOP 5 — 완전 하드코딩
const POPULAR_DOCS = [
    { title: "근로계약서 (정규직)", downloads: 1250, saves: 430, trend: "+12%" },
    { title: "상가임대차계약서", downloads: 890, saves: 310, trend: "+5%" },
    { title: "주주간계약서", downloads: 650, saves: 490, trend: "+24%" },
    { title: "비밀유지계약서 (NDA)", downloads: 580, saves: 210, trend: "-2%" },
    { title: "취업규칙 샘플", downloads: 420, saves: 180, trend: "+8%" },
];

// 2. 실시간 검색어 — 완전 하드코딩
const SEARCH_KEYWORDS = ["근로계약서", "스톡옵션", "동업계약", "투자계약", "개인정보", "사직서"];
```

#### 하드코딩된 KPI 카드 (JSX 인라인)

| # | 항목 | 하드코딩 값 | 변화율 | 렌더링 방식 |
|---|------|-----------|--------|-----------|
| 1 | 총 다운로드 수 | `4,520건` | `+15%` (초록 TrendingUp) | JSX 인라인 텍스트 |
| 2 | 총 활성 유저 (조회) | `1,284명` | `+8%` (초록 TrendingUp) | JSX 인라인 텍스트 |
| 3 | 스타터 팩 다운로드율 | `42%` | `-3%` (빨강 TrendingDown) | JSX 인라인 텍스트 |

#### 하드코딩된 인사이트

> "주주간계약서" 및 "투자계약" 검색량이 저번달 대비 24% 급증했습니다. 관련 스타터 팩을 상단에 고정하는 것을 권장합니다.

#### 기간 필터 (UI만 존재)

```typescript
const [timeRange, setTimeRange] = useState<"week" | "month" | "year">("month");
// 버튼 3개: "최근 1주일" | "최근 1개월" | "올해"
// 상태 변경만 되고 어떤 API 호출이나 데이터 변경도 없음
```

#### 유일한 동적 로직: 노후 항목 감지

```typescript
// items prop으로 전달받은 아이템의 updated_at 기준 365일 초과 필터링
// → 빨간 경고 배너로 표시 (최대 3개 + "더 보기")
// 이 로직은 실제 데이터에 기반하므로 하드코딩이 아님
```

### 2.2 기존 Summary API 상세

**소스:** `app/features/ops/application/actionkit/service.py` → `get_summary()`

```python
async def get_summary(session: AsyncSession) -> ActionKitOpsSummary:
    # 전체 아이템을 메모리에 로드 후 Python에서 집계
    result = await session.execute(select(ActionKitItem))
    all_items = list(result.scalars().all())
    total = len(all_items)
    inactive = sum(1 for i in all_items if not i.is_active)

    # File 테이블에서 actionkit_item owner를 가진 고유 owner_id 수
    file_stmt = select(File.owner_id).where(
        File.owner_type == "actionkit_item"
    ).distinct()
    ...
```

**응답 구조:**
```json
{
    "total_items": 42,         // 전체 ActionKit 아이템 수
    "items_with_files": 38,    // 파일이 1개 이상 첨부된 아이템 수
    "inactive_items": 3,       // is_active=False 아이템 수
    "total_related_laws": 65,  // 전체 관련 법령 레코드 수
    "total_highlights": 120    // 전체 하이라이트 레코드 수
}
```

**프론트엔드 사용:** `view.tsx` 상단 5개 카드에 표시 (항상 노출, 탭 무관)
- 전체 항목 (Package 아이콘, 파란색)
- 파일 첨부 (Paperclip 아이콘, 초록색)
- 미공개 (EyeOff 아이콘, 주황색)
- 관련 법령 (Scale 아이콘, 보라색)
- 하이라이트 (Highlighter 아이콘, 노란색)

### 2.3 사용자 뷰 기능 상세 분석

#### localStorage 키 전수 목록

| 키 | 저장 형식 | 용도 | 추적 가능성 |
|---|---------|------|-----------|
| `actionkit_bookmarks` | `Record<string, ActionKitItem>` (JSON) | 서랍장 찜 목록 | 서버 미전송 |
| `actionkit_checklists` | `Record<string, boolean>` (JSON) | 체크리스트 체크 상태 (`{kitId}_{checkItem}`: true) | 서버 미전송 |
| `actionkit_recents` | `ActionKitItem[]` (JSON, 최대 5개) | 최근 본 항목 | 서버 미전송 |
| `actionkit_onboarding_shown` | `"true"` | 온보딩 가이드 표시 여부 | 추적 불필요 |

#### 사용자 행동별 추적 현황

| 행동 | 트리거 | 현재 추적 | 추적 삽입 위치 |
|------|--------|----------|-------------|
| 단일 파일 다운로드 | `GET /items/{id}/download` 호출 | **없음** | 서버: `files.py:download_item_current_file()` |
| 파일 뷰어 열기 | `GET /items/{id}/view` 호출 | **없음** | 서버: `files.py:view_item_current_file()` |
| ZIP 일괄 다운로드 | `handleBulkDownload()` → JSZip 클라이언트 생성 | **없음** | 클라이언트: `ActionKitLibraryView.tsx:178` |
| 검색어 입력 | `searchQuery` state 변경 → 메모리 필터링 | **없음** | 클라이언트: `ActionKitLibraryView.tsx:95` (debounce 필요) |
| 북마크 추가/제거 | `toggleBookmark()` → localStorage 저장 | **localStorage만** | 클라이언트: `ActionKitLibraryView.tsx:150` |
| 체크리스트 체크 | `handleChecklistToggle()` → localStorage | **localStorage만** | 클라이언트: `ActionKitLibraryView.tsx:218` |
| 최근 본 항목 | `addToRecent()` → localStorage (최대 5개 유지) | **localStorage만** | 클라이언트: `ActionKitLibraryView.tsx:141` |
| 스타터 팩 선택 | `setActiveStarterPack()` → 키워드 필터 | **없음** | 클라이언트: `ActionKitLibraryView.tsx:460` |
| 상세 모달 열기 | `setDetailItem()` or `setPreviewKit()` | **없음** | 클라이언트: `ActionKitLibraryView.tsx:98-99` |
| 법령→키트 탐색 | `onNavigateToLaw()` → 탭 전환 + 검색 | **없음** | 클라이언트: `ActionKitContainer.tsx:14` |

#### ZIP 일괄 다운로드 상세 흐름

```typescript
handleBulkDownload() {
    const zip = new JSZip();
    for (const item of bookmarkedItems) {
        // 각 아이템에 대해 개별 GET /download 호출
        const res = await apiClient.get(`/actionkits/items/${itemId}/download`,
            { responseType: 'blob' });
        zip.file(filename, blob);
    }
    const content = await zip.generateAsync({ type: 'blob' });
    saveAs(content, '나만의_액션키트_보관함.zip');
}
```

**주의:** 서버 측 추적을 download 엔드포인트에 넣으면 ZIP 내 개별 파일 다운로드도 자동 추적됨. 하지만 "ZIP 일괄 다운로드" 행위 자체는 별도 클라이언트 추적 필요.

#### 스타터 팩 구성

```typescript
const STARTER_PACKS = [
    { id: "hire", title: "직원 채용 필수 팩", keywords: ["근로계약서", "취업규칙", "비밀유지"] },
    { id: "office", title: "사무실 계약 팩", keywords: ["임대차", "화재안전", "건축물"] },
    { id: "invest", title: "투자 유치 준비 팩", keywords: ["주주", "정관", "이사회"] },
];
```

스타터 팩 선택 시 해당 키워드로 아이템을 필터링하여 관련 문서 묶음을 보여준다. 스타터 팩 다운로드율(42%)은 하드코딩이지만, 이 기능과 연계된 실제 추적이 가능하다.

### 2.4 Ops 관리 UI 현황

**view.tsx** 구조:

```
┌────────────────────────────────────────────────┐
│ 헤더: "액션 키트 관리 (Admin)" + "새 항목 등록" 버튼  │
├────────────────────────────────────────────────┤
│ Summary 카드 5개 (GET /ops/actionkit/summary)    │
│ [전체항목] [파일첨부] [미공개] [관련법령] [하이라이트]  │
├────────────────────────────────────────────────┤
│ 도메인 탭: [액션 키트] [법령 가이드] [통계 대시보드]  │
├────────────────────────────────────────────────┤
│ 키트/법령 선택 시:                                │
│  ├─ 카테고리 서브탭 (더블클릭 수정, + 추가)          │
│  ├─ 검색 입력                                    │
│  └─ 아이템 테이블 (DnD 재정렬)                     │
│      [상태][제목][종류/태그][첨부버전][순서][관리]     │
├────────────────────────────────────────────────┤
│ 통계 대시보드 선택 시:                              │
│  └─ OpsActionKitStatsDashboard (현재 하드코딩)     │
└────────────────────────────────────────────────┘
```

**stats-dashboard.tsx 전달 방식:**
```typescript
// view.tsx에서 stats 탭 선택 시:
{activeDomain === "stats" ? (
    <OpsActionKitStatsDashboard items={items} />  // 현재 카테고리의 items만 전달
) : ( ... )}
```

**문제:** `items` prop에는 **현재 선택된 카테고리의 아이템만** 전달됨. 통계 대시보드에는 **전체 아이템**이 필요하므로, 탭 전환 시 items 소스를 전체로 바꿔야 함. 현재 노후 항목 감지가 일부 카테고리 아이템에서만 동작하는 버그가 있다.

### 2.5 OpsReportsService 패턴 (참조용)

기존 `app/features/ops/application/reports/service.py`의 delta 계산 패턴:

```python
class OpsReportsService:
    async def get_summary(self, range_days: int = 7) -> dict:
        now = _utcnow()
        since = _shift(now, -range_days)
        prev_since = _shift(now, -range_days * 2)
        prev_until = since

        # 현재 기간 vs 이전 기간 비교
        active_users = await self._count_active_users(since)
        prev_active = await self._count_active_users(prev_since, prev_until)

        return {
            "active_users": active_users,
            "active_users_delta": _delta(active_users, prev_active),
            ...
        }

def _delta(current: int | float, previous: int | float) -> float | None:
    if previous == 0:
        return None
    return round((current - previous) / previous, 3)
```

이 패턴을 ActionKitStatsService에서 그대로 재사용한다.

---

## 3. 구현 방안

### 3.1 아키텍처 개요

```
사용자 행동          프론트엔드              백엔드                  저장소
──────────          ──────────             ────────                ──────

다운로드 클릭  ──→  GET /download  ────→  files.py + 추적 ──────→  PostgreSQL
파일 뷰어 열기 ──→  GET /view     ────→  files.py + 추적 ──────→  (actionkit_events)
ZIP 다운로드   ──→  POST /track   ────→  tracking.py     ──────→
검색어 입력    ──→  POST /track   ────→  (debounce 1초)  ──────→
북마크 추가    ──→  POST /track   ────→                  ──────→
                                                ↓
통계 대시보드  ←──  GET /stats    ←────  StatsService    ←──────  집계 쿼리
                                         ├─ 기간별 집계
                                         ├─ 델타 계산
                                         ├─ 인기 순위
                                         └─ 인사이트 생성
```

### 3.2 Option A: PostgreSQL 단독 (권장)

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

### 3.3 Option B: PostgreSQL + Redis 하이브리드

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

## 4. 상세 구현 설계

### 4.1 Phase 1: 이벤트 수집 모델 (백엔드)

#### 새 모델: `ActionKitEvent`

```python
# app/models/actionkit_event.py
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel
from sqlalchemy import Index

class ActionKitEvent(SQLModel, table=True):
    __tablename__ = "actionkit_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str = Field(index=True)
    # "view" | "download" | "bulk_download" | "search" | "bookmark"

    item_id: Optional[int] = Field(
        default=None,
        foreign_key="actionkit_items.id",
        index=True,
    )
    user_id: Optional[int] = Field(
        default=None,
        foreign_key="user.id",
        index=True,
    )
    # user_id nullable: 비로그인 사용자도 추적 (view/download API 인증 불필요)

    search_query: Optional[str] = Field(default=None, max_length=200)
    # event_type="search"일 때만 사용

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        index=True,
    )

    __table_args__ = (
        Index("ix_actionkit_events_type_created", "event_type", "created_at"),
        Index("ix_actionkit_events_item_created", "item_id", "created_at"),
    )
```

**설계 근거:**
- 단일 테이블로 모든 이벤트 타입 통합 (view/download/search/bookmark)
- `item_id` nullable → search 이벤트는 특정 아이템과 무관
- `user_id` nullable → 비로그인 다운로드도 추적 (현재 view/download API는 인증 불필요)
- 복합 인덱스로 기간별 집계 쿼리 최적화
- `datetime.now(timezone.utc).replace(tzinfo=None)` — 기존 ActionKit 모델 패턴 준수

#### 이벤트 타입 정의 (확장)

```python
class ActionKitEventType:
    VIEW = "view"                   # 파일 뷰어 열기
    DOWNLOAD = "download"           # 단일 파일 다운로드
    BULK_DOWNLOAD = "bulk_download" # Zip 일괄 다운로드
    SEARCH = "search"               # 검색어 입력
    BOOKMARK = "bookmark"           # 서랍장 찜 추가
    DETAIL_VIEW = "detail_view"     # 상세 모달 열기
```

**기존 보고서 대비 추가:** `bookmark`, `detail_view` 이벤트 타입. 사용자 관심도 측정에 유용.

### 4.2 Phase 2: 이벤트 수집 API (백엔드)

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
    event_type: Literal["view", "download", "bulk_download", "search", "bookmark", "detail_view"]
    item_id: int | None = None
    search_query: str | None = None
```

#### 기존 files.py 엔드포인트에 추적 삽입

**현재 코드 (수정 전):**
```python
@router.get("/items/{item_id}/download")
async def download_item_current_file(
    item_id: int = Path(description="다운로드할 아이템 ID"),
    session: AsyncSession = Depends(get_session),
):
    storage_key, current_file = await _resolve_file(item_id, session)
    # ... 파일 반환 로직
```

**수정 후:**
```python
@router.get("/items/{item_id}/download")
async def download_item_current_file(
    item_id: int = Path(description="다운로드할 아이템 ID"),
    session: AsyncSession = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
):
    storage_key, current_file = await _resolve_file(item_id, session)

    # 추적 (실패해도 다운로드는 정상 진행)
    try:
        event = ActionKitEvent(
            event_type="download",
            item_id=item_id,
            user_id=current_user.id if current_user else None,
        )
        session.add(event)
        await session.commit()
    except Exception:
        logger.warning("Failed to track download event for item %d", item_id)

    # ... 기존 파일 반환 로직
```

**view 엔드포인트도 동일 패턴으로 수정.**

**양쪽 접근 (Belt-and-Suspenders):**
- 서버 사이드: download/view 엔드포인트에서 자동 기록 (누락 없음)
- 클라이언트 사이드: `POST /track`으로 search, bulk_download, bookmark 등 서버가 감지 못하는 이벤트 기록

**주의: `get_optional_current_user` 의존성 추가 필요.** 현재 view/download 엔드포인트에는 인증 의존성이 없으므로, 인증 실패 시 None을 반환하는 optional 버전이 필요하다. 이미 프로젝트에 이 패턴이 존재하는지 확인 필요.

### 4.3 Phase 3: 통계 집계 서비스 (백엔드)

#### ActionKitStatsService

```python
# app/features/ops/application/actionkit/stats_service.py

class ActionKitStatsService:
    """OpsReportsService 패턴 기반"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stats(self, range_days: int = 30) -> ActionKitStatsResponse:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        current_start = now - timedelta(days=range_days)
        previous_start = current_start - timedelta(days=range_days)

        return {
            "kpi": await self._get_kpi(current_start, previous_start, now),
            "popular_items": await self._get_popular_items(current_start, now, limit=5),
            "search_keywords": await self._get_search_keywords(current_start, now, limit=10),
            "insight": await self._generate_insight(current_start, previous_start, now),
            "range_days": range_days,
            "generated_at": now.isoformat(),
        }

    async def _get_kpi(self, current_start, previous_start, now) -> dict:
        """상단 3개 KPI 카드 데이터"""

        # 현재/이전 기간 다운로드 수 (download + bulk_download)
        curr_downloads = await self._count_events(
            ["download", "bulk_download"], current_start, now
        )
        prev_downloads = await self._count_events(
            ["download", "bulk_download"], previous_start, current_start
        )

        # 현재/이전 기간 고유 사용자 수 (user_id IS NOT NULL인 고유 수)
        curr_users = await self._count_unique_users(current_start, now)
        prev_users = await self._count_unique_users(previous_start, current_start)

        # 다운로드율 (= 다운로드 수 / 조회 수 × 100)
        curr_views = await self._count_events(["view"], current_start, now)
        prev_views = await self._count_events(["view"], previous_start, current_start)
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
        """인기 서류 TOP N — download + view 이벤트 기반"""
        stmt = (
            select(
                ActionKitEvent.item_id,
                ActionKitItem.name,
                func.count().filter(
                    ActionKitEvent.event_type.in_(["download", "bulk_download"])
                ).label("downloads"),
                func.count().filter(
                    ActionKitEvent.event_type == "view"
                ).label("views"),
            )
            .join(ActionKitItem, ActionKitEvent.item_id == ActionKitItem.id)
            .where(
                ActionKitEvent.event_type.in_(["download", "bulk_download", "view"]),
                ActionKitEvent.item_id.isnot(None),
                ActionKitEvent.created_at.between(start, end),
            )
            .group_by(ActionKitEvent.item_id, ActionKitItem.name)
            .order_by(func.count().desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        # 이전 기간 다운로드로 trend 계산
        prev_start = start - (end - start)
        items = []
        for row in rows:
            prev_count = await self._count_item_events(
                row.item_id, ["download", "bulk_download"], prev_start, start
            )
            curr_count = row.downloads
            items.append({
                "item_id": row.item_id,
                "name": row.name,
                "downloads": curr_count,
                "views": row.views,
                "trend": self._delta(curr_count, prev_count),
            })
        return items

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
                ActionKitEvent.search_query != "",
                ActionKitEvent.created_at.between(start, end),
            )
            .group_by(ActionKitEvent.search_query)
            .order_by(func.count().desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [
            {"keyword": row.search_query, "rank": i + 1, "volume": row.volume}
            for i, row in enumerate(result.all())
        ]

    async def _generate_insight(self, current_start, previous_start, now) -> str | None:
        """규칙 기반 자동 인사이트 생성"""
        popular = await self._get_popular_items(current_start, now, limit=3)
        keywords = await self._get_search_keywords(current_start, now, limit=3)

        insights = []
        # 가장 급성장한 아이템
        trending = [p for p in popular if p.get("trend") and p["trend"] > 0.1]
        if trending:
            top = max(trending, key=lambda x: x["trend"])
            insights.append(
                f'"{top["name"]}" 다운로드가 이전 기간 대비 '
                f'{int(top["trend"] * 100)}% 증가했습니다.'
            )
        # 인기 검색어
        if keywords:
            top_kw = keywords[0]
            insights.append(
                f'가장 많이 검색된 키워드는 "{top_kw["keyword"]}" ({top_kw["volume"]}회)입니다.'
            )
        return " ".join(insights) if insights else None

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
    insight: str | None
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

### 4.4 Phase 4: 프론트엔드 연동

#### API 함수 추가 (api.ts)

```typescript
// app-frontend/src/features/ops/actionkit/api.ts 에 추가

export interface ActionKitStatsResponse {
    kpi: {
        total_downloads: number;
        total_downloads_delta: number | null;
        active_users: number;
        active_users_delta: number | null;
        download_rate: number;
        download_rate_delta: number | null;
    };
    popular_items: {
        item_id: number;
        name: string;
        downloads: number;
        views: number;
        trend: number | null;
    }[];
    search_keywords: {
        keyword: string;
        rank: number;
        volume: number;
    }[];
    insight: string | null;
    range_days: number;
    generated_at: string;
}

export const fetchStats = async (rangeDays: number = 30): Promise<ActionKitStatsResponse> => {
    const { data } = await apiClient.get('/ops/actionkit/stats', {
        params: { range_days: rangeDays },
    });
    return data;
};

// 이벤트 트래킹 (fire-and-forget)
export const trackEvent = (payload: {
    event_type: string;
    item_id?: number;
    search_query?: string;
}) => {
    apiClient.post('/actionkits/track', payload).catch(() => {});
};
```

#### 사용자 뷰에 트래킹 삽입 (ActionKitLibraryView.tsx)

```typescript
import { trackEvent } from "@/features/ops/actionkit/api";
// 또는 별도 경량 trackEvent 유틸 생성

// 1. 검색어 트래킹 (debounce 1초)
const trackSearch = useMemo(
    () => debounce((query: string) => {
        if (query.length >= 2) {
            trackEvent({ event_type: 'search', search_query: query });
        }
    }, 1000),
    []
);

// searchQuery 변경 시 호출
useEffect(() => { trackSearch(searchQuery); }, [searchQuery]);

// 2. ZIP 일괄 다운로드 트래킹 (기존 handleBulkDownload에 추가)
const handleBulkDownload = async () => {
    // 기존 ZIP 생성 로직...
    // + 트래킹 (각 아이템에 대해)
    for (const item of Object.values(bookmarkedItems)) {
        trackEvent({ event_type: 'bulk_download', item_id: item.id });
    }
};

// 3. 북마크 트래킹 (기존 toggleBookmark에 추가)
const toggleBookmark = (kit: ActionKitItem, e: React.MouseEvent) => {
    // 기존 localStorage 로직...
    if (!bookmarkedItems[identifier]) {
        trackEvent({ event_type: 'bookmark', item_id: kit.id });
    }
};

// 4. 상세 모달 열기 트래킹
const openDetail = (item: ActionKitItem) => {
    setDetailItem(item);
    trackEvent({ event_type: 'detail_view', item_id: item.id });
};
```

#### stats-dashboard.tsx 전면 교체

```typescript
interface OpsActionKitStatsDashboardProps {
    allItems: StatsItem[];  // 전체 아이템 (현재 카테고리가 아닌 전체)
}

export function OpsActionKitStatsDashboard({ allItems }: OpsActionKitStatsDashboardProps) {
    const [stats, setStats] = useState<ActionKitStatsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState<number>(30);

    useEffect(() => {
        setLoading(true);
        fetchStats(timeRange)
            .then(setStats)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [timeRange]);

    // 기간 필터 매핑
    const TIME_OPTIONS = [
        { label: "최근 1주일", value: 7 },
        { label: "최근 1개월", value: 30 },
        { label: "올해", value: 365 },
    ];

    // 노후 항목 감지 (기존 동적 로직 유지 — allItems 기반)
    const outdatedItems = allItems.filter(item => { ... });

    // 빈 데이터 상태 UI
    if (!stats && !loading) {
        return <EmptyState message="아직 충분한 데이터가 수집되지 않았습니다." />;
    }

    // KPI, popular_items, search_keywords를 stats 객체에서 렌더링
    // ...
}
```

#### view.tsx 수정 사항

```typescript
// 현재: stats 탭에 현재 카테고리 items만 전달
<OpsActionKitStatsDashboard items={items} />

// 수정 후: 전체 아이템 + stats 데이터 전달
// view.tsx에 allItems state 추가 (전체 카테고리의 모든 아이템)
const [allItems, setAllItems] = useState<OpsActionKitItem[]>([]);

useEffect(() => {
    // 모든 카테고리에서 아이템 로드 (stats 탭용)
    Promise.all(categories.map(c => fetchCategoryItems(c.id)))
        .then(results => setAllItems(results.flat()));
}, [categories]);

// stats 탭
<OpsActionKitStatsDashboard allItems={allItems} />
```

---

## 5. 데이터베이스 마이그레이션

### 5.1 새 마이그레이션 파일

```python
# alembic/versions/018_actionkit_events.py

def upgrade() -> None:
    op.create_table(
        "actionkit_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(20), nullable=False, index=True),
        sa.Column("item_id", sa.Integer,
            sa.ForeignKey("actionkit_items.id", ondelete="SET NULL"),
            nullable=True, index=True),
        sa.Column("user_id", sa.Integer,
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True, index=True),
        sa.Column("search_query", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.func.now(), index=True),
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

### 5.2 인덱스 전략

| 인덱스 | 컬럼 | 용도 |
|--------|------|------|
| `ix_event_type` | `event_type` | 이벤트 타입별 필터 |
| `ix_created_at` | `created_at` | 기간별 범위 쿼리 |
| `ix_type_created` | `(event_type, created_at)` | KPI 집계 (타입 + 기간) |
| `ix_item_created` | `(item_id, created_at)` | 아이템별 인기 순위 |
| `ix_user_id` | `user_id` | 고유 사용자 수 집계 |

### 5.3 데이터 보존 정책

이벤트 로그는 무한 증가하므로 보존 기간 설정 필요:

```python
# ARQ cron job으로 90일 이전 데이터 삭제
async def cleanup_old_actionkit_events(ctx):
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    await session.execute(
        delete(ActionKitEvent).where(ActionKitEvent.created_at < cutoff)
    )
```

### 5.4 체크리스트 (Alembic 규칙 참조)

1. `app/models/actionkit_event.py` 생성
2. `app/models/__init__.py`에 import + `__all__` 추가
3. `alembic/env.py`에 모듈 import 추가 (누락 시 autogenerate 불가)
4. FK에 `ondelete="SET NULL"` 명시 (아이템/사용자 삭제 시 이벤트 보존)
5. 마이그레이션 후 `alembic check`로 diff 없음 확인
6. dind DB + Docker DB 양쪽에 마이그레이션 적용

---

## 6. 상단 카드 vs 통계 탭 구조

### 6.1 현재 구조

```
┌─────────────────────────────────────────────────┐
│ Summary 카드 5개 (항상 표시) — GET /summary API    │
│ [전체항목 42] [파일첨부 38] [미공개 3] [법령 65] [HL 120] │
├─────────────────────────────────────────────────┤
│ [액션 키트]  [법령 가이드]  [통계 대시보드]            │
├─────────────────────────────────────────────────┤
│ 통계 탭: 하드코딩 데이터 (KPI/인기순위/검색어/인사이트)  │
└─────────────────────────────────────────────────┘
```

### 6.2 권장 구조 (변경 후)

```
┌─────────────────────────────────────────────────┐
│ Summary 카드 5개 (항상 표시) — 콘텐츠 현황            │
│ → 정적 집계: 아이템/파일/미공개/법령/하이라이트 수       │
│ → 역할: "관리할 콘텐츠가 얼마나 있나?"                │
├─────────────────────────────────────────────────┤
│ [액션 키트]  [법령 가이드]  [이용 통계]               │
├─────────────────────────────────────────────────┤
│ 이용 통계 탭: 실제 이벤트 데이터 — GET /stats API     │
│ ┌──────────┬──────────┬──────────┐              │
│ │ 다운로드  │ 활성유저  │ 전환율   │ ← KPI 카드    │
│ │ 123건    │ 45명     │ 38.2%   │              │
│ │ +12%     │ +5%      │ -2%     │              │
│ └──────────┴──────────┴──────────┘              │
│ ┌──────────────────────┬────────────┐           │
│ │ 인기 다운로드 TOP 5    │ 인기 검색어  │           │
│ │ 1. 근로계약서 (45건)   │ 1. 근로계약  │           │
│ │ 2. 임대차계약서 (32건) │ 2. 스톡옵션  │           │
│ │ ...                  │ ...        │           │
│ │                      │ 💡 인사이트  │           │
│ └──────────────────────┴────────────┘           │
│ ⚠️ 노후 항목 경고 (전체 아이템 기반)                 │
└─────────────────────────────────────────────────┘
```

- **Summary 카드**: 콘텐츠 관리 현황 (기존 summary API) — "관리할 대상"
- **통계 탭**: 사용자 행동 분석 (새 stats API) — "사용자가 무엇을 하는가"
- **역할이 다르므로 중복이 아님**

---

## 7. 구현 페이즈 및 작업량

### Phase 1: 이벤트 수집 인프라 (BE)

| 작업 | 파일 | 예상 규모 |
|------|------|----------|
| ActionKitEvent 모델 생성 | `app/models/actionkit_event.py` | 신규 ~40줄 |
| `__init__.py`에 import 추가 | `app/models/__init__.py` | 1줄 |
| Alembic 마이그레이션 | `alembic/versions/018_*.py` | 신규 ~30줄 |
| `alembic/env.py`에 import | `alembic/env.py` | 1줄 |
| 트래킹 API 엔드포인트 | `app/api/v1/actionkit/tracking.py` | 신규 ~30줄 |
| 라우터 등록 | `app/api/v1/actionkit/router.py` | 2줄 |
| 기존 download/view에 추적 삽입 | `app/api/v1/actionkit/files.py` | ~15줄 수정 |
| optional 인증 의존성 확인/추가 | `app/api/deps.py` | 0~10줄 |

### Phase 2: 통계 집계 서비스 (BE)

| 작업 | 파일 | 예상 규모 |
|------|------|----------|
| ActionKitStatsService | `app/features/ops/application/actionkit/stats_service.py` | 신규 ~180줄 |
| 응답 스키마 정의 | `app/api/v1/ops/schemas.py` | ~50줄 추가 |
| Stats API 엔드포인트 | `app/api/v1/ops/actionkit.py` | ~15줄 추가 |
| 인사이트 생성 로직 | stats_service.py 내 | ~40줄 |
| 데이터 정리 cron job | `app/workers/roadmap_worker.py` | ~15줄 |

### Phase 3: 프론트엔드 연동

| 작업 | 파일 | 예상 규모 |
|------|------|----------|
| fetchStats + trackEvent API 함수 | `ops/actionkit/api.ts` | ~40줄 |
| 트래킹 호출 삽입 (search/zip/bookmark/detail) | `actionkit/components/ActionKitLibraryView.tsx` | ~30줄 |
| 트래킹 호출 삽입 (law view) | `actionkit/components/LawGuideView.tsx` | ~10줄 |
| stats-dashboard.tsx 전면 교체 | `ops/actionkit/components/stats-dashboard.tsx` | ~220줄 |
| view.tsx allItems + stats 연동 | `ops/actionkit/view.tsx` | ~20줄 수정 |
| 빈 데이터 상태 UI | stats-dashboard.tsx 내 | ~15줄 |

### Phase 4: 테스트

| 작업 | 파일 | 예상 규모 |
|------|------|----------|
| 이벤트 기록 API 테스트 | `tests/api/test_actionkit_tracking.py` | 신규 ~100줄 |
| 통계 집계 서비스 테스트 | `tests/services/test_actionkit_stats.py` | 신규 ~150줄 |
| 마이그레이션 검증 | `alembic check` | - |

### 총 작업량 요약

| Phase | 신규 파일 | 수정 파일 | 코드량 |
|-------|----------|----------|--------|
| 1. 이벤트 수집 | 3개 | 4~5개 | ~130줄 |
| 2. 집계 서비스 | 1개 | 2개 | ~300줄 |
| 3. FE 연동 | 0개 | 5개 | ~335줄 |
| 4. 테스트 | 2개 | 0개 | ~250줄 |
| **합계** | **6개** | **11~12개** | **~1,015줄** |

---

## 8. 데이터 수집 시작 시점 문제

통계 대시보드는 이벤트 데이터가 쌓여야 의미가 있음. 구현 직후에는 데이터가 0건.

### 해결 방안

1. **빈 상태 UI**: "아직 충분한 데이터가 수집되지 않았습니다" 표시 + 수집 시작일 안내
2. **기간 필터 최소값**: `range_days >= 7` — 최소 1주일 데이터 필요
3. **점진 전환**: Phase 1~2 배포 후 1~2주 데이터 수집 → Phase 3(FE) 배포
4. **delta가 None인 경우**: 이전 기간 데이터 0이면 변화율 대신 "신규" 뱃지 표시

---

## 9. 리스크 및 고려사항

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 이벤트 테이블 무한 증가 | 디스크/쿼리 성능 | 90일 보존 cron + 파티셔닝 고려 |
| 비로그인 사용자 추적 | user_id=NULL 다수 | COUNT 기반 집계에 영향 없음; 고유 사용자 수는 user_id IS NOT NULL로 제한 |
| 봇/크롤러 트래픽 | 통계 왜곡 | User-Agent 필터 또는 rate limit (slowapi 이미 의존) |
| 검색 debounce 누락 | 과다 이벤트 | FE에서 1초 debounce 필수; 백엔드 rate limit 보조 |
| 기존 다운로드 API 수정 | 기능 영향 | 추적 실패해도 다운로드는 정상 진행 (try/except) |
| files.py에 인증 의존성 추가 | 기존 비인증 접근 유지 | `get_optional_current_user` 사용 (인증 실패=None) |
| ZIP 다운로드 중복 카운트 | download + bulk_download 이중 집계 | bulk_download는 별도 event_type으로 구분; 서버측 download 이벤트 발생 시 중복 방지 로직 필요 |
| stats 탭에 현재 카테고리 아이템만 전달 | 노후 항목 감지 일부만 동작 | allItems 전체 로드로 수정 |

### ZIP 다운로드 중복 카운트 상세

현재 `handleBulkDownload()`는 각 아이템에 대해 `GET /items/{id}/download`를 호출한다.
서버에 download 추적을 넣으면, ZIP 다운로드 시 **개별 download 이벤트도 기록된다**.

**해결 방안:**
- 클라이언트에서 bulk_download용 요청에 `?bulk=true` 파라미터 추가
- 서버에서 `bulk=true`인 경우 download 이벤트 기록 스킵 (클라이언트가 bulk_download를 별도 POST)
- 또는: 서버에서 그냥 다 기록하되, 집계 시 bulk_download와 download을 합산

---

## 10. 참고 파일 (보완)

### 백엔드 모델

| 파일 | 설명 |
|------|------|
| `app/models/actionkit.py` | ActionKitCategory, ActionKitItem, Highlight, Checklist, RelatedLaw |
| `app/models/file.py` | 통합 File 모델 (owner_type, version, is_current) |
| `app/models/__init__.py` | 모델 등록 (신규 모델 추가 시 필수) |

### 백엔드 서비스

| 파일 | 설명 |
|------|------|
| `app/features/actionkit/application/service.py` | 사용자 공개 서비스 (리스트, 뷰, 다운로드, 업로드) |
| `app/features/actionkit/application/file_pipeline.py` | 파일 경로/MIME 유틸 |
| `app/features/ops/application/actionkit/service.py` | Ops 서비스 (CRUD, summary, 버전 관리) |
| `app/features/ops/application/reports/service.py` | OpsReportsService (delta 패턴 참조) |
| `app/features/roadmaps/application/actionkit_matcher.py` | 로드맵 생성 시 ActionKit 매칭 |
| `app/repositories/actionkit_repository.py` | ActionKit 데이터 접근 |
| `app/repositories/file_repository.py` | File 데이터 접근 (버전 관리) |

### 백엔드 API

| 파일 | 설명 |
|------|------|
| `app/api/v1/actionkit/router.py` | 사용자 공개 라우터 등록 |
| `app/api/v1/actionkit/listing.py` | 목록 엔드포인트 (laws, kits) |
| `app/api/v1/actionkit/detail.py` | 상세 엔드포인트 |
| `app/api/v1/actionkit/files.py` | 뷰어/다운로드/업로드 (추적 삽입 대상) |
| `app/api/v1/actionkit/schemas.py` | 응답 모델 |
| `app/api/v1/ops/actionkit.py` | Ops 관리 엔드포인트 (stats 추가 대상) |
| `app/api/v1/ops/schemas.py` | Ops 스키마 (stats 응답 추가 대상) |

### 프론트엔드 사용자 뷰

| 파일 | 설명 |
|------|------|
| `src/features/actionkit/components/ActionKitContainer.tsx` | 탭 전환 (Laws/Kits) + 교차 탐색 |
| `src/features/actionkit/components/ActionKitLibraryView.tsx` | 키트 라이브러리 (검색, 북마크, ZIP, 스타터팩) |
| `src/features/actionkit/components/LawGuideView.tsx` | 법령 가이드 (챕터 탐색, 완료 체크) |
| `src/features/actionkit/components/ActionKitDetailModal.tsx` | 상세 모달 (체크리스트, 하이라이트, 법령) |
| `src/features/actionkit/components/LawDetailPopup.tsx` | 법령 상세 팝업 |
| `src/features/actionkit/hooks/useActionKit.ts` | 키트 데이터 fetch hook |
| `src/features/actionkit/hooks/useLawGuide.ts` | 법령 데이터 fetch hook |
| `src/features/actionkit/types/index.ts` | 타입 정의 |

### 프론트엔드 Ops 뷰

| 파일 | 설명 |
|------|------|
| `src/features/ops/actionkit/view.tsx` | Ops 메인 뷰 (탭, 카드, 테이블) |
| `src/features/ops/actionkit/api.ts` | Ops API 클라이언트 (fetchStats 추가 대상) |
| `src/features/ops/actionkit/components/stats-dashboard.tsx` | 통계 대시보드 (전면 교체 대상) |
| `src/features/ops/actionkit/components/actionkit-edit-modal.tsx` | 아이템 CRUD 모달 |
| `src/features/ops/actionkit/components/category-edit-modal.tsx` | 카테고리 CRUD 모달 |

### 마이그레이션

- `app-backend/alembic/versions/` — 기존 017번까지 완료 (018번으로 추가)
- `app-backend/alembic/env.py` — 신규 모델 import 추가 필수

### 테스트

| 파일 | 설명 |
|------|------|
| `tests/api/test_actionkit_tracking.py` | 신규 — 이벤트 기록 API |
| `tests/services/test_actionkit_stats.py` | 신규 — 집계 서비스 |
| `src/features/actionkit/__tests__/useActionKit.test.ts` | 기존 — 키트 데이터 로딩 |
