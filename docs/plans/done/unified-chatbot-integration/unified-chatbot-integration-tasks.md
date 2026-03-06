# 글로벌 챗봇 + AI 코치 통합 — 작업 체크리스트

> **Last Updated**: 2026-03-02
> **Status**: 구현 완료
> **Branch**: `feature/4-ai-coach-chatbot`

---

## Section A: 백엔드 — 통합 SSE 스트리밍

### A-1. UnifiedChatRequest 스키마 추가 (S)

- [x] `app-backend/app/api/v1/schemas.py` 수정
  - [x] `UnifiedChatRequest` 클래스 추가
  - [x] `message: str` (min_length=1, max_length=2000)
  - [x] `thread_id: UUID | None = None`
  - [x] `roadmap_id: UUID | None = None`
  - [x] `step_id: int | None = None`
  - [x] `model_validator`: roadmap_id와 step_id 쌍 검증

### A-2. ChatService.stream() 메서드 추가 (M)

- [x] `app-backend/app/features/rag/application/chat_service.py` 수정
  - [x] `_classify()` 내부 메서드 추출 (기존 `chat()`의 분류 로직)
  - [x] `stream()` AsyncGenerator 메서드 추가
    - [x] out_of_scope → SSE error 이벤트
    - [x] legal → `rag_service.query()` 결과를 SSE token으로 래핑
    - [x] general → `llm.astream()` 토큰 단위 SSE
  - [x] `_sse_event()` 헬퍼 import (`roadmap_chat_service.py`에서)
  - [x] 기존 `chat()` 메서드 변경 없음 확인

### A-3. UnifiedChatService 생성 (L)

- [x] `app-backend/app/features/rag/application/unified_chat_service.py` 생성
  - [x] `UnifiedChatService` 클래스
  - [x] `__init__`: chat_service, semantic_router, chat_repo, session
  - [x] `stream()` AsyncGenerator 메서드
    - [x] roadmap_id + step_id 존재 시:
      - [x] 로드맵 소유권 검증 (team_id 매칭)
      - [x] 로드맵 + 스텝 조회
      - [x] 스레드 get_or_create (RoadmapChatRepository 활용)
      - [x] RoadmapChatService.stream() 위임
    - [x] roadmap_id 없을 시:
      - [x] ChatService.stream() 위임
  - [x] 에러 처리 (404 로드맵, 권한 부족 등)

### A-4. DI 팩토리 추가 (S)

- [x] `app-backend/app/features/rag/application/deps.py` 수정
  - [x] `get_unified_chat_service()` 함수 추가
  - [x] `session: AsyncSession` 파라미터 (DI에서 주입)
  - [x] 내부: ChatService + SemanticRouter + RoadmapChatRepository + RoadmapChatService 조합

### A-5. SSE 라우터 엔드포인트 추가 (M)

- [x] `app-backend/app/api/v1/rag/router.py` 수정
  - [x] `POST /chat/stream` 엔드포인트 추가
  - [x] `UnifiedChatRequest` 스키마 사용
  - [x] `get_current_user`, `get_current_team` 의존성
  - [x] `get_session` 의존성 (코치 모드 DB 저장용)
  - [x] `StreamingResponse` 반환 (media_type="text/event-stream")
  - [x] SSE 헤더: Cache-Control, Connection, X-Accel-Buffering
  - [x] 기존 `POST /chat` 변경 없음 확인

### A-6. 백엔드 테스트 (M)

- [x] `app-backend/tests/api/test_unified_chat.py` 생성
  - [x] 일반 모드 스트리밍 테스트 (roadmap_id 없음)
  - [x] 코치 모드 스트리밍 테스트 (roadmap_id + step_id)
  - [x] roadmap_id만 있고 step_id 없을 때 422 에러
  - [x] 존재하지 않는 로드맵 → SSE error
  - [x] 비인증 요청 → 401
  - [x] 빈 메시지/2000자 초과 → 422
- [x] 기존 테스트 전체 통과 확인
  - [x] `cd app-backend && .venv/bin/pytest -q` → 433 passed, 30 skipped

### A-추가. 버그 수정

- [x] `app/api/problem.py`: validation_exception_to_problem에서 ValueError 객체 JSON 직렬화 실패 수정

---

## Section B: 프론트엔드 기반 — 공유 유틸 추출

### B-1. SSE 유틸리티 추출 (M)

- [x] `app-frontend/src/features/chatbot/utils/sseClient.ts` 생성
  - [x] `getApiBaseUrl()` — `useStepChat.ts`에서 추출
  - [x] `tryRefreshToken()` — `useStepChat.ts`에서 추출
  - [x] SSE 이벤트 타입 정의 (Token, Sources, Meta, Done, Error)
  - [x] `parseSSELine(line: string): SSEEvent | null` — SSE 라인 파싱 유틸
  - [x] `getAuthHeaders()` — JWT + Team-Id 헤더 구성

### B-2. ChatMessage 타입 확장 (S)

- [x] `app-frontend/src/features/chatbot/types/chat.ts` 수정
  - [x] `CitationSource` 인터페이스 추가 (id, type, title, url?)
  - [x] `ChatMessage`에 `sources?: CitationSource[]` 추가
  - [x] `ChatMessage`에 `isStreaming?: boolean` 추가

### B-3. 출처 렌더링 유틸 추출 (M)

- [x] `app-frontend/src/features/chatbot/utils/renderCitationLine.tsx` 생성
  - [x] `StepChatPanel.tsx`의 `renderCitationLine()` 추출
  - [x] [법령 N], [서류 N] 패턴 인라인 배지 렌더링
- [x] `app-frontend/src/features/chatbot/components/SourcesCard.tsx` 생성
  - [x] `StepChatPanel.tsx`의 SourcesCard 추출
  - [x] 메시지 하단 출처 목록 카드

### B-4. ChatContextProvider 생성 (L)

- [x] `app-frontend/src/features/chatbot/providers/ChatContextProvider.tsx` 생성
  - [x] `ChatContext` React Context 정의
  - [x] `ChatContextValue` 인터페이스 (roadmapId, stepId, stepTitle, hasCoachContext)
  - [x] `setCoachContext()` — 외부에서 수동 주입
  - [x] `clearCoachContext()` — 컨텍스트 해제
  - [x] localStorage `stepzero_active_roadmap_id` 변경 감지 (storage event)
  - [x] roadmapId 변경 시 로드맵 detail API 호출 → IN_PROGRESS 단계 자동 선택
  - [x] `useChatContext()` 커스텀 훅 export
  - [x] `isPanelOpen`, `openPanel()`, `closePanel()`, `togglePanel()` 추가

---

## Section C: 프론트엔드 통합 — 시각적 변경

### C-1. useChatbot SSE 리팩토링 (XL)

- [x] `app-frontend/src/features/chatbot/hooks/useChatbot.ts` 수정
  - [x] `apiClient.post("/rag/chat")` → native `fetch` + ReadableStream
  - [x] `useChatContext()`에서 roadmapId, stepId 읽기
  - [x] 요청에 roadmap_id, step_id, thread_id 포함
  - [x] SSE 파싱: sseClient.ts 유틸 사용
  - [x] `isStreaming` 상태 추가
  - [x] 토큰 단위 메시지 업데이트 (어시스턴트 메시지 append)
  - [x] sources, meta, done, error 이벤트 처리
  - [x] 코치 모드: threadId 관리 + 이력 로드 (loadHistory)
  - [x] 일반 모드: 기존 메모리 기반 (DB 저장 없음)
  - [x] 401 → tryRefreshToken → 1회 재시도
  - [x] AbortController로 이전 요청 취소
  - [x] 반환 타입에 hasCoachContext, stepTitle 추가

### C-2. ChatBubble 업그레이드 (M)

- [x] `app-frontend/src/features/chatbot/components/ChatBubble.tsx` 수정
  - [x] `message.sources` 존재 시 → `renderCitationLine()` 사용
  - [x] `message.sources` 없을 시 → 기존 `renderAnswerLine()` 유지
  - [x] `message.isStreaming` → 커서 깜빡임 CSS 애니메이션
  - [x] 메시지 하단 `SourcesCard` 조건부 렌더링
  - [x] 기존 source 배지 ("법률 RAG" / "일반 AI") 유지

### C-3. ChatPanel 업그레이드 (S)

- [x] `app-frontend/src/features/chatbot/components/ChatPanel.tsx` 수정
  - [x] 코치 컨텍스트 활성 시: "AI 코치 · {stepTitle}" 서브타이틀
  - [x] 코치 컨텍스트 비활성 시: 기존 "AI 어시스턴트"
  - [x] 면책 문구: "AI가 생성한 정보이며, 정확성을 보장하지 않습니다."
  - [x] `isStreaming` prop → 전송 버튼/입력 비활성화

### C-4. ChatMessageList 업그레이드 (S)

- [x] `app-frontend/src/features/chatbot/components/ChatMessageList.tsx` 수정
  - [x] 코치 모드 빈 상태: "현재 단계에 대해 물어보세요"
  - [x] 일반 모드 빈 상태: "무엇이든 물어보세요!"
  - [x] 이력 로딩 스피너 (코치 모드 DB 이력 로드 시)

### C-5. GlobalChatbot + layout.tsx (S)

- [x] `app-frontend/src/features/chatbot/components/GlobalChatbot.tsx` 수정
  - [x] `useChatbot()`에서 isStreaming, hasCoachContext, stepTitle 소비
  - [x] ChatPanel에 새 props 전달
- [x] `app-frontend/src/app/layout.tsx` 수정
  - [x] `<ChatContextProvider>` 래핑 (AuthProvider 내부)

---

## Section D: 정리 + 검증

### D-1. TimelineStepItem 전환 (M)

- [x] `app-frontend/src/features/roadmap/components/TimelineStepItem.tsx` 수정
  - [x] "AI 코치" 버튼 → `useChatContext().setCoachContext()` + `openPanel()`
  - [x] `StepChatPanel` import 제거
  - [x] `stepChatOpen` 로컬 상태 제거
  - [x] StepChatPanel 렌더링 코드 제거

### D-2. 레거시 파일 삭제 (S)

- [x] `app-frontend/src/features/roadmap/components/StepChatPanel.tsx` 삭제
- [x] `app-frontend/src/features/roadmap/hooks/useStepChat.ts` 삭제
- [x] `features/roadmap/hooks/index.ts`에서 `useStepChat` export 제거
- [x] `features/roadmap/components/index.ts`에서 `StepChatPanel` export 제거
- [x] `features/chatbot/index.ts` export 업데이트 (새 컴포넌트/유틸 추가)
- [x] 프로젝트 전체 StepChatPanel/useStepChat 참조 0건 확인

### D-3. 최종 검증 (M)

- [x] 백엔드 전체 테스트 통과
  - [x] `cd app-backend && .venv/bin/pytest -q` → 433 passed, 30 skipped, 0 failed
- [x] 프론트엔드 lint 통과
  - [x] `cd app-frontend && npm run lint` → 0 errors
- [x] 프론트엔드 빌드 성공
  - [x] `cd app-frontend && npm run build` → 19 정적 + 2 동적 페이지
- [x] 레거시 삭제 후 재검증: lint 0 errors, build 성공

---

## 최종 결과

| Section | 태스크 수 | 상태 |
|---------|-----------|------|
| A (백엔드) | 6 + 1 (버그 수정) | 완료 |
| B (FE 기반) | 4 | 완료 |
| C (FE 통합) | 5 | 완료 |
| D (정리) | 3 | 완료 |
| **합계** | **19** | **전체 완료** |
