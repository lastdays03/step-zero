# Tasks: 메인 대시보드 정리 및 품질 개선

Last Updated: 2026-03-06

## Phase 1: 미사용 소스 정리 [Effort: S]

- [ ] 1.1 `StatsGrid.tsx` 삭제
  - 파일: `features/dashboard/components/StatsGrid.tsx`
  - `components/index.ts`에서 `export { StatsGrid }` 줄 제거
  - AC: Grep "StatsGrid" 결과 0건

- [ ] 1.2 `mocks/dashboardMock.ts` 삭제
  - 파일: `features/dashboard/mocks/dashboardMock.ts`
  - `mocks/` 디렉토리 삭제
  - AC: Grep "dashboardMock\|MOCK_DASHBOARD_DATA\|fetchDashboardMock" 결과 0건

- [ ] 1.3 `api/index.ts` 삭제
  - 파일: `features/dashboard/api/index.ts` (빈 `export {}`)
  - `api/` 디렉토리 삭제
  - `features/dashboard/index.ts`에서 `export * from "./api"` 제거
  - AC: 파일 미존재

- [ ] 1.4 `types/index.ts` 삭제
  - 파일: `features/dashboard/types/index.ts`
  - `types/` 디렉토리 삭제
  - `features/dashboard/index.ts`에서 `export * from "./types"` 제거
  - AC: 파일 미존재, DashboardData 타입은 useDashboard.ts에서 직접 import 유지

- [ ] 1.5 빌드/린트/테스트 검증
  - `pnpm lint` 통과
  - `pnpm test` 통과 (Dashboard.test.tsx 6건)
  - AC: 에러 0건

---

## Phase 2: 중복 코드 제거 [Effort: L]

- [ ] 2.1 `#36a4f2` → 디자인 토큰 통일
  - **주의: primary=#257bf4 ≠ #36a4f2 — 단순 `primary` 교체 불가**
  - 사전: 디자인 의도 확인 후 방안 결정
    - 방안 A: tailwind.config에 `accent: #36a4f2` 별도 토큰 추가 → `bg-accent/10`, `text-accent`
    - 방안 B: primary 값을 `#36a4f2`로 변경 (영향 범위 확인 필요)
    - 방안 C: 의도적 구분이면 현행 유지 (하드코딩은 토큰화만)
  - `ProgressCard.tsx:64` — `text-[#36a4f2]`
  - `RoadmapStepper.tsx:70,96,99,113` — 4곳
  - `DashboardView.tsx:235` — `bg-[#36a4f2]`
  - AC: Grep `#36a4f2` in dashboard/ = 0건 (토큰으로 대체)
  - Deps: 없음

- [ ] 2.2 카드 스타일 상수 추출
  - `DashboardView.tsx:222,284,295`에서 반복되는 클래스 문자열
  - `"bg-white/90 backdrop-blur-sm border border-white/50 rounded-3xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.05)]"`
  - 상수 `GLASS_CARD_CLASS` 또는 유사 이름으로 추출
  - AC: 동일 클래스 문자열 1곳에만 정의

- [ ] 2.3 네비게이션 메뉴 설정 공유
  - 신규: `features/dashboard/config/nav-config.ts`
  - 공통 항목: href, icon, desktopLabel, mobileLabel, caption
  - `Sidebar.tsx`의 menuItems → nav-config import
  - `MobileNav.tsx`의 navItems → nav-config import
  - canAccessOps 조건부 항목도 config에서 관리
  - AC: 메뉴 항목 추가/제거 시 1곳만 수정하면 됨
  - Deps: 없음

- [ ] 2.4 `AccountMenu` 공통 컴포넌트 추출
  - 신규: `features/dashboard/components/AccountMenu.tsx`
  - Props: `variant: "desktop" | "mobile"`, `onLogout: () => void`
  - 내용: DropdownMenuContent (프로필관리/구독플랜/로그아웃)
  - `Sidebar.tsx`에서 드롭다운 내용 → `<AccountMenu variant="desktop" />`
  - `MobileNav.tsx`에서 드롭다운 내용 → `<AccountMenu variant="mobile" />`
  - variant별 차이: width (w-64/w-56), side (default/top), animation
  - AC: Sidebar/MobileNav 각각 36줄 → ~5줄로 축소
  - Deps: 2.3 완료 후

- [ ] 2.5 `SocialAuthModal` 단일화
  - 현재: ColdStartHero, AuthGuard, Sidebar, MobileNav — 4곳에서 각각 인스턴스
  - 방안: layout.tsx에 단일 `<SocialAuthModal>` + Context `useAuthModal()`
  - 신규: `features/dashboard/providers/AuthModalProvider.tsx` (또는 기존 AuthProvider 확장)
  - 각 컴포넌트에서 `const { openAuthModal } = useAuthModal()` 호출
  - 4곳의 `useState(isAuthModalOpen)` + `<SocialAuthModal>` 제거
  - AC: Grep "SocialAuthModal" in dashboard/ = layout.tsx 1건 + Provider 1건만
  - Deps: 없음

- [ ] 2.6 빌드/린트/테스트 검증
  - `pnpm lint` 통과
  - `pnpm test` 통과
  - 브라우저: Sidebar 드롭다운, MobileNav 드롭다운, 로그인 모달 동작 확인
  - AC: 에러 0건

---

## Phase 3: P0 버그 수정 [Effort: S]

- [ ] 3.1 ProgressCard: window.location.href → router.push
  - `ProgressCard.tsx:87` — `window.location.href = "/roadmap"` → Next.js `useRouter` + `router.push`
  - Props에 `onNavigate` 콜백 추가하거나 컴포넌트 내부에서 `useRouter` 사용
  - AC: window.location.href 미사용, SPA 내비게이션 동작

- [ ] 3.2 activeRoadmapId 갱신 로직 추가
  - `DashboardView.tsx:19-22` — setter 없는 `useState`
  - storage 이벤트 리스너로 `stepzero_active_roadmap_id` 변경 감지
  - 변경 시 setActiveRoadmapId 호출 → useDashboard 재호출
  - AC: 로드맵 페이지에서 활성 로드맵 전환 → 대시보드 복귀 시 올바른 데이터 표시

- [ ] 3.3 테스트 검증
  - 기존 Dashboard.test.tsx 통과
  - AC: 6건 모두 pass

---

## Phase 4: P1 UX 개선 [Effort: M]

- [ ] 4.1 Header 시간대별 인사말
  - `Header.tsx:15` — 현재 시간 기반 분기
  - 06-12: "좋은 아침입니다", 12-18: "좋은 오후입니다", 18-06: "좋은 저녁입니다"
  - 부제: 현재 단계명 또는 일반 동기부여 문구 (Header에 prop 추가 또는 useDashboard 연동)
  - AC: 시간대별 인사말 변경 확인

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

- [ ] 5.1 백엔드 DashboardResult 타입 개선
  - `dashboard_service.py:8-14` — `dict` → typed dataclass 또는 Pydantic
  - `current_phase: CurrentPhaseResult`, `stats: DashboardStatsResult` 등
  - AC: mypy 통과, dict 키 오타 시 타입 에러 발생

- [ ] 5.2 게스트 데이터 이중 정의 해소
  - `useDashboard.ts:8-28`의 GUEST_DASHBOARD_DATA 삭제
  - 미로그인 시에도 BE API 호출 (게스트 엔드포인트 지원 중)
  - 네트워크 에러 시 최소 폴백만 유지 (current_phase만)
  - AC: 프론트/백 게스트 데이터 정의 = 백엔드 1곳만

- [ ] 5.3 테스트 mock status 소문자 통일
  - `Dashboard.test.tsx:58-61` — "COMPLETED"→"completed", "CURRENT"→"current", "LOCKED"→"locked"
  - AC: 백엔드 실제 응답과 동일한 형식

- [ ] 5.4 다운로드 URL 프로토콜 검증
  - `DashboardView.tsx:156-162` — downloadUrl 추출 후 검증
  - 허용: `https://`, `http://`, `/api/` (상대 경로)
  - 거부: `javascript:`, `data:`, 기타
  - AC: 악성 프로토콜 URL 시 "다운로드 링크 없음" 표시

- [ ] 5.5 백엔드 테스트 + 프론트 테스트 검증
  - `cd app-backend && make test`
  - `cd app-frontend && pnpm test`
  - AC: 전체 통과
