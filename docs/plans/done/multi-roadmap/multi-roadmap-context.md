# Multi-Roadmap - Context & Decisions (v2)

## Status
- Phase: Planning
- Progress: 0 / 25 tasks complete
- Last Updated: 2026-02-25

## Key Files

### Modified (Backend)

| File | Purpose |
|------|---------|
| `app-backend/app/repositories/roadmap_repository.py` | `list_for_team()`, `soft_delete()`, `update_title()` 메서드 추가 |
| `app-backend/app/api/v1/schemas.py` | `RoadmapSummaryItem`, `RoadmapListResponse`, `RoadmapUpdateRequest` 스키마 추가 |
| `app-backend/app/api/v1/roadmaps/get.py` | `GET /roadmaps`, `DELETE /roadmaps/{id}`, `PATCH /roadmaps/{id}` 엔드포인트 추가 |

### Modified (Frontend)

| File | Purpose |
|------|---------|
| `app-frontend/src/app/(dashboard)/roadmap/page.tsx` | 활성 로드맵 기반 실행 뷰 + 생성 모드 전환으로 리팩토링 |
| `app-frontend/src/features/roadmap/types/roadmap.ts` | `RoadmapSummary`, `RoadmapListResponse` 타입 추가 |
| `app-frontend/src/features/roadmap/api/index.ts` | 목록/삭제/이름변경/상세 API 함수 추가 |
| `app-frontend/src/features/roadmap/components/index.ts` | 새 컴포넌트 export 추가 |
| `app-frontend/src/features/roadmap/hooks/index.ts` | 새 훅 export 추가 |
| `app-frontend/src/features/roadmap/components/RoadmapHeader.tsx` | Switcher 트리거 버튼 통합 |
| `app-frontend/src/features/roadmap/components/RoadmapGenerationPanel.tsx` | `onGenerated` 콜백 정비, `onCancel` prop 추가 |
| `app-frontend/src/features/dashboard/components/RoadmapStepper.tsx` | "전체 계획 보기" 링크 확인 |
| `app-frontend/src/features/dashboard/components/DashboardView.tsx` | 생성 완료 후 이동 로직 수정 |

### New (Backend)

| File | Purpose |
|------|---------|
| `app-backend/tests/api/test_roadmap_multi.py` | 멀티 로드맵 API 단위 테스트 |

### New (Frontend)

| File | Purpose |
|------|---------|
| `app-frontend/src/features/roadmap/hooks/useActiveRoadmap.ts` | localStorage 기반 활성 로드맵 관리 훅 |
| `app-frontend/src/features/roadmap/hooks/useRoadmapList.ts` | 로드맵 목록 조회/관리 훅 |
| `app-frontend/src/features/roadmap/components/RoadmapSwitcher.tsx` | 로드맵 전환/관리 UI 컴포넌트 |
| `app-frontend/src/features/roadmap/components/RoadmapDeleteDialog.tsx` | 삭제 확인 다이얼로그 |
| `app-frontend/src/features/roadmap/components/RoadmapRenameDialog.tsx` | 이름 변경 다이얼로그 |

### 삭제된 항목 (v1 대비)

| v1 File (취소됨) | 이유 |
|----------|------|
| `app-frontend/src/features/roadmap/components/RoadmapCard.tsx` | 목록 페이지 제거됨, Switcher 내 아이템으로 대체 |
| `app-frontend/src/features/roadmap/components/RoadmapListView.tsx` | 목록 페이지 제거됨 |
| `app-frontend/src/features/roadmap/hooks/useRoadmapDetail.ts` | `useActiveRoadmap`으로 통합 |
| `app-frontend/src/app/(dashboard)/roadmap/[id]/page.tsx` | 별도 상세 페이지 불필요 |

## Key Decisions

### 1. DB 마이그레이션 불필요 (2026-02-25)
- **Rationale**: `Roadmap` 테이블은 이미 `team_id` FK로 1:N 관계. `deleted_at` soft-delete 필드도 존재.
- **Alternatives**: `active_roadmap_id`를 Team 모델에 추가하여 서버 사이드로 활성 로드맵 관리
- **Trade-offs**: 프론트엔드 localStorage로 관리하면 마이그레이션이 불필요하고 배포 위험이 없음. 다만 브라우저/기기 간 동기화 안됨 (현재 단일 사용자 환경에서는 문제 없음).

### 2. `/latest/detail` 엔드포인트 유지 (2026-02-25)
- **Rationale**: 대시보드(`DashboardView`, `DashboardService`)가 이 엔드포인트에 의존. 삭제하면 회귀 발생.
- **Alternatives**: `/latest/detail`을 deprecated로 표시하고 대시보드도 목록 기반으로 전환
- **Trade-offs**: 하위 호환성 유지 vs 코드 중복. 안전한 전환을 위해 유지 선택.

### 3. 프론트엔드 라우팅 전략 - 변경됨 (2026-02-25, v2 수정)
- **v1**: `/roadmap` = 목록 페이지, `/roadmap/[id]` = 상세 페이지
- **v2**: `/roadmap` = **활성 로드맵 실행 뷰 + Switcher** (단일 페이지)
- **Rationale**: 사용자가 `/roadmap` 접근 시 바로 실행 중인 로드맵을 보는 것이 직관적. 목록 페이지를 거치는 것은 불필요한 단계.
- **Alternatives**: (a) v1 방식 유지 (목록 -> 상세), (b) Sidebar에 목록 상시 표시
- **Trade-offs**: Switcher 방식은 UX가 깔끔하나 목록을 한눈에 보기 어려움. Switcher 패널을 충분히 넓게 만들어 보완.

### 4. 대시보드는 "최신 로드맵" 기준 유지 (2026-02-25)
- **Rationale**: 대시보드 진행률/단계 표시는 단일 로드맵 기준이 적합. 멀티 표시는 UX 복잡도 증가.
- **Alternatives**: (a) 대시보드에 로드맵 선택 드롭다운, (b) 모든 로드맵 통합 진행률
- **Trade-offs**: 단순함 유지. 향후 사용자 피드백에 따라 대시보드 로드맵 선택 기능 추가 가능.

### 5. 소프트 삭제 (2026-02-25)
- **Rationale**: `Roadmap` 모델에 이미 `deleted_at` 필드 존재. 기존 패턴 따름.
- **Alternatives**: 하드 삭제 (cascade로 step/action 모두 삭제)
- **Trade-offs**: 소프트 삭제는 데이터 복구 가능하지만 쿼리에 항상 `deleted_at IS NULL` 조건 필요. 이미 기존 코드에서 이 패턴 사용 중.

### 6. 활성 로드맵 저장: localStorage (2026-02-25, v2 신규)
- **Rationale**: 백엔드에 `active_roadmap_id` 컬럼을 추가하면 DB 마이그레이션이 필요하고 배포 위험이 증가. 현재 단일 사용자/단일 브라우저 환경에서는 localStorage로 충분.
- **Alternatives**:
  - (a) Team 모델에 `active_roadmap_id: UUID | None` 컬럼 추가 -> DB 마이그레이션 필요
  - (b) 별도 `UserPreference` 테이블 -> 과도한 설계
  - (c) sessionStorage -> 탭 닫으면 사라짐, 사용성 나쁨
- **Trade-offs**:
  - 장점: 마이그레이션 없음, 즉시 구현 가능, 프론트엔드만 변경
  - 단점: 브라우저/기기 간 동기화 안됨, 브라우저 데이터 삭제 시 초기화
  - 후속: 다중 기기 지원이 필요해지면 백엔드로 이관 (Phase 2로 분리 가능)
- **localStorage key**: `stepzero_active_roadmap_id`
- **기본값 결정**: localStorage에 값이 없거나 해당 ID가 404인 경우, 목록의 첫 번째(최신 생성) 로드맵을 활성으로 설정

### 7. `/roadmap/[id]` 별도 상세 페이지 불필요 (2026-02-25, v2 신규)
- **Rationale**: Switcher로 전환하면 같은 `/roadmap` URL에서 해당 로드맵의 실행 뷰가 표시되므로 별도 동적 라우트가 불필요.
- **Alternatives**: `/roadmap/[id]`를 직접 링크/공유용으로 유지
- **Trade-offs**:
  - 장점: 라우팅 단순화, 구현 범위 축소
  - 단점: 특정 로드맵에 대한 직접 링크(공유) 불가
  - 후속: 공유 기능이 필요해지면 `/roadmap?id=xxx` 쿼리 파라미터 또는 `/roadmap/[id]` 라우트 추가 검토

### 8. 신규 로드맵 추가: 같은 페이지 내 GenerationPanel 전환 (2026-02-25, v2 신규)
- **Rationale**: `/roadmap/new` 별도 페이지를 만들면 라우팅이 복잡해지고, 기존 GenerationPanel을 재사용할 수 있으므로 같은 `/roadmap` 내에서 모드를 전환하는 것이 적합.
- **구현 방식**:
  1. Switcher에서 "+ 새 로드맵 만들기" 클릭
  2. 페이지 상태를 `creating` 모드로 전환
  3. 실행 뷰 대신 `RoadmapGenerationPanel` 표시
  4. 생성 완료 -> 새 로드맵을 활성으로 설정, 실행 뷰로 전환
  5. 생성 취소 -> 이전 활성 로드맵으로 복귀
- **Alternatives**: (a) `/roadmap/new` 별도 라우트, (b) 모달로 생성
- **Trade-offs**: 인라인 전환은 자연스러운 UX. 단, 기존 실행 뷰 상태가 마운트 해제되므로 돌아올 때 재로드 필요.

## API Endpoints

### New Endpoints

#### `GET /roadmaps`
팀의 전체 로드맵 목록 조회 (soft-delete 제외)

```json
// Response: RoadmapListResponse
{
  "items": [
    {
      "roadmap_id": "uuid",
      "title": "카페 창업 로드맵",
      "business_type": "휴게음식점",
      "location": "서울 마포구",
      "created_at": "2026-02-20T10:00:00",
      "progress": 33,
      "total_steps": 6,
      "completed_steps": 2
    }
  ],
  "total": 3
}
```

#### `DELETE /roadmaps/{roadmap_id}`
로드맵 소프트 삭제

```json
// Response: 204 No Content
```

#### `PATCH /roadmaps/{roadmap_id}`
로드맵 제목 변경

```json
// Request: RoadmapUpdateRequest
{ "title": "변경된 제목" }

// Response: { "roadmap_id": "uuid", "title": "변경된 제목" }
```

### Existing Endpoints (변경 없음)

| Endpoint | Description |
|----------|-------------|
| `GET /roadmaps/latest/detail` | 최신 로드맵 상세 (유지, 대시보드에서 사용) |
| `GET /roadmaps/{id}/detail` | 특정 로드맵 상세 (유지, 활성 로드맵 조회에 사용) |
| `GET /roadmaps/{id}` | 특정 로드맵 기본 (유지) |
| `POST /roadmaps/jobs` | 비동기 생성 (유지) |
| `POST /roadmaps/jobs/validate` | 입력 검증 (유지) |
| `PATCH /roadmaps/tasks/{step_id}` | 단계 상태 변경 (유지) |
| `PATCH /roadmaps/tasks/{step_id}/actions/{action_id}` | 액션 상태 변경 (유지) |

## Repository Method Specifications

### `list_for_team(team_id, offset=0, limit=20) -> tuple[list[Roadmap], int]`
```python
stmt = (
    select(Roadmap)
    .where(Roadmap.team_id == team_id, Roadmap.deleted_at.is_(None))
    .order_by(Roadmap.created_at.desc())
    .offset(offset)
    .limit(limit)
)
# Also return count for total
```

### `soft_delete(roadmap_id, team_id) -> bool`
```python
roadmap = await self.get_by_id_for_team(roadmap_id, team_id)
if not roadmap:
    return False
roadmap.deleted_at = datetime.utcnow()
await self.session.flush()
return True
```

### `update_title(roadmap_id, team_id, new_title) -> Roadmap | None`
```python
roadmap = await self.get_by_id_for_team(roadmap_id, team_id)
if not roadmap:
    return None
roadmap.title = new_title
roadmap.updated_at = datetime.utcnow()
await self.session.flush()
return roadmap
```

## Frontend Component Hierarchy (v2)

```
/roadmap (page.tsx) - 상태: 'loading' | 'empty' | 'viewing' | 'creating'
  |
  |-- [loading] --> 로딩 스피너
  |
  |-- [empty: 로드맵 0개] --> RoadmapGenerationPanel (기존)
  |     |-- onGenerated -> 새 로드맵 활성 설정, 'viewing' 상태로 전환
  |
  |-- [viewing: 활성 로드맵 표시]
  |     |-- RoadmapHeader (확장됨)
  |     |     |-- 제목 표시
  |     |     |-- 현재 단계 표시
  |     |     |-- [Switcher 트리거 버튼] --> RoadmapSwitcher 열기
  |     |
  |     |-- RoadmapSwitcher (드롭다운/패널)
  |     |     |-- 로드맵 목록 아이템 (각각: 제목, 진행률 바, 생성일)
  |     |     |     |-- 활성 로드맵 체크 표시
  |     |     |     |-- 클릭 -> 해당 로드맵 활성으로 전환
  |     |     |     |-- 더보기 메뉴: 이름 변경, 삭제
  |     |     |-- Separator
  |     |     |-- "+ 새 로드맵 만들기" 버튼 -> 'creating' 상태로 전환
  |     |     |-- RoadmapDeleteDialog (삭제 확인)
  |     |     |-- RoadmapRenameDialog (이름 변경)
  |     |
  |     |-- RoadmapExecutionView (기존 재사용)
  |     |-- RoadmapSidebar (기존 재사용)
  |
  |-- [creating: 새 로드맵 생성 모드]
  |     |-- 상단: "< 로드맵으로 돌아가기" 링크 (이전 활성 로드맵으로 복귀)
  |     |-- RoadmapGenerationPanel
  |     |     |-- onGenerated -> 새 로드맵 활성 설정, 'viewing' 상태로 전환
  |     |     |-- onCancel -> 이전 활성 로드맵으로 복귀, 'viewing' 상태로 전환
```

## RoadmapSwitcher 컴포넌트 상세 스펙

### UI 구조
- **트리거**: RoadmapHeader 내 제목 옆 아이콘 버튼 (ChevronDown 또는 Layers 아이콘)
- **패널**: DropdownMenu 기반, 최대 높이 제한 + 스크롤
- **너비**: min-w-[320px] 또는 반응형

### 아이템 구성
각 로드맵 아이템:
```
[체크 아이콘] 카페 창업 로드맵                    [...]
              휴게음식점 | 서울 마포구
              ██████░░░░ 33% (2/6)
```
- 좌측: 활성 로드맵이면 체크 아이콘 (`Check`), 아니면 빈 공간
- 중앙: 제목 (bold), 업종|지역 (sub text), 진행률 바 + 텍스트
- 우측: 더보기 버튼 (`MoreHorizontal`) -> 이름 변경, 삭제

### 하단
```
--separator--
[+] 새 로드맵 만들기
```

### Props
```typescript
interface RoadmapSwitcherProps {
  roadmaps: RoadmapSummary[];
  activeRoadmapId: string | null;
  onSelect: (roadmapId: string) => void;
  onDelete: (roadmapId: string) => void;
  onRename: (roadmapId: string, newTitle: string) => void;
  onCreateNew: () => void;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}
```

### 사용 UI 라이브러리
- `DropdownMenu` (shadcn/ui) - 메인 패널
- `Progress` (shadcn/ui) - 진행률 바
- `Badge` (shadcn/ui) - 업종/지역 표시
- `Dialog` (shadcn/ui) - 삭제/이름변경 다이얼로그
- `Separator` (shadcn/ui) - 구분선
- lucide-react 아이콘: `Check`, `ChevronDown`, `MoreHorizontal`, `Pencil`, `Trash2`, `Plus`, `MapPin`, `Briefcase`

## useActiveRoadmap Hook 스펙

```typescript
interface UseActiveRoadmapReturn {
  /** 현재 활성 로드맵 ID (localStorage에서 로드) */
  activeRoadmapId: string | null;
  /** 활성 로드맵 상세 데이터 */
  activeRoadmap: RoadmapDetailResponse | null;
  /** 로딩 상태 */
  loading: boolean;
  /** 에러 메시지 */
  error: string | null;
  /** 활성 로드맵 변경 (localStorage 저장 + 상세 로드) */
  setActiveRoadmap: (roadmapId: string) => Promise<void>;
  /** 활성 로드맵 클리어 (삭제 시 등) */
  clearActiveRoadmap: () => void;
  /** 현재 활성 로드맵 상세 다시 로드 */
  reloadActiveRoadmap: () => Promise<void>;
}
```

### 내부 로직
1. 마운트 시: localStorage에서 `stepzero_active_roadmap_id` 읽기
2. 값이 있으면: `GET /roadmaps/{id}/detail` 호출
   - 성공: 해당 로드맵 데이터 설정
   - 404: localStorage 클리어, `null` 반환 (외부에서 fallback 처리)
3. `setActiveRoadmap(id)`: localStorage에 저장 + 상세 로드
4. `clearActiveRoadmap()`: localStorage 삭제 + 상태 초기화

## UX Design Direction (v2)

### `/roadmap` 페이지 - 활성 로드맵 뷰
- 기존 `RoadmapExecutionView`와 동일한 레이아웃 (타임라인 + 사이드바)
- RoadmapHeader에 Switcher 트리거 추가 (제목 옆 드롭다운 아이콘)
- Switcher 열면 현재 로드맵에 체크 표시, 다른 로드맵 클릭 시 전환

### 신규 로드맵 추가 플로우
1. Switcher에서 "+ 새 로드맵 만들기" 클릭
2. 실행 뷰 대신 `RoadmapGenerationPanel` 표시
3. 상단에 "< 로드맵으로 돌아가기" 링크 (취소 경로)
4. 생성 완료 -> 새 로드맵 활성 설정, 실행 뷰 전환
5. 취소 클릭 -> 이전 활성 로드맵으로 복귀

### 대시보드
- 기존과 동일: 최신 로드맵 기준 ProgressCard + RoadmapStepper
- RoadmapStepper의 "전체 계획 보기"는 `/roadmap`으로 이동 (기존과 동일)

## Testing Notes

### 백엔드 테스트
- 기존 테스트 63건 회귀 확인
- 새 테스트: `test_roadmap_multi.py`
  - `test_list_roadmaps_empty`: 로드맵 없을 때 빈 목록 반환
  - `test_list_roadmaps_multiple`: 복수 로드맵 목록 반환 및 정렬
  - `test_list_roadmaps_excludes_deleted`: soft-delete된 항목 제외
  - `test_delete_roadmap`: 삭제 후 목록에서 사라짐
  - `test_delete_nonexistent_roadmap`: 404 반환
  - `test_update_roadmap_title`: 이름 변경 성공
  - `test_update_nonexistent_roadmap`: 404 반환

### 프론트엔드 테스트
- 기존 `RoadmapRenderer.test.tsx` 회귀 확인
- 타입 체크: `npx tsc --noEmit` 통과
- 신규 테스트 고려: RoadmapSwitcher, useActiveRoadmap 단위 테스트

## Known Issues

### 향후 개선
1. **활성 로드맵 서버 동기화**: localStorage에서 백엔드 `active_roadmap_id`로 이관 (다중 기기 지원)
2. **로드맵 복제**: 기존 로드맵을 복사하여 새로 시작
3. **로드맵 비교**: 두 로드맵의 진행률 비교 뷰
4. **로드맵 아카이브**: 완료된 로드맵 아카이브 분리
5. **대시보드 로드맵 선택**: 대시보드에서 표시할 로드맵을 선택하는 드롭다운
6. **직접 링크/공유**: `/roadmap?id=xxx` 또는 `/roadmap/[id]` 라우트로 특정 로드맵 직접 접근
