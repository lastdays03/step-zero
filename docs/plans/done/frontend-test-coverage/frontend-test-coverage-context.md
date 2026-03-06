# Context: 프론트엔드 테스트 커버리지 확대

> Last Updated: 2026-03-06

## Origin

- `docs/plans/done/test-performance-audit/` Phase 3 (P2) 항목에서 분리

## Key Files

### 테스트 인프라
| 파일 | 역할 |
|------|------|
| `app-frontend/jest.config.js` | Jest 설정 (jsdom, setupFiles) |
| `app-frontend/jest.setup.js` | `@testing-library/jest-dom` import |

### 기존 테스트 (참조 패턴)
| 파일 | 패턴 |
|------|------|
| `features/auth/__tests__/LoginForm.test.tsx` | 컴포넌트 + 훅 mock 통합 |
| `features/roadmap/__tests__/roadmap-utils.test.ts` | 순수 함수 단위 |
| `features/dashboard/__tests__/Dashboard.test.tsx` | 비동기 API mock + waitFor |

### 테스트 대상 (우선순위순)
| Feature | 주요 대상 | 테스트 종류 |
|---------|----------|------------|
| growth-club | `api/growth-club.ts` (8개 메서드), usePosts, PostCard | API + 훅 + 컴포넌트 |
| chat | `utils/api.ts` (6개 함수), `utils/sse.ts`, useChat, ChatInput | API + 유틸 + 훅 + 컴포넌트 |
| roadmap | useRoadmapJob, useRoadmapList, useActiveRoadmap, RoadmapSwitcher, ReadinessTracker | 훅 + 컴포넌트 |
| notifications | `api/notifications.ts` (3개 메서드), useNotifications, NotificationBell | API + 훅 + 컴포넌트 |
| actionkit | `hooks/useActionKit.ts` (API 호출 + 상태 관리) | 훅 |
| shared | `file/utils/url.ts`, `file/utils/validation.ts` | 유틸 |

### 제외 대상 (근거)
| Feature | 제외 사유 |
|---------|----------|
| ops | 관리자 전용, 낮은 사용 빈도, superuser 의존성으로 모킹 복잡 |
| profile | 구조만 존재, 실질 비즈니스 로직 미미 |
| announcements | 단순 목록 조회/표시, 별도 비즈니스 로직 없음 |

## Key Decisions

| 결정 | 근거 |
|------|------|
| ops feature 제외 | 관리자 전용, 낮은 사용 빈도, superuser 모킹 복잡 |
| profile feature 제외 | 구조만 존재, 실질 로직 미미 |
| announcements feature 제외 | 단순 목록 조회/표시, 별도 비즈니스 로직 없음 |
| actionkit은 훅만 테스트 | `api/index.ts`가 빈 파일, 테스트 가능 로직은 `useActionKit` 훅에 집중 |
| 순수 함수 → 훅 → 컴포넌트 순서 | 난이도 점진적 상승, 초기 ROI 극대화 |
| renderHook 패턴 채택 | @testing-library/react 내장, 추가 의존성 불필요 |
| feature 커버리지 = `__tests__/` 존재 + 통과 테스트 1개 이상 | 코드 라인 커버리지(%)는 추후 별도 계획으로 |

## Testing Patterns

### API 유틸 테스트 패턴
```typescript
jest.mock('@/lib/api-client');
const mockGet = jest.mocked(apiClient.get);
mockGet.mockResolvedValue({ data: { ... } });
await expect(fetchSomething()).resolves.toEqual(...);
expect(mockGet).toHaveBeenCalledWith('/api/v1/...');
```

### 훅 테스트 패턴
```typescript
import { renderHook, waitFor } from '@testing-library/react';
const { result } = renderHook(() => useMyHook());
await waitFor(() => expect(result.current.data).toBeDefined());
```

### 컴포넌트 테스트 패턴
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
render(<MyComponent />);
expect(screen.getByText('...')).toBeInTheDocument();
fireEvent.click(screen.getByRole('button'));
```

## File Path Reference

> shared 유틸은 `features/shared/file/utils/`에 위치 (`features/shared/utils/`가 아님)

| 대상 | 실제 경로 |
|------|---------|
| SSE 파서 | `features/chat/utils/sse.ts` |
| 채팅 API | `features/chat/utils/api.ts` (6개 함수) |
| ChatInput | `features/chat/components/ChatInput.tsx` |
| URL 유틸 | `features/shared/file/utils/url.ts` |
| 파일 검증 | `features/shared/file/utils/validation.ts` |
| Growth Club API | `features/growth-club/api/growth-club.ts` (8개 메서드) |
| PostCard | `features/growth-club/components/PostCard.tsx` |
| CreatePostForm | `features/growth-club/components/CreatePostForm.tsx` |
| usePosts | `features/growth-club/hooks/usePosts.ts` |
| Notifications API | `features/notifications/api/notifications.ts` (3개 메서드) |
| NotificationBell | `features/notifications/components/NotificationBell.tsx` |
| useRoadmapJob | `features/roadmap/hooks/useRoadmapJob.ts` |
| useRoadmapList | `features/roadmap/hooks/useRoadmapList.ts` |
| useActiveRoadmap | `features/roadmap/hooks/useActiveRoadmap.ts` |
| RoadmapSwitcher | `features/roadmap/components/RoadmapSwitcher.tsx` |
| ReadinessTracker | `features/roadmap/components/ReadinessTracker.tsx` |
| useActionKit | `features/actionkit/hooks/useActionKit.ts` |

## Dependencies

- `@testing-library/react` — 이미 설치됨
- `jest` ^30.2.0, `jest-environment-jsdom` ^30.2.0 — 이미 설치됨
- 추가 패키지 불필요
