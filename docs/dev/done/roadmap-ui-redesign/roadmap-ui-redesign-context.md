# 로드맵 UI 리디자인 - Context

> Last Updated: 2026-02-24

## 디자인 레퍼런스

- `.temp/stitch_stepzero_roadmaps/screen.png` — 수직 타임라인 디자인 스크린샷
- `.temp/stitch_stepzero_roadmaps/code.html` — 전체 HTML/Tailwind CSS 구현 코드

## Key Files

### 백엔드 (수정 대상)

| 파일 | 역할 | 변경 내용 |
|------|------|----------|
| `app-backend/app/models/roadmap.py` | SQLModel 정의 | `RoadmapStep.completed_at` 추가 |
| `app-backend/app/features/roadmaps/application/roadmap_progress_service.py` | Step 상태 전환 로직 | `completed_at` 타임스탬프 관리 |
| `app-backend/app/api/v1/schemas.py` | Pydantic 응답 스키마 | `completed_at`, `created_at` 추가 |
| `app-backend/app/api/v1/roadmaps/get.py` | API 직렬화 | 새 필드 직렬화 |

### 프론트엔드 (수정 대상)

| 파일 | 역할 | 변경 내용 |
|------|------|----------|
| `app-frontend/src/features/roadmap/components/RoadmapExecutionView.tsx` | 메인 실행 뷰 (291줄) | 전면 재작성 |
| `app-frontend/src/features/roadmap/components/index.ts` | 컴포넌트 export | 신규 컴포넌트 export 추가 |
| `app-frontend/src/app/(dashboard)/roadmap/page.tsx` | 페이지 오케스트레이터 (165줄) | 타입 확장 (`created_at`) |

### 프론트엔드 (신규 생성)

| 파일 | 역할 |
|------|------|
| `app-frontend/src/features/roadmap/components/roadmap-utils.ts` | Phase 상태 도출, 타입, 상수, 유틸 함수 |
| `app-frontend/src/features/roadmap/components/RoadmapHeader.tsx` | 헤더 (타이틀 + 진행률) |
| `app-frontend/src/features/roadmap/components/TimelineStepItem.tsx` | Step 아이템 (체크리스트) |
| `app-frontend/src/features/roadmap/components/TimelinePhaseCard.tsx` | Phase 카드 (타임라인 dot + 확장) |
| `app-frontend/src/features/roadmap/components/RoadmapSidebar.tsx` | 사이드바 (AI + 일정 + 가이드) |

### 참고 파일 (변경 없음)

| 파일 | 참고 이유 |
|------|----------|
| `app-frontend/src/features/dashboard/components/RoadmapStepper.tsx` | 타임라인 dot/색상 패턴 참고 |
| `app-frontend/src/components/ui/progress.tsx` | shadcn/ui Progress 컴포넌트 확인 |
| `app-backend/app/repositories/roadmap_repository.py` | 쿼리 패턴 참고 |

## Key Decisions

### 1. `completed_at` NULLABLE TIMESTAMP
- 기존 데이터에 영향 없음 (NULL 기본값)
- 마이그레이션: `ALTER TABLE roadmapstep ADD COLUMN completed_at TIMESTAMP;`
- `datetime.utcnow()` 패턴 사용 (asyncpg TIMESTAMP WITHOUT TIME ZONE 호환)

### 2. Phase 상태 도출 (클라이언트 사이드)
- 백엔드에 Phase 엔티티 없음 → `RoadmapStepDetail.phase`로 그룹핑
- Phase 상태 규칙:
  - COMPLETED: 모든 step이 COMPLETED
  - CURRENT: 하나 이상의 step이 IN_PROGRESS
  - LOCKED: 이전 Phase가 미완료
  - FUTURE: LOCKED 이후의 Phase

### 3. D-Day 날짜 계산 (클라이언트 사이드)
- `roadmap.created_at` + 누적 `estimated_days`로 예상 마감일 도출
- 백엔드에 별도 deadline 필드 불필요

### 4. 선행 조건 메시지 (클라이언트 사이드)
- LOCKED step에 "'{이전 step 이름}' 완료 후 진행 가능" 표시
- 백엔드 변경 불필요

### 5. 가이드북/AI 어드바이저
- 현재 ActionKit 기능 존재하나 미연결
- 1차: 정적 placeholder로 처리
- 추후: ActionKit 연동 고려

## Dependencies

### 기존 설치 확인됨
- shadcn/ui: Card, CardContent, Badge, Button, Progress
- lucide-react: 다양한 아이콘
- tailwindcss-animate: 애니메이션

### 현재 타입 정의 (RoadmapExecutionView.tsx 내 인라인)

```typescript
interface RoadmapDetailAction {
    id: number;
    action_type: string;
    title: string;
    description: string;
    source_url?: string | null;
    metadata_json?: Record<string, unknown>;
}

interface RoadmapDetailStep {
    id: number;
    title: string;
    status: string;
    detail?: {
        id: number;
        phase: string;
        objective: string;
        estimated_days: number;
        actions: RoadmapDetailAction[];
    } | null;
}

interface RoadmapDetailResponse {
    roadmap_id: string;
    title: string;
    steps: RoadmapDetailStep[];
}
```

**변경 후 추가 필드:**
- `RoadmapDetailResponse.created_at: string` (ISO format)
- `RoadmapDetailStep.completed_at: string | null` (ISO format)

## Props 인터페이스 (유지)

```typescript
interface RoadmapExecutionViewProps {
    data: RoadmapDetailResponse;
    onStepStatusChange: (stepId: number, status: "IN_PROGRESS" | "COMPLETED") => Promise<void>;
    onActionCompletionChange: (stepId: number, actionId: number, completed: boolean) => Promise<void>;
    updatingStepId: number | null;
    updatingActionId: number | null;
}
```
