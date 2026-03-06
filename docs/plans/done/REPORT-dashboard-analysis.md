# REPORT: 대시보드 미구현 기능 및 전체 보강 분석

Last Updated: 2026-03-06

---

## 1. Executive Summary

대시보드는 UI 골격이 잘 구성되어 있으나, **실제 데이터와 연동되지 않는 가짜(mock) 기능이 다수** 존재한다.
사용자에게 "프로 플랜", "1,200+ 로드맵", "12명 동료 창업자" 등을 보여주지만 이는 모두 하드코딩 값이다.
아래에서 미구현 기능, 데이터 연동 공백, 품질/보안/접근성 이슈를 분석하고 보강 방안을 제시한다.

---

## 2. 미구현/하드코딩 기능 전수 조사

### 2.1 구독/빌링 시스템 — 완전 미구현

| 항목 | 위치 | 현재 상태 |
|------|------|-----------|
| "프로 플랜" 텍스트 | `Sidebar.tsx:110`, `AccountMenu.tsx:53` | 모든 사용자에게 동일 표시 (하드코딩) |
| /billing 페이지 | `app/(dashboard)/billing/page.tsx` | PlaceholderPage ("준비 중인 페이지") |
| 백엔드 billing API | app-backend/app/api/v1/ | 디렉토리 자체 미존재 |
| User/Team 모델 | models/user.py, models/team.py | subscription_plan 필드 없음 |

**영향**: 사용자가 "구독 플랜" 메뉴를 클릭하면 빈 페이지 도달. 실제 결제 없이 "프로 플랜 사용 중" 표시.

### 2.2 그로스 클럽 온라인 수 — 모의 데이터

| 상황 | 반환값 | 위치 |
|------|--------|------|
| 게스트 | 1,250명 | `dashboard_service.py:69` |
| 로그인 (로드맵 없음) | 12명 | `dashboard_service.py:88` |
| 로그인 (로드맵 있음) | 12명 | `dashboard_service.py:170` |

- 실제 온라인 사용자 집계 로직 없음
- growth_club 테이블에 대한 COUNT 쿼리 미호출
- WebSocket/SSE 실시간 통신 미구현 (Chat SSE만 존재)

### 2.3 ColdStartHero 소셜 프루프 — 전부 하드코딩

| 지표 | 값 | 위치 | 실제 데이터 |
|------|----|------|------------|
| Roadmaps Created | 1,200+ | `ColdStartHero.tsx:91` | 미연동 |
| Active Builders | 850+ | `ColdStartHero.tsx:96` | 미연동 |
| Satisfaction | 4.9/5 | `ColdStartHero.tsx:101` | 미연동 |

### 2.4 아바타 이미지 — dicebear 임시 사용

| 위치 | 방식 | 비고 |
|------|------|------|
| `Sidebar.tsx:78` | `dicebear.com/...?seed=${username}` | 사용자명 기반 생성 |
| `GrowthClubCard.tsx:35,39` | `?seed=A`, `?seed=B` | 완전 하드코딩 |

- `UserProfile` 모델에 `profile_img` 필드 존재 (`models/profile.py:9`)
- 프로필 페이지에서 이미지 업로드 API 완전 구현
- **하지만 대시보드 Sidebar에서는 업로드된 이미지를 사용하지 않고 dicebear만 사용**

### 2.5 days_left 계산 — 30일 고정

```python
# dashboard_service.py:155
days_left = max(0, 30 - (datetime.now(timezone.utc) - created_at).days)
```

- `RoadmapCreateRequest`에 `goal_horizon_days: int = 30` 필드 존재하지만 DB 미저장
- Roadmap 모델에 `goal_horizon_days` 컬럼 없음
- 모든 로드맵이 생성일 기준 30일 마감으로 고정

### 2.6 정상 연동 확인된 기능

| 기능 | 상태 | 비고 |
|------|------|------|
| 알림 시스템 (NotificationBell) | 완전 구현 | FE/BE 모두 구현, 60초 폴링 |
| 프로필 이미지 업로드 | 완전 구현 | 로컬 파일 저장, 프로필 페이지에서 작동 |
| 로드맵 데이터 | 정상 연동 | Dashboard API + RoadmapDetail API |
| 인증/세션 만료 | 정상 작동 | AuthModalProvider + SessionExpiredBanner |

---

## 3. 백엔드 API 분석

### 3.1 API 응답 구조 — 프론트엔드 요구사항 대비 누락 필드

| 누락 데이터 | 현재 | 필요 사유 |
|-------------|------|-----------|
| `roadmap_id` | 미포함 | 대시보드에서 특정 로드맵 상세 페이지 이동 시 필요 |
| `deadline_date` (ISO) | `days_left` (int)만 반환 | 마감일 표시 UI, 캘린더 연동 |
| `current_phase.step_id` | 미포함 | 현재 단계 상세 직접 링크 |

### 3.2 비즈니스 로직 이슈

**진행률(progress) 계산: Step 기반 vs Action 기반 불일치**

```python
# dashboard_service.py:92-94 — Step 기반
tasks_completed = len([step for step in steps if step.status == "COMPLETED"])
progress = int((tasks_completed / total_tasks) * 100)
```

- 백엔드: Step 레벨 완료율 (3 step 중 1 완료 = 33%)
- 프론트엔드: `computeEndowedProgress`로 보정 적용 (endowed steps 추가)
- Step 하위 Action(체크리스트) 완료율과는 별개 → 사용자 혼란 가능

**Phase/Status 결정 로직 모호성**

- `step.title` vs `detail.phase`: detail.phase가 있으면 override하지만 우선순위 문서화 없음
- status는 단순 이진 (IN_PROGRESS | COMPLETED)만 제공

### 3.3 데이터 접근 패턴 — 양호

- 총 쿼리 2~3개 (list_steps + list_step_details + get_latest/by_id)
- `.in_()` 배치 처리로 N+1 쿼리 없음
- 읽기 전용이므로 트랜잭션 이슈 없음

### 3.4 보안 — 양호

- 게스트: 모의 데이터만 반환 (실제 DB 접근 불가)
- 팀 경계: `TeamMember` 테이블 + 리포지토리 `team_id` 필터 이중 검증
- `roadmap_id` 쿼리 파라미터: `get_by_id_for_team(roadmap_id, team_id)`로 교차 접근 차단

### 3.5 테스트 커버리지 — 부족

**현재**: 3개 테스트 (`tests/api/test_dashboard.py`, 170줄)

| 시나리오 | 테스트 여부 |
|---------|-----------|
| 기본 응답 구조 | O |
| detail.phase override | O |
| phase별 그룹화 | O |
| 게스트 대시보드 | X |
| 로드맵 없음 (READY) | X |
| progress 계산 검증 | X |
| days_left 계산 검증 | X |
| invalid roadmap_id | X |
| X-Team-Id 권한 검증 | X |

---

## 4. 프론트엔드 품질 분석

### 4.1 접근성(a11y) — 심각하게 부족

| 문제 | 영향 범위 |
|------|----------|
| `aria-label` 미사용 | NotificationBell 버튼, MobileNav 버튼, 전체 인터랙티브 요소 |
| `role` 속성 부재 | DropdownMenu trigger, 네비게이션 항목 |
| `sr-only` 클래스 미사용 | 아이콘 전용 버튼에 텍스트 대안 없음 |
| 키보드 네비게이션 미고려 | RoadmapStepper 드래그 전용, 키보드 스크롤 불가 |

### 4.2 모바일 safe-area — 미적용

```tsx
// MobileNav.tsx:39 — pb-8 (32px) 고정
<nav className="fixed bottom-0 ... pb-8 pt-2 px-6 ...">
```

- `env(safe-area-inset-bottom)` 미사용
- iPhone 홈 인디케이터 영역에서 네비게이션 가림 가능

### 4.3 에러 처리 — 양호하나 일부 누락

| 상태 | 구현 여부 | 비고 |
|------|----------|------|
| 대시보드 로딩 | O | 스켈레톤 UI |
| 게스트 폴백 | O | GUEST_DASHBOARD_DATA |
| 문서 로딩 에러 | O | 에러 메시지 표시 |
| **useDashboard error 미표시** | X | `error` 반환하지만 DashboardView에서 미사용 |
| **네트워크 전체 실패** | 부분 | 게스트 데이터로 폴백하지만 에러 알림 없음 |

### 4.4 성능 — 양호

- `useMemo`/`useCallback` 적절히 사용 (DashboardView 6개소)
- cancelled 플래그로 race condition 방지
- 알림 폴링 60초 (비효율적이나 현 규모에서 문제 없음)

### 4.5 TypeScript 타입 안전성

- `as Array<{...}>` 캐스트 (`DashboardView.tsx:155`): API 응답 타입 부정확으로 인한 방어 코드
- `as Record<string, unknown>` (`DashboardView.tsx:165`): metadata_json 타입 미정의
- 전반적으로 적절한 수준, 과도한 `any` 없음

---

## 5. 보강 방안 (우선순위별)

### P0 — 거짓 정보 제거 (즉시)

| # | 작업 | 파일 | 노력 |
|---|------|------|------|
| 1 | "프로 플랜" 하드코딩 → "무료 플랜" 또는 조건부 표시 제거 | Sidebar.tsx, AccountMenu.tsx | S |
| 2 | ColdStartHero 소셜 프루프 수치 제거 또는 "Beta" 표시 | ColdStartHero.tsx | S |
| 3 | GrowthClubCard 하드코딩 아바타(seed=A/B) → 제거 또는 익명 아이콘 | GrowthClubCard.tsx | S |

**사유**: 실제 데이터 없는 구체적 수치(1,200+, 850+, 4.9/5)는 사용자 기만. MVP라도 거짓 정보는 제거해야 함.

### P1 — 데이터 연동 보강 (1~2주)

| # | 작업 | 범위 | 노력 |
|---|------|------|------|
| 4 | Sidebar 아바타 → UserProfile.profile_img 연동 | FE: Sidebar, BE: user API 응답에 profile_img 포함 | M |
| 5 | founders_online 실제 집계 | BE: 최근 N분 내 활동 사용자 COUNT, FE: 기존 연동 유지 | M |
| 6 | days_left → goal_horizon_days 연동 | BE: Roadmap 모델 + 마이그레이션, FE: 변경 없음 | M |
| 7 | Dashboard API에 roadmap_id 포함 | BE: DashboardResult + 스키마 확장 | S |
| 8 | useDashboard error 상태 UI 표시 | FE: DashboardView에 에러 배너 추가 | S |

### P2 — 접근성 개선 (1주)

| # | 작업 | 범위 | 노력 |
|---|------|------|------|
| 9 | 모든 인터랙티브 요소에 aria-label 추가 | NotificationBell, MobileNav, Sidebar 등 | M |
| 10 | 아이콘 전용 버튼에 sr-only 텍스트 추가 | 전체 컴포넌트 | S |
| 11 | RoadmapStepper 키보드 접근성 | 좌우 화살표 키 스크롤 | S |
| 12 | MobileNav safe-area-inset-bottom 적용 | MobileNav.tsx | S |

### P3 — 백엔드 테스트 보강 (1주)

| # | 작업 | 비고 |
|---|------|------|
| 13 | 게스트 대시보드 응답 검증 테스트 | status=GUEST, founders_online=1250 |
| 14 | 로드맵 없음 (READY) 상태 테스트 | roadmap=[], status=READY |
| 15 | progress 계산 정확성 테스트 | 3 step 중 1 완료 = 33% |
| 16 | days_left 경계값 테스트 | 생성 후 30일 초과 = 0 |
| 17 | invalid roadmap_id 처리 테스트 | UUID 형식 오류 시 graceful 처리 |
| 18 | X-Team-Id 권한 검증 테스트 | 비멤버 팀 접근 시 403 |

### P4 — 기능 확장 (향후)

| # | 작업 | 비고 | 노력 |
|---|------|------|------|
| 19 | 구독/빌링 시스템 구현 | 별도 PLAN 필요 | XL |
| 20 | 알림 폴링 → WebSocket/SSE 전환 | 실시간성 향상 | L |
| 21 | ColdStartHero 소셜 프루프 실제 집계 연동 | 플랫폼 통계 API | M |
| 22 | 멀티 기기 로드맵 동기화 | localStorage → 서버 상태 | L |

---

## 6. 위험 요소

| 리스크 | 심각도 | 설명 |
|--------|--------|------|
| 거짓 소셜 프루프 | 높음 | "1,200+ Roadmaps Created" 등 실제 데이터 없는 수치가 사용자 신뢰 훼손 |
| 구독 표시 불일치 | 중간 | 결제 없이 "프로 플랜 사용 중" 표시 → 향후 유료화 시 혼란 |
| 접근성 미비 | 중간 | 장애인차별금지법 관련 리스크 (WCAG 2.1 미준수) |
| 테스트 부족 | 낮음 | 게스트/엣지 케이스 6개 시나리오 미검증 |

---

## 7. 결론

대시보드의 **UI/UX 완성도는 높지만, 데이터 진실성(data truthfulness)에 심각한 갭**이 있다.
가장 시급한 것은 P0 항목(거짓 정보 제거)이며, 이는 코드 변경량이 적고 리스크도 낮다.
P1(데이터 연동)은 백엔드 모델 변경을 수반하므로 별도 계획이 필요하다.
