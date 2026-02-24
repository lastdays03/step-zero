# 로드맵 실행 화면 UI 리디자인

> Last Updated: 2026-02-24

## Executive Summary

현재 로드맵 실행 뷰(`RoadmapExecutionView.tsx`)를 3컬럼 그리드에서 **수직 타임라인 기반 2컬럼 레이아웃**으로 전면 리디자인한다. 백엔드 API에 누락된 필드(`completed_at`, `created_at`)를 추가하고, 프론트엔드를 6개 서브 컴포넌트로 분해하여 Phase 상태별 시각적 구분과 D-Day 일정 계산을 구현한다.

## Current State Analysis

### 현재 레이아웃
- 3컬럼 그리드: 왼쪽 Phase 버튼(220px) | 중앙 Step 카드(1fr) | 오른쪽 상태(300px)
- Phase 선택 기반 (클릭해서 전환)
- 단순한 진행률 표시

### 백엔드 API 갭
| 디자인 요구사항 | 현재 상태 | 필요한 변경 |
|----------------|----------|------------|
| Phase 완료 날짜 | `RoadmapStep`에 `completed_at` 없음 | 모델 + 서비스 + 스키마 |
| 로드맵 생성일 (D-Day 기준) | `RoadmapDetailResponse`에 `created_at` 미포함 | 응답 스키마에 추가 |
| 캘린더 날짜 | `estimated_days`만 존재 | 프론트에서 계산 (변경 불필요) |
| Phase 설명 | step 수준 `objective`만 | 클라이언트 도출 (변경 불필요) |

## Proposed Future State

| 항목 | 현재 | 변경 후 |
|------|------|---------|
| 레이아웃 | 3컬럼 | 2컬럼 (8cols + 4cols) |
| Phase 표현 | 버튼 리스트 | 수직 타임라인 카드 (dot + line) |
| Phase 상태 | 선택 기반 | COMPLETED/CURRENT/LOCKED/FUTURE 시각적 구분 |
| Step 표현 | 플랫 카드 리스트 | CURRENT Phase 내 인라인 체크리스트 |
| 사이드바 | 상태/일정/도움말 | AI 어드바이저 + D-Day 일정 + 가이드북 |

## Implementation Phases

### Phase 1: 백엔드 변경 (B1~B4)

#### B1. `RoadmapStep` 모델에 `completed_at` 추가 [S]
- **파일**: `app-backend/app/models/roadmap.py`
- `completed_at: datetime | None = None` 필드 추가
- DB 마이그레이션: `ALTER TABLE roadmapstep ADD COLUMN completed_at TIMESTAMP;`

#### B2. 상태 전환 시 `completed_at` 기록 [S]
- **파일**: `app-backend/app/features/roadmaps/application/roadmap_progress_service.py`
- `_apply_step_status_transition`: COMPLETED 전환 시 타임스탬프 기록
- `update_action_completion`: 자동 완료/되돌림 시 동기화
- 의존: B1

#### B3. 응답 스키마 업데이트 [S]
- **파일**: `app-backend/app/api/v1/schemas.py`
- `RoadmapDetailStepResponse`에 `completed_at: str | None` 추가
- `RoadmapDetailResponse`에 `created_at: str` 추가

#### B4. 직렬화 함수 업데이트 [S]
- **파일**: `app-backend/app/api/v1/roadmaps/get.py`
- `_serialize_roadmap_detail`에서 새 필드 포함
- 의존: B1, B3

### Phase 2: 프론트엔드 유틸리티 (F1)

#### F1. `roadmap-utils.ts` 생성 [M]
- **파일**: `app-frontend/src/features/roadmap/components/roadmap-utils.ts`
- 타입: `PhaseState`, `StepItemState`, `EnhancedPhaseGroup`
- 상수: `STATUS_LABEL`, `ACTION_TYPE_LABEL`, `TOGGLE_ACTION_TYPES`
- 함수: `derivePhaseGroups()`, `deriveStepItemState()`, `computeDeadlineDate()`

### Phase 3: 프레젠테이셔널 컴포넌트 (F2~F5)

#### F2. `RoadmapHeader.tsx` [S]
- Props: `title`, `currentPhaseName`, `overallProgress`, `completedSteps`, `totalSteps`
- shadcn/ui: Card, CardContent, Progress

#### F3. `TimelineStepItem.tsx` [M]
- 3가지 상태: DONE / ACTIVE / LOCKED
- 체크리스트 토글, 선행 조건 메시지, 액션 버튼

#### F4. `TimelinePhaseCard.tsx` [L]
- COMPLETED: 초록 dot, 접힌 카드, `completed_at` 날짜
- CURRENT: blue dot + ring, 확장 카드, 진행률 바
- LOCKED: 회색 dot, dashed 보더
- FUTURE: 작은 dot, 텍스트만
- 의존: F3

#### F5. `RoadmapSidebar.tsx` [M]
- AI 어드바이저 카드 (placeholder)
- 주요 일정 카드 (D-Day, `computeDeadlineDate()`)
- 가이드북 카드 (placeholder)
- 의존: F1

### Phase 4: 통합 (F6~F7)

#### F6. `RoadmapExecutionView.tsx` 재작성 [L]
- 컴포넌트 조합, 2컬럼(lg:grid-cols-12) 레이아웃
- 의존: F1~F5

#### F7. 프론트엔드 타입 업데이트 [S]
- `RoadmapDetailResponse`에 `created_at: string` 추가
- `RoadmapDetailStep`에 `completed_at: string | null` 추가
- `page.tsx` 및 `index.ts` 업데이트

## 데이터 흐름

```
백엔드 DB                    API 응답                     프론트엔드 도출
─────────                    ────────                     ──────────────
Roadmap.created_at      →  created_at (ISO string)    →  D-Day 날짜 계산 기준
RoadmapStep.completed_at →  completed_at (ISO string)  →  Phase 완료 날짜 표시
RoadmapStep.status       →  status                     →  Phase 상태 도출
RoadmapStepDetail.phase  →  phase                      →  Phase 그룹핑
  .estimated_days        →  estimated_days             →  예상 마감일 계산
  .objective             →  objective                  →  Phase 설명
```

## 컴포넌트 구조

```
RoadmapExecutionView (오케스트레이터)
├── RoadmapHeader
├── Main (lg:col-span-8) — 수직 타임라인
│   ├── 타임라인 라인 (absolute, w-0.5)
│   └── TimelinePhaseCard × N
│       ├── 타임라인 dot (상태별)
│       ├── 상태 Badge + 완료 날짜
│       └── TimelineStepItem × N (CURRENT만 확장)
└── RoadmapSidebar (lg:col-span-4)
    ├── AI 어드바이저
    ├── 주요 일정 (D-Day)
    └── 가이드북
```

## Risk Assessment

| 리스크 | 영향 | 완화 전략 |
|--------|------|----------|
| DB 마이그레이션 실패 | 높음 | NULLABLE 컬럼 추가로 기존 데이터 영향 없음 |
| 기존 테스트 깨짐 | 중간 | 스키마 변경 시 기본값 설정으로 하위 호환 유지 |
| 타입 불일치 | 중간 | `tsc --noEmit`으로 빌드 전 검증 |
| 반응형 레이아웃 깨짐 | 낮음 | lg breakpoint 기준 2컬럼/1컬럼 전환 |

## Success Metrics

1. `python -m pytest` 전체 통과
2. `npx tsc --noEmit` 에러 없음
3. `npx next build` 성공
4. GET `/roadmaps/latest/detail` 응답에 `created_at`, `completed_at` 포함
5. Phase별 타임라인 카드 정상 렌더링
6. Step 상태 변경/체크박스 토글 동작

## Resources & Dependencies

- **shadcn/ui**: Card, CardContent, Badge, Button, Progress (기존 설치)
- **lucide-react**: Check, Lock, ChevronDown, ChevronUp, Bot, BookOpen, ExternalLink
- **디자인 레퍼런스**: `.temp/stitch_stepzero_roadmaps/screen.png`, `code.html`

## Timeline

| Phase | 작업 | 예상 Effort |
|-------|------|------------|
| 1 | 백엔드 B1~B4 | S (각각) |
| 2 | F1 유틸리티 | M |
| 3 | F2~F5 컴포넌트 | S~L |
| 4 | F6~F7 통합 | L + S |
