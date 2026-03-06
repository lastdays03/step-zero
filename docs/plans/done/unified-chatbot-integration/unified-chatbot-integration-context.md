# 글로벌 챗봇 + AI 코치 통합 — 핵심 컨텍스트

> **Last Updated**: 2026-03-02

---

## 1. Key Files

### 백엔드 — 수정 대상

| 파일 | 역할 | 변경 내용 |
|------|------|-----------|
| `app-backend/app/api/v1/schemas.py` | API 스키마 | `UnifiedChatRequest` 추가 |
| `app-backend/app/features/rag/application/chat_service.py` | 일반/RAG 채팅 | `stream()` 메서드 추가 |
| `app-backend/app/features/rag/application/deps.py` | DI 팩토리 | `get_unified_chat_service()` 추가 |
| `app-backend/app/api/v1/rag/router.py` | RAG 라우터 | `POST /chat/stream` 엔드포인트 추가 |

### 백엔드 — 새 파일

| 파일 | 역할 |
|------|------|
| `app-backend/app/features/rag/application/unified_chat_service.py` | 통합 SSE 디스패처 |
| `app-backend/tests/api/test_unified_chat.py` | 통합 엔드포인트 테스트 |

### 백엔드 — 변경 없이 재사용

| 파일 | 역할 |
|------|------|
| `app-backend/app/features/roadmaps/application/roadmap_chat_service.py` | AI 코치 SSE 서비스 |
| `app-backend/app/features/roadmaps/application/context_builder.py` | 3레이어 프롬프트 빌더 |
| `app-backend/app/repositories/roadmap_chat_repository.py` | 채팅 DB 레포지토리 |
| `app-backend/app/models/roadmap_chat.py` | Thread/Message 모델 |
| `app-backend/app/api/v1/roadmaps/chat.py` | 기존 로드맵 챗봇 엔드포인트 (하위호환) |
| `app-backend/app/features/rag/application/semantic_router.py` | 질문 분류기 |

### 프론트엔드 — 수정 대상

| 파일 | 변경 내용 |
|------|-----------|
| `app-frontend/src/features/chatbot/types/chat.ts` | `CitationSource`, `isStreaming`, `sources` 추가 |
| `app-frontend/src/features/chatbot/hooks/useChatbot.ts` | JSON→SSE 스트리밍 + 코치 모드 전면 리팩토링 |
| `app-frontend/src/features/chatbot/components/GlobalChatbot.tsx` | ChatContext 연결 |
| `app-frontend/src/features/chatbot/components/ChatPanel.tsx` | 코치 헤더 + 면책 문구 |
| `app-frontend/src/features/chatbot/components/ChatBubble.tsx` | 출처 인용 + 스트리밍 커서 |
| `app-frontend/src/features/chatbot/components/ChatMessageList.tsx` | 모드별 빈 상태 |
| `app-frontend/src/features/roadmap/components/TimelineStepItem.tsx` | StepChatPanel → ChatContext |
| `app-frontend/src/app/layout.tsx` | ChatContextProvider 래핑 |
| `app-frontend/src/features/chatbot/index.ts` | export 업데이트 |

### 프론트엔드 — 새 파일

| 파일 | 역할 |
|------|------|
| `app-frontend/src/features/chatbot/providers/ChatContextProvider.tsx` | 로드맵 컨텍스트 전역 Provider |
| `app-frontend/src/features/chatbot/utils/sseClient.ts` | SSE 파싱, auth, URL 유틸리티 |
| `app-frontend/src/features/chatbot/utils/renderCitationLine.tsx` | 출처 인라인 렌더링 |
| `app-frontend/src/features/chatbot/components/SourcesCard.tsx` | 출처 카드 컴포넌트 |

### 프론트엔드 — 삭제 대상

| 파일 | 이유 |
|------|------|
| `app-frontend/src/features/roadmap/components/StepChatPanel.tsx` | 글로벌 챗봇으로 대체 |
| `app-frontend/src/features/roadmap/hooks/useStepChat.ts` | SSE 로직 → sseClient.ts로 이동 |

---

## 2. Key Decisions

| # | 결정 | 근거 |
|---|------|------|
| D1 | 전체 SSE 스트리밍 | 일관된 UX — 일반/코치 모두 실시간 타이핑 효과 |
| D2 | `roadmap_id` + `step_id` 선택적 파라미터 | 단일 엔드포인트로 일반/코치 모드 통합 |
| D3 | SemanticRouter 자동 분류 | 모드 전환 UI 불필요 — 질문 내용 기반 자동 라우팅 |
| D4 | ChatContextProvider + localStorage | 페이지 전환해도 컨텍스트 유지, 기존 `stepzero_active_roadmap_id` 활용 |
| D5 | StepChatPanel 삭제 | 글로벌 챗봇으로 완전 대체 — 코드 중복 제거 |
| D6 | 기존 엔드포인트 유지 | Breaking change 방지 — `/roadmaps/{id}/steps/{sid}/chat/*` 그대로 |
| D7 | UnifiedChatService = 조합 패턴 | 기존 ChatService, RoadmapChatService 변경 최소화 |

---

## 3. Dependencies

### 내부 의존성 (구현 순서)

```
A-1 (스키마)
  └─ A-5 (라우터)
A-2 (ChatService.stream)
  └─ A-3 (UnifiedChatService)
       └─ A-4 (DI) → A-5 (라우터)
B-1 (sseClient) + B-2 (타입) + B-3 (출처 렌더링)
  └─ B-5 (useChatbot 리팩토링)
B-4 (ChatContextProvider)
  └─ B-5 (useChatbot) → B-9 (layout.tsx)
B-5 (useChatbot) + B-3 (출처 렌더링)
  └─ B-6 (ChatBubble) + B-7 (ChatPanel) + B-8 (ChatMessageList)
       └─ B-9 (GlobalChatbot) → C-1 (정리)
```

### 외부 의존성

- OpenAI API key (`OPENAI_API_KEY`) — LLM 스트리밍 필수
- pgvector — RAG 벡터 검색 (기존 인프라)
- Redis — 직접 사용하지 않음 (워커 전용)

---

## 4. SSE 프로토콜 (기존 roadmap_chat_service.py 그대로)

```
data: {"type":"token","token":"안녕하세요"}\n\n
data: {"type":"token","token":", 카페"}\n\n
...
data: {"type":"sources","sources":[{"id":1,"type":"legal_basis","title":"식품위생법","url":"..."}]}\n\n
data: {"type":"meta","thread_id":"uuid","message_id":42}\n\n
data: {"type":"done"}\n\n
```

에러:
```
data: {"type":"error","code":"OUT_OF_SCOPE","message":"전문가 상담을 권장합니다..."}\n\n
```

하트비트 (15초 간격):
```
: heartbeat\n\n
```

---

## 5. 3레이어 시스템 프롬프트 구조 (context_builder.py)

```
<FACTS>
업종: 카페 (음료/디저트)
지역: 서울특별시 강남구
현재 단계: 1단계 - 사업자등록
관련 법령:
  1. 식품위생법 제37조 (영업허가)
  2. ...
필요 서류:
  1. 사업자등록 신청서
  2. ...
</FACTS>

<STATUS>
체크리스트:
  - [x] 사업계획서 작성
  - [ ] 사업자등록 신청 ← 현재 진행 중
  - [ ] 영업신고
위험 요소: 위생교육 미이수 시 영업허가 불가
</STATUS>

<RULES>
1. 항상 한국어로 답변
2. 법령 인용 시 [법령 N] 형식 사용
3. 서류 인용 시 [서류 N] 형식 사용
4. 확실하지 않은 정보는 "전문가 상담을 권장합니다" 안내
5. 투자, 세금, 소송 등 전문 분야는 답변하지 않음
</RULES>
```

---

## 6. ChatContextProvider 자동 감지 흐름

```
1. 마운트 시 localStorage.getItem("stepzero_active_roadmap_id") 읽기
2. storage 이벤트 리스너 등록 (다른 탭/같은 탭에서 변경 감지)
3. roadmapId 있으면 → GET /api/v1/roadmaps/{roadmapId} 호출
4. 응답의 steps 중 status === "IN_PROGRESS" 자동 선택
5. stepId + stepTitle 상태 설정
6. IN_PROGRESS 없으면 hasCoachContext = false
7. roadmapId 없으면 clearCoachContext()
```

---

## 7. useChatbot SSE 스트리밍 흐름

```
1. sendMessage(content)
2. ChatContext에서 roadmapId, stepId 읽기
3. fetch(POST /api/v1/rag/chat/stream, {message, roadmap_id, step_id, thread_id})
4. ReadableStream + TextDecoder로 SSE 파싱
5. "token" → 어시스턴트 메시지에 append
6. "sources" → receivedSources 저장
7. "meta" → threadId 업데이트, serverMessageId로 교체
8. "done" → isStreaming=false, sources 적용
9. "error" → error 상태 설정
10. 401 → tryRefreshToken() → 1회 재시도
```
