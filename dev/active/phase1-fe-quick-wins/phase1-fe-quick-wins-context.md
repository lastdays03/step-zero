# Phase 1: FE Quick Wins — Context

> Last Updated: 2026-03-02

---

## 1. Key Files Map

### 수정된 파일

| 파일 | 경로 | 변경 내용 |
|------|------|----------|
| **roadmap-constants.ts** | `app-frontend/src/features/roadmap/components/roadmap-constants.ts` | ENDOWED_STEPS/LABELS, READINESS_LEVELS, MILESTONE_INSIGHTS, INTAKE_CONFIRMATION_MESSAGES, STAGE_MESSAGES, GENERATING_INSIGHTS |
| **roadmap-utils.ts** | `app-frontend/src/features/roadmap/components/roadmap-utils.ts` | ReadinessLevel/ReadinessInfo 타입, computeEndowedProgress(), computeReadinessLevel() |
| **RoadmapExecutionView.tsx** | `app-frontend/src/features/roadmap/components/RoadmapExecutionView.tsx` | computeEndowedProgress 적용, overallProgress를 TimelinePhaseCard에 전달 |
| **RoadmapSidebar.tsx** | `app-frontend/src/features/roadmap/components/RoadmapSidebar.tsx` | Endowed 진행률 표시, 첫 방문 배지, ReadinessTracker 통합 |
| **TimelinePhaseCard.tsx** | `app-frontend/src/features/roadmap/components/TimelinePhaseCard.tsx` | 3개 스텝 접힘, Phase 축하 트리거, 스텝 20% 인사이트(30s cooldown), readiness tracking |
| **RoadmapChatIntake.tsx** | `app-frontend/src/features/roadmap/components/RoadmapChatIntake.tsx` | renderedHistory에 정규화 확인 메시지 삽입 |
| **RoadmapGeneratingState.tsx** | `app-frontend/src/features/roadmap/components/RoadmapGeneratingState.tsx` | 동적 stageMessage + 인사이트 5s 로테이션, 정적 3개 목록 제거 |
| **ProgressCard.tsx** | `app-frontend/src/features/dashboard/components/ProgressCard.tsx` | Endowed progress 원형 표시 + readinessLabel 배지 |
| **DashboardView.tsx** | `app-frontend/src/features/dashboard/components/DashboardView.tsx` | Endowed/readiness 계산, localStorage 등급 업그레이드 토스트 |
| **components/index.ts** | `app-frontend/src/features/roadmap/components/index.ts` | MilestoneCelebration, computeEndowedProgress, computeReadinessLevel, ReadinessTracker export |

### 신규 생성 파일

| 파일 | 경로 | 용도 |
|------|------|------|
| **ReadinessTracker.tsx** | `app-frontend/src/features/roadmap/components/ReadinessTracker.tsx` | 5단계 준비도 수평 트랙 컴포넌트 |
| **MilestoneCelebration.tsx** | `app-frontend/src/features/roadmap/components/MilestoneCelebration.tsx` | Phase 컨페티 모달 + Step 인사이트 토스트 |
| **roadmap-utils.test.ts** | `app-frontend/src/features/roadmap/__tests__/roadmap-utils.test.ts` | computeEndowedProgress + computeReadinessLevel 유닛 테스트 (14 tests) |

### 수정된 테스트 파일

| 파일 | 변경 내용 |
|------|----------|
| `LoginForm.test.tsx` | useAuth mock 반환값에 `login` 추가 |
| `Dashboard.test.tsx` | `computeEndowedProgress`, `computeReadinessLevel` mock 추가, `fetchRoadmapDetail` mock 추가 |

---

## 2. Key Decisions

| 결정 | 선택 | 근거 |
|------|------|------|
| Endowed Progress 가상 스텝 수 | **3** (17% 시작) | Columbia/Drexel 연구 기반 |
| 준비도 등급 경계값 | 0/10/35/65/90% | 초반 진행 보상 강화 설계 |
| 접힘 기본값 | **3개 스텝만 펼침** | Basecamp Hill Chart 패턴 |
| 컨페티 라이브러리 | `canvas-confetti@^1.9.4` | 경량(6kB), SSR 안전 |
| 인사이트 메시지 방식 | 프론트엔드 정적 데이터 | BE 변경 없음 제약 |
| 등급 업그레이드 알림 | localStorage 기반 비교 | 서버 없이 이전 상태 추적 |
| 스텝 완료 랜덤 인사이트 | 20% 확률 + 30초 cooldown | Asana 변동비율 강화 + 연속 방지 |
| Phase 축하 readiness 추적 | **state 기반** (not useRef) | ESLint react-hooks/refs 규칙 준수 |
| 첫 방문 Endowed 배지 | **useState lazy init** | ESLint react-hooks/set-state-in-effect 규칙 준수 |
| 생성 중 정적 메시지 | **동적 stageMessage로 완전 대체** | 계획 3.5C 명시 요구 |

---

## 3. Session-specific Technical Decisions

### 3.1 ESLint 호환 패턴 (이 세션에서 해결)

**문제 1**: `react-hooks/set-state-in-effect` — useEffect 내 동기 setState 금지
- **해결**: `useState(() => { ... })` lazy initializer로 localStorage 읽기 + 초기값 설정
- **적용 파일**: `RoadmapSidebar.tsx` — 첫 방문 Endowed 배지

**문제 2**: `react-hooks/refs` — render 중 ref 접근/수정 금지
- **해결**: `useRef` 대신 `useState` + render-time state comparison 패턴 사용
- **적용 파일**: `TimelinePhaseCard.tsx` — `trackedReadiness` state로 이전 readiness 추적

**문제 3**: `lastInsightTimeRef`는 event handler에서만 사용 → lint 통과 (render 중 미접근)

### 3.2 구현 위치 변경

| 계획 | 실제 | 이유 |
|------|------|------|
| 스텝 인사이트를 TimelineStepItem에 구현 | TimelinePhaseCard의 handleStepStatusChange 래퍼 | onStepStatusChange 콜백 래핑이 더 깔끔, Step 컴포넌트 수정 불필요 |
| 등급 업그레이드 토스트를 ReadinessTracker에 구현 | DashboardView에서 직접 구현 | localStorage roadmapId 접근이 DashboardView에서만 가능 |

---

## 4. Dependencies

### 4.1 선행 작업

| 작업 | 상태 |
|------|:----:|
| Phase 0 PR → develop 머지 | **완료** |
| `types:sync` 결과물 커밋 | **완료** |

### 4.2 npm 의존성

| 패키지 | 설치 버전 | 용도 |
|--------|----------|------|
| `canvas-confetti` | ^1.9.4 | 컨페티 애니메이션 |
| `@types/canvas-confetti` | ^1.9.0 | TypeScript 타입 (devDependency) |

---

## 5. Quality Gates 결과 (2026-03-02 최종)

| Gate | 결과 |
|------|:----:|
| `npm run lint` | PASS (0 errors, 0 warnings) |
| `npm run build` | PASS (18 routes, 11.3s 컴파일) |
| `npm test` | PASS (3 suites, 22 tests) |

---

## 6. Reference Documents

| 문서 | 경로 |
|------|------|
| 마스터 플랜 | `docs/research/roadmap-improvement/01-master-plan.md` |
| 구현 순서 보고서 | `docs/research/roadmap-improvement/implementation-order-report.md` |
| Phase 0 완료 | `dev/done/phase0-roadmap-fix/` |
