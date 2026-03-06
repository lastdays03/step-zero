# Tasks: 메인 대시보드 정리 및 품질 개선

Last Updated: 2026-03-06 — ALL PHASES COMPLETE

## Phase 1: 미사용 소스 정리 [Effort: S] — DONE (이전 세션)

- [x] 1.1 `StatsGrid.tsx` 삭제
- [x] 1.2 `mocks/dashboardMock.ts` 삭제
- [x] 1.3 `api/index.ts` 삭제
- [x] 1.4 `types/index.ts` 삭제
- [x] 1.5 빌드/린트/테스트 검증

---

## Phase 2: 중복 코드 제거 [Effort: L] — DONE

- [x] 2.1 `#36a4f2` → 디자인 토큰 통일
  - dashboard/ 내 #36a4f2 = 0건 (이전 세션에서 이미 제거됨)
  - AC: Grep `#36a4f2` in dashboard/ = 0건 ✓

- [x] 2.2 카드 스타일 상수 추출
  - `GLASS_CARD` 상수로 추출 (DashboardView.tsx:17)

- [x] 2.3 네비게이션 메뉴 설정 공유
  - `features/dashboard/config/nav-config.ts` 생성
  - Sidebar.tsx, MobileNav.tsx에서 `getNavItems()` import

- [x] 2.4 `AccountMenu` 공통 컴포넌트 추출
  - `features/dashboard/components/AccountMenu.tsx` 생성 (variant: desktop/mobile)
  - Sidebar, MobileNav에서 사용

- [x] 2.5 `SocialAuthModal` 단일화
  - `features/dashboard/providers/AuthModalProvider.tsx` 생성
  - layout.tsx에 `<AuthModalProvider>` 래핑 + 단일 `<SocialAuthModal>`
  - ColdStartHero, AuthGuard, Sidebar, MobileNav — 4곳 모두 `useAuthModal()` 전환

- [x] 2.6 빌드/린트/테스트 검증
  - `pnpm lint` 통과, `pnpm test` 133 passed, `pytest` 406 passed

---

## Phase 3: P0 버그 수정 [Effort: S] — DONE

- [x] 3.1 ProgressCard: window.location.href → router.push
  - `useRouter` + `router.push("/roadmap")` 적용

- [x] 3.2 activeRoadmapId 갱신 로직 추가
  - `storage` 이벤트 리스너로 localStorage 변경 감지 → `setActiveRoadmapId` 호출

- [x] 3.3 테스트 검증 — lint/test 통과

---

## Phase 4: P1 UX 개선 [Effort: M] — DONE

- [x] 4.1 Header 시간대별 인사말
  - `getGreeting()` 함수 추가 (06-12/12-18/18+ 분기)
  - 부제: "오늘도 한 걸음 더 나아가 봅시다." 고정 문구

- [x] 4.2 스켈레톤 로딩 UI
  - DashboardView.tsx:200-210 — animate-pulse 스켈레톤 카드 6개 영역 구현

- [x] 4.3 ColdStartHero 입력 영역 명확화
  - 전체 CTA 영역을 `<button>`으로 감싸서 클릭 가능하게 구현

- [x] 4.4 md 브레이크포인트 그리드 수정
  - md:grid-cols-4로 통일, col-span 합계 일치 (3+1, 4, 2+1+1)

- [x] 4.5 테스트/브라우저 검증
  - lint/test 통과

---

## Phase 5: P2 품질/보안 [Effort: M] — DONE

- [x] 5.1 백엔드 DashboardResult 타입 개선
  - `CurrentPhaseResult`, `DashboardStatsResult`, `GrowthClubResult`, `RoadmapItemResult` dataclass 생성
  - `stats.py`에서 `__dict__` → `asdict()` 변환

- [x] 5.2 게스트 데이터 이중 정의 해소
  - GUEST_DASHBOARD_DATA 삭제, BE API가 게스트 데이터 제공
  - 에러 시 최소 폴백 (FALLBACK_CURRENT_PHASE + 빈 roadmap/stats)

- [x] 5.3 테스트 mock status 소문자 통일
  - Dashboard.test.tsx: "COMPLETED"→"completed", "CURRENT"→"current", "LOCKED"→"locked"

- [x] 5.4 다운로드 URL 프로토콜 검증
  - DashboardView.tsx:181 — isSafe 검증 (https/http/상대경로만 허용)

- [x] 5.5 백엔드 테스트 + 프론트 테스트 검증
  - BE: 406 passed, 10 skipped / FE: 133 passed, lint 통과
