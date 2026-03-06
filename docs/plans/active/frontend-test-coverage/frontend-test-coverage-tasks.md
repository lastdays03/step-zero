# Tasks: 프론트엔드 테스트 커버리지 확대

> Last Updated: 2026-03-06

## Phase 1: 순수 함수 & API 유틸 단위 테스트

- [x] 1-1. growth-club API 단위 테스트 (8개 메서드, 10건) [S]
- [x] 1-2. chat API 유틸 단위 테스트 (세션/메시지 CRUD, 7건) [S]
- [x] 1-3. chat SSE 파서 단위 테스트 (10건) [S]
- [x] 1-4. notifications API 단위 테스트 (3건) [S]
- [x] 1-5. shared 파일 유틸 단위 테스트 (resolveUploadUrl + validateFiles, 14건) [S]
- [x] 1-6. actionkit useActionKit 훅 단위 테스트 (2건) [S]

## Phase 2: 커스텀 훅 테스트

- [x] 2-1. useRoadmapJob 훅 테스트 (startJob/fetchJob/fetchResult, 4건) [M]
- [x] 2-2. useRoadmapList / useActiveRoadmap 훅 테스트 (10건) [M]
- [x] 2-3. usePosts 훅 테스트 (fetch/refetch/error, 4건) [M]
- [x] 2-4. useChat 훅 테스트 (SSE 스트리밍, 8건) [L]
- [x] 2-5. useNotifications 훅 테스트 (fetch/markRead/markAllRead, 3건) [S]

## Phase 3: 핵심 컴포넌트 렌더링 테스트

- [ ] 3-1. NotificationBell 컴포넌트 테스트 [S]
- [ ] 3-2. RoadmapSwitcher 컴포넌트 테스트 [M]
- [ ] 3-3. PostCard / CreatePostForm 컴포넌트 테스트 [M]
- [ ] 3-4. ChatInput 컴포넌트 테스트 [S]
- [ ] 3-5. ReadinessTracker 컴포넌트 테스트 [M]

## Phase 4: 통합 테스트 (Backlog)

- [ ] 4-1. AuthProvider 통합 테스트 [L]
- [ ] 4-2. ChatWidget E2E 스타일 테스트 [XL]
