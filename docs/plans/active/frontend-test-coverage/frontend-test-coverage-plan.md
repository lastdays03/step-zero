# Plan: 프론트엔드 테스트 커버리지 확대

> Last Updated: 2026-03-06

## Executive Summary

프론트엔드 8개 feature 중 3개(auth, dashboard, roadmap)만 테스트가 존재하며, 총 22개 테스트만 있다.
핵심 사용자 플로우(로드맵 생성, AI 채팅, 액션킷)의 프론트엔드 테스트가 부재하여 회귀 감지가 불가능하다.

순수 함수/유틸 → 훅 → 컴포넌트 순으로 테스트를 확대하여 핵심 비즈니스 로직의 커버리지를 확보한다.

## Current State

| 지표 | 현재 |
|------|------|
| 테스트 파일 | 3개 |
| 테스트 케이스 | 22개 |
| feature 커버리지 | 3/8 (37.5%) |
| 실행 시간 | 2.8초 |
| 테스트 종류 | 유틸 함수 14, 컴포넌트 8 |

### Feature별 현황

| Feature | 테스트 | 비고 |
|---------|--------|------|
| auth | O | LoginForm만 (2건) |
| dashboard | O | DashboardView (6건) |
| roadmap | O | 유틸 함수만 (14건), 컴포넌트 미테스트 |
| chat | **X** | 핵심 기능, SSE 스트리밍 |
| actionkit | **X** | 법률 행정 키트 |
| growth-club | **X** | 커뮤니티 게시판 |
| notifications | **X** | 알림 벨 |
| ops | **X** | 관리자 콘솔 (낮은 우선순위) |
| profile | **X** | 프로필 (구조만 존재) |
| shared | **X** | 파일 업/다운로드 훅 |

## Proposed Future State

| 지표 | 목표 |
|------|------|
| 테스트 파일 | ~15개 |
| 테스트 케이스 | ~80개 |
| feature 커버리지 | 7/8 (87.5%, ops 제외) |
| 실행 시간 | <10초 |

---

## Phase 1: 순수 함수 & API 유틸 단위 테스트

난이도 낮음, ROI 높음. 모킹 최소화.

### 1-1. growth-club API 단위 테스트
- `growthClubApi`의 8개 메서드 테스트 (getPosts, createPost, addComment 등)
- `apiClient` mock으로 요청 URL/payload 검증
- **파일**: `features/growth-club/__tests__/growth-club-api.test.ts`
- **Effort**: S

### 1-2. chat API 유틸 단위 테스트
- `features/chat/utils/api.ts`의 세션/메시지 CRUD 함수 테스트
- `apiClient` mock
- **파일**: `features/chat/__tests__/chat-api.test.ts`
- **Effort**: S

### 1-3. chat SSE 파서 단위 테스트
- `features/chat/utils/sse.ts`의 SSE 파싱 로직 테스트
- 순수 함수 위주, fetch mock 최소화
- **파일**: `features/chat/__tests__/sse.test.ts`
- **Effort**: S

### 1-4. notifications API 단위 테스트
- 알림 API 함수 테스트
- **파일**: `features/notifications/__tests__/notifications-api.test.ts`
- **Effort**: S

### 1-5. shared 유틸 단위 테스트
- `url.ts`, `validation.ts` 유틸 함수 테스트
- **파일**: `features/shared/__tests__/utils.test.ts`
- **Effort**: S

---

## Phase 2: 커스텀 훅 테스트

`@testing-library/react-hooks` 또는 `renderHook` 활용.

### 2-1. useRoadmapJob 훅 테스트
- 폴링 로직, 상태 전이 (QUEUED → GENERATING → COMPLETED) 검증
- API mock + `jest.useFakeTimers()`
- **파일**: `features/roadmap/__tests__/useRoadmapJob.test.ts`
- **Effort**: M

### 2-2. useRoadmapList / useActiveRoadmap 훅 테스트
- 목록 조회, 활성 로드맵 선택/전환 로직
- **파일**: `features/roadmap/__tests__/useRoadmapList.test.ts`
- **Effort**: M

### 2-3. usePosts 훅 테스트
- 게시물 목록 조회, 생성, 삭제, 좋아요 상태 관리
- **파일**: `features/growth-club/__tests__/usePosts.test.ts`
- **Effort**: M

### 2-4. useChat 훅 테스트
- 메시지 전송, SSE 스트리밍 수신, 세션 관리
- AbortController + fetch mock 필요
- **파일**: `features/chat/__tests__/useChat.test.ts`
- **Effort**: L

### 2-5. useNotifications 훅 테스트
- 알림 목록 조회, 읽음 처리
- **파일**: `features/notifications/__tests__/useNotifications.test.ts`
- **Effort**: S

---

## Phase 3: 핵심 컴포넌트 렌더링 테스트

### 3-1. NotificationBell 컴포넌트 테스트
- 미읽음 뱃지 렌더링, 클릭 시 드롭다운 표시
- **파일**: `features/notifications/__tests__/NotificationBell.test.tsx`
- **Effort**: S

### 3-2. RoadmapSwitcher 컴포넌트 테스트
- 로드맵 목록 드롭다운, 선택 시 콜백 호출
- **파일**: `features/roadmap/__tests__/RoadmapSwitcher.test.tsx`
- **Effort**: M

### 3-3. PostCard / CreatePostForm 컴포넌트 테스트
- 게시물 렌더링, 좋아요/댓글 버튼 상호작용
- **파일**: `features/growth-club/__tests__/PostCard.test.tsx`
- **Effort**: M

### 3-4. ChatInput 컴포넌트 테스트
- 메시지 입력, 전송 버튼, Enter 키 이벤트
- **파일**: `features/chat/__tests__/ChatInput.test.tsx`
- **Effort**: S

### 3-5. ReadinessTracker 컴포넌트 테스트
- 진행률 표시, 단계별 상태 렌더링
- **파일**: `features/roadmap/__tests__/ReadinessTracker.test.tsx`
- **Effort**: M

---

## Phase 4: 통합 테스트 (Backlog)

### 4-1. AuthProvider 통합 테스트
- login/logout 플로우, 탭 간 동기화, silent refresh
- localStorage + API mock
- **Effort**: L

### 4-2. ChatWidget E2E 스타일 테스트
- 메시지 전송 → SSE 수신 → 인용 표시 전체 플로우
- **Effort**: XL

---

## Risk Assessment

| 리스크 | 확률 | 영향 | 완화 |
|--------|------|------|------|
| SSE 모킹 복잡도로 테스트 불안정 | 중 | 중 | 순수 파서 로직과 네트워크 로직 분리 테스트 |
| 훅 테스트에서 Provider 의존성 | 중 | 낮 | renderHook wrapper로 Provider 제공 |
| 테스트 추가로 CI 시간 증가 | 낮 | 낮 | Jest 병렬 실행, 현재 2.8초로 여유 |

## Success Metrics

- feature 커버리지 7/8 이상
- 테스트 케이스 80개 이상
- 모든 테스트 `pnpm test` 통과
- 실행 시간 10초 이내 유지
