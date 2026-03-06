# Context: 메인 대시보드 정리 및 품질 개선

Last Updated: 2026-03-06 (세션 2)

## Key Files

### Frontend - Dashboard Feature
| 파일 | 역할 | 변경 |
|------|------|------|
| `app-frontend/src/features/dashboard/components/DashboardView.tsx` | 메인 컨테이너 (318줄) | Phase 2,3,4,5 수정 |
| `app-frontend/src/features/dashboard/components/ProgressCard.tsx` | 진행도 카드 | Phase 3 (router.push), Phase 2 (#36a4f2) |
| `app-frontend/src/features/dashboard/components/RoadmapStepper.tsx` | 로드맵 타임라인 | Phase 2 (#36a4f2 → primary) |
| `app-frontend/src/features/dashboard/components/GrowthClubCard.tsx` | 온라인 수 카드 | 변경 없음 |
| `app-frontend/src/features/dashboard/components/ColdStartHero.tsx` | 콜드스타트 히어로 | Phase 2 (SocialAuthModal 제거), Phase 4 (입력필드) |
| `app-frontend/src/features/dashboard/components/Header.tsx` | 상단 헤더 | Phase 4 (시간대 인사말) |
| `app-frontend/src/features/dashboard/components/AuthGuard.tsx` | 세션 만료 배너 | Phase 2 (SocialAuthModal 제거) |
| `app-frontend/src/features/dashboard/components/Sidebar.tsx` | 데스크톱 사이드바 | Phase 2 (드롭다운 추출, SocialAuthModal 제거, nav-config) |
| `app-frontend/src/features/dashboard/components/MobileNav.tsx` | 모바일 네비게이션 | Phase 2 (드롭다운 추출, SocialAuthModal 제거, nav-config) |
| `app-frontend/src/features/dashboard/components/index.ts` | 배럴 export | Phase 1 (StatsGrid 제거), Phase 2 (신규 컴포넌트 추가) |
| `app-frontend/src/features/dashboard/components/StatsGrid.tsx` | **삭제** | Phase 1 |
| `app-frontend/src/features/dashboard/hooks/useDashboard.ts` | API 호출 훅 | Phase 5 (게스트 데이터 정리) |
| `app-frontend/src/features/dashboard/mocks/dashboardMock.ts` | **삭제** | Phase 1 |
| `app-frontend/src/features/dashboard/api/index.ts` | **삭제** | Phase 1 |
| `app-frontend/src/features/dashboard/types/index.ts` | **삭제** | Phase 1 |
| `app-frontend/src/features/dashboard/index.ts` | 배럴 re-export | Phase 1 (api, types 제거) |
| `app-frontend/src/features/dashboard/__tests__/Dashboard.test.tsx` | 테스트 | Phase 5 (mock status 소문자) |

### Frontend - Layout
| 파일 | 역할 | 변경 |
|------|------|------|
| `app-frontend/src/app/(dashboard)/layout.tsx` | 공통 레이아웃 | Phase 2 (SocialAuthModal 단일 인스턴스 추가) |

### Frontend - 신규 파일 (Phase 2)
| 파일 | 역할 |
|------|------|
| `app-frontend/src/features/dashboard/components/AccountMenu.tsx` | 공통 프로필 드롭다운 메뉴 |
| `app-frontend/src/features/dashboard/config/nav-config.ts` | 네비게이션 메뉴 항목 정의 |

### Backend
| 파일 | 역할 | 변경 |
|------|------|------|
| `app-backend/app/features/dashboard/application/dashboard_service.py` | 대시보드 서비스 | Phase 5 (DashboardResult 타입 개선) |

## Key Decisions

1. **SocialAuthModal 통합 방식**: 레이아웃 수준 Context + `useAuthModal()` 훅으로 open/close 제어
2. **게스트 데이터 단일화**: FE의 GUEST_DASHBOARD_DATA 삭제, BE API만 사용. FE는 에러 시 최소 폴백만 유지
3. **진행률 계산**: FE의 endowed progress 로직 유지 (BE는 raw progress만 제공, 보정은 FE 담당)
4. **색상 통일**: `#36a4f2` 하드코딩을 디자인 토큰으로 교체. **primary=#257bf4 ≠ #36a4f2이므로 단순 `primary` 교체 불가.** 별도 토큰(`accent` 등) 추가 또는 primary 값 변경 결정 필요
5. **AccountMenu props**: `variant: "desktop" | "mobile"` prop으로 width/animation 차이 제어

## Implementation Progress (세션 2)

### 완료
- **Phase 2.2~2.5**: GLASS_CARD 상수, nav-config, AccountMenu, AuthModalProvider 구현
- **Phase 3.1~3.2**: router.push 전환, activeRoadmapId storage 동기화
- **Phase 4.1**: Header 시간대별 인사말
- **Phase 5.1**: DashboardResult typed dataclass 전환 + `asdict()` 직렬화
- **Phase 5.3**: 테스트 mock status 소문자 통일

### 신규 파일 (미커밋)
- `app-frontend/src/features/dashboard/components/AccountMenu.tsx`
- `app-frontend/src/features/dashboard/providers/AuthModalProvider.tsx`
- `app-frontend/src/features/dashboard/config/nav-config.ts` (이전 세션 생성, 이미 tracked)

### 미완료
- **Phase 2.1**: #36a4f2 색상 토큰화 (디자인 의도 미결정)
- **Phase 2.6/3.3**: 빌드/린트/테스트 검증 미실행
- **Phase 4.2~4.5**: 스켈레톤 UI, ColdStartHero 입력, md 그리드, 검증
- **Phase 5.2**: 게스트 데이터 이중 정의 해소
- **Phase 5.4~5.5**: 다운로드 URL 검증, 전체 테스트

## Dependencies

- `@/providers/AuthProvider` — useAuth 훅 인터페이스 변경 없음
- `@/features/auth/components/SocialAuthModal` — props 변경 없음 (isOpen, onClose)
- `@/features/roadmap/components/roadmap-utils.ts` — computeEndowedProgress, computeReadinessLevel 변경 없음
- `@/components/ui/` — Card, Badge, Button, Avatar, DropdownMenu 변경 없음

## Tailwind primary 색상 불일치 (확인됨)

- **primary**: HSL `217 91% 55%` = **#257bf4** (진한 파란색)
- **하드코딩**: **#36a4f2** (밝은 파란색)
- 두 색상은 **다른 값**임. 단순 `primary` 교체 시 시각적 변화 발생.
- 구현 전 디자인 의도 확인 필요: 의도적 구분 vs 실수.
