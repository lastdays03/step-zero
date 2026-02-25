# Multi-Roadmap - Strategic Plan (v2)

## Executive Summary

현재 팀당 하나의 로드맵만 활용 가능한 구조를 멀티(다중) 로드맵으로 확장한다. **핵심 변경**: `/roadmap` 페이지는 목록이 아니라 **활성 로드맵의 실행 뷰**를 바로 표시하며, Switcher UI로 로드맵을 전환한다. 로드맵이 없을 때만 GenerationPanel을 표시하고, 이미 로드맵이 있는 상태에서 새 로드맵을 추가하는 플로우도 Switcher 내에서 지원한다. 활성 로드맵은 프론트엔드 localStorage로 관리하여 백엔드 변경을 최소화한다.

## Current State

### 제한 사항
1. **백엔드**: `RoadmapRepository.get_latest_for_team()`이 `LIMIT 1`로 최신 로드맵만 반환
2. **대시보드 서비스**: `DashboardService.get_dashboard()`도 `get_latest_for_team()`으로 최신 1건만 참조
3. **프론트엔드**: `RoadmapPage`가 바이너리 상태(`hasRoadmap` true/false)로 동작하며, `GET /roadmaps/latest/detail`만 호출
4. **프론트엔드 대시보드**: `DashboardView`도 `/roadmaps/latest/detail`만 호출하여 현재 단계 추출
5. **로드맵 생성 시 기존 데이터 처리 로직 없음**: 새 로드맵 생성 시 기존 로드맵 유지/삭제에 대한 의사결정 없음
6. **신규 로드맵 추가 플로우 없음**: 이미 로드맵이 있을 때 추가로 새 로드맵을 만드는 경로가 없음

### 이미 지원하는 것
- DB 테이블 구조는 이미 `Roadmap.team_id` FK로 1:N 지원
- `GET /roadmaps/{roadmap_id}/detail` 엔드포인트는 이미 존재
- `RoadmapRepository.get_by_id_for_team()` 메서드 존재
- 소프트 삭제 패턴 (`deleted_at` 필드) 이미 모델에 포함
- shadcn/ui 컴포넌트: `DropdownMenu`, `Dialog`, `Card`, `Progress`, `Badge` 사용 가능

## Proposed Solution

### Architecture

```
[프론트엔드]                           [백엔드]                    [DB]
                                                                (변경 없음)
/roadmap (활성 로드맵 실행 뷰)
  |-- Switcher ------------>  GET  /roadmaps            -------> Roadmap 테이블
  |     |                                                        (이미 1:N)
  |     |-- 전환 ---------->  GET  /roadmaps/{id}/detail (기존)
  |     |-- 삭제 ---------->  DELETE /roadmaps/{id}      (신규)
  |     |-- 이름 변경 ------>  PATCH  /roadmaps/{id}      (신규)
  |     |-- 새로 생성 ------>  POST   /roadmaps/jobs      (기존)
  |
  |-- [활성 로드맵 ID] -----> localStorage 저장
  |-- [없으면] ------------> RoadmapGenerationPanel 표시

활성 로드맵 결정 로직 (프론트엔드):
  1. localStorage에 저장된 active_roadmap_id 확인
  2. 있으면 해당 ID로 상세 조회 (404면 fallback)
  3. 없거나 404면 목록의 첫 번째(최신) 로드맵을 활성으로 설정
  4. 목록도 비어있으면 GenerationPanel 표시
```

### Design Decisions

1. **DB 마이그레이션 없음**: 테이블 구조는 변경 불필요. 활성 로드맵 ID는 프론트엔드 localStorage로 관리.
2. **`/latest/detail` 하위 호환 유지**: 기존 엔드포인트 유지, 대시보드에서도 계속 사용
3. **목록 API 신규 추가**: `GET /roadmaps` - 팀의 전체 로드맵 목록 (페이지네이션, soft-delete 제외)
4. **삭제 API 신규 추가**: `DELETE /roadmaps/{id}` - 소프트 삭제 (deleted_at 갱신)
5. **이름 변경 API 신규 추가**: `PATCH /roadmaps/{id}` - title 변경
6. **활성 로드맵 저장: localStorage** (Decision 6 - 신규, 상세는 context.md 참조)
7. **라우팅: `/roadmap` = 활성 로드맵 실행 뷰** (변경됨)
8. **`/roadmap/[id]` 라우트 불필요** (Decision 8 - 신규, 상세는 context.md 참조)
9. **대시보드**: 기본 표시 로드맵을 "최신 1건" 유지 (멀티로드맵 전환은 로드맵 페이지에서)
10. **신규 로드맵 추가**: Switcher 내 "+ 새 로드맵" 버튼 -> 같은 페이지 내 GenerationPanel 전환 (별도 라우트 불필요)

## Implementation Phases

### Phase 1: Backend API Layer (2-3 days)
**Goal**: 멀티 로드맵을 지원하는 백엔드 API를 완성한다

**Tasks**:
- [ ] 1-1. Repository: `list_for_team()` 메서드 추가 - File: `app-backend/app/repositories/roadmap_repository.py` - Size: S
- [ ] 1-2. Repository: `soft_delete()` 메서드 추가 - File: `app-backend/app/repositories/roadmap_repository.py` - Size: S
- [ ] 1-3. Repository: `update_title()` 메서드 추가 - File: `app-backend/app/repositories/roadmap_repository.py` - Size: S
- [ ] 1-4. Schema: `RoadmapListResponse`, `RoadmapSummaryItem`, `RoadmapUpdateRequest` 추가 - File: `app-backend/app/api/v1/schemas.py` - Size: S
- [ ] 1-5. API: `GET /roadmaps` (목록 조회) 엔드포인트 추가 - File: `app-backend/app/api/v1/roadmaps/get.py` - Size: M
- [ ] 1-6. API: `DELETE /roadmaps/{id}` (소프트 삭제) 엔드포인트 추가 - File: `app-backend/app/api/v1/roadmaps/get.py` - Size: M
- [ ] 1-7. API: `PATCH /roadmaps/{id}` (이름 변경) 엔드포인트 추가 - File: `app-backend/app/api/v1/roadmaps/get.py` - Size: S
- [ ] 1-8. Tests: 목록/삭제/이름변경 API 단위 테스트 - File: `app-backend/tests/api/test_roadmap_multi.py` - Size: M

### Phase 2: Frontend - API Layer & Hooks (1-2 days)
**Goal**: 프론트엔드에서 멀티 로드맵 API를 호출하고 활성 로드맵을 관리할 수 있는 기반을 마련한다

**Tasks**:
- [ ] 2-1. API 타입 추가: `RoadmapSummary`, `RoadmapListResponse` 등 - File: `app-frontend/src/features/roadmap/types/roadmap.ts` - Size: S
- [ ] 2-2. API 함수 추가: `fetchRoadmapList`, `deleteRoadmap`, `updateRoadmapTitle`, `fetchRoadmapDetail` - File: `app-frontend/src/features/roadmap/api/index.ts` - Size: M
- [ ] 2-3. Hook: `useActiveRoadmap` (활성 로드맵 관리 - localStorage 연동) - File: `app-frontend/src/features/roadmap/hooks/useActiveRoadmap.ts` - Size: M
- [ ] 2-4. Hook: `useRoadmapList` (목록 조회, 삭제, 이름 변경) - File: `app-frontend/src/features/roadmap/hooks/useRoadmapList.ts` - Size: M

### Phase 3: Frontend - Switcher UI & 페이지 리팩토링 (3-4 days)
**Goal**: `/roadmap` 페이지에서 활성 로드맵을 바로 보여주고, Switcher로 전환/관리/추가할 수 있도록 한다

**Tasks**:
- [ ] 3-1. RoadmapSwitcher 컴포넌트 (핵심 신규 UI) - File: `app-frontend/src/features/roadmap/components/RoadmapSwitcher.tsx` - Size: L
- [ ] 3-2. 삭제 확인 다이얼로그 - File: `app-frontend/src/features/roadmap/components/RoadmapDeleteDialog.tsx` - Size: S
- [ ] 3-3. 이름 변경 다이얼로그 - File: `app-frontend/src/features/roadmap/components/RoadmapRenameDialog.tsx` - Size: S
- [ ] 3-4. RoadmapHeader 확장 (Switcher 트리거 통합) - File: `app-frontend/src/features/roadmap/components/RoadmapHeader.tsx` - Size: M
- [ ] 3-5. `/roadmap` 페이지 리팩토링 (활성 로드맵 기반) - File: `app-frontend/src/app/(dashboard)/roadmap/page.tsx` - Size: XL
- [ ] 3-6. Feature exports 업데이트 - File: `app-frontend/src/features/roadmap/components/index.ts`, `hooks/index.ts` - Size: S

### Phase 4: Dashboard 연동 & 생성 플로우 정비 (1-2 days)
**Goal**: 대시보드와 기존 흐름이 멀티 로드맵 환경에서 정상 동작하고, 신규 로드맵 추가 플로우가 완성되도록 한다

**Tasks**:
- [ ] 4-1. RoadmapStepper "전체 계획 보기" 링크 확인/수정 - File: `app-frontend/src/features/dashboard/components/RoadmapStepper.tsx` - Size: S
- [ ] 4-2. DashboardView 생성 후 이동 로직 수정 - File: `app-frontend/src/features/dashboard/components/DashboardView.tsx` - Size: M
- [ ] 4-3. RoadmapGenerationPanel `onGenerated` 콜백 정비 - File: `app-frontend/src/features/roadmap/components/RoadmapGenerationPanel.tsx` - Size: M
- [ ] 4-4. 신규 로드맵 추가 플로우 통합 (Switcher -> GenerationPanel 전환) - File: `app-frontend/src/app/(dashboard)/roadmap/page.tsx` - Size: M

### Phase 5: QA & Polish (1 day)
**Goal**: 전체 흐름 통합 테스트 및 엣지 케이스 처리

**Tasks**:
- [ ] 5-1. 통합 테스트: 전체 플로우 (생성/전환/삭제/이름변경/추가) - Size: M
- [ ] 5-2. 엣지 케이스: 마지막 로드맵 삭제 시 빈 상태 전환 - Size: S
- [ ] 5-3. 엣지 케이스: localStorage의 활성 ID가 삭제된 로드맵인 경우 - Size: S
- [ ] 5-4. 엣지 케이스: 생성 중 취소 -> 이전 활성 로드맵으로 복귀 - Size: S
- [ ] 5-5. 로딩/에러 상태 UX 점검 - Size: S
- [ ] 5-6. 기존 테스트 회귀 확인 (63건 + 프론트 타입체크) - Size: S

## Risk Assessment

### High Risk
- **기존 대시보드/로드맵 페이지 회귀**: 현재 `latest/detail`에 의존하는 코드가 DashboardView와 RoadmapPage 양쪽에 존재
  - **Mitigation**: `/latest/detail` 엔드포인트는 변경하지 않고 유지. 대시보드는 계속 latest 사용. RoadmapPage만 활성 로드맵 기반으로 전환.

### Medium Risk
- **localStorage 활성 ID와 서버 상태 불일치**: 삭제된 로드맵 ID가 localStorage에 남아있는 경우
  - **Mitigation**: `fetchRoadmapDetail`이 404를 반환하면 localStorage를 클리어하고 목록의 첫 번째 로드맵으로 fallback.
- **로드맵 생성 플로우 UX 복잡도 증가**: 기존에는 생성 후 즉시 표시. 멀티에서는 Switcher + 생성 모드 전환이 필요
  - **Mitigation**: 생성 완료 후 자동으로 새 로드맵을 활성으로 설정. 생성 취소 시 이전 활성 로드맵으로 복귀.
- **Switcher UI 성능**: 로드맵 수가 많아지면 드롭다운 성능 우려
  - **Mitigation**: 현실적으로 팀당 로드맵은 10개 미만 예상. 필요시 가상 스크롤 적용.

### Low Risk
- **DB 성능**: 팀당 로드맵 수가 증가하면 목록 쿼리 성능 우려
  - **Mitigation**: `team_id`와 `created_at`에 이미 인덱스 존재. 페이지네이션 적용.

## Success Metrics

- 기존 테스트 63건 모두 통과 (회귀 없음)
- `/roadmap` 접근 시 활성 로드맵 실행 뷰가 바로 표시됨
- Switcher를 통한 로드맵 전환, 삭제, 이름 변경 정상 동작
- 이미 로드맵이 있는 상태에서 Switcher를 통해 새 로드맵 생성 가능
- 생성 완료 후 새 로드맵이 자동으로 활성 로드맵으로 설정됨
- 생성 취소 시 이전 활성 로드맵으로 복귀
- 대시보드는 최신 로드맵 기준으로 기존과 동일하게 동작
- 새 API 엔드포인트 테스트 커버리지 확보

## Dependencies

- **코드 의존성**: Phase 1 (Backend) -> Phase 2 (Frontend API/Hooks) -> Phase 3 (UI) -> Phase 4 (연동)
- **외부 의존성**: 없음 (DB 마이그레이션 불필요)

## Timeline

| Phase | 내용 | 예상 기간 |
|-------|------|-----------|
| Phase 1 | Backend API Layer | 2-3일 |
| Phase 2 | Frontend API & Hooks | 1-2일 |
| Phase 3 | Switcher UI & 페이지 리팩토링 | 3-4일 |
| Phase 4 | Dashboard 연동 & 생성 플로우 | 1-2일 |
| Phase 5 | QA & Polish | 1일 |
| **Total** | | **8-12일** |

## v1 -> v2 변경 요약

### 삭제된 항목
- `/roadmap` 목록 페이지 UI (RoadmapCard 그리드, RoadmapListView)
- `/roadmap/[id]` 동적 라우트 상세 페이지
- `useRoadmapDetail` 훅 (활성 로드맵 관리로 대체)
- RoadmapHeader "목록 돌아가기" 버튼

### 추가된 항목
- **RoadmapSwitcher** 컴포넌트 (드롭다운/패널 형태의 로드맵 전환 UI)
- **useActiveRoadmap** 훅 (localStorage 기반 활성 로드맵 관리)
- **신규 로드맵 추가 플로우** (Switcher -> GenerationPanel 전환 -> 자동 활성화)
- **활성 로드맵 저장 방식 Design Decision** (localStorage vs 백엔드)
- **생성 취소 시 복귀 로직**

### 변경된 항목
- `/roadmap` 페이지: 목록 뷰 -> 활성 로드맵 실행 뷰 + Switcher
- RoadmapHeader: Switcher 트리거 버튼 통합
- Phase 3: 목록 페이지 UI -> Switcher UI & 페이지 리팩토링
- Phase 4: 신규 로드맵 추가 플로우 태스크 추가
