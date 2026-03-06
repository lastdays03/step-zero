# PLAN: 메인 대시보드 정리 및 품질 개선

Last Updated: 2026-03-06

## 1. Executive Summary

메인 대시보드(`/dashboard`)의 미사용 소스 삭제, 중복 코드 제거, 버그 수정, UX 개선을 수행한다.
318줄짜리 DashboardView 단일 컴포넌트에 집중된 상태 관리, 4중 SocialAuthModal 인스턴스,
Sidebar/MobileNav 간 36줄 드롭다운 복붙, 프론트/백엔드 게스트 데이터 이중 정의 등을 정리한다.

## 2. Current State

### 문제 요약

| 카테고리 | 건수 | 핵심 |
|----------|------|------|
| 미사용 소스 | 4파일 (79줄) | StatsGrid, dashboardMock, 빈 api/types |
| 중복 코드 | 7건 | SocialAuthModal 4중, 드롭다운 복붙, 게스트 데이터 이중, 색상 혼용 |
| 버그 (P0) | 2건 | window.location.href 풀 리로드, activeRoadmapId 미갱신 |
| UX 결함 (P1) | 4건 | 고정 인사말, Loading 텍스트, 가짜 입력필드, md 그리드 깨짐 |
| 품질/보안 (P2) | 5건 | dict 타입, API 2회 호출, 진행률 이중 계산, 테스트 불일치, URL 미검증 |

### 영향 범위

- `app-frontend/src/features/dashboard/` 전체 (12 파일)
- `app-frontend/src/app/(dashboard)/` 레이아웃
- `app-backend/app/features/dashboard/` 서비스

## 3. Proposed Future State

1. 미사용 파일 4개 삭제, export 정리
2. SocialAuthModal을 레이아웃 수준 1개로 통합
3. Sidebar/MobileNav 공통 드롭다운 컴포넌트 추출
4. 네비게이션 메뉴 설정 공유
5. `#36a4f2` 하드코딩 → 디자인 토큰 통일 (primary=#257bf4와 다르므로 별도 토큰 검토)
6. P0 버그 2건 수정
7. P1 UX 4건 개선
8. P2 품질/보안 개선

## 4. Implementation Phases

### Phase 1: 미사용 소스 정리 (리스크 없음)
- StatsGrid.tsx 삭제
- mocks/dashboardMock.ts 삭제
- api/index.ts 삭제
- types/index.ts 삭제
- 관련 export/re-export 정리

### Phase 2: 중복 코드 제거
- SocialAuthModal 단일화 (레이아웃 수준 Context)
- AccountMenu 공통 컴포넌트 추출 (Sidebar/MobileNav 드롭다운)
- 네비게이션 메뉴 설정 공유 (nav-config)
- `#36a4f2` → 디자인 토큰 통일 (primary와 다른 색상이므로 별도 토큰 또는 primary 값 변경 결정 필요)
- 카드 스타일 상수 추출

### Phase 3: P0 버그 수정
- ProgressCard: window.location.href → router.push
- DashboardView: activeRoadmapId storage 이벤트 감지 + 갱신

### Phase 4: P1 UX 개선
- Header: 시간대별 인사말 + 동적 부제
- DashboardView: 스켈레톤 로딩 UI
- ColdStartHero: 가짜 입력필드 → 실제 input 또는 클릭 영역 명확화
- DashboardView: md 브레이크포인트 그리드 수정

### Phase 5: P2 품질/보안
- 백엔드 DashboardResult: dict → typed dataclass/Pydantic
- 게스트 데이터: FE/BE 이중 정의 해소 (FE 삭제, BE만 사용)
- 테스트 mock status: 소문자 통일
- 다운로드 URL 검증 (프로토콜 화이트리스트)
- 진행률 계산 로직 정리 (BE에서 endowed 포함 계산 or FE에서만)

## 5. Risk Assessment

| 리스크 | 영향 | 완화 |
|--------|------|------|
| SocialAuthModal 통합 시 열기 로직 누락 | 로그인 모달 안 열림 | Context API로 open 함수 제공, 전환 후 전체 시나리오 테스트 |
| 드롭다운 추출 시 스타일 차이 | Sidebar/MobileNav 디자인 틀어짐 | Props로 variant 구분 (desktop/mobile) |
| md 그리드 수정 시 다른 브레이크포인트 영향 | 레이아웃 깨짐 | lg/md/sm 각각 브라우저 테스트 |
| 게스트 데이터 FE 삭제 시 오프라인/네트워크 에러 | 빈 화면 | FE에 최소 폴백 유지 또는 에러 바운더리 |

## 6. Success Metrics

- [ ] 미사용 파일 0개 (Grep 검증)
- [ ] SocialAuthModal DOM 인스턴스 = 1개
- [ ] `#36a4f2` 하드코딩 = 0건 (디자인 토큰으로 대체)
- [ ] `pnpm lint` 통과
- [ ] `pnpm test` 통과
- [ ] 기존 Dashboard.test.tsx 6개 테스트 통과
- [ ] 브라우저 테스트: sm/md/lg 그리드 정상
