# Phase 4 AI 코치 챗봇 — 코드 아키텍처 리뷰

Last Updated: 2026-03-02

---

## Executive Summary

Phase 4 구현은 전반적으로 잘 설계되어 있으며 기존 패턴을 대체로 따르고 있습니다. SSE 스트리밍, 3레이어 컨텍스트 빌더, 출처 파싱 등 핵심 기능이 동작하도록 구현되었습니다. 다만 **중복 팩토리 함수**, **SSE 하트비트 미작동**, **레이어 간 트랜잭션 책임 혼재**, **프론트엔드 Silent Refresh 미적용** 등 수정이 필요한 이슈가 발견되었습니다.

---

## Critical Issues (반드시 수정)

### C-1. `deps.py`의 `get_roadmap_chat_service()`가 사용되지 않음 (Dead Code + 중복 팩토리)

**파일:** `app/features/roadmaps/application/deps.py:40-50` / `app/api/v1/roadmaps/chat.py:41-63`

`deps.py`에 `get_roadmap_chat_service()` 함수가 정의되어 있지만, `chat.py` 라우터는 이를 사용하지 않고 별도의 `_build_chat_service()` 함수를 직접 구현하고 있습니다. 두 함수가 동일한 역할을 수행하며 동기화 상태가 유지되지 않아 버그 발생 위험이 있습니다.

- `deps.py`의 `get_roadmap_chat_service()`는 `get_semantic_router()`를 직접 호출 (예외 미처리)
- `chat.py`의 `_build_chat_service()`는 try/except로 SemanticRouter 로드 실패를 허용

**권장 수정:** `chat.py`에서 `deps.py`의 `get_roadmap_chat_service()`를 사용하도록 통일. 예외 처리 방식 결정 후 한 곳에서만 관리.

---

### C-2. `_heartbeat_sender()`가 실제로 하트비트를 전송하지 않음

**파일:** `app/features/roadmaps/application/roadmap_chat_service.py:271-283`

`_heartbeat_sender()` 코루틴은 `asyncio.sleep()` 무한 루프만 실행하며, 실제 SSE 이벤트를 `yield`하지 않습니다. `stream()` 제너레이터 외부에서 `asyncio.create_task()`로 실행되기 때문에 클라이언트에 하트비트 메시지가 전달되지 않습니다.

결과적으로 LLM 응답이 30초 이상 걸리는 경우, 리버스 프록시(Nginx 기본 60초)나 클라이언트가 연결을 끊을 수 있습니다. 주석에도 "실제 하트비트는 외부에서 처리해야 함"이라고 되어 있지만, 실제 구현이 없는 상태입니다.

**권장 수정:** `stream()` 제너레이터 내에서 LLM 청크 사이에 `": heartbeat\n\n"` SSE 코멘트를 주기적으로 `yield`하거나, `asyncio.wait_for()`를 활용한 타임아웃 방식으로 변경.

---

### C-3. 서비스 레이어에서 `session.commit()` 직접 호출

**파일:** `app/features/roadmaps/application/roadmap_chat_service.py:178`

`roadmap_chat_service.py`의 `stream()` 메서드 내부에서 `await session.commit()`을 직접 호출합니다. 기존 `chat_service.py`는 commit을 호출하지 않으며, 트랜잭션 관리는 라우터/의존성 주입 레이어의 책임입니다.

특히 SSE 스트리밍 중간에 commit이 일어나므로, 이후에 예외 발생 시 일관성 없는 상태가 됩니다.

**권장 수정:** `stream()` 제너레이터에서 `session.commit()` 제거. 라우터 또는 미들웨어에서 트랜잭션을 관리하도록 변경.

---

### C-4. `list_chat_threads()` — DB에서 전체 조회 후 Python 레벨 필터링

**파일:** `app/api/v1/roadmaps/chat.py:198-209`

```python
threads = await chat_repo.list_threads(roadmap_id, step_id)
return [... for t in threads if t.user_id == current_user.id]
```

`list_threads()` 쿼리에 `user_id` 필터가 없어 특정 단계의 모든 사용자 스레드를 DB에서 가져온 후 Python에서 필터링합니다. 팀 내 멤버가 많을수록 불필요한 데이터 전송이 발생하며, 잠재적인 데이터 노출 위험이 있습니다.

**권장 수정:** `list_threads()` 쿼리에 `user_id` 필터 추가.

---

### C-5. `get_thread_messages()` — `offset` 파라미터가 실제로 동작하지 않음

**파일:** `app/api/v1/roadmaps/chat.py:249` / `app/repositories/roadmap_chat_repository.py:97-111`

라우터에서 `offset: int = Query(0, ...)` 파라미터를 받지만, `get_recent_messages()`는 `limit` 파라미터만 지원하고 `offset`을 지원하지 않습니다. API 계약과 실제 구현이 불일치합니다.

**권장 수정:** `get_recent_messages()`에 `offset` 파라미터를 추가하거나, 라우터에서 `offset` 파라미터를 제거.

---

### C-6. `get_or_create_thread()` — 동시 요청 시 Race Condition

**파일:** `app/repositories/roadmap_chat_repository.py:14-39`

SELECT 후 INSERT 패턴에서, 두 요청이 동시에 스레드가 없다고 판단하면 두 스레드가 생성됩니다. DB 레벨의 UNIQUE constraint가 `(roadmap_id, step_id, user_id)`에 없어 중복 스레드가 생성될 수 있습니다.

**권장 수정:** Alembic 마이그레이션에서 `(roadmap_id, step_id, user_id)` 복합 UNIQUE constraint 추가. `INSERT ... ON CONFLICT DO NOTHING` 또는 `SELECT FOR UPDATE` 패턴 사용.

---

### C-7. 프론트엔드 SSE — Silent Refresh 미적용

**파일:** `app-frontend/src/features/roadmap/hooks/useStepChat.ts:206-216`

SSE 엔드포인트만 native `fetch()`를 사용하면서 `localStorage.getItem("token")`으로 토큰을 직접 읽습니다. 기존 `apiClient`(Axios)는 토큰 만료 시 silent refresh를 자동으로 처리하지만, 이 SSE fetch는 401 응답 시 단순 에러 메시지만 표시하고 자동 갱신을 시도하지 않습니다.

사용자가 긴 세션에서 토큰 만료 시 재로그인이 필요한 UX 문제가 발생합니다.

**권장 수정:** SSE 요청 전 `apiClient`를 통해 토큰 유효성을 확인하거나, token refresh 로직을 fetch 호출 전에 삽입. 또는 `eventsource-parser` 라이브러리와 함께 Axios interceptor 패턴을 적용.

---

## Important Improvements (수정 권장)

### I-1. 컨텍스트 중복 — 최근 대화가 LLM에 두 번 전달됨

**파일:** `app/features/roadmaps/application/roadmap_chat_service.py:117-123` / `context_builder.py:267-274`

`stream()` 내에서:
1. `context_builder.build()`를 호출하면서 `recent` 메시지 전달 → RULES 레이어 내에 텍스트로 포함
2. `_build_chat_messages()`에서 동일한 `recent` 메시지를 LangChain HumanMessage/AIMessage로 추가

최근 5개 대화가 시스템 프롬프트와 메시지 배열 두 곳에 중복 전달됩니다. 토큰 낭비이며, LLM 컨텍스트 혼란을 야기할 수 있습니다.

**권장 수정:** 두 방식 중 하나 선택. 일반적으로 `recent` 메시지는 LangChain 메시지 배열로만 전달하고, 시스템 프롬프트의 RULES 레이어에서는 제거하는 것이 더 효율적.

---

### I-2. 출처 파싱을 위한 중복 DB 쿼리

**파일:** `app/features/roadmaps/application/roadmap_chat_service.py:163-166`

```python
step_actions = await self.context_builder.roadmap_repo.list_step_actions([step.id])
```

`context_builder.build()` 내에서 이미 `list_step_actions()`를 한 번 호출했는데, 출처 파싱을 위해 동일한 쿼리를 다시 호출합니다.

**권장 수정:** `build()` 메서드가 actions 목록을 반환하도록 변경하거나, 서비스에 actions를 파라미터로 전달.

---

### I-3. `ix_roadmap_chat_threads_roadmap_step` 인덱스 비효율

**파일:** `app/models/roadmap_chat.py:17-23`

`get_or_create_thread()` 쿼리는 `(roadmap_id, step_id, user_id)` 3개 컬럼으로 조회하지만, 복합 인덱스는 `(roadmap_id, step_id)` 2개 컬럼만 포함. `user_id`가 인덱스에 없어 인덱스 범위 스캔 후 row fetch + user_id 필터링이 발생.

**권장 수정:** 인덱스를 `(roadmap_id, step_id, user_id)`로 확장. C-6의 UNIQUE constraint와 함께 처리 가능.

---

### I-4. `RoadmapChatMessage.role` — DB 레벨 제약 없음

**파일:** `app/models/roadmap_chat.py:52`

`role: str` 타입으로 `"user"`, `"assistant"`, `"system"` 외의 임의 값 삽입이 가능합니다. Pydantic 스키마에도 `Literal` 타입이 아니어서 API 레벨 검증도 없습니다.

**권장 수정:** `Literal["user", "assistant", "system"]` 타입 적용 또는 DB CHECK constraint 추가.

---

### I-5. `context_builder.py`의 `session` 파라미터 미사용

**파일:** `app/features/roadmaps/application/context_builder.py:47`

`build()` 메서드가 `session: AsyncSession` 파라미터를 받지만 실제로 사용하지 않습니다. `roadmap_repo`가 이미 세션을 보유하므로 불필요한 파라미터입니다.

**권장 수정:** `session` 파라미터 제거.

---

### I-6. `add_message()` 내 스레드 재조회 비효율

**파일:** `app/repositories/roadmap_chat_repository.py:83-94`

메시지를 추가할 때마다 스레드를 SELECT로 재조회합니다. 호출 측(서비스)에서 이미 `thread` 인스턴스를 보유하므로, 인스턴스를 파라미터로 전달하면 추가 쿼리를 피할 수 있습니다.

---

### I-7. `SemanticRouter` — `out_of_scope` 분류가 기존 `ChatService`에서 처리되지 않음

**파일:** `app/features/rag/application/semantic_router.py:60-71` / `app/features/rag/application/chat_service.py:96-102`

`SemanticRouter.classify()`는 `"out_of_scope"` 카테고리를 반환할 수 있지만, `ChatService.chat()`에서는 `legal`/`general`만 처리하고 `out_of_scope`는 `general`로 fallthrough됩니다. 반면 `RoadmapChatService.stream()`은 `out_of_scope`를 올바르게 처리합니다.

기존 RAG 챗봇과 신규 AI 코치 간 일관성 없음.

---

### I-8. 프론트엔드 — `done` 이벤트 처리에서 잘못된 ID 비교

**파일:** `app-frontend/src/features/roadmap/hooks/useStepChat.ts:292-300`

`meta` 이벤트에서 `assistantId`가 서버 메시지 ID로 교체된 후, `done` 이벤트에서 다시 `assistantId`로 탐색합니다. `meta` → `done` 순서가 보장되면 `assistantId`로 찾을 수 없어 `isStreaming: false` 처리가 실패할 수 있습니다.

```typescript
// done 이벤트에서:
prev.map((m) =>
  m.id === assistantId || m.id === String((event as SSEDoneEvent & { message_id?: number }).message_id)
    ? { ...m, isStreaming: false, sources: receivedSources }
    : m,
)
```

`SSEDoneEvent`에 `message_id`가 없어 타입 캐스팅이 안전하지 않습니다. 스트리밍 종료 후 cleanup 로직(라인 311-320)이 보완하므로 실제 버그는 없지만 코드가 혼란스럽습니다.

**권장 수정:** `meta` 이벤트 이후 별도 ref에 서버 메시지 ID를 보관하고, `done`에서 이를 사용.

---

## Minor Suggestions (선택적 개선)

### M-1. 한국어 토큰 추정 부정확

**파일:** `context_builder.py:30` / `roadmap_chat_service.py:177`

`_CHARS_PER_TOKEN = 4` (char/4)를 사용하지만, 한국어는 1글자가 1.5~2 토큰으로 실제 토큰 예산이 최대 50% 초과될 수 있습니다. `tiktoken` 라이브러리 사용이 정확하나, 간단하게는 `char/2`로 조정하는 것이 더 보수적입니다.

---

### M-2. 프롬프트 최종 절단 시 XML 태그 손상 가능성

**파일:** `context_builder.py:342-348`

최악의 경우 `result[:max_chars]`로 단순 절단 시 `</FACTS>`, `</STATUS>` 등의 태그가 잘릴 수 있습니다. LLM이 불완전한 XML 구조를 받게 되어 응답 품질이 저하됩니다.

---

### M-3. `StepChatPanel` — 스트리밍 중 전체 메시지 목록 re-render

**파일:** `app-frontend/src/features/roadmap/components/StepChatPanel.tsx:217-219`

매 토큰 수신 시 `setMessages()`로 상태가 업데이트되어 모든 `ChatBubble`이 re-render됩니다. `React.memo(ChatBubble)`을 적용하면 스트리밍 중인 메시지만 re-render됩니다.

---

### M-4. `SemanticRouter` 키워드 매칭 오분류 가능성

**파일:** `app/features/rag/application/semantic_router.py:139-141`

`any(kw in query for kw in LEGAL_KEYWORDS)` — 단순 포함 여부 검사라 "세금사기", "영업정지"처럼 키워드를 포함한 비법률 맥락도 `"legal"`로 분류됩니다. 단어 경계 검사 또는 더 정밀한 임베딩 분류 사용 권장.

---

### M-5. `ThreadSummary` 스키마에 `title` 필드 누락

**파일:** `app/api/v1/schemas.py:214-218`

`RoadmapChatThread` 모델에 `title: str | None` 필드가 있지만 `ThreadSummary` 응답 스키마에 없습니다. 향후 스레드 제목 기능 구현 시 스키마 추가 필요.

---

### M-6. 레이트 리밋 없음

**파일:** `app/api/v1/roadmaps/chat.py:113-169`

`/chat/stream` 엔드포인트에 레이트 리밋이 없어 악의적 사용자가 LLM API를 무제한 호출할 수 있습니다. 사용자당 분당 요청 수 제한(slowapi 등) 적용 권장.

---

### M-7. 모바일 키보드 오프셋 직접 DOM 조작

**파일:** `app-frontend/src/features/roadmap/components/StepChatPanel.tsx:110-114`

`panel.style.paddingBottom`를 직접 수정하는 것은 React 패턴과 맞지 않습니다. state를 통해 `paddingBottom` 값을 관리하는 방식 권장.

---

## Architecture Considerations

### 아키텍처 관찰 1 — 트랜잭션 경계 설계

서비스 레이어에서 `flush()`만 사용하고 `commit()`은 라우터 레이어에서 처리하는 것이 기존 패턴 (e.g., `get_or_create_thread`에서 flush만 사용). `roadmap_chat_service.py`가 이 패턴을 깨고 commit을 직접 호출함. SSE 스트리밍 특성상 라우터에서 commit을 하기 어려운 구조적 문제가 있지만, FastAPI `BackgroundTask` 또는 `yield` 의존성 패턴으로 해결 가능.

### 아키텍처 관찰 2 — SemanticRouter의 `out_of_scope` 처리

AI 코치에서 `out_of_scope`는 단계 범위 외 질문을 차단하는 용도이지만, 시스템 프롬프트의 RULES 레이어에서 이미 "범위 제한" 규칙을 LLM에게 안내합니다. SemanticRouter 차단과 LLM 프롬프트 차단이 중복됩니다. SemanticRouter는 명백한 out-of-scope(소송, 의료 등)만 차단하고, 모호한 경우는 LLM이 판단하도록 하는 것이 현재 설계이므로 의도적인 것으로 보입니다.

### 아키텍처 관찰 3 — SSE 연결 종료 시 부분 응답 처리

클라이언트가 연결을 끊으면 `asyncio.CancelledError`가 발생하지만, 이미 DB에 저장된 user 메시지는 남아 있고 assistant 응답은 없는 불완전한 상태가 됩니다. 이 상태에서 사용자가 다시 접속하면 대화 이력에 응답 없는 user 메시지가 표시됩니다. `CancelledError` 처리에서 partial response를 저장하거나, user 메시지를 롤백하는 로직이 필요합니다.

---

## 이슈 우선순위 요약

| 번호 | 파일 | 심각도 | 이슈 |
|------|------|--------|------|
| C-1 | `deps.py` / `chat.py` | **Must Fix** | 중복 팩토리 함수 (dead code) |
| C-2 | `roadmap_chat_service.py` | **Must Fix** | 하트비트 미작동 (좀비 SSE 연결 위험) |
| C-3 | `roadmap_chat_service.py` | **Must Fix** | 서비스 레이어 직접 commit — 트랜잭션 책임 혼재 |
| C-4 | `chat.py` | **Must Fix** | 스레드 목록 user_id 필터 누락 (DB 효율 + 데이터 노출) |
| C-5 | `chat.py` / `roadmap_chat_repository.py` | **Must Fix** | offset 파라미터 미동작 (API 계약 불이행) |
| C-6 | `roadmap_chat_repository.py` | **Must Fix** | 동시 요청 race condition (중복 스레드 생성) |
| C-7 | `useStepChat.ts` | **Must Fix** | SSE에 silent refresh 미적용 (만료 토큰 처리 불가) |
| I-1 | `roadmap_chat_service.py` | Should Fix | 최근 대화 중복 전달 (토큰 낭비) |
| I-2 | `roadmap_chat_service.py` | Should Fix | 출처 파싱을 위한 중복 DB 쿼리 |
| I-3 | `roadmap_chat.py` | Should Fix | 인덱스 컬럼 누락 |
| I-4 | `roadmap_chat.py` | Should Fix | role 필드 제약 없음 |
| I-5 | `context_builder.py` | Should Fix | 미사용 session 파라미터 |
| I-6 | `roadmap_chat_repository.py` | Should Fix | add_message 내 스레드 재조회 |
| I-7 | `chat_service.py` / `semantic_router.py` | Should Fix | out_of_scope 분류 기존 서비스 미처리 |
| I-8 | `useStepChat.ts` | Should Fix | done 이벤트 ID 비교 불안전 |
| M-1~7 | 다수 | Nice to Have | 토큰 추정, 메모이제이션, 레이트 리밋 등 |

---

## Next Steps

1. C-1: `chat.py`의 `_build_chat_service()` 제거 후 `deps.py`의 `get_roadmap_chat_service()` 사용
2. C-6: Alembic 마이그레이션에서 `(roadmap_id, step_id, user_id)` UNIQUE constraint 추가
3. C-4: `list_threads()` 쿼리에 `user_id` 필터 추가
4. C-5: repository에 offset 지원 추가 또는 API에서 offset 제거
5. C-3: `stream()` 내 `session.commit()` 제거, 대안 방식 설계
6. C-2: 실제 동작하는 하트비트 구현 (SSE comment 방식)
7. C-7: 프론트엔드 SSE fetch에 silent refresh 로직 통합

**중요:** 코드 수정 전 팀장 승인 필요. 이 문서는 리뷰 결과만 포함합니다.
