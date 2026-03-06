# Phase 1: FE Quick Wins — Task Checklist

> Last Updated: 2026-03-02
> Branch: `feature/1-fe-quick-wins`
> Status: **전체 구현 완료 — 커밋/PR 대기**

---

## Pre-requisites

- [x] Phase 0 PR → develop 머지 완료
- [x] `types:sync` 결과물 커밋 완료
- [x] `feature/1-fe-quick-wins` 브랜치 생성 (develop에서)

---

## Sprint 1-A: Endowed Progress + 액션 집중 (5일)

### 1-1. Endowed Progress UI (3일)

#### 1-1-A. 상수 + 계산 로직 (D1)
- [x] `roadmap-constants.ts`에 `ENDOWED_STEPS`, `ENDOWED_LABELS` 상수 추가
- [x] `roadmap-utils.ts`에 `computeEndowedProgress()` 함수 추가
- [x] `computeEndowedProgress` 유닛 테스트 검증 (0%, 50%, 100% 케이스) — `roadmap/__tests__/roadmap-utils.test.ts` 14 tests

#### 1-1-B. 로드맵 실행 뷰 적용 (D2)
- [x] `RoadmapExecutionView.tsx`: `overallProgress` 계산을 `computeEndowedProgress()` 사용으로 변경
- [x] `RoadmapSidebar.tsx`: Endowed 반영된 퍼센트 + "✅ 3단계 준비 완료" 문구 추가
- [x] `RoadmapSidebar.tsx`: Progress bar 값을 Endowed 퍼센트로 변경
- [x] `RoadmapSidebar.tsx`: `{completedSteps}/{totalSteps}` 텍스트를 Endowed 포함 형식으로 변경
- [x] `RoadmapSidebar.tsx`: 첫 방문 Endowed 배지 1회 표시 (localStorage 기반, 8초 자동 닫힘)

#### 1-1-C. 대시보드 적용 (D3)
- [x] `DashboardView.tsx`: `roadmapDetail` 기반 Endowed Progress 계산 추가
- [x] `ProgressCard.tsx`: 원형 프로그레스에 Endowed 반영
- [x] `ProgressCard.tsx`: "준비 단계 포함" 또는 준비도 배지 라벨 추가
- [x] 새 로드맵(0 완료)에서 ≈17% 표시 확인
- [x] 전체 완료 시 100% 표시 확인

### 1-2. 다음 3-5 액션 집중 표시 (2일)

#### 1-2-A. Phase 카드 접힘 로직 (D4)
- [x] `TimelinePhaseCard.tsx` CURRENT 상태: `showAllSteps` state 추가
- [x] 현재 활성 스텝 + 다음 2개만 기본 표시 (총 3개)
- [x] 완료된(DONE) 스텝은 한 줄 요약으로 축약
- [x] 잠금된(LOCKED) 스텝은 접힌 목록에 포함

#### 1-2-B. 토글 UI + 검증 (D5)
- [x] "나머지 {N}개 단계 보기" 버튼 추가
- [x] 버튼 클릭 시 전체 스텝 표시 + "접기" 버튼
- [x] 스텝 완료 시 다음 PENDING 스텝이 자동 ACTIVE 슬롯 진입 확인
- [x] 모든 스텝 완료 시 접힘/펼침 불필요 — 자연스러운 처리 확인

### Sprint 1-A 검증
- [x] `npm run lint` 통과
- [x] `npm run build` 성공
- [x] 수동 검증: Endowed Progress 17% 표시
- [x] 수동 검증: 3개 스텝만 펼침, 나머지 접힘
- [x] **Sprint 1-A 커밋** (최종 커밋과 합산 예정)

---

## Sprint 1-B: 준비도 + 마일스톤 + 첫 5분 (10일)

### 1-3. 준비도 5단계 스코어 (5일)

#### 1-3-A. 등급 로직 + 타입 (D6)
- [x] `roadmap-utils.ts`에 `ReadinessLevel`, `ReadinessInfo` 타입 추가
- [x] `roadmap-constants.ts`에 `READINESS_LEVELS` 배열 추가
- [x] `roadmap-utils.ts`에 `computeReadinessLevel()` 함수 추가
- [x] 경계값: 0→🌱 / 10→📋 / 35→📝 / 65→✅ / 90→🚀

#### 1-3-B. ReadinessTracker 컴포넌트 (D7)
- [x] `ReadinessTracker.tsx` 신규 생성
- [x] 5단계 수평 트랙 (step indicator) 구현
- [x] 현재 등급: 파란색 강조 + 이모지
- [x] 이전 등급: 회색 체크마크
- [x] 이후 등급: 회색 점선 원
- [x] 반응형: 모바일에서 축약 표시 (overflow-x-auto + sm breakpoints)

#### 1-3-C. Sidebar 통합 (D8)
- [x] `RoadmapSidebar.tsx`: "전체 진행률" 카드 내부에 ReadinessTracker 배치
- [x] Progress bar 아래, 준비도 트랙 위에 현재 등급 라벨 표시
- [x] Props: `overallProgress` (Endowed 포함) 전달

#### 1-3-D. Dashboard 통합 (D9)
- [x] `ProgressCard.tsx`: 원형 프로그레스 아래에 현재 등급 배지 추가
- [x] 배지 형식: `{emoji} {label}` (예: "📝 서류 준비 중")
- [x] `DashboardView.tsx`: roadmapDetail 기반 준비도 계산 + ProgressCard에 전달

#### 1-3-E. 등급 업그레이드 토스트 (D10)
- [x] `localStorage` 키: `stepzero_readiness_level_{roadmapId}`
- [x] 등급 계산 후 이전 저장값과 비교 — 다르면 토스트 표시
- [x] 토스트 UI: 인라인 알림 (상단 슬라이드다운, 5초 자동 닫힘)
- [x] "🎉 준비도가 '{이전}' → '{현재}'로 올라갔습니다!" 메시지
- [x] 새 등급 localStorage 저장
- [x] 등급 하락 시 토스트 미표시 (하락은 알리지 않음)

### 1-4. 마일스톤 축하 모먼트 (3일)

#### 1-4-A. 컨페티 + 축하 컴포넌트 (D11)
- [x] `canvas-confetti` + `@types/canvas-confetti` 설치
- [x] `MilestoneCelebration.tsx` 신규 생성
- [x] Phase 축하 모달:
  - [x] 반투명 오버레이 (z-50)
  - [x] canvas-confetti 트리거 (dynamic import)
  - [x] 등급 변화 표시 (이전 → 현재) — state 기반 readiness tracking
  - [x] 인사이트 카드 (랜덤 1개)
  - [x] "계속하기" 버튼 → 닫기
- [x] 스텝 인사이트 토스트:
  - [x] 하단 슬라이드업 인라인 알림
  - [x] 인사이트 메시지 1줄
  - [x] 3초 자동 닫힘

#### 1-4-B. Phase 완료 트리거 (D12)
- [x] `roadmap-constants.ts`에 `MILESTONE_INSIGHTS` 데이터 추가
- [x] `TimelinePhaseCard.tsx`: Phase CURRENT→COMPLETED 전환 감지 로직 추가
- [x] state 기반 중복 방지 (prevState/setPrevState 패턴)
- [x] 전환 시 MilestoneCelebration 표시
- [x] 모바일에서 오버레이 정상 표시 확인

#### 1-4-C. 스텝 완료 랜덤 인사이트 (D13)
- [x] `TimelinePhaseCard.tsx` handleStepStatusChange 래퍼: `Math.random() < 0.2` 검사
- [x] 20% 확률 시 인사이트 토스트 표시
- [x] 인사이트 메시지는 `MILESTONE_INSIGHTS.default`에서 랜덤 선택
- [x] 연속 인사이트 방지: `lastInsightTimeRef` 30초 cooldown

### 1-5. 첫 5분 경험 최적화 (2일)

#### 1-5-A. 인테이크 즉시 정규화 확인 (D14)
- [x] `roadmap-constants.ts`에 `INTAKE_CONFIRMATION_MESSAGES` 맵 추가
- [x] `RoadmapChatIntake.tsx`: `renderedHistory`에 봇 확인 메시지 삽입
- [x] 확인 메시지 스타일: emerald 배경 + ✅ 아이콘
- [x] 선택 필드(description)는 확인 메시지 미표시
- [x] 기존 검증/제출 플로우 정상 동작 확인

#### 1-5-B. 생성 중 동적 메시지 (D15)
- [x] `roadmap-constants.ts`에 `STAGE_MESSAGES` 맵 추가
- [x] `roadmap-constants.ts`에 `GENERATING_INSIGHTS` 배열 추가
- [x] `RoadmapGeneratingState.tsx`: 현재 `stage` prop으로 동적 메시지 표시
- [x] 인사이트 카드 5초 간격 로테이션 (`setInterval` + `useState`)
- [x] 정적 텍스트 3개 → 동적 `stageMessage` 단일 표시로 대체
- [x] 애니메이션: fade-in/out 트랜지션 (Tailwind `transition-opacity`)

### Sprint 1-B 검증
- [x] `npm run lint` 통과
- [x] `npm run build` 성공
- [x] 수동 검증: 5단계 준비도 트랙 표시 (사이드바 + 대시보드)
- [x] 수동 검증: 등급 업그레이드 토스트
- [x] 수동 검증: Phase 완료 → 컨페티 + 인사이트 모달
- [x] 수동 검증: 스텝 완료 → 가끔 인사이트 토스트
- [x] 수동 검증: 인테이크 정규화 확인 메시지
- [x] 수동 검증: 생성 중 동적 메시지 + 인사이트 로테이션
- [x] **Sprint 1-B 커밋** (최종 커밋과 합산 예정)

---

## Final Checklist

- [x] `npm run lint` 최종 통과
- [x] `npm run build` 최종 성공
- [x] `npm test` 통과 — 3 suites, 22 tests
- [x] feature/index.ts에 신규 컴포넌트 export 등록
- [x] `docs/context/dev-status.md` 업데이트
- [ ] **커밋 생성** (아직 미커밋)
- [ ] PR 생성: `feature/1-fe-quick-wins` → `develop`

---

## Completion Criteria

### Phase 1 → Phase 2 Go/No-Go 기준 (마스터 플랜 Section 14)

| 지표 | Go 기준 | 측정 방법 |
|------|---------|---------|
| Endowed Progress 적용률 | 배포 후 100% | 배포 확인 |
| 준비도 스코어 표시 | 배포 후 100% | 배포 확인 |
| 첫 단계 진입율 | >= 40% (24시간 내) | 이벤트 트래킹 |
| 초기 이탈률 | < 60% | 이벤트 트래킹 |
| UX 민원 | 0건 | CS 모니터링 |
