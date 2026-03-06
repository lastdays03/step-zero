# Phase 1: FE Quick Wins 구현 계획

> Last Updated: 2026-03-01
> Branch: `feature/1-fe-quick-wins` (from `develop`)
> 선행 조건: Phase 0 완료 (PR 머지 후 착수)
> 총 공수: 15일 (Sprint 1-A 5일 + Sprint 1-B 10일)

---

## 1. Executive Summary

Phase 0(링크 오류 수정 + startup_method 정리)이 완료된 상태에서, **BE 변경 없이 순수 프론트엔드만으로 UX 가치를 즉시 전달**하는 5개 Quick Win 기능을 구현한다.

### 핵심 목표
- 초기 이탈률 20-55% 감소 (Endowed Progress)
- 인지 부하 40% 감소 (다음 액션 집중)
- 온보딩 전환율 35% → 55% (첫 5분 최적화)
- 완료 동기 강화 (준비도 스코어 + 마일스톤 축하)

### 제약사항
- **BE 변경 없음** — 기존 API 응답 데이터만 활용
- `api-types.ts` 수동 편집 금지 (자동 생성 파일)
- feature 간 내부 경로 import 금지 (`index.ts` public entry만 사용)
- 새 npm 패키지: `canvas-confetti`만 추가 허용 (마일스톤 축하용)

---

## 2. Current State Analysis

### 2.1 진행률 표시 현황

**RoadmapExecutionView** (`:32-35`):
```typescript
const totalCompleted = data.steps.filter((s) => s.status === "COMPLETED").length;
const overallProgress = data.steps.length
    ? Math.round((totalCompleted / data.steps.length) * 100) : 0;
```
- 순수 step 기준 0%→100% 선형 계산
- Endowed Progress 미적용 (0%에서 시작)

**RoadmapSidebar** (`:34-50`):
- `전체 진행률` 카드에 `{overallProgress}%` + Progress bar
- `{completedSteps}/{totalSteps} 단계 완료` 텍스트
- 준비도 등급 시스템 없음

**DashboardView > ProgressCard** (`:31-58`):
- SVG 원형 프로그레스 (`phase.progress * 2.827 / 282.7`)
- `현재 진행 단계` + 퍼센트 표시
- 준비도 등급 없음

### 2.2 Phase 카드 현황

**TimelinePhaseCard**:
- 4가지 상태: `COMPLETED` / `CURRENT` / `LOCKED` / `FUTURE`
- COMPLETED: 접힌 상태 기본, 펼침 가능
- CURRENT: 항상 펼침, 체크리스트 진행률 표시
- LOCKED/FUTURE: 스텝 목록만 표시
- **Phase 완료 시 축하 UX 없음**

### 2.3 Step 카드 현황

**TimelineStepItem**:
- 3가지 상태: `DONE` / `ACTIVE` / `LOCKED`
- ACTIVE: 체크리스트 + 서류 + 법적근거 전체 표시
- **다음 액션 집중 표시 없음** — 모든 액션이 동일 수준으로 노출

### 2.4 인테이크 폼 현황

**RoadmapChatIntake** (`:92-446`):
- 7단계 순차 질문 (6 필수 + 1 선택)
- 답변 후 즉시 AI 정규화 확인 없음
- 검증 후 요약 카드는 있음 (`validated.summary`)
- 생성 상태: 진행률 바 + stage 텍스트 (의미 있는 메시지 아님)

**RoadmapGeneratingState** (`:11-70`):
- 정적 텍스트 3개 (단계 생성, 상세 계획 병렬 생성, 결과 저장)
- 업종별 인사이트 없음

---

## 3. Implementation Design — 5개 기능

### 3.1 Endowed Progress UI (Sprint 1-A, 3일)

> "18단계 중 3단계 이미 완료(17%)" — 초기 이탈 20-55% 감소

**원리**: 인테이크에서 수집한 6개 필드(업종, 지역, 형태, 방식, 오픈시점, 예산)를 "이미 완료한 준비 작업"으로 프레이밍. 프로그레스 바가 0%가 아니라 17%에서 시작하는 것처럼 표시.

**구현 방식**:

#### A. 상수 정의 (`roadmap-constants.ts`)
```typescript
/** Endowed Progress: 인테이크 수집 정보를 "이미 완료한 준비 단계"로 프레이밍 */
export const ENDOWED_STEPS = 3; // 정보 수집 + 업종 분석 + 규제 매핑
export const ENDOWED_LABELS = [
  "비즈니스 정보 수집",
  "업종별 규제 분석",
  "맞춤 로드맵 설계",
];
```

#### B. 진행률 계산 로직 변경 (`roadmap-utils.ts`)
```typescript
export function computeEndowedProgress(
  completedSteps: number,
  totalSteps: number,
): { display: number; actual: number; endowedSteps: number; totalWithEndowed: number } {
  const endowedSteps = ENDOWED_STEPS;
  const totalWithEndowed = totalSteps + endowedSteps;
  const completedWithEndowed = completedSteps + endowedSteps;
  return {
    display: Math.round((completedWithEndowed / totalWithEndowed) * 100),
    actual: Math.round((completedSteps / totalSteps) * 100),
    endowedSteps,
    totalWithEndowed,
  };
}
```

#### C. RoadmapExecutionView 수정
- `overallProgress` 계산을 `computeEndowedProgress()` 사용으로 변경
- `RoadmapSidebar`에 `endowedSteps` prop 전달

#### D. RoadmapSidebar 수정
- "전체 진행률" 카드에 Endowed 반영된 퍼센트 표시
- 프로그레스 바 아래: `"✅ 3단계 준비 완료 + {completedSteps}/{totalSteps} 단계 진행 중"` 문구
- 로드맵 생성 직후 첫 방문 시 Endowed 배지 1회 표시:
  "이미 3단계 준비가 완료되었습니다! 정보 수집, 업종 분석, 규제 매핑이 끝났습니다."

#### E. DashboardView > ProgressCard 수정
- 원형 프로그레스에 Endowed 반영된 퍼센트 적용
- "준비 단계 포함" 라벨 추가

**검증 기준**:
- [ ] 새 로드맵(0개 완료) 진행률 ≈ 17% (3/(3+15) 기준)
- [ ] 3개 스텝 완료 시 ≈ 33% (6/18)
- [ ] 전체 완료 시 100%
- [ ] `npm run build` 성공

---

### 3.2 다음 3-5 액션 집중 표시 (Sprint 1-A, 2일)

> 현재 단계 + 다음 2개만 펼침, 나머지 접기 — 인지 부하 40% 감소

**원리**: Basecamp "Hill Chart" + Todoist 패턴. 현재 초점과 전체 조감을 분리.

**구현 방식**:

#### A. TimelinePhaseCard CURRENT 상태 수정
현재: 모든 스텝이 펼쳐진 상태.
변경: IN_PROGRESS 또는 첫 PENDING 스텝 + 다음 2개만 펼침. 나머지는 접힌 요약 목록.

```typescript
// 현재 CURRENT 렌더링 내부
const visibleCount = 3; // 현재 + 다음 2개
const activeIndex = group.steps.findIndex(
  (s) => s.status === "IN_PROGRESS" || s.status === "PENDING"
);
const visibleSlice = group.steps.slice(
  Math.max(0, activeIndex),
  activeIndex + visibleCount
);
const hiddenSteps = group.steps.filter((s) => !visibleSlice.includes(s));
```

#### B. 접힘 토글 추가
- 접힌 영역: "나머지 {N}개 단계 보기" 버튼
- 클릭 시 전체 표시, "접기" 버튼으로 변환
- `useState<boolean>(false)` — `showAllSteps`

#### C. 완료된 스텝은 자동 접힘
- DONE 상태 스텝: 한 줄 요약 (제목 + ✅)
- 완료 후 다음 PENDING 스텝이 자동으로 ACTIVE 슬롯에 진입

**검증 기준**:
- [ ] CURRENT Phase에서 최대 3개 스텝만 상세 표시
- [ ] "나머지 N개 단계 보기" 버튼 동작
- [ ] 전체 보기 → 접기 토글 정상
- [ ] 스텝 완료 시 다음 스텝이 ACTIVE 슬롯에 자연스럽게 표시

---

### 3.3 준비도 5단계 스코어 (Sprint 1-B, 5일)

> 🌱 아이디어 → 📋 준비 착수 → 📝 서류 준비 중 → ✅ 인허가 완료 → 🚀 창업 준비 완료

**원리**: Stripe Atlas "5단계 중 3단계 완료" 패턴. 진행률 숫자 대신 단계별 등급으로 목표 명확화.

**구현 방식**:

#### A. 등급 결정 로직 (`roadmap-utils.ts`)
```typescript
export type ReadinessLevel = 1 | 2 | 3 | 4 | 5;

export interface ReadinessInfo {
  level: ReadinessLevel;
  emoji: string;
  label: string;
  description: string;
}

export const READINESS_LEVELS: ReadinessInfo[] = [
  { level: 1, emoji: "🌱", label: "아이디어", description: "창업 아이디어를 구체화하는 단계" },
  { level: 2, emoji: "📋", label: "준비 착수", description: "필요한 절차를 파악하고 있는 단계" },
  { level: 3, emoji: "📝", label: "서류 준비 중", description: "서류와 인허가를 준비하는 단계" },
  { level: 4, emoji: "✅", label: "인허가 완료", description: "주요 인허가가 완료된 단계" },
  { level: 5, emoji: "🚀", label: "창업 준비 완료", description: "사업 시작을 위한 모든 준비가 끝난 단계" },
];

export function computeReadinessLevel(progressPercent: number): ReadinessInfo {
  if (progressPercent >= 90) return READINESS_LEVELS[4]; // 🚀
  if (progressPercent >= 65) return READINESS_LEVELS[3]; // ✅
  if (progressPercent >= 35) return READINESS_LEVELS[2]; // 📝
  if (progressPercent >= 10) return READINESS_LEVELS[1]; // 📋
  return READINESS_LEVELS[0]; // 🌱
}
```

#### B. ReadinessTracker 컴포넌트 (신규)
새 파일: `features/roadmap/components/ReadinessTracker.tsx`

- 5단계 수평 트랙 (step indicator)
- 현재 등급에 파란색 강조 + 이모지
- 이전 등급: 회색 체크
- 이후 등급: 회색 점선
- 등급 라벨 + 설명 텍스트

```
[✓ 아이디어] — [✓ 준비 착수] — [📝 서류 준비 중] — [○ 인허가 완료] — [○ 창업 준비 완료]
```

#### C. RoadmapSidebar에 통합
- "전체 진행률" 카드 내부, Progress bar 아래에 ReadinessTracker 배치
- 현재 등급: `{emoji} {label}` 강조 표시

#### D. DashboardView > ProgressCard에 통합
- 원형 프로그레스 아래에 현재 등급 배지
- `"현재 준비도: 📝 서류 준비 중"` 표시

#### E. 등급 업그레이드 토스트
- 등급 변경 감지: `useEffect`에서 이전 등급과 비교
- 변경 시 토스트 알림: `"🎉 준비도가 '📋 준비 착수'에서 '📝 서류 준비 중'으로 올라갔습니다!"`
- `localStorage`에 마지막 등급 저장하여 새로고침 후에도 비교 가능

**검증 기준**:
- [ ] 0% 진행 시 🌱 아이디어 표시
- [ ] 50% 진행 시 📝 서류 준비 중 표시
- [ ] 100% 진행 시 🚀 창업 준비 완료 표시
- [ ] 대시보드와 로드맵 뷰 양쪽 동일 등급 표시
- [ ] 등급 업그레이드 시 토스트 알림 1회 표시

---

### 3.4 마일스톤 축하 모먼트 (Sprint 1-B, 3일)

> Phase 완료 시 컨페티 + 인사이트 카드 — 완료 동기 강화

**원리**: Asana 변동비율 강화 스케줄. Phase 완료 = 확정 축하, 개별 스텝 완료 = 1/5 확률 랜덤.

**구현 방식**:

#### A. 의존성 추가
```bash
cd app-frontend && npm install canvas-confetti
npm install -D @types/canvas-confetti
```

#### B. 인사이트 카드 데이터 (`roadmap-constants.ts`)
```typescript
export const MILESTONE_INSIGHTS: Record<string, string[]> = {
  default: [
    "이 단계를 완료한 창업자의 87%가 1주 내 다음 단계도 완료했습니다.",
    "지금까지의 진행 속도라면, 목표보다 빠르게 준비를 마칠 수 있습니다.",
    "창업 준비의 가장 어려운 부분은 '시작'입니다. 이미 해내고 있습니다!",
    "같은 업종 창업자 평균보다 빠른 속도로 진행 중입니다.",
    "다음 단계는 보통 2-3일이면 충분합니다. 이 기세를 이어가세요!",
  ],
};
```

#### C. MilestoneCelebration 컴포넌트 (신규)
새 파일: `features/roadmap/components/MilestoneCelebration.tsx`

- **Phase 완료**: 오버레이 모달
  - 컨페티 애니메이션 (canvas-confetti)
  - 등급 변화 표시 (이전 → 현재)
  - 인사이트 카드 (랜덤 1개)
  - "계속하기" 버튼
- **스텝 완료 (1/5 확률)**:
  - 인라인 토스트 (하단 슬라이드업)
  - 인사이트 메시지 1줄
  - 3초 후 자동 닫힘

#### D. TimelinePhaseCard에 축하 트리거 통합
- Phase의 마지막 스텝 완료 시점 감지
- `group.state`가 CURRENT → COMPLETED 전환 시 MilestoneCelebration 트리거
- `useRef`로 이미 표시된 Phase 추적 (중복 방지)

#### E. TimelineStepItem에 랜덤 인사이트 트리거
- 스텝 완료 콜백 성공 후 `Math.random() < 0.2` 확률로 인사이트 토스트

**검증 기준**:
- [ ] Phase 완료 시 컨페티 + 모달 표시
- [ ] 인사이트 카드에 무작위 메시지 표시
- [ ] 같은 Phase에 대해 중복 축하 없음
- [ ] 스텝 완료 시 약 20% 확률로 토스트 표시
- [ ] 모바일에서 오버레이 정상 표시

---

### 3.5 첫 5분 경험 최적화 (Sprint 1-B, 2일)

> 인테이크 폼 즉시 정규화 확인 + 생성 중 업종 인사이트

**원리**: 각 답변 후 AI가 즉시 확인하는 느낌. "서울 강남구 카페로 설정합니다."

**구현 방식**:

#### A. RoadmapChatIntake 즉시 정규화 확인
- 각 "다음 질문" 클릭 시, 봇 대화 버블에 정규화 확인 메시지 추가:
  ```
  사용자: 카페
  봇: ✅ 업종을 '카페'로 설정합니다. 카페 창업 시 영업허가, 위생교육 등 평균 14단계 절차가 필요합니다.
  ```
- 확인 메시지는 프론트엔드 로컬 생성 (BE 호출 없음)
- 필드별 정규화 메시지 맵 (`INTAKE_CONFIRMATION_MESSAGES`)

```typescript
export const INTAKE_CONFIRMATION_MESSAGES: Record<string, (value: string) => string> = {
  business_type: (v) => `✅ 업종을 '${v}'(으)로 설정합니다.`,
  location: (v) => `✅ 지역을 '${v}'(으)로 설정합니다.`,
  startup_type: (v) => `✅ 창업 형태를 '${v}'(으)로 설정합니다.`,
  startup_method: (v) => `✅ 창업 방식을 '${v}'(으)로 설정합니다.`,
  open_timeline: (v) => `✅ 오픈 목표를 '${v}'(으)로 설정합니다.`,
  budget_range: (v) => `✅ 초기 예산을 '${v}'(으)로 설정합니다.`,
};
```

#### B. 대화 이력에 확인 메시지 포함
- `renderedHistory` 배열에 봇 확인 메시지를 각 답변 뒤에 삽입
- 봇 확인 메시지는 녹색 체크 스타일 (emerald 배경)

#### C. RoadmapGeneratingState 개선
- 정적 텍스트 3개 → stage별 동적 메시지로 변경:
  ```typescript
  const STAGE_MESSAGES: Record<string, string> = {
    QUEUED: "로드맵 생성을 준비하고 있습니다...",
    OUTLINE_GENERATING: "업종별 규제를 분석하여 전체 단계를 구성 중입니다...",
    DETAIL_GENERATING: "각 단계별 상세 체크리스트와 필요 서류를 매칭 중입니다...",
    SAVING: "생성된 로드맵을 저장하고 있습니다...",
  };
  ```
- 진행 중 업종 인사이트 슬라이딩 카드 (5초 간격 로테이션):
  ```typescript
  const GENERATING_INSIGHTS = [
    "💡 카페 창업 시 가장 먼저 확인할 것: 해당 지역의 영업 가능 용도",
    "💡 개인사업자 등록은 보통 1-2일이면 완료됩니다",
    "💡 위생교육은 사전 이수가 필요하며, 온라인으로도 가능합니다",
    "💡 인테리어 공사 전 소방시설 완비증명을 받아야 합니다",
  ];
  ```

**검증 기준**:
- [ ] 각 질문 답변 후 "✅ ... 설정합니다" 봇 메시지 표시
- [ ] 생성 중 stage별 메시지 변경
- [ ] 인사이트 카드 5초 간격 로테이션
- [ ] 기존 검증/제출 플로우 정상 동작

---

## 4. Sprint 구조

### Sprint 1-A (Week 1, 5일)

| 일차 | 작업 | 파일 |
|:----:|------|------|
| D1 | Endowed Progress 상수 + 계산 로직 | `roadmap-constants.ts`, `roadmap-utils.ts` |
| D2 | Endowed Progress UI 적용 (Sidebar + ExecutionView) | `RoadmapSidebar.tsx`, `RoadmapExecutionView.tsx` |
| D3 | Endowed Progress 대시보드 적용 + 배지 | `ProgressCard.tsx`, `DashboardView.tsx` |
| D4 | 다음 3-5 액션 집중 — Phase 카드 접힘 로직 | `TimelinePhaseCard.tsx` |
| D5 | 다음 3-5 액션 집중 — 토글 UI + 테스트 | `TimelinePhaseCard.tsx` |

**Sprint 1-A Go/No-Go**:
- `npm run build` 성공
- `npm run lint` 통과
- Endowed Progress 17% 표시 확인
- 스텝 접힘/펼침 동작 확인

### Sprint 1-B (Week 2-3, 10일)

| 일차 | 작업 | 파일 |
|:----:|------|------|
| D6 | 준비도 등급 로직 + 상수 정의 | `roadmap-utils.ts`, `roadmap-constants.ts` |
| D7 | ReadinessTracker 컴포넌트 구현 | `ReadinessTracker.tsx` (신규) |
| D8 | ReadinessTracker → Sidebar 통합 | `RoadmapSidebar.tsx` |
| D9 | ReadinessTracker → Dashboard 통합 | `ProgressCard.tsx`, `DashboardView.tsx` |
| D10 | 등급 업그레이드 토스트 + localStorage 연동 | `ReadinessTracker.tsx` |
| D11 | canvas-confetti 설치 + MilestoneCelebration 컴포넌트 | `MilestoneCelebration.tsx` (신규) |
| D12 | Phase 완료 축하 트리거 + 인사이트 카드 | `TimelinePhaseCard.tsx` |
| D13 | 스텝 완료 랜덤 인사이트 + 중복 방지 | `TimelineStepItem.tsx` |
| D14 | 인테이크 즉시 정규화 확인 메시지 | `RoadmapChatIntake.tsx` |
| D15 | 생성 중 동적 메시지 + 인사이트 로테이션 | `RoadmapGeneratingState.tsx` |

**Sprint 1-B 완료 기준**:
- `npm run build` 성공
- `npm run lint` 통과
- 5개 기능 모두 시각적 동작 확인

---

## 5. Risk Assessment

| 리스크 | 영향도 | 완화 전략 |
|--------|:------:|----------|
| TimelineStepItem 충돌 (Phase 0에서 이미 수정) | ★★★☆☆ | Phase 0 PR 머지 후 최신 develop에서 분기 |
| canvas-confetti SSR 호환성 | ★★☆☆☆ | `dynamic import` + `"use client"` 처리 |
| Endowed Progress 계산이 대시보드 API와 불일치 | ★★★☆☆ | 프론트엔드 계산만 사용, BE `progress` 필드 무시 |
| 준비도 등급 경계값이 실제 로드맵과 부자연스러움 | ★★☆☆☆ | 경계값을 configurable 상수로 분리, 추후 조정 |
| 접힘/펼침 UX가 사용자 혼란 유발 | ★★☆☆☆ | "나머지 N개 단계" 명확한 CTA, 첫 방문 시 펼친 상태 |

---

## 6. Success Metrics

| 지표 | 측정 방법 | 목표 |
|------|----------|------|
| Endowed Progress 적용률 | 배포 확인 | 100% |
| 준비도 스코어 표시 | 배포 확인 | 100% |
| 첫 단계 진입율 | 이벤트 트래킹 (향후) | >= 40% (24시간 내) |
| 초기 이탈률 | 이벤트 트래킹 (향후) | < 60% |
| `npm run build` | CI | 성공 |
| `npm run lint` | CI | 통과 |

---

## 7. 파일 변경 요약

### 수정 파일 (10개)
| 파일 | 변경 내용 |
|------|----------|
| `roadmap-constants.ts` | Endowed 상수, 인사이트 데이터, 확인 메시지, 생성 단계 메시지 |
| `roadmap-utils.ts` | `computeEndowedProgress()`, `computeReadinessLevel()`, ReadinessInfo 타입 |
| `RoadmapExecutionView.tsx` | Endowed Progress 계산 적용 |
| `RoadmapSidebar.tsx` | Endowed 진행률 + ReadinessTracker 통합 |
| `TimelinePhaseCard.tsx` | 3-5 액션 집중 접힘 + 축하 트리거 |
| `TimelineStepItem.tsx` | 랜덤 인사이트 토스트 |
| `RoadmapChatIntake.tsx` | 즉시 정규화 확인 메시지 |
| `RoadmapGeneratingState.tsx` | 동적 stage 메시지 + 인사이트 로테이션 |
| `ProgressCard.tsx` | Endowed Progress + 준비도 배지 |
| `DashboardView.tsx` | Endowed Progress 전달 |

### 신규 파일 (2개)
| 파일 | 용도 |
|------|------|
| `ReadinessTracker.tsx` | 5단계 준비도 트랙 컴포넌트 |
| `MilestoneCelebration.tsx` | 마일스톤 축하 모달/토스트 |

### 의존성 추가 (1개)
| 패키지 | 용도 |
|--------|------|
| `canvas-confetti` | 컨페티 애니메이션 |

---

## 8. Quality Gates

변경 완료 전 반드시 실행:

```bash
cd app-frontend && npm run lint      # ESLint 통과
cd app-frontend && npm run build     # Next.js 빌드 성공
cd app-frontend && npm test          # Jest 테스트 통과 (있는 경우)
```

### 수동 검증 체크리스트
- [ ] 로드맵 없는 상태 → 인테이크 → 정규화 확인 메시지 표시
- [ ] 로드맵 생성 중 → 동적 메시지 + 인사이트 로테이션
- [ ] 새 로드맵 → Endowed Progress 17% 시작
- [ ] 로드맵 실행 뷰 → 3개 스텝만 펼침, 나머지 접힘
- [ ] 스텝 완료 → 가끔 인사이트 토스트 (체감 20%)
- [ ] Phase 완료 → 컨페티 + 인사이트 모달
- [ ] 사이드바 → 준비도 5단계 트랙 표시
- [ ] 대시보드 → 준비도 배지 표시
- [ ] 모바일 반응형 정상
