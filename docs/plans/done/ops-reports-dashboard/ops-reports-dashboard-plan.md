# Ops Reports Dashboard - Phase 1 구현 계획

> Last Updated: 2026-03-04
> 기획: `docs/planning/PLAN-ops-reports-dashboard.md`

---

## Executive Summary

StepZero 운영 콘솔(`/ops/reports`)에 실제 DB 집계 쿼리를 연결하고, KPI를 기존 3종에서 확장 8종+비율 지표+총계로 확장한다. 기간 필터(7d/30d)와 전기간 대비 변화율을 추가하여 운영자가 서비스 상태를 정량적으로 파악할 수 있도록 한다.

**범위:** Phase 1 (내부 DB 쿼리 기반만, 외부 서비스 미사용, Slack 알림 미포함)

---

## 1. Current State Analysis

### 백엔드

| 구성 요소 | 상태 | 파일 |
|-----------|------|------|
| **서비스** | Placeholder (하드코딩 0) | `app-backend/app/features/ops/application/reports/service.py` |
| **API 라우트** | 라우트만 존재 (파라미터 없음) | `app-backend/app/api/v1/ops/reports.py` |
| **__init__** | 함수 export | `app-backend/app/features/ops/application/reports/__init__.py` |

현재 `get_summary()` — 동기 함수, DB 세션 없음, TypedDict 4필드(active_users_7d, new_signups_7d, roadmaps_generated_7d, generated_at) 모두 0 반환.

### 프론트엔드

| 구성 요소 | 상태 | 파일 |
|-----------|------|------|
| **타입** | 4필드 정의 | `app-frontend/src/features/ops/reports/types.ts` |
| **API** | 파라미터 없는 GET | `app-frontend/src/features/ops/reports/api.ts` |
| **뷰** | 3개 KPI 카드 (인라인 `<dl>`) | `app-frontend/src/features/ops/reports/view.tsx` |
| **페이지** | 래퍼만 | `app-frontend/src/app/(dashboard)/ops/reports/page.tsx` |

### 사용 가능한 DB 모델/필드

| 지표 | 모델 | 필드 | 인덱스 |
|------|------|------|--------|
| 활성 사용자 | `User` | `last_login_at: datetime?` | O |
| 신규 가입 | `User` | `created_at: datetime` | O (implicit) |
| 로드맵 생성 | `Roadmap` | `created_at`, `deleted_at` | O |
| 채팅 세션 | `RoadmapChatThread` | `created_at`, `is_deleted` | - |
| 커뮤니티 | `GrowthClubPost` | `created_at` | - |
| 팀 | `Team` | `created_at`, `deleted_at` | O |
| 가입→로드맵 | `Roadmap.created_by` → `User.id` | FK 조인 | O |

**Soft delete 패턴:** `Roadmap`, `Team` → `deleted_at IS NULL` 필터 필요
**Chat soft delete:** `RoadmapChatThread` → `is_deleted = False` 필터 필요
**DateTime 저장:** `datetime.now(timezone.utc).replace(tzinfo=None)` (naive UTC)

---

## 2. Proposed Future State

### 확장된 API 응답 구조

```
GET /api/v1/ops/reports/summary?range=7d|30d

Response:
{
  // 성장 지표 (선택 기간)
  "active_users": 127,
  "new_signups": 23,
  // 핵심 기능 사용
  "roadmaps_generated": 45,
  "chat_sessions": 89,
  "community_posts": 15,
  // 비율 지표
  "dau_mau_ratio": 0.423,
  "signup_to_roadmap_rate": 0.682,
  // 총계
  "total_users": 1234,
  "total_teams": 89,
  "total_roadmaps": 456,
  // 전기간 대비 변화율 (null if 이전 기간 데이터 = 0)
  "active_users_delta": 0.125,
  "new_signups_delta": -0.052,
  "roadmaps_generated_delta": 0.301,
  // 메타
  "generated_at": "2026-03-04T09:00:00Z",
  "range": "7d"
}
```

### 프론트엔드 UI

```
┌─────────────────────────────────────────────────┐
│ 운영 리포트        [7일] [30일]    생성: ...     │
├─────────────────────────────────────────────────┤
│ Row 1: 핵심 지표 (delta 표시)                      │
│ [활성 사용자] [신규 가입] [로드맵 생성] [채팅 세션] │
├─────────────────────────────────────────────────┤
│ Row 2: 비율 + 총계                                │
│ [DAU/MAU]  [가입→로드맵] [커뮤니티] [총 사용자]     │
└─────────────────────────────────────────────────┘
```

---

## 3. Implementation Phases

### Phase A: 백엔드 서비스 재작성 (Effort: L)

#### A-1. `OpsReportsService` 클래스 생성
- `service.py` 전면 재작성
- `AsyncSession` 주입 패턴 (기존 `DashboardService` 참조)
- `get_summary(range_days: int) -> OpsSummary` 비동기 메서드

#### A-2. DB 집계 쿼리 구현
각 쿼리 메서드 (private):
- `_count_active_users(since, until?)` → `User.last_login_at >= since AND is_active AND NOT is_suspended`
- `_count_new_signups(since, until?)` → `User.created_at >= since`
- `_count_roadmaps(since, until?)` → `Roadmap.created_at >= since AND deleted_at IS NULL`
- `_count_chat_sessions(since, until?)` → `RoadmapChatThread.created_at >= since AND NOT is_deleted`
- `_count_community_posts(since, until?)` → `GrowthClubPost.created_at >= since`
- `_count_total(Model, filter?)` → 전체 COUNT
- `_calc_signup_to_roadmap_rate(since)` → subquery 패턴

#### A-3. Delta 계산 로직
- 현재 기간 vs 직전 동일 기간 비교
- `(current - prev) / prev` (prev=0 → None)

#### A-4. DAU/MAU 비율 계산
- `active_users_7d / active_users_30d` (30d=0 → 0.0)

### Phase B: 백엔드 API 수정 (Effort: S)

#### B-1. 라우트에 `range` Query 파라미터 추가
- `Query("7d", pattern="^(7d|30d)$")`
- `session: AsyncSession = Depends(get_session)`

#### B-2. `__init__.py` export 업데이트

### Phase C: 프론트엔드 타입/API (Effort: S)

#### C-1. `OpsSummary` 타입 확장
- 4필드 → ~15필드

#### C-2. `fetchOpsSummary(range)` 파라미터 추가

### Phase D: 프론트엔드 UI 확장 (Effort: M)

#### D-1. `MetricCard` 컴포넌트 추출
- Props: `title`, `value`, `delta?`, `suffix?`, `badge?`
- Delta 포맷: `+12.5%` 녹색 / `-5.2%` 빨간색 / `N/A`

#### D-2. 기간 필터 탭 추가
- 7일 / 30일 토글 (state 관리 → API 재호출)

#### D-3. KPI 카드 그리드 2행 × 4열
- Row 1: 활성 사용자, 신규 가입, 로드맵 생성, 채팅 세션 (with delta)
- Row 2: DAU/MAU, 가입→로드맵, 커뮤니티, 총 사용자/팀

### Phase E: 검증 (Effort: S)

#### E-1. 백엔드 pytest 통과 확인
#### E-2. 프론트엔드 lint 통과 확인
#### E-3. 수동 API/UI 테스트

---

## 4. Risk Assessment

| 리스크 | 영향 | 대응 |
|--------|------|------|
| `last_login_at` 미기록 사용자 (OAuth 초기 가입자) | 활성 사용자 과소 집계 | `last_login_at IS NOT NULL` 조건 명시, 향후 로그인 시 업데이트 확인 |
| 대량 데이터 시 집계 느림 | API 응답 지연 | COUNT 쿼리는 인덱스 활용, 초기 데이터 적으므로 당장 문제 없음 |
| `range` 파라미터 validation | 잘못된 값 입력 | FastAPI Query pattern 검증 |
| 프론트엔드 타입 변경 | 기존 렌더링 깨짐 | 새 필드는 모두 추가(확장), 기존 필드명 유지 |

---

## 5. Success Metrics

1. `/ops/reports?range=7d` 호출 시 실제 DB 데이터 반환 (0이 아닌 값)
2. 7일/30일 기간 전환 시 서로 다른 집계 결과
3. 전기간 대비 변화율이 정확히 계산됨
4. 8개 KPI 카드가 2행 × 4열로 렌더링
5. 기존 pytest 전체 통과 + ESLint 0 error

---

## 6. Dependencies

- **기존 DB 모델 변경 없음** — 새 마이그레이션 불필요
- **기존 리포지토리 변경 없음** — 서비스에서 직접 session 쿼리
- **새 패키지 설치 없음** — SQLAlchemy func.count 이미 사용 가능
- **프론트엔드 새 패키지 없음** — 기존 shadcn/ui + Tailwind 활용

---

## 7. Files to Modify

| 순서 | 파일 경로 | 변경 유형 |
|------|----------|----------|
| 1 | `app-backend/app/features/ops/application/reports/service.py` | 전면 재작성 |
| 2 | `app-backend/app/features/ops/application/reports/__init__.py` | export 변경 |
| 3 | `app-backend/app/api/v1/ops/reports.py` | DI + 파라미터 추가 |
| 4 | `app-frontend/src/features/ops/reports/types.ts` | 타입 확장 |
| 5 | `app-frontend/src/features/ops/reports/api.ts` | 파라미터 추가 |
| 6 | `app-frontend/src/features/ops/reports/view.tsx` | UI 전면 재작성 |
