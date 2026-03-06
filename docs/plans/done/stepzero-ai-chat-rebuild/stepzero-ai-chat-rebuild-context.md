# StepZero AI 챗봇 클린 재작성 — 핵심 컨텍스트

> **Last Updated**: 2026-03-03
> **Status**: 구현 대기
> **Branch**: `feature/4-ai-coach-chatbot`

---

## 1. 핵심 설계 결정 (D1~D9)

| # | 항목 | 결정 | 근거 |
|---|------|------|------|
| D1 | AI 정체성 | **"StepZero AI"** 단일 이름 | 이원화된 정체성이 사용자 혼란 유발 |
| D2 | 대화 저장 | **모든 대화 DB 저장** | 새로고침 시 대화 소실 방지 |
| D3 | 세션 관리 | **ChatGPT식** — 새 대화, 히스토리, 이름 변경/삭제 | 가장 직관적인 UX 패턴 |
| D4 | 컨텍스트 주입 | **질문 기반 자동 분류** (5카테고리) | 항상 주입 시 맥락 오염 문제 해결 |
| D5 | 히스토리 UI | **패널 내 슬라이드** | 공간 효율 + 전환 비용 최소화 |
| D6 | RAG 실패 | **LLM 폴백 + ⚠️ 경고 배지** | 무응답보다 경고 포함 답변이 UX 우수 |
| D7 | 로드맵 버튼 | **"AI에게 물어보기" 버튼 제거** | FAB 상시 존재 + 자동 분류로 불필요 |
| D8 | 세션 제목 | **첫 질문 기반** (30자) | 가장 자연스러운 자동 이름 생성 |
| D9 | 구현 방식 | **클린 재작성** | 수정보다 제거 후 신규 작성이 깔끔 |

---

## 2. 재사용 파일 (변경 없이 사용)

| 파일 | 라인 | 역할 | 호출 방식 |
|------|------|------|----------|
| `app/features/roadmaps/application/context_builder.py` | 401 | 3레이어 코치 프롬프트 빌드 | `build(roadmap, step, token_budget=1200)` |
| `app/features/rag/application/semantic_router.py` | 142 | 임베딩 유사도 분류 | `classify(query, threshold=0.7)` → "legal"/"general"/"out_of_scope" |
| `app/features/rag/application/rag_service.py` | 123 | 법령 벡터 검색 | `query(question)` → RAG 답변 |

---

## 3. 확장 파일 (수정 필요)

### 3.1 DB 모델 — `app/models/roadmap_chat.py` (62 lines)

**변경 내용:**
- `RoadmapChatThread.roadmap_id` → `Optional` (nullable)
- `RoadmapChatThread.step_id` → `Optional` (nullable)
- `RoadmapChatThread.is_deleted` → 새 필드 (`Boolean`, default=False)
- `RoadmapChatThread.__table_args__` → UNIQUE 제약 제거
- `RoadmapChatMessage.intent_category` → 새 필드 (`VARCHAR(20)`, nullable)

**Alembic 마이그레이션 필요:**
```sql
ALTER TABLE roadmap_chat_threads
  ALTER COLUMN roadmap_id DROP NOT NULL,
  ALTER COLUMN step_id DROP NOT NULL,
  ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE;

ALTER TABLE roadmap_chat_messages
  ADD COLUMN intent_category VARCHAR(20);

-- UNIQUE 제약 제거 (uq_roadmap_step_user)
```

### 3.2 레포지토리 — `app/repositories/roadmap_chat_repository.py` (143 lines)

**기존 메서드 (재사용):**
- `get_or_create_thread()` — 세션 생성/조회
- `add_message()` — 메시지 저장
- `get_recent_messages()` — 최근 메시지 로드
- `list_threads()` — 스레드 목록
- `count_messages()` — 메시지 카운트

**추가 필요 메서드:**
- `list_sessions(user_id, limit, offset)` — 세션 목록 (is_deleted=false, 페이지네이션)
- `update_thread_title(thread_id, title)` — 제목 변경
- `soft_delete_thread(thread_id)` — 소프트 삭제
- `create_empty_session(user_id, roadmap_id?, step_id?)` — 빈 세션 생성

---

## 4. 새로 생성할 파일

### 4.1 백엔드 (`app/features/chat/`)

| 파일 | 크기 | 핵심 책임 |
|------|------|----------|
| `application/__init__.py` | S | 패키지 초기화 |
| `application/intent_classifier.py` | L | 5카테고리 분류 (SemanticRouter 조합 + ActionKit 키워드) |
| `application/session_service.py` | M | 세션 CRUD + 자동 제목 |
| `application/chat_service.py` | XL | 통합 SSE 스트리밍 + DB 저장 + 분기 |
| `application/schemas.py` | S | ChatStreamRequest, SessionResponse 등 |
| `application/deps.py` | S | DI 팩토리 (get_chat_service, get_session_service) |
| `__init__.py` | S | 패키지 초기화 |

### 4.2 백엔드 라우터 (`app/api/v1/chat/`)

| 파일 | 핵심 엔드포인트 |
|------|---------------|
| `__init__.py` | 패키지 |
| `router.py` | POST /stream, GET/POST/PATCH/DELETE /sessions |

### 4.3 프론트엔드 (`src/features/chat/`) — 100% 신규

| 파일 | 역할 |
|------|------|
| `types/index.ts` | ChatMessage, Session, SSEEvent, IntentCategory 타입 |
| `utils/sse.ts` | SSE 파싱, parseSSELine, getAuthHeaders |
| `utils/citations.tsx` | [법령 N], [서류 N] 인라인 배지 렌더링 |
| `utils/api.ts` | 세션 CRUD API 함수 (fetch 기반) |
| `providers/ChatProvider.tsx` | 세션 상태, 로드맵 컨텍스트, 패널 상태 |
| `hooks/useChat.ts` | SSE 스트리밍 + 메시지 관리 + intent/warning 처리 |
| `hooks/useSessions.ts` | 세션 목록 + CRUD + 날짜 그룹핑 |
| `components/ChatWidget.tsx` | 메인 래퍼 (FAB + Panel 조합) |
| `components/ChatFAB.tsx` | 플로팅 액션 버튼 |
| `components/ChatPanel.tsx` | 패널 (대화 ↔ 히스토리 슬라이드 전환) |
| `components/ChatMessages.tsx` | 메시지 리스트 + 자동 스크롤 |
| `components/ChatMessage.tsx` | 개별 메시지 버블 + 인용 |
| `components/ChatInput.tsx` | 입력 필드 + 전송 버튼 |
| `components/ChatHistory.tsx` | 히스토리 목록 (날짜 그룹 + 이름 변경/삭제) |
| `components/ChatEmptyState.tsx` | 빈 상태 + 추천 질문 |
| `components/SourcesCard.tsx` | 출처 카드 |
| `components/ChatWarningBadge.tsx` | RAG 폴백 경고 배지 |
| `index.ts` | 모듈 export |

---

## 5. 삭제 대상 파일

### 5.1 프론트엔드 (전체 삭제)

```
src/features/chatbot/          ← 전체 디렉토리 삭제
├── components/
│   ├── ChatBubble.tsx
│   ├── ChatMessageList.tsx
│   ├── ChatPanel.tsx
│   ├── GlobalChatbot.tsx
│   ├── SourcesCard.tsx
│   └── index.ts
├── hooks/
│   ├── useChatbot.ts
│   └── index.ts
├── providers/
│   ├── ChatContextProvider.tsx
│   └── index.ts
├── types/
│   ├── chat.ts
│   └── index.ts
├── utils/
│   ├── sseClient.ts
│   ├── renderCitationLine.tsx
│   └── index.ts
└── index.ts
```

### 5.2 백엔드 (삭제 또는 정리)

| 파일 | 처리 |
|------|------|
| `app/features/rag/application/chat_service.py` | **삭제** — 로직이 새 chat_service로 이전 |
| `app/features/rag/application/unified_chat_service.py` | **삭제** — 디스패처 불필요 |
| `app/features/rag/application/deps.py` | **정리** — 챗봇 관련 DI만 제거 |
| `app/features/roadmaps/application/roadmap_chat_service.py` | **삭제** — 로직이 새 chat_service에 흡수 |
| `app/api/v1/rag/router.py` | **정리** — `/chat`, `/chat/stream` 제거, `/query` 유지 |
| `app/api/v1/roadmaps/chat.py` | **삭제** — 전체 파일 |
| `app/api/v1/schemas.py` | **정리** — `UnifiedChatRequest` 등 챗봇 스키마 제거 |
| `tests/api/test_unified_chat.py` | **삭제** — 새 테스트로 대체 |

### 5.3 프론트엔드 수정 파일

| 파일 | 변경 |
|------|------|
| `src/app/layout.tsx` | `ChatContextProvider` + `GlobalChatbot` → `ChatProvider` + `ChatWidget` |
| `src/features/roadmap/components/TimelineStepItem.tsx` | "AI에게 물어보기" 버튼 + `useChatContext` import 제거 |

---

## 6. 내부 의존성 그래프

```
IntentClassifier
  ├── SemanticRouter.classify()        ← 재사용
  ├── ActionKit 키워드 풀              ← 로드맵 단계에서 추출
  └── step 매칭 (current vs other)

ChatService (SSE)
  ├── IntentClassifier.classify()      ← 신규
  ├── ContextBuilder.build()           ← 재사용
  ├── RagService.query()               ← 재사용
  ├── SessionService                   ← 신규
  └── LLM (OpenAI astream)

SessionService
  └── RoadmapChatRepository            ← 확장 재사용

ChatProvider (FE)
  ├── useChat                          ← 신규
  ├── useSessions                      ← 신규
  └── localStorage (roadmap context)
```

---

## 7. 외부 의존성

| 서비스 | 용도 | 필수 |
|--------|------|------|
| OpenAI API | LLM 스트리밍 + 임베딩 | 필수 |
| PostgreSQL 16 + pgvector | DB + 벡터 검색 | 필수 |
| Redis | 직접 사용 안 함 | 불필요 |

---

## 8. SSE 프로토콜 (전체)

```
-- 기존 유지
data: {"type":"token","token":"텍스트"}\n\n
data: {"type":"sources","sources":[...]}\n\n
data: {"type":"meta","session_id":"uuid","message_id":42}\n\n
data: {"type":"done"}\n\n
data: {"type":"error","code":"OUT_OF_SCOPE","message":"..."}\n\n
: heartbeat\n\n

-- 신규 추가
data: {"type":"intent","category":"current_step","step_title":"사업자등록"}\n\n
data: {"type":"warning","code":"RAG_FALLBACK","message":"출처 미확인 정보..."}\n\n
```

---

## 9. IntentClassifier 분류 흐름

```
질문 입력
  │
  ├─ [1순위] out_of_scope 체크 (SemanticRouter threshold: 0.75)
  │   └─ 투자/세금계산/소송/의료 → 차단
  │
  ├─ [2순위] step_related 매칭 (로드맵 보유 사용자만)
  │   ├─ 현재 단계 ActionKit 키워드 매칭 → current_step
  │   ├─ "이 단계", "지금", "현재", "체크리스트" 키워드 → current_step
  │   ├─ 다른 단계명/번호 언급 → other_step
  │   └─ 다른 단계 ActionKit 키워드 매칭 → other_step
  │
  ├─ [3순위] legal vs general (SemanticRouter threshold: 0.7)
  │   ├─ legal 유사도 ≥ 0.7 → legal_general
  │   ├─ legal 키워드 폴백 → legal_general
  │   └─ 기본 → general
  │
  └─ [기본값] general
```

---

## 10. API 엔드포인트 상세

### POST /api/v1/chat/stream

**Request:**
```json
{
  "message": "사업자등록 절차 알려줘",
  "session_id": "uuid-or-null"
}
```

**SSE Response Flow:**
1. `intent` → 분류 결과 전달
2. `token` × N → 스트리밍 토큰
3. `sources` → 출처 (있을 때만)
4. `warning` → RAG 폴백 경고 (있을 때만)
5. `meta` → session_id + message_id
6. `done` → 완료

### GET /api/v1/chat/sessions
- Query: `?limit=50&offset=0`
- Response: `{ sessions: [...], total: N }`

### POST /api/v1/chat/sessions
- Body: `{}` (빈 세션 생성)
- Response: `{ id, title: null, created_at }`

### PATCH /api/v1/chat/sessions/{id}
- Body: `{ "title": "새 제목" }`
- Response: `{ id, title }`

### DELETE /api/v1/chat/sessions/{id}
- Response: `204 No Content` (소프트 삭제)

### GET /api/v1/chat/sessions/{id}/messages
- Query: `?limit=50&offset=0`
- Response: `{ messages: [...], total: N }`

---

## 11. 관련 문서 링크

| 문서 | 경로 | 역할 |
|------|------|------|
| 설계 문서 (마스터) | `dev/active/unified-chatbot-integration/chatbot-ux-improvement-plan.md` | 전체 UX 설계 + 결정 근거 |
| UX 리서치 | `dev/active/unified-chatbot-integration/chatbot-unification-research.md` | 문제 시나리오 + 대안 분석 |
| 기존 통합 계획 | `dev/active/unified-chatbot-integration/unified-chatbot-integration-plan.md` | 이전 통합 작업 (완료) 참조 |
| 기존 작업 체크리스트 | `dev/active/unified-chatbot-integration/unified-chatbot-integration-tasks.md` | 이전 통합 작업 완료 내역 |
| 구현 계획 | `dev/active/stepzero-ai-chat-rebuild/stepzero-ai-chat-rebuild-plan.md` | Phase별 구현 상세 |
| 작업 체크리스트 | `dev/active/stepzero-ai-chat-rebuild/stepzero-ai-chat-rebuild-tasks.md` | 진행 추적 |
