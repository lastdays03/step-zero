# Phase 4: AI 코치 챗봇 MVP — 핵심 컨텍스트 문서

> **Last Updated**: 2026-03-02

---

## 1. 핵심 파일 맵 (수정/생성 대상)

### 1.1 신규 생성 파일

| 파일 | 역할 | Section |
|------|------|:-------:|
| `app-backend/app/models/roadmap_chat.py` | RoadmapChatThread + RoadmapChatMessage 모델 | A-1 |
| `app-backend/alembic/versions/011_roadmap_chat.py` | DB 마이그레이션 | A-2 |
| `app-backend/app/features/roadmaps/application/context_builder.py` | 3레이어 시스템 프롬프트 빌더 | A-3 |
| `app-backend/app/repositories/roadmap_chat_repository.py` | Chat Thread/Message CRUD | A-5 |
| `app-backend/app/features/roadmaps/application/roadmap_chat_service.py` | SSE 스트리밍 채팅 서비스 | B-1 |
| `app-backend/app/api/v1/roadmaps/chat.py` | SSE 라우터 엔드포인트 | B-2 |
| `app-frontend/src/features/roadmap/hooks/useStepChat.ts` | SSE 기반 채팅 훅 | C-1 |
| `app-frontend/src/features/roadmap/components/StepChatPanel.tsx` | 채팅 패널 UI | C-2 |

### 1.2 수정 대상 파일

| 파일 | 변경 내용 | Section |
|------|---------|:-------:|
| `app-backend/app/models/__init__.py` | RoadmapChatThread, RoadmapChatMessage import + `__all__` 추가 | A-1 |
| `app-backend/alembic/env.py` | `roadmap_chat` 모듈 import 추가 | A-1 |
| `app-backend/app/features/rag/application/semantic_router.py` | `out_of_scope` 앵커 카테고리 추가 | A-4 |
| `app-backend/app/api/v1/roadmaps/router.py` | `chat_router` include 추가 | B-2 |
| `app-backend/app/api/v1/roadmaps/schemas.py` | StepChatRequest, ThreadSummary, ChatMessageResponse 스키마 추가 | B-2 |
| `app-frontend/src/features/roadmap/components/TimelineStepItem.tsx` | "AI에게 물어보기" 버튼 추가 | C-4 |
| `app-frontend/src/features/roadmap/components/index.ts` | StepChatPanel export 추가 | C-2 |
| `app-frontend/src/features/roadmap/hooks/index.ts` | useStepChat export 추가 | C-1 |

---

## 2. 핵심 참조 파일 (읽기 전용 / 패턴 참고)

### 2.1 백엔드 패턴 참고

| 파일 | 참고 포인트 |
|------|-----------|
| `app-backend/app/features/rag/application/chat_service.py` | ChatOpenAI 설정, chain 구성, 에러 핸들링 패턴 |
| `app-backend/app/features/rag/application/rag_service.py` | 벡터 검색 + 문서 포맷팅 패턴 |
| `app-backend/app/features/rag/application/semantic_router.py` | 앵커 기반 분류 + 코사인 유사도 구현 |
| `app-backend/app/features/rag/application/deps.py` | `@lru_cache` 싱글톤 의존성 주입 패턴 |
| `app-backend/app/features/roadmaps/application/llm_personalizer.py` | 팩트-지능 분리, `_validate_and_repair_references()` |
| `app-backend/app/features/roadmaps/application/roadmap_generation_service.py` | 파이프라인 플로우, GenerationPayload 구조 |
| `app-backend/app/repositories/roadmap_repository.py` | `list_steps()`, `list_step_details()`, `list_step_actions()` 메서드 |
| `app-backend/app/repositories/roadmap_job_repository.py` | 비동기 잡 상태 관리 패턴 |
| `app-backend/app/models/roadmap.py` | Roadmap, RoadmapStep, RoadmapStepDetail, RoadmapStepAction 구조 |
| `app-backend/app/models/roadmap_template.py` | 최근 모델 추가 패턴 (FK, 복합 인덱스, __table_args__) |
| `app-backend/app/api/deps.py` | `get_current_user()`, `get_current_team()`, JWT 검증 |
| `app-backend/app/api/v1/roadmaps/get.py` | 로드맵 상세 조회 + 단계 상태 업데이트 라우터 패턴 |
| `app-backend/app/api/v1/roadmaps/jobs.py` | 비동기 잡 라우터 패턴 |

### 2.2 프론트엔드 패턴 참고

| 파일 | 참고 포인트 |
|------|-----------|
| `app-frontend/src/features/chatbot/hooks/useChatbot.ts` | 메시지 상태 관리, sendMessage 패턴, scrollToBottom |
| `app-frontend/src/features/chatbot/components/ChatPanel.tsx` | 패널 레이아웃, 헤더, 입력 영역 구조 |
| `app-frontend/src/features/chatbot/components/ChatBubble.tsx` | 메시지 렌더링, 소스 배지, 줄바꿈 처리 |
| `app-frontend/src/features/chatbot/components/ChatInput.tsx` | textarea, Enter 키 핸들링, disabled 상태 |
| `app-frontend/src/features/chatbot/components/ChatMessageList.tsx` | 빈 상태, 로딩 상태, scrollRef 사용 |
| `app-frontend/src/features/chatbot/utils/renderAnswerLine.tsx` | URL 파싱 정규식 패턴 |
| `app-frontend/src/features/chatbot/types/chat.ts` | ChatMessage 인터페이스 |
| `app-frontend/src/features/roadmap/components/TimelineStepItem.tsx` | ACTIVE 상태 렌더링, 버튼 위치, confirming 패턴 |
| `app-frontend/src/features/roadmap/components/RoadmapExecutionView.tsx` | 메인 레이아웃, 상태 변경 핸들러 |
| `app-frontend/src/features/roadmap/components/roadmap-utils.ts` | RoadmapDetailStep, RoadmapDetailAction 타입 |
| `app-frontend/src/lib/api-client.ts` | Axios 설정, 토큰 인터셉터, silent refresh |
| `app-frontend/src/providers/AuthProvider.tsx` | useAuth() 훅, 토큰 접근 방식 |

---

## 3. 기술 결정 사항

### 3.1 확정된 결정

| 결정 | 선택 | 근거 |
|------|------|------|
| **스트리밍 프로토콜** | SSE (Server-Sent Events) | WebSocket보다 단순, 단방향 충분, HTTP/2 호환 |
| **클라이언트 SSE 구현** | `fetch` + `ReadableStream` | `EventSource`는 커스텀 헤더 불가 → JWT 전달 불가 |
| **LLM 호출 방식** | `ChatOpenAI.astream()` (LangChain) | 기존 의존성 활용, 체인 구성 용이 |
| **LLM 모델** | gpt-4o-mini (기존 설정 유지) | 비용 효율 + 충분한 품질 |
| **LLM Temperature** | 0.3 | 팩트 기반 응답 → 낮은 창의성 |
| **응답 토큰 제한** | max_tokens=1000 | 간결한 단계별 안내에 충분 |
| **대화 이력 제한** | 최근 5개 메시지 | 토큰 예산 내 유지 |
| **시스템 프롬프트 예산** | ~1,200 토큰 | LAYER 1(600) + LAYER 2(300) + LAYER 3(300) |
| **Thread 모델** | 1 Thread per (roadmap, step, user) | 단계별 컨텍스트 격리 |
| **출처 인용 형식** | `[법령 N]`, `[서류 N]` | Perplexity 패턴 차용 |
| **면책 문구** | FE 하단 고정 렌더링 | AI 기본법 준수 |
| **하트비트 간격** | 15초 | SSE 연결 유지 |
| **응답 타임아웃** | 30초 | LLM 응답 + 네트워크 여유 |
| **마이그레이션 번호** | 011 | 010 (템플릿) 이후 |

### 3.2 미결정 사항 (구현 시 확정)

| 항목 | 후보 | 결정 시점 |
|------|------|---------|
| OUT_OF_SCOPE 앵커 문장 수 | 8-12개 | A-4 구현 시 |
| 모바일 패널 높이 | 85vh vs 100vh | C-6 구현 시 |
| 토큰 트리밍 전략 | CHECKLIST 우선 vs 균등 | A-3 구현 시 |
| 대화 이력 보관 기간 | 무제한 vs 90일 | D-3 이후 |
| 동시 SSE 연결 제한 | 무제한 vs 사용자당 1개 | D-3 성능 테스트 |

---

## 4. 의존성 체크리스트

### 4.1 선행 완료 확인

- [x] Phase 0: 링크 오류 수정 + startup_method 정리 (develop 머지됨)
- [x] Phase 1: FE Quick Wins (develop 머지됨)
- [x] Phase 2: 템플릿 BE (develop 머지됨)
- [x] Phase 3: 템플릿 FE (develop 머지됨)

### 4.2 외부 의존성

| 의존성 | 상태 | 영향 |
|--------|------|------|
| OpenAI API (gpt-4o-mini) | ✅ 사용 중 | LLM 호출 |
| LangChain `astream` 지원 | ✅ `langchain-openai>=0.0.5` | SSE 스트리밍 |
| FastAPI `StreamingResponse` | ✅ `fastapi>=0.109.0` | SSE 응답 |
| PostgreSQL 16 + pgvector | ✅ 운영 중 | DB 저장 |
| Redis + ARQ | ✅ 운영 중 | (AI 코치는 ARQ 미사용, 동기 SSE) |

### 4.3 패키지 추가 필요 여부

**추가 불필요** — 모든 필요 패키지가 이미 설치됨:
- `fastapi` (StreamingResponse)
- `langchain-openai` (ChatOpenAI.astream)
- `sqlmodel` (모델)
- `python-jose` (JWT)

---

## 5. 데이터 흐름 상세

### 5.1 SSE 채팅 플로우

```
[사용자] "이 단계에서 영업신고 어떻게 해요?"
    │
    ▼ (fetch POST)
[SSE 라우터] /roadmaps/{id}/steps/{id}/chat/stream
    │
    ├─ JWT 검증 → AuthenticatedUser
    ├─ Team 권한 → Team
    ├─ Roadmap 소유권 → Roadmap
    ├─ Step 조회 → RoadmapStep (status 검증)
    │
    ▼
[RoadmapChatService.stream()]
    │
    ├─ 1. SemanticRouter.classify(message)
    │     ├─ "legal" / "general" → 계속
    │     └─ "out_of_scope" → 에러 SSE + return
    │
    ├─ 2. ChatRepository.get_or_create_thread()
    │     → RoadmapChatThread
    │
    ├─ 3. ChatRepository.add_message(user_message)
    │
    ├─ 4. ChatRepository.get_recent_messages(limit=5)
    │
    ├─ 5. ContextBuilder.build(roadmap, step, session, recent)
    │     ├─ RoadmapRepository.list_step_details([step_id])
    │     ├─ RoadmapRepository.list_step_actions([step_id])
    │     ├─ LAYER 1: 불변 팩트 (<FACTS>)
    │     ├─ LAYER 2: 실행 상태 (<STATUS>)
    │     └─ LAYER 3: 안내 규칙 (<RULES>)
    │
    ├─ 6. ChatOpenAI.astream([system, ...history, user])
    │     │
    │     ├─ yield SSE: {"type":"token","token":"영업"}
    │     ├─ yield SSE: {"type":"token","token":"신고는"}
    │     ├─ yield SSE: {"type":"token","token":"..."}
    │     └─ (스트리밍 완료)
    │
    ├─ 7. _parse_citations(full_response, actions)
    │     └─ yield SSE: {"type":"sources","sources":[...]}
    │
    ├─ 8. ChatRepository.add_message(assistant, full_response, sources)
    │     └─ yield SSE: {"type":"meta","thread_id":"...","message_id":42}
    │
    └─ 9. yield SSE: {"type":"done"}
```

### 5.2 대화 이력 로드 플로우

```
[StepChatPanel 마운트]
    │
    ▼
[useStepChat.loadHistory()]
    │
    ├─ GET /roadmaps/{id}/steps/{id}/chat/threads
    │     → threads: [{thread_id, message_count, ...}]
    │
    ├─ (최신 thread 선택)
    │
    └─ GET /roadmaps/{id}/steps/{id}/chat/threads/{tid}/messages
          → messages: [{role, content, sources, ...}]
```

---

## 6. 기존 코드 스니펫 참조

### 6.1 ChatOpenAI 설정 패턴 (chat_service.py)

```python
# 현재 코드 (참고용)
self.llm = ChatOpenAI(
    model=settings.OPENAI_CHAT_MODEL,
    timeout=20,
    max_retries=2,
    temperature=0.7,
)

# AI 코치에서 변경할 부분
self.llm = ChatOpenAI(
    model=settings.OPENAI_CHAT_MODEL,
    streaming=True,         # 추가
    timeout=30,             # 증가
    max_retries=2,
    temperature=0.3,        # 감소 (팩트 기반)
    max_tokens=1000,        # 추가
)
```

### 6.2 RoadmapRepository 활용 메서드

```python
# LAYER 1/2 데이터 조회에 사용할 기존 메서드
repo = RoadmapRepository(session)

# Step 조회
steps = await repo.list_steps(roadmap_id)

# StepDetail 조회 (phase, objective, estimated_days, risk_notes 등)
details = await repo.list_step_details([step.id])

# StepAction 조회 (CHECKLIST, DOCUMENT, LEGAL_BASIS + metadata_json)
actions = await repo.list_step_actions([step.id])
```

### 6.3 SemanticRouter 앵커 추가 패턴

```python
# 현재 구조
self.anchors = {
    "legal": [
        "창업 시 필요한 인허가 절차",
        "영업신고 방법과 서류",
        # ... 8개
    ],
    "general": [
        "카페 인테리어 추천",
        # ... 4개
    ],
}

# 추가할 카테고리
"out_of_scope": [
    "세금 얼마나 내야 하나요",
    "소송을 진행하고 싶어요",
    "투자 전략을 알려주세요",
    "의료 관련 상담",
    "부동산 계약 조건",
    "노동법 위반 시 벌금",
    "주식 투자 추천",
    "대출 금리 비교",
    # ... 8-12개
]
```

### 6.4 SSE StreamingResponse 패턴 (신규)

```python
from fastapi.responses import StreamingResponse

async def _sse_generator():
    yield f"data: {json.dumps({'type': 'token', 'token': '안녕'})}\n\n"
    # ... 스트리밍
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

return StreamingResponse(
    _sse_generator(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # nginx 버퍼링 방지
    },
)
```

### 6.5 프론트엔드 fetch + ReadableStream 패턴 (신규)

```typescript
const token = localStorage.getItem("token");
const teamId = localStorage.getItem("current_team_id");

const response = await fetch(
  `${API_BASE}/roadmaps/${roadmapId}/steps/${stepId}/chat/stream`,
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "X-Team-Id": teamId || "",
    },
    body: JSON.stringify({ message, thread_id: threadId }),
    signal: abortController.signal,  // 취소 지원
  },
);

if (!response.ok) {
  throw new Error(`HTTP ${response.status}`);
}

const reader = response.body!.getReader();
const decoder = new TextDecoder();
let buffer = "";

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, { stream: true });
  const lines = buffer.split("\n");
  buffer = lines.pop() || "";

  for (const line of lines) {
    if (line.startsWith(": ")) continue;  // 하트비트 무시
    if (!line.startsWith("data: ")) continue;

    try {
      const event = JSON.parse(line.slice(6));
      switch (event.type) {
        case "token": /* 토큰 추가 */ break;
        case "sources": /* 출처 저장 */ break;
        case "meta": /* thread_id 저장 */ break;
        case "done": /* 완료 처리 */ break;
        case "error": /* 에러 표시 */ break;
      }
    } catch { /* JSON 파싱 실패 무시 */ }
  }
}
```

---

## 7. 분석 문서 참조

| 문서 | 위치 | 참조 섹션 |
|------|------|---------|
| 챗봇 개선 분석 | `docs/research/roadmap-improvement/chatbot-enhancement-analysis.md` | Part 1 전체 (AI 코치 설계) |
| 구현 순서 보고서 | `docs/research/roadmap-improvement/implementation-order-report.md` | Phase 4 (Section 4 항목 4-A, 4-B, 4-C) |
| 템플릿 분석 | `docs/research/roadmap-improvement/roadmap-template-management-analysis.md` | Section 2-4 (공통 vs 개인화 전략) |
| 개발 상태 | `docs/context/dev-status.md` | Phase 0-3 완료 상태 |
| 기술 결정 | `docs/context/decisions.md` | FK CASCADE, Dialog 패턴, 감사로그 등 |

---

## 8. 테스트 전략

### 8.1 백엔드 테스트

| 대상 | 테스트 유형 | 위치 |
|------|:--------:|------|
| RoadmapChatThread/Message 모델 | 단위 | `tests/models/test_roadmap_chat.py` |
| RoadmapChatRepository CRUD | 통합 | `tests/repositories/test_roadmap_chat_repository.py` |
| RoadmapContextBuilder | 단위 | `tests/services/test_context_builder.py` |
| SemanticRouter (OUT_OF_SCOPE) | 단위 | `tests/services/test_semantic_router.py` |
| RoadmapChatService (모의 LLM) | 통합 | `tests/services/test_roadmap_chat_service.py` |
| SSE 라우터 | API | `tests/api/test_roadmap_chat.py` |
| 출처 파싱 | 단위 | `tests/services/test_citation_parser.py` |

### 8.2 프론트엔드 테스트

| 대상 | 테스트 유형 | 위치 |
|------|:--------:|------|
| useStepChat hook | 유닛 | `features/roadmap/__tests__/useStepChat.test.ts` |
| StepChatPanel | 컴포넌트 | `features/roadmap/__tests__/StepChatPanel.test.tsx` |
| 출처 파싱 | 유닛 | `features/roadmap/__tests__/citations.test.ts` |

### 8.3 Quality Gates

```bash
# 백엔드 변경 시 반드시 실행
cd app-backend && .venv/bin/pytest -q

# 프론트엔드 변경 시 반드시 실행
cd app-frontend && npm run lint
cd app-frontend && npm run build

# 마이그레이션 변경 시
docker compose -f docker-compose.dev.yml exec app-backend python -m alembic upgrade head
docker compose -f docker-compose.dev.yml exec app-backend python -m alembic check
```
