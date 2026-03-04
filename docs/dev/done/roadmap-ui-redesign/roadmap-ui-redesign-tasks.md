# 로드맵 UI 리디자인 - Tasks

> Last Updated: 2026-02-24
> Status: COMPLETED

## Phase 1: 백엔드 변경

- [x] **B1** `RoadmapStep` 모델에 `completed_at` 추가 [S]
- [x] **B2** 상태 전환 시 `completed_at` 기록 [S]
- [x] **B3** 응답 스키마 업데이트 [S]
- [x] **B4** 직렬화 함수 업데이트 [S]

## Phase 2: 프론트엔드 유틸리티

- [x] **F1** `roadmap-utils.ts` 생성 [M]

## Phase 3: 프레젠테이셔널 컴포넌트

- [x] **F2** `RoadmapHeader.tsx` 생성 [S]
- [x] **F3** `TimelineStepItem.tsx` 생성 [M]
- [x] **F4** `TimelinePhaseCard.tsx` 생성 [L]
- [x] **F5** `RoadmapSidebar.tsx` 생성 [M]

## Phase 4: 통합

- [x] **F6** `RoadmapExecutionView.tsx` 재작성 [L]
- [x] **F7** 타입 업데이트 및 export [S]

## Phase 5: 검증

- [x] **V1** 백엔드 테스트 통과 확인 (65 passed)
- [x] **V2** 프론트엔드 빌드 검증 (tsc + next build 통과)
- [x] **V3** API 응답 확인 (created_at, completed_at 포함)
- [x] **V4** 브라우저 테스트 (6차 피드백 반영 완료)

## 추가 구현 (피드백 반영)

- [x] AI Advisor 카드 제거, 창업 법령 가이드 링크 연동
- [x] 사이드바 카드 디자인 통일 (white card)
- [x] 전체 진행률 카드를 사이드바 상단으로 이동
- [x] 타임라인/사이드바 독립 스크롤 + scrollbar-thin
- [x] LOCKED/FUTURE 단계에 step 목록 표시
- [x] 현재 진행 단계로 자동 스크롤
- [x] CURRENT 카드 진행률을 체크리스트 기준으로 변경
- [x] 완료 처리 전 확인 UI 추가
- [x] 되돌리기 기능 (마지막 완료 단계만, 백엔드 검증 포함)
