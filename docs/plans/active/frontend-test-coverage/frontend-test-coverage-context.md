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
| growth-club | growthClubApi (8개 메서드), usePosts, PostCard | API + 훅 + 컴포넌트 |
| chat | api.ts, sse.ts, useChat, ChatInput | API + 유틸 + 훅 + 컴포넌트 |
| roadmap | useRoadmapJob, useRoadmapList, RoadmapSwitcher, ReadinessTracker | 훅 + 컴포넌트 |
| notifications | API, useNotifications, NotificationBell | API + 훅 + 컴포넌트 |
| shared | url.ts, validation.ts | 유틸 |

## Key Decisions

| 결정 | 근거 |
|------|------|
| ops feature 제외 | 관리자 전용, 낮은 사용 빈도, 모킹 복잡도 높음 |
| profile feature 제외 | 구조만 존재, 실질 로직 미미 |
| 순수 함수 → 훅 → 컴포넌트 순서 | 난이도 점진적 상승, 초기 ROI 극대화 |
| renderHook 패턴 채택 | @testing-library/react 내장, 추가 의존성 불필요 |

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

## Dependencies

- `@testing-library/react` — 이미 설치됨
- `jest` ^30.2.0, `jest-environment-jsdom` ^30.2.0 — 이미 설치됨
- 추가 패키지 불필요
