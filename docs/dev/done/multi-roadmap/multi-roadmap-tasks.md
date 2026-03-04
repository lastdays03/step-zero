# Multi-Roadmap - Task Checklist (v2)

## Status Legend
- [x] Complete
- [x] Complete (use when marking done)

## Progress Summary
25 / 25 tasks complete (100%) — **완료됨 (2026-02-25)**

## v1 -> v2 변경 요약
- **삭제**: RoadmapCard, RoadmapListView, `/roadmap/[id]` 상세 페이지, useRoadmapDetail, RoadmapHeader "목록 돌아가기"
- **추가**: RoadmapSwitcher, useActiveRoadmap, 신규 로드맵 추가 플로우, 생성 취소 복귀 로직
- **변경**: `/roadmap` 페이지 목록->활성 뷰, RoadmapHeader Switcher 트리거, Phase 구조 재편

---

## Phase 1: Backend API Layer (2-3 days)

### 1-1. Repository: `list_for_team()` 메서드 추가
- File: `app-backend/app/repositories/roadmap_repository.py`
- Details:
  - `list_for_team(team_id: UUID, offset: int = 0, limit: int = 20) -> tuple[list[Roadmap], int]`
  - `deleted_at IS NULL` 필터, `created_at DESC` 정렬
  - 총 건수(count)도 함께 반환 (페이지네이션용)
- Acceptance: 메서드 단독 테스트에서 정상 동작
- Size: S
- Dependencies: 없음
- [x] Complete

### 1-2. Repository: `soft_delete()` 메서드 추가
- File: `app-backend/app/repositories/roadmap_repository.py`
- Details:
  - `soft_delete(roadmap_id: UUID, team_id: UUID) -> bool`
  - `get_by_id_for_team()`으로 존재 확인 후 `deleted_at = datetime.utcnow()` 설정
  - 존재하지 않으면 `False` 반환
- Acceptance: 삭제 후 `get_by_id_for_team()`에서 None 반환
- Size: S
- Dependencies: 없음
- [x] Complete

### 1-3. Repository: `update_title()` 메서드 추가
- File: `app-backend/app/repositories/roadmap_repository.py`
- Details:
  - `update_title(roadmap_id: UUID, team_id: UUID, new_title: str) -> Roadmap | None`
  - `get_by_id_for_team()`으로 존재 확인 후 `title`, `updated_at` 갱신
- Acceptance: 업데이트 후 재조회 시 새 제목 반환
- Size: S
- Dependencies: 없음
- [x] Complete

### 1-4. Schema: Response/Request 모델 추가
- File: `app-backend/app/api/v1/schemas.py`
- Details:
  ```python
  class RoadmapSummaryItem(BaseModel):
      roadmap_id: UUID
      title: str
      business_type: str
      location: str
      created_at: str
      progress: int          # 0~100
      total_steps: int
      completed_steps: int

  class RoadmapListResponse(BaseModel):
      items: list[RoadmapSummaryItem]
      total: int

  class RoadmapUpdateRequest(BaseModel):
      title: str = Field(min_length=1, max_length=200)
  ```
- Acceptance: Pydantic 직렬화/역직렬화 정상 동작
- Size: S
- Dependencies: 없음
- [x] Complete

### 1-5. API: `GET /roadmaps` 목록 조회 엔드포인트
- File: `app-backend/app/api/v1/roadmaps/get.py`
- Details:
  - 쿼리 파라미터: `offset: int = 0`, `limit: int = 20`
  - `RoadmapRepository.list_for_team()` 호출
  - 각 로드맵의 step 진행률 계산 (completed/total)
  - `RoadmapListResponse` 반환
- Acceptance: 멀티 로드맵 팀에서 전체 목록 정상 반환, soft-delete 항목 제외
- Size: M
- Dependencies: 1-1, 1-4
- [x] Complete

### 1-6. API: `DELETE /roadmaps/{id}` 소프트 삭제 엔드포인트
- File: `app-backend/app/api/v1/roadmaps/get.py`
- Details:
  - `RoadmapRepository.soft_delete()` 호출
  - 성공: `204 No Content`
  - 실패 (not found): `404`
  - `commit()` 호출 필요
- Acceptance: 삭제 후 목록에서 사라지고, `GET /roadmaps/{id}` 시 404
- Size: M
- Dependencies: 1-2
- [x] Complete

### 1-7. API: `PATCH /roadmaps/{id}` 이름 변경 엔드포인트
- File: `app-backend/app/api/v1/roadmaps/get.py`
- Details:
  - Request Body: `RoadmapUpdateRequest` (`title` 필드)
  - `RoadmapRepository.update_title()` 호출
  - 성공: `{ "roadmap_id": ..., "title": ... }` 반환
  - 실패: `404`
  - `commit()` 호출 필요
  - **주의**: 기존 `PATCH /roadmaps/tasks/{step_id}` 라우트와 충돌하지 않도록 순서 배치
    - `{roadmap_id}`는 UUID 형식이므로 FastAPI가 자동 구분하나, 라우터 등록 순서를 확인할 것
- Acceptance: 이름 변경 후 재조회 시 새 제목 반영
- Size: S
- Dependencies: 1-3, 1-4
- [x] Complete

### 1-8. Tests: 멀티 로드맵 API 테스트
- File: `app-backend/tests/api/test_roadmap_multi.py`
- Details:
  - `test_list_roadmaps_empty` - 빈 목록 반환
  - `test_list_roadmaps_multiple` - 복수 생성 후 목록 확인 (최신순 정렬)
  - `test_list_roadmaps_excludes_deleted` - soft-delete 제외
  - `test_list_roadmaps_pagination` - offset/limit 동작
  - `test_delete_roadmap_success` - 삭제 후 204 반환
  - `test_delete_roadmap_not_found` - 404 반환
  - `test_update_title_success` - 제목 변경 성공
  - `test_update_title_not_found` - 404 반환
  - `test_update_title_empty` - 빈 문자열 시 422 반환
- Acceptance: 모든 테스트 PASSED
- Size: M
- Dependencies: 1-5, 1-6, 1-7
- [x] Complete

---

## Phase 2: Frontend - API Layer & Hooks (1-2 days)

### 2-1. API 타입 추가
- File: `app-frontend/src/features/roadmap/types/roadmap.ts`
- Details:
  ```typescript
  export interface RoadmapSummary {
      roadmap_id: string;
      title: string;
      business_type: string;
      location: string;
      created_at: string;
      progress: number;       // 0~100
      total_steps: number;
      completed_steps: number;
  }

  export interface RoadmapListResponse {
      items: RoadmapSummary[];
      total: number;
  }
  ```
- Acceptance: 타입 컴파일 통과 (`npx tsc --noEmit`)
- Size: S
- Dependencies: Phase 1 완료
- [x] Complete

### 2-2. API 함수 추가
- File: `app-frontend/src/features/roadmap/api/index.ts`
- Details:
  ```typescript
  export async function fetchRoadmapList(offset?: number, limit?: number): Promise<RoadmapListResponse>
  export async function deleteRoadmap(roadmapId: string): Promise<void>
  export async function updateRoadmapTitle(roadmapId: string, title: string): Promise<{ roadmap_id: string; title: string }>
  export async function fetchRoadmapDetail(roadmapId: string): Promise<RoadmapDetailResponse>
  ```
  - 모두 `apiClient` 사용
- Acceptance: 타입 컴파일 통과
- Size: M
- Dependencies: 2-1
- [x] Complete

### 2-3. Hook: `useActiveRoadmap`
- File: `app-frontend/src/features/roadmap/hooks/useActiveRoadmap.ts`
- Details:
  - localStorage key: `stepzero_active_roadmap_id`
  - 마운트 시 localStorage에서 ID 로드 -> 상세 조회
  - 404 fallback: localStorage 클리어, null 반환
  - `setActiveRoadmap(id)`: localStorage 저장 + 상세 로드
  - `clearActiveRoadmap()`: localStorage 삭제 + 상태 초기화
  - `reloadActiveRoadmap()`: 현재 ID로 재조회
  - 반환 타입: `UseActiveRoadmapReturn` (context.md 참조)
- Acceptance: localStorage 연동, 상세 로드, fallback 동작 확인
- Size: M
- Dependencies: 2-2
- [x] Complete

### 2-4. Hook: `useRoadmapList`
- File: `app-frontend/src/features/roadmap/hooks/useRoadmapList.ts`
- Details:
  - `list`: `RoadmapSummary[]` 상태
  - `total`: 전체 건수
  - `loading`, `error` 상태
  - `loadList()`: API 호출
  - `handleDelete(id)`: 삭제 API 호출 + 목록 갱신
  - `handleRename(id, newTitle)`: 이름 변경 API 호출 + 목록 갱신
- Acceptance: Hook 정상 동작 (목록 로드, 삭제, 이름 변경)
- Size: M
- Dependencies: 2-2
- [x] Complete

---

## Phase 3: Frontend - Switcher UI & 페이지 리팩토링 (3-4 days)

### 3-1. RoadmapSwitcher 컴포넌트 (핵심 신규 UI)
- File: `app-frontend/src/features/roadmap/components/RoadmapSwitcher.tsx`
- Details:
  - Props: `RoadmapSwitcherProps` (context.md 참조)
  - **패널 구조**:
    - 헤더: "나의 로드맵" + 개수 badge
    - 로드맵 아이템 목록 (스크롤 가능, max-h 제한)
      - 각 아이템: 활성 체크 아이콘 + 제목 + 업종|지역 + 진행률 바 + 더보기 메뉴
      - 활성 로드맵: 배경 하이라이트
      - 클릭 -> `onSelect` 호출
      - 더보기 -> 이름 변경, 삭제
    - Separator
    - "+ 새 로드맵 만들기" 버튼 -> `onCreateNew` 호출
  - shadcn/ui: `DropdownMenu`, `Progress`, `Badge`, `Separator`
  - lucide-react: `Check`, `MoreHorizontal`, `Pencil`, `Trash2`, `Plus`, `MapPin`, `Briefcase`
- Acceptance: 패널 열기/닫기, 아이템 표시, 전환/삭제/이름변경/생성 이벤트 정상 발생
- Size: L
- Dependencies: 2-1
- [x] Complete

### 3-2. RoadmapDeleteDialog
- File: `app-frontend/src/features/roadmap/components/RoadmapDeleteDialog.tsx`
- Details:
  - Props: `open: boolean`, `roadmapTitle: string`, `onConfirm`, `onCancel`
  - shadcn/ui `Dialog` 사용 (AlertDialog 미설치, Dialog로 구현)
  - 경고 문구: "'{title}' 로드맵을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다."
  - 확인(빨간색)/취소 버튼
  - 활성 로드맵 삭제 시 추가 안내: "현재 보고 있는 로드맵입니다."
- Acceptance: 다이얼로그 열기/닫기 정상, 확인 시 콜백 호출
- Size: S
- Dependencies: 없음
- [x] Complete

### 3-3. RoadmapRenameDialog
- File: `app-frontend/src/features/roadmap/components/RoadmapRenameDialog.tsx`
- Details:
  - Props: `open: boolean`, `currentTitle: string`, `onConfirm(newTitle)`, `onCancel`
  - shadcn/ui `Dialog` 사용
  - 제목 입력 필드 (기존 제목으로 pre-fill)
  - 빈 문자열 방지 유효성 검사
  - 확인/취소 버튼
- Acceptance: 다이얼로그 열기/닫기, 입력/제출 정상
- Size: S
- Dependencies: 없음
- [x] Complete

### 3-4. RoadmapHeader 확장 (Switcher 트리거 통합)
- File: `app-frontend/src/features/roadmap/components/RoadmapHeader.tsx`
- Details:
  - **기존 Props 유지**: `title`, `currentPhaseName`
  - **새 Props 추가**:
    - `onSwitcherToggle?: () => void` - Switcher 열기/닫기 트리거
    - `roadmapCount?: number` - 전체 로드맵 개수 (badge 표시용)
  - **UI 변경**:
    - 제목 "나의 로드맵" 옆에 Switcher 트리거 버튼 추가
    - 버튼: `ChevronDown` 아이콘 + 로드맵 개수 badge
    - 클릭 시 `onSwitcherToggle` 호출
  - `onSwitcherToggle`이 없으면 (대시보드 등에서 사용 시) 버튼 숨김
- Acceptance: 트리거 버튼 표시/클릭 동작, 기존 동작 유지 (하위 호환)
- Size: M
- Dependencies: 없음
- [x] Complete

### 3-5. `/roadmap` 페이지 리팩토링 (활성 로드맵 기반) - 핵심 태스크
- File: `app-frontend/src/app/(dashboard)/roadmap/page.tsx`
- Details:
  - **기존 로직 제거**:
    - `loadLatestRoadmapDetail()` 제거
    - 바이너리 `hasRoadmap` 상태 제거
    - 대시보드 API (`/dashboard`) 호출로 로드맵 유무 판단하는 로직 제거
  - **새 로직 - 4가지 상태 관리**:
    ```typescript
    type PageMode = 'loading' | 'empty' | 'viewing' | 'creating';
    ```
    1. **loading**: 초기 로드 (목록 조회 + 활성 로드맵 조회)
    2. **empty**: 로드맵 0개 -> `RoadmapGenerationPanel` 표시
    3. **viewing**: 활성 로드맵 실행 뷰 (`RoadmapExecutionView`) + Switcher
    4. **creating**: 새 로드맵 생성 모드 -> `RoadmapGenerationPanel` + 취소 버튼
  - **초기 로드 플로우**:
    1. `useRoadmapList()`로 목록 로드
    2. `useActiveRoadmap()`으로 활성 로드맵 로드
    3. 목록 비어있음 -> `empty` 모드
    4. 활성 로드맵 있음 -> `viewing` 모드
    5. 활성 로드맵 없음 (localStorage 없거나 404) -> 목록 첫 번째를 활성으로 설정 -> `viewing`
  - **이벤트 핸들러**:
    - Switcher 로드맵 선택 -> `setActiveRoadmap(id)`, `viewing` 유지
    - Switcher 삭제 -> `handleDelete(id)`, 활성 로드맵이면 다음 로드맵으로 전환
    - Switcher 이름 변경 -> `handleRename(id, title)`, 목록 갱신
    - Switcher "+ 새 로드맵" -> `creating` 모드 전환
    - GenerationPanel 생성 완료 -> `setActiveRoadmap(newId)`, `viewing` 전환
    - GenerationPanel 취소 -> `viewing` 모드 복귀
    - step/action 상태 변경 -> 기존 `PATCH` 호출 + `reloadActiveRoadmap()`
  - **`creating` 모드에서**:
    - 상단에 "< 로드맵으로 돌아가기" 링크
    - `RoadmapGenerationPanel` 렌더링
    - `onGenerated` 콜백: 새 roadmap_id를 활성으로 설정, 목록 갱신, `viewing` 전환
    - `onCancel` 콜백 (취소 또는 링크 클릭): `viewing` 복귀
- Acceptance: 전체 상태 전환 정상 동작, 기존 step/action 변경 동작 유지
- Size: XL
- Dependencies: 2-3, 2-4, 3-1, 3-2, 3-3, 3-4
- [x] Complete

### 3-6. Feature exports 업데이트
- File: `app-frontend/src/features/roadmap/components/index.ts`
- Details:
  - 새 컴포넌트 export: `RoadmapSwitcher`, `RoadmapDeleteDialog`, `RoadmapRenameDialog`
- File: `app-frontend/src/features/roadmap/hooks/index.ts`
- Details:
  - 새 훅 export: `useActiveRoadmap`, `useRoadmapList`
- Acceptance: 외부에서 import 가능
- Size: S
- Dependencies: 3-1 ~ 3-5
- [x] Complete

---

## Phase 4: Dashboard 연동 & 생성 플로우 정비 (1-2 days)

### 4-1. RoadmapStepper "전체 계획 보기" 링크 확인/수정
- File: `app-frontend/src/features/dashboard/components/RoadmapStepper.tsx`
- Details:
  - 현재: `window.location.href = "/roadmap"` -> `/roadmap`으로 이동
  - v2에서 `/roadmap`은 활성 로드맵 뷰이므로 **변경 불필요** (이미 올바른 대상)
  - 개선 사항: `window.location.href` -> `next/navigation`의 `useRouter().push()` 로 SPA 전환 전환
- Acceptance: 클릭 시 `/roadmap` 활성 로드맵 뷰로 정상 이동
- Size: S
- Dependencies: 3-5
- [x] Complete

### 4-2. DashboardView 생성 후 이동 로직 수정
- File: `app-frontend/src/features/dashboard/components/DashboardView.tsx`
- Details:
  - 현재: `onGenerated={() => void reload()}` -> 생성 완료 시 대시보드 리로드
  - 변경: 생성 완료 시 `router.push("/roadmap")` 로 로드맵 페이지 이동
    - 새 로드맵의 ID를 `localStorage`에 활성으로 저장 후 이동
  - `onGenerated` 콜백에서 `roadmapId`를 받아야 함
  - `useRouter()` import 추가
  - localStorage에 `stepzero_active_roadmap_id` 저장 후 `/roadmap`으로 이동하면 자동으로 해당 로드맵 표시
- Acceptance: 대시보드에서 로드맵 생성 후 `/roadmap` 페이지에서 해당 로드맵 바로 표시
- Size: M
- Dependencies: 3-5
- [x] Complete

### 4-3. RoadmapGenerationPanel `onGenerated` 콜백 정비
- File: `app-frontend/src/features/roadmap/components/RoadmapGenerationPanel.tsx`
- Details:
  - 기존 `onGenerated` 시그니처: `(roadmapId: string | number) => Promise<void> | void` -- 유지
  - **새 prop 추가**: `onCancel?: () => void`
    - `creating` 모드에서 취소 시 호출
    - RoadmapChatIntake의 적절한 위치에 취소 버튼 연동 또는 page.tsx에서 직접 처리
  - `/roadmap` 페이지에서 사용:
    - `onGenerated` -> 새 활성 로드맵 설정 + `viewing` 전환
    - `onCancel` -> `viewing` 복귀
  - 대시보드에서 사용:
    - `onGenerated` -> localStorage 저장 + `/roadmap` 이동
    - `onCancel` -> 미사용 (대시보드에서는 생성이 기본 상태)
- Acceptance: 콜백 정상 동작, 하위 호환 유지
- Size: M
- Dependencies: 3-5
- [x] Complete

### 4-4. 신규 로드맵 추가 플로우 통합
- File: `app-frontend/src/app/(dashboard)/roadmap/page.tsx`
- Details:
  - 3-5에서 기본 구조는 완성됨. 이 태스크는 통합/정교화:
  - **생성 완료 후 처리**:
    1. `onGenerated(roadmapId)` 호출됨
    2. `setActiveRoadmap(roadmapId)` -> localStorage 저장 + 상세 로드
    3. `loadList()` -> 목록 갱신 (새 로드맵 포함)
    4. `pageMode = 'viewing'` 전환
  - **생성 취소 처리**:
    1. "< 로드맵으로 돌아가기" 클릭 또는 `onCancel`
    2. 이전 활성 로드맵이 있으면 -> `viewing` 전환 (이전 데이터 그대로)
    3. 이전 활성 로드맵이 없으면 -> `empty` 전환 (이 경우는 드물음)
  - **생성 중 Switcher**:
    - `creating` 모드에서도 Switcher 접근 가능하게 할지? -> 아니요, creating 모드에서는 숨김
  - **엣지 케이스**: 생성 중 다른 탭에서 로드맵 삭제 -> 무시 (실시간 동기화 불필요)
- Acceptance: 생성 완료/취소 전체 플로우 정상 동작
- Size: M
- Dependencies: 3-5, 4-3
- [x] Complete

---

## Phase 5: QA & Polish (1 day)

### 5-1. 통합 테스트: 전체 플로우
- Details:
  - 시나리오 A: 최초 사용자 -> 로드맵 0개 -> GenerationPanel -> 생성 -> 활성 로드맵 실행 뷰 표시
  - 시나리오 B: 로드맵 1개 있는 상태 -> Switcher -> "+ 새 로드맵" -> 생성 -> 새 로드맵이 활성으로
  - 시나리오 C: 로드맵 2개 -> Switcher에서 다른 로드맵 선택 -> 전환 정상
  - 시나리오 D: Switcher에서 이름 변경 -> Switcher 목록에 반영 + Header 제목 반영
  - 시나리오 E: 비활성 로드맵 삭제 -> 목록에서 사라짐, 활성 로드맵 유지
  - 시나리오 F: 활성 로드맵 삭제 -> 다음 로드맵이 활성으로 전환
  - 시나리오 G: 대시보드 -> ProgressCard -> 최신 로드맵 기준 정상 표시
  - 시나리오 H: 대시보드에서 생성 -> `/roadmap`으로 이동 -> 새 로드맵 표시
- Acceptance: 전체 플로우 정상 동작
- Size: M
- Dependencies: Phase 1-4 모두 완료
- [x] Complete

### 5-2. 엣지 케이스: 마지막 로드맵 삭제
- Details:
  - 로드맵 1개 -> Switcher에서 삭제 -> 빈 상태 -> RoadmapGenerationPanel 표시
  - localStorage의 활성 ID도 클리어됨
  - 대시보드: 최신 로드맵 없으므로 "READY" 상태 표시
- Acceptance: 정상 전환
- Size: S
- Dependencies: 5-1
- [x] Complete

### 5-3. 엣지 케이스: localStorage의 활성 ID가 삭제된 로드맵인 경우
- Details:
  - localStorage에 `stepzero_active_roadmap_id = "deleted-uuid"` 저장됨
  - `/roadmap` 접근 시 `GET /roadmaps/{deleted-uuid}/detail` -> 404
  - `useActiveRoadmap`이 localStorage 클리어
  - `useRoadmapList`의 첫 번째 로드맵을 활성으로 설정
  - 목록도 비어있으면 `empty` 모드
- Acceptance: 404 시 자동 fallback, 사용자에게 에러 메시지 없이 자연스러운 전환
- Size: S
- Dependencies: 2-3
- [x] Complete

### 5-4. 엣지 케이스: 생성 중 취소
- Details:
  - `creating` 모드에서 "< 로드맵으로 돌아가기" 클릭
  - 이전 활성 로드맵으로 즉시 복귀 (재조회 불필요, 기존 데이터 유지)
  - 폴링 중이었다면 폴링 중단 (`RoadmapGenerationPanel` 내부 cleanup)
- Acceptance: 취소 시 이전 활성 로드맵 정상 표시, 폴링 정리
- Size: S
- Dependencies: 4-4
- [x] Complete

### 5-5. 로딩/에러 상태 UX 점검
- Details:
  - 초기 로딩: 목록 + 활성 로드맵 로딩 스피너 또는 스켈레톤
  - Switcher 내 로드맵 전환: 실행 뷰 로딩 상태
  - 삭제/이름 변경 중: 버튼 disabled + 로딩 표시
  - API 에러: 재시도 버튼 또는 에러 메시지
- Acceptance: 모든 비동기 상태에 적절한 UI 피드백
- Size: S
- Dependencies: 3-5
- [x] Complete

### 5-6. 기존 테스트 회귀 확인
- Details:
  - 백엔드: `pytest` 전체 실행 (63건 + 새 테스트)
  - 프론트엔드: `npx tsc --noEmit` 타입 체크
  - 프론트엔드: `RoadmapRenderer.test.tsx` 등 기존 테스트 통과
- Acceptance: 전체 PASSED, 타입 에러 0건
- Size: S
- Dependencies: 전체
- [x] Complete

---

## Deployment Checklist

- [ ] Database migrations: **불필요** (스키마 변경 없음, 활성 로드맵은 localStorage)
- [ ] Environment variables: 추가 없음
- [ ] Backend tests passing (`pytest`)
- [ ] Frontend type check passing (`npx tsc --noEmit`)
- [ ] Existing tests passing (63건 회귀)
- [ ] New tests passing
- [ ] Documentation updated (이 문서)

## Notes

- **라우트 충돌 주의**: `PATCH /roadmaps/{roadmap_id}`와 `PATCH /roadmaps/tasks/{step_id}` 경로 구분 필요. `roadmap_id`는 UUID 형식이므로 FastAPI가 자동 구분하나, 라우터 등록 순서를 확인할 것.
- **`api-types.ts` 자동 생성 주의**: 이 파일은 `AUTO-GENERATED FILE`로 OpenAPI에서 생성됨. 수동 변경하면 다음 생성 시 덮어씌워짐. 새 타입은 `features/roadmap/types/roadmap.ts`에 추가.
- **RoadmapGenerationPanel 취소 처리**: `onCancel` prop 추가 시 `RoadmapChatIntake`에도 취소 버튼이 필요할 수 있음. 또는 page.tsx에서 상단 "< 돌아가기" 링크로 처리하여 `RoadmapGenerationPanel` 변경을 최소화.
- **Switcher vs Popover**: shadcn/ui의 `DropdownMenu`는 기본적으로 메뉴 아이템 방식. 복잡한 레이아웃(진행률 바 등)이 필요하면 `Popover` 컴포넌트가 더 적합할 수 있음. `Popover`가 미설치 상태이면 `npx shadcn@latest add popover`로 추가 필요. 또는 `DropdownMenu`의 custom content로 구현.
