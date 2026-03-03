# StepZero AI 챗봇 클린 재작성 — 작업 체크리스트

> **Last Updated**: 2026-03-03
> **Status**: ✅ 구현 완료
> **Branch**: `feature/4-ai-coach-chatbot`

---

## Section A: 백엔드 — 새 chat feature 구축

### A-1. DB 모델 확장 + Alembic 마이그레이션 (M)

- [ ] `app/models/roadmap_chat.py` 수정
  - [ ] `RoadmapChatThread.roadmap_id` → `Optional[UUID]` (nullable)
  - [ ] `RoadmapChatThread.step_id` → `Optional[int]` (nullable)
  - [ ] `RoadmapChatThread.is_deleted` 필드 추가 (`Boolean`, default=False)
  - [ ] `RoadmapChatThread.__table_args__` UNIQUE 제약 제거
  - [ ] `RoadmapChatMessage.intent_category` 필드 추가 (`VARCHAR(20)`, nullable)
- [ ] Alembic 마이그레이션 생성
  - [ ] `alembic revision --autogenerate -m "chat session model extension"`
  - [ ] 마이그레이션 파일 검토 (nullable 변경, 필드 추가, 제약 제거)
  - [ ] Docker 내 `alembic upgrade head` 실행
  - [ ] `alembic check` → diff 0 확인
- [ ] 기존 데이터 호환 확인 (기존 Thread/Message 데이터 깨짐 없음)

### A-2. IntentClassifier 구현 (L)

- [ ] `app/features/chat/__init__.py` 생성
- [ ] `app/features/chat/application/__init__.py` 생성
- [ ] `app/features/chat/application/intent_classifier.py` 생성
  - [ ] `IntentCategory` Enum/Literal 정의 (current_step, other_step, legal_general, general, out_of_scope)
  - [ ] `IntentResult` 데이터클래스 (category, step_id?, step_title?, confidence?)
  - [ ] `IntentClassifier` 클래스
    - [ ] `__init__(semantic_router)` — SemanticRouter 주입
    - [ ] `classify(query, roadmap_steps?) → IntentResult`
    - [ ] 1순위: out_of_scope 체크 (SemanticRouter, threshold=0.75)
    - [ ] 2순위: step_related 매칭 (ActionKit 키워드 + 단계명/번호)
      - [ ] 현재 단계 키워드 매칭 → current_step
      - [ ] "이 단계", "지금", "현재", "체크리스트" 키워드 → current_step
      - [ ] 다른 단계명/번호 언급 → other_step
      - [ ] 다른 단계 ActionKit 키워드 → other_step
    - [ ] 3순위: legal vs general (SemanticRouter, threshold=0.7)
    - [ ] 기본값: general

### A-3. SessionService 구현 (M)

- [ ] `app/features/chat/application/session_service.py` 생성
  - [ ] `SessionService` 클래스
    - [ ] `__init__(session, repository)` — DB 세션 + 레포 주입
    - [ ] `create_session(user_id, team_id, roadmap_id?, step_id?) → Thread`
    - [ ] `list_sessions(user_id, limit=50, offset=0) → (list, total)` — is_deleted=false 필터
    - [ ] `get_session(session_id, user_id) → Thread` — 소유권 검증
    - [ ] `get_messages(session_id, user_id, limit=50, offset=0) → (list, total)`
    - [ ] `update_title(session_id, user_id, title) → Thread`
    - [ ] `soft_delete(session_id, user_id) → None`
    - [ ] `set_auto_title(session_id, first_message) → None` — 첫 30자 자동 제목
- [ ] `app/repositories/roadmap_chat_repository.py` 확장
  - [ ] `list_sessions(user_id, limit, offset)` 메서드 추가
  - [ ] `update_thread_title(thread_id, title)` 메서드 추가
  - [ ] `soft_delete_thread(thread_id)` 메서드 추가
  - [ ] `create_empty_session(user_id, team_id, roadmap_id?, step_id?)` 메서드 추가

### A-4. ChatService 구현 — 통합 SSE 스트리밍 (XL)

- [ ] `app/features/chat/application/chat_service.py` 생성
  - [ ] `ChatService` 클래스
    - [ ] `__init__` — intent_classifier, session_service, context_builder, rag_service, llm, repository, session 주입
    - [ ] `stream(message, session_id?, user, team) → AsyncGenerator` — 핵심 메서드
      - [ ] 세션 get_or_create (session_id 없으면 새 세션)
      - [ ] 첫 메시지일 때 자동 제목 설정
      - [ ] 사용자 메시지 DB 저장
      - [ ] IntentClassifier.classify() 호출
      - [ ] SSE intent 이벤트 발행
      - [ ] 카테고리별 분기:
        - [ ] `current_step` → ContextBuilder.build(현재 단계) + LLM astream
        - [ ] `other_step` → ContextBuilder.build(해당 단계) + LLM astream + "N단계 기준" 프리픽스
        - [ ] `legal_general` → RagService.query() (성공 시 출처 포함, 실패 시 LLM 폴백 + warning)
        - [ ] `general` → LLM astream (시스템 프롬프트: 창업 도우미)
        - [ ] `out_of_scope` → SSE error 이벤트 (차단 메시지)
      - [ ] 어시스턴트 응답 DB 저장 (intent_category 포함)
      - [ ] SSE meta 이벤트 (session_id, message_id)
      - [ ] SSE done 이벤트
    - [ ] `_sse_event(type, data) → str` — SSE 포맷 헬퍼
    - [ ] 하트비트 로직 (15초 간격)
    - [ ] 에러 핸들링 (try/except → SSE error 이벤트)

### A-5. 스키마 + DI 팩토리 (S)

- [ ] `app/features/chat/application/schemas.py` 생성
  - [ ] `ChatStreamRequest` — message(str, 1~2000), session_id(UUID|None)
  - [ ] `SessionCreateRequest` — 빈 바디 (향후 확장 가능)
  - [ ] `SessionUpdateRequest` — title(str, 1~100)
  - [ ] `SessionResponse` — id, title, message_count, roadmap_id?, step_id?, created_at, updated_at
  - [ ] `SessionListResponse` — sessions[], total
  - [ ] `MessageResponse` — id, role, content, sources_json?, intent_category?, created_at
  - [ ] `MessageListResponse` — messages[], total
- [ ] `app/features/chat/application/deps.py` 생성
  - [ ] `get_intent_classifier()` — SemanticRouter 주입
  - [ ] `get_session_service(session)` — DB 세션 + 레포 주입
  - [ ] `get_chat_service(session)` — 전체 의존성 조합

### A-6. 라우터 + main.py 등록 (M)

- [ ] `app/api/v1/chat/__init__.py` 생성
- [ ] `app/api/v1/chat/router.py` 생성
  - [ ] `POST /stream` — SSE 스트리밍 (StreamingResponse)
    - [ ] ChatStreamRequest 스키마
    - [ ] get_current_user, get_current_team 의존성
    - [ ] get_chat_service DI
    - [ ] SSE 헤더 (Cache-Control, Connection, X-Accel-Buffering)
  - [ ] `GET /sessions` — 세션 목록
    - [ ] limit, offset 쿼리 파라미터
    - [ ] SessionListResponse 반환
  - [ ] `POST /sessions` — 새 세션 생성
    - [ ] SessionResponse 반환
  - [ ] `GET /sessions/{id}/messages` — 메시지 조회
    - [ ] limit, offset 쿼리 파라미터
    - [ ] MessageListResponse 반환
  - [ ] `PATCH /sessions/{id}` — 제목 변경
    - [ ] SessionUpdateRequest 스키마
    - [ ] SessionResponse 반환
  - [ ] `DELETE /sessions/{id}` — 소프트 삭제
    - [ ] 204 No Content
- [ ] `app/main.py` 수정
  - [ ] chat 라우터 import + 등록 (`prefix="/api/v1/chat"`)

### A-7. 백엔드 테스트 (L)

- [ ] `tests/api/test_chat_sessions.py` 생성
  - [ ] 세션 생성 테스트 (POST /sessions → 201)
  - [ ] 세션 목록 테스트 (GET /sessions → 200, 페이지네이션)
  - [ ] 세션 제목 변경 테스트 (PATCH /sessions/{id} → 200)
  - [ ] 세션 삭제 테스트 (DELETE /sessions/{id} → 204, 소프트 삭제 확인)
  - [ ] 비인증 요청 → 401
  - [ ] 다른 사용자 세션 접근 → 403 또는 404
- [ ] `tests/api/test_chat_stream.py` 생성
  - [ ] 일반 모드 SSE 스트리밍 테스트 (general 카테고리)
  - [ ] 코치 모드 SSE 스트리밍 테스트 (current_step 카테고리)
  - [ ] out_of_scope 차단 테스트
  - [ ] 빈 메시지 → 422
  - [ ] 2000자 초과 → 422
  - [ ] 비인증 → 401
  - [ ] intent SSE 이벤트 포함 확인
  - [ ] meta SSE 이벤트 (session_id, message_id) 확인
  - [ ] 첫 메시지 시 자동 제목 설정 확인
- [ ] `tests/services/test_intent_classifier.py` 생성
  - [ ] current_step 분류 테스트 (ActionKit 키워드 매칭)
  - [ ] other_step 분류 테스트 (다른 단계명 언급)
  - [ ] legal_general 분류 테스트 (법률 키워드)
  - [ ] general 분류 테스트 (기본값)
  - [ ] out_of_scope 분류 테스트 (전문 영역)
  - [ ] 로드맵 없는 사용자 → step 관련 분류 건너뜀
- [ ] 기존 전체 테스트 통과 확인
  - [ ] `cd app-backend && .venv/bin/pytest -q` → 0 failed

---

## Section B: 프론트엔드 — 새 chat feature 구축

### B-1. 타입 정의 + SSE 유틸 + API 클라이언트 (M)

- [ ] `src/features/chat/types/index.ts` 생성
  - [ ] `IntentCategory` type (5가지)
  - [ ] `ChatMessage` interface (id, role, content, sources?, intent_category?, isStreaming?, warning?)
  - [ ] `ChatSession` interface (id, title, message_count, roadmap_id?, step_id?, created_at, updated_at)
  - [ ] `SSEEvent` type (token, sources, meta, intent, warning, done, error)
  - [ ] `CitationSource` interface (id, type, title, url?)
- [ ] `src/features/chat/utils/sse.ts` 생성
  - [ ] `parseSSELine(line: string): SSEEvent | null`
  - [ ] `getAuthHeaders(): HeadersInit` — JWT + Team-Id
  - [ ] `getApiBaseUrl(): string`
  - [ ] `tryRefreshToken(): Promise<boolean>`
- [ ] `src/features/chat/utils/api.ts` 생성
  - [ ] `fetchSessions(limit, offset): Promise<SessionListResponse>`
  - [ ] `createSession(): Promise<Session>`
  - [ ] `fetchMessages(sessionId, limit, offset): Promise<MessageListResponse>`
  - [ ] `updateSessionTitle(sessionId, title): Promise<Session>`
  - [ ] `deleteSession(sessionId): Promise<void>`

### B-2. ChatProvider 구현 (L)

- [ ] `src/features/chat/providers/ChatProvider.tsx` 생성
  - [ ] `ChatContext` React Context 정의
  - [ ] `ChatProviderValue` interface
    - [ ] `currentSessionId`, `setCurrentSessionId()`
    - [ ] `roadmapContext` — { roadmapId, stepId, stepTitle } | null
    - [ ] `isPanelOpen`, `openPanel()`, `closePanel()`, `togglePanel()`
    - [ ] `isHistoryView`, `showHistory()`, `showChat()`
  - [ ] localStorage `stepzero_active_roadmap_id` 변경 감지
  - [ ] roadmapId 변경 시 → 로드맵 API 호출 → IN_PROGRESS 단계 자동 선택
  - [ ] `useChatProvider()` 커스텀 훅 export

### B-3. useChat 훅 구현 (XL)

- [ ] `src/features/chat/hooks/useChat.ts` 생성
  - [ ] `messages` 상태 관리
  - [ ] `isStreaming` 상태
  - [ ] `sendMessage(content: string)` — SSE 스트리밍 전체 플로우
    - [ ] fetch + ReadableStream으로 SSE 파싱
    - [ ] token 이벤트 → 메시지 실시간 append
    - [ ] intent 이벤트 → 분류 결과 처리
    - [ ] sources 이벤트 → 출처 업데이트
    - [ ] warning 이벤트 → 경고 배지 표시
    - [ ] meta 이벤트 → session_id 업데이트
    - [ ] done 이벤트 → isStreaming false
    - [ ] error 이벤트 → 에러 메시지 표시
  - [ ] `loadHistory(sessionId)` — 기존 세션 메시지 로드
  - [ ] 401 → tryRefreshToken → 1회 재시도
  - [ ] AbortController로 이전 요청 취소
  - [ ] 세션 전환 시 메시지 초기화 + 새 세션 로드

### B-4. useSessions 훅 구현 (M)

- [ ] `src/features/chat/hooks/useSessions.ts` 생성
  - [ ] `sessions` 상태
  - [ ] `isLoading` 상태
  - [ ] `loadSessions()` — API 호출
  - [ ] `createSession()` — 빈 세션 생성
  - [ ] `renameSession(id, title)` — 제목 변경
  - [ ] `deleteSession(id)` — 소프트 삭제 + 목록에서 제거
  - [ ] 날짜별 그룹핑 (오늘/어제/이전)

### B-5. UI 컴포넌트 — 코어 (XL)

- [ ] `src/features/chat/components/ChatWidget.tsx` 생성
  - [ ] ChatFAB + ChatPanel 조합
  - [ ] ChatProvider에서 isPanelOpen 소비
- [ ] `src/features/chat/components/ChatFAB.tsx` 생성
  - [ ] 새 디자인 — 원형 버튼 (모바일) / 텍스트 포함 (데스크톱)
  - [ ] "StepZero AI에게 물어보기" 라벨
  - [ ] 패널 열기 클릭 핸들러
- [ ] `src/features/chat/components/ChatPanel.tsx` 생성
  - [ ] 패널 레이아웃 (헤더 + 바디 + 푸터)
  - [ ] 헤더: ☰ 히스토리 + "StepZero AI" + [+ 새 대화] + ✕
  - [ ] 📍 로드맵 컨텍스트 서브헤더 (있을 때만)
  - [ ] 대화 ↔ 히스토리 슬라이드 전환 애니메이션
  - [ ] 면책 문구: "AI 생성 정보 · 정확성 미보장"
- [ ] `src/features/chat/components/ChatMessages.tsx` 생성
  - [ ] 메시지 리스트 렌더링
  - [ ] 자동 스크롤 (새 메시지 시)
  - [ ] 로딩 스피너 (이력 로드 시)
- [ ] `src/features/chat/components/ChatMessage.tsx` 생성
  - [ ] 사용자/AI 메시지 분기 렌더링
  - [ ] AI 메시지: 인용 렌더링 (citations 유틸)
  - [ ] AI 메시지: SourcesCard 조건부 표시
  - [ ] AI 메시지: ChatWarningBadge 조건부 표시
  - [ ] 스트리밍 커서 애니메이션 (isStreaming)
- [ ] `src/features/chat/components/ChatInput.tsx` 생성
  - [ ] 입력 필드 + 전송 버튼
  - [ ] Enter 전송, Shift+Enter 줄바꿈
  - [ ] isStreaming 시 비활성화
  - [ ] 최대 2000자 제한

### B-6. UI 컴포넌트 — 부가 (L)

- [ ] `src/features/chat/components/ChatHistory.tsx` 생성
  - [ ] 세션 목록 (날짜 그룹: 오늘/어제/이전)
  - [ ] 각 항목: 제목 + 시간 + 메시지 수
  - [ ] [⋮] 메뉴: 이름 변경 / 삭제
  - [ ] [+ 새 대화] 버튼
  - [ ] 세션 클릭 → 대화 화면 전환 + 메시지 로드
- [ ] `src/features/chat/components/ChatEmptyState.tsx` 생성
  - [ ] StepZero AI 로고/이름
  - [ ] "창업에 필요한 모든 것을 물어보세요"
  - [ ] 추천 질문 (로드맵 유무에 따라 다른 질문)
  - [ ] 추천 질문 클릭 → sendMessage 호출
- [ ] `src/features/chat/components/SourcesCard.tsx` 생성
  - [ ] 출처 목록 카드 (접기/펼치기)
  - [ ] "📎 출처 N건" 헤더
  - [ ] 각 출처: 타입 아이콘 + 제목 + 링크
- [ ] `src/features/chat/components/ChatWarningBadge.tsx` 생성
  - [ ] ⚠️ 출처 미확인 정보 경고 박스
  - [ ] "정확한 내용은 전문가 확인을 권장합니다"
- [ ] `src/features/chat/utils/citations.tsx` 생성
  - [ ] `renderCitationLine(text, sources)` — [법령 N], [서류 N] 인라인 배지

### B-7. layout.tsx 연동 + 모듈 export (S)

- [ ] `src/features/chat/index.ts` 생성
  - [ ] ChatWidget, ChatProvider export
- [ ] `src/app/layout.tsx` 수정
  - [ ] `ChatContextProvider` → `ChatProvider` import 변경
  - [ ] `GlobalChatbot` → `ChatWidget` import 변경
  - [ ] (이 시점에서는 기존과 새 것을 교체)

### B-8. FE 검증 (M)

- [ ] `cd app-frontend && npm run lint` → 0 errors
- [ ] `cd app-frontend && npm run build` → 성공
- [ ] 수동 기능 확인 (FAB → 패널 열기 → 메시지 전송 → 응답 확인)

---

## Section C: 정리 + 전환

### C-1. FE 기존 chatbot feature 삭제 (M)

- [ ] `src/features/chatbot/` 전체 디렉토리 삭제
- [ ] `src/app/layout.tsx`에서 기존 import 제거 확인
  - [ ] `ChatContextProvider` import 없음
  - [ ] `GlobalChatbot` import 없음
- [ ] 프로젝트 전체에서 `features/chatbot` import 0건 확인 (grep)
- [ ] `src/features/chatbot` 관련 테스트 파일 삭제 (있으면)

### C-2. FE TimelineStepItem 정리 (S)

- [ ] `src/features/roadmap/components/TimelineStepItem.tsx` 수정
  - [ ] "AI에게 물어보기" 버튼 코드 제거
  - [ ] `useChatContext` import 제거
  - [ ] 관련 상태 변수 제거

### C-3. BE 기존 챗봇 코드 정리 (M)

- [ ] `app/features/rag/application/chat_service.py` 삭제
- [ ] `app/features/rag/application/unified_chat_service.py` 삭제
- [ ] `app/features/roadmaps/application/roadmap_chat_service.py` 삭제
- [ ] `app/features/rag/application/deps.py` 정리 (챗봇 관련 DI 제거)
- [ ] `app/api/v1/rag/router.py` 정리
  - [ ] `POST /chat` 엔드포인트 제거
  - [ ] `POST /chat/stream` 엔드포인트 제거
  - [ ] `/query` 엔드포인트만 유지
- [ ] `app/api/v1/roadmaps/chat.py` 전체 삭제
- [ ] `app/api/v1/roadmaps/__init__.py` 또는 라우터 등록에서 chat 라우터 제거
- [ ] `app/api/v1/schemas.py`에서 `UnifiedChatRequest` 등 챗봇 관련 스키마 제거
- [ ] `app/main.py`에서 기존 챗봇 라우터 등록 제거 (이미 새 라우터로 교체됨)

### C-4. BE 기존 테스트 정리 (S)

- [ ] `tests/api/test_unified_chat.py` 삭제
- [ ] `tests/api/test_roadmap_chat.py` 삭제 (있으면)
- [ ] `tests/api/test_rag.py`에서 챗봇 관련 테스트 제거 (있으면)
- [ ] 기존 conftest.py에서 챗봇 관련 fixture 정리 (있으면)

### C-5. 최종 통합 검증 (L)

- [ ] 백엔드 전체 테스트 통과
  - [ ] `cd app-backend && .venv/bin/pytest -q` → 0 failed
- [ ] 프론트엔드 lint 통과
  - [ ] `cd app-frontend && npm run lint` → 0 errors
- [ ] 프론트엔드 빌드 성공
  - [ ] `cd app-frontend && npm run build` → 성공
- [ ] 레거시 참조 0건 확인
  - [ ] grep `chatbot` (features 디렉토리) → 0건
  - [ ] grep `unified_chat` (BE) → 0건
  - [ ] grep `roadmap_chat_service` (BE) → 0건
  - [ ] grep `StepChatPanel` (FE) → 0건
  - [ ] grep `useChatContext` (FE) → 0건
  - [ ] grep `GlobalChatbot` (FE) → 0건
- [ ] 수동 UX 시나리오 테스트 (14개)
  - [ ] S1: 로드맵 없는 사용자 FAB 클릭 → 빈 상태 + 일반 추천
  - [ ] S2: 로드맵 있는 사용자 FAB 클릭 → 📍 단계 + 추천
  - [ ] S3: 현재 단계 질문 → current_step 코치 답변
  - [ ] S4: 다른 단계 질문 → other_step "N단계 기준"
  - [ ] S5: 일반 법률 질문 → legal_general RAG 답변
  - [ ] S6: RAG 실패 시 → LLM 폴백 + ⚠️ 경고
  - [ ] S7: 일반 창업 질문 → general LLM 답변
  - [ ] S8: 전문 영역 질문 → out_of_scope 차단
  - [ ] S9: 새 대화 → 자동 저장 + 빈 세션
  - [ ] S10: 히스토리 세션 선택 → 메시지 로드
  - [ ] S11: 세션 이름 변경
  - [ ] S12: 세션 삭제
  - [ ] S13: 새로고침 → 마지막 세션 자동 로드
  - [ ] S14: 로드맵 생성 후 → 컨텍스트 자동 활성화

---

## 진행 요약

| Section | 태스크 수 | 상태 |
|---------|-----------|------|
| A (백엔드) | 7 | ✅ 완료 |
| B (프론트엔드) | 8 | ✅ 완료 |
| C (정리) | 5 | ✅ 완료 |
| **합계** | **20** | **✅ 구현 완료** |
