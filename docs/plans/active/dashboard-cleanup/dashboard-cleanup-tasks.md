# Tasks: 메인 대시보드 정리 및 품질 개선

Last Updated: 2026-03-06

## Phase 1: 미사용 소스 정리 [Effort: S] — DONE (이전 세션)

- [x] 1.1 `StatsGrid.tsx` 삭제
- [x] 1.2 `mocks/dashboardMock.ts` 삭제
- [x] 1.3 `api/index.ts` 삭제
- [x] 1.4 `types/index.ts` 삭제
- [x] 1.5 빌드/린트/테스트 검증

---

## Phase 2: 중복 코드 제거 [Effort: L]

- [ ] 2.1 `#36a4f2` → 디자인 토큰 통일
  - **주의: primary=#257bf4 ≠ #36a4f2 — 단순 `primary` 교체 불가**
  - 사전: 디자인 의도 확인 후 방안 결정 (미결정)
  - AC: Grep `#36a4f2` in dashboard/ = 0건
  - 통일로 결정

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

- [ ] 2.6 빌드/린트/테스트 검증 — **미실행**
  - `pnpm lint` / `pnpm test` 미확인
  - 브라우저 테스트 미확인

---

## Phase 3: P0 버그 수정 [Effort: S]

- [x] 3.1 ProgressCard: window.location.href → router.push
  - `useRouter` + `router.push("/roadmap")` 적용

- [x] 3.2 activeRoadmapId 갱신 로직 추가
  - `storage` 이벤트 리스너로 localStorage 변경 감지 → `setActiveRoadmapId` 호출

- [ ] 3.3 테스트 검증 — **미실행**

---

## Phase 4: P1 UX 개선 [Effort: M]

- [x] 4.1 Header 시간대별 인사말
  - `getGreeting()` 함수 추가 (06-12/12-18/18+ 분기)
  - 부제: "오늘도 한 걸음 더 나아가 봅시다." 고정 문구

- [ ] 4.2 스켈레톤 로딩 UI
  - `DashboardView.tsx:175-177` — "Loading..." 텍스트
  - 6개 위젯 영역에 맞는 스켈레톤 카드 렌더링
  - Tailwind `animate-pulse` + 위젯별 대략적 크기
  - AC: 로딩 중 레이아웃 shift 없음, 스켈레톤 표시

- [ ] 4.3 ColdStartHero 입력 영역 명확화
  - `ColdStartHero.tsx:58-62` — `<span>` → 전체 영역 클릭 가능하게
  - 옵션 A: 전체 박스를 button으로 감싸기 (현재 의도에 가까움)
  - 옵션 B: 실제 input으로 변경 + 입력값을 /roadmap에 쿼리스트링 전달
  - AC: 사용자가 플레이스홀더 영역 클릭 시 동작 발생

- [ ] 4.4 md 브레이크포인트 그리드 수정
  - `DashboardView.tsx:198,222,284,295`
  - 문제: md에서 3열인데 3행이 2+1+1=4 span
  - 수정: md에서도 4열로 변경하거나, 서류카드를 md:col-span-1로 조정
  - AC: md (768px~1024px) 브라우저에서 3행 카드 정상 배치

- [ ] 4.5 테스트/브라우저 검증
  - `pnpm test` 통과
  - 브라우저: sm/md/lg 각 브레이크포인트 확인
  - AC: 레이아웃 깨짐 없음

---

## Phase 5: P2 품질/보안 [Effort: M]

- [x] 5.1 백엔드 DashboardResult 타입 개선
  - `CurrentPhaseResult`, `DashboardStatsResult`, `GrowthClubResult`, `RoadmapItemResult` dataclass 생성
  - `stats.py`에서 `__dict__` → `asdict()` 변환

- [ ] 5.2 게스트 데이터 이중 정의 해소
  - `useDashboard.ts:8-28`의 GUEST_DASHBOARD_DATA 삭제
  - 미로그인 시에도 BE API 호출 (게스트 엔드포인트 지원 중)
  - 네트워크 에러 시 최소 폴백만 유지 (current_phase만)
  - AC: 프론트/백 게스트 데이터 정의 = 백엔드 1곳만

- [x] 5.3 테스트 mock status 소문자 통일
  - Dashboard.test.tsx: "COMPLETED"→"completed", "CURRENT"→"current", "LOCKED"→"locked"

- [ ] 5.4 다운로드 URL 프로토콜 검증
  - `DashboardView.tsx:156-162` — downloadUrl 추출 후 검증
  - 허용: `https://`, `http://`, `/api/` (상대 경로)
  - 거부: `javascript:`, `data:`, 기타
  - AC: 악성 프로토콜 URL 시 "다운로드 링크 없음" 표시

- [ ] 5.5 백엔드 테스트 + 프론트 테스트 검증
  - `cd app-backend && make test`
  - `cd app-frontend && pnpm test`
  - AC: 전체 통과
