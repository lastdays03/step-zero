# StepZero AI 챗봇 — 구현 계획 vs 실제 구현 감사 보고서

> **Date**: 2026-03-03
> **Branch**: `feature/4-ai-coach-chatbot`
> **기준 커밋**: `c03ddfa` (리뷰 반영) + 핫픽스 2건 적용 후
> **감사 범위**: 계획 문서 4건 대비 BE 14개 영역 + FE 21개 영역 전수 대조
> **최종 수정**: 미구현 6건 + 허용편차 1건 일괄 수정 완료

---

## 1. 전체 요약

| 영역 | 검사 항목 | 일치 | 미구현/불일치 | 허용 가능 편차 |
|------|----------|------|-------------|--------------|
| BE 모델/마이그레이션 | 5 | 5 | 0 | 0 |
| BE IntentClassifier | 10 | 10 | 0 | 0 |
| BE SessionService | 7 | 4 | 0 | 3 |
| BE ChatService (SSE) | 18 | 18 | 0 | 0 |
| BE 스키마/DI/라우터 | 13 | 13 | 0 | 0 |
| BE 레거시 정리 | 8 | 8 | 0 | 0 |
| FE 타입/유틸 | 15 | 15 | 0 | 0 |
| FE Provider/훅 | 14 | 14 | 0 | 0 |
| FE 컴포넌트 | 30+ | 30+ | 0 | 0 |
| FE 레거시 정리 | 3 | 3 | 0 | 0 |
| **합계** | **120+** | **120+** | **0** | **6** |

**결론**: 미구현 6건 전부 수정 완료. 허용 가능 편차 6건은 의도적 개선/기능 동일로 유지.

---

## 2. 핫픽스 적용 내역 (감사 과정에서 발견 → 즉시 수정)

감사 시작 전, 기존 코드 분석 과정에서 2건의 버그를 발견하여 수정 완료함.

### 2.1 `mountedRef.current = true` 복원 (FE)

- **파일**: `app-frontend/src/features/chat/hooks/useChat.ts`
- **원인**: `c03ddfa` 리팩토링에서 "불필요 할당"으로 오판하여 제거
- **증상**: React 18 StrictMode에서 `mountedRef.current`가 `false`로 고정 → SSE 이벤트 8곳의 가드에 의해 모든 state 업데이트 차단 → 채팅창에 응답 표시 안 됨
- **수정**: `useEffect` 내 `mountedRef.current = true` 1줄 복원

### 2.2 `session.commit()` 추가 (BE)

- **파일**: `app-backend/app/api/v1/chat/router.py`
- **원인**: 최초 구현(`1d335cc`)부터 누락
- **증상**: 스트리밍 중 `flush()`로 DB에 SQL 전송되지만, `get_session()` 종료 시 트랜잭션 롤백 → 세션/메시지/제목이 영구 저장되지 않음
- **수정**: `_stream_and_commit()` 래퍼 제너레이터로 스트리밍 완료 후 `await session.commit()` 호출

---

## 3. 미구현 / 불일치 항목 (6건 → ✅ 전부 수정 완료)

### 3.1 ✅ [프로토콜] `intent` SSE 이벤트 분리

| | 내용 |
|---|------|
| **계획** | 별도 `intent` 이벤트 발행: `{"type":"intent","category":"current_step","step_title":"사업자등록"}` |
| **수정 전** | intent 정보가 `meta` 이벤트에만 합쳐짐 |
| **수정 후** | `meta` 이벤트 직후 별도 `intent` 이벤트 발행 (`chat_service.py:188-193`). FE `case "intent":` 핸들러가 정상 동작 |

### 3.2 ✅ [프로토콜] `done` 이벤트에 `message_id` 포함

| | 내용 |
|---|------|
| **계획** | 스트리밍 완료 후 `message_id` 전달 |
| **수정 전** | `message_id` 필드 없음 |
| **수정 후** | 어시스턴트 메시지 DB 저장 후 `done` 이벤트에 `message_id` 포함 (`chat_service.py:247-250`). FE `serverMessageId` 정상 수신 |

### 3.3 ✅ [기능] `other_step` 응답에 "N단계 기준" 프리픽스

| | 내용 |
|---|------|
| **계획** | other_step 카테고리 응답 시 "N단계 기준으로 답변합니다" 안내 포함 |
| **수정 전** | `current_step`과 `other_step` 완전히 동일 처리 |
| **수정 후** | `other_step`일 때 `📍 N단계(제목) 기준으로 답변합니다.` 프리픽스 토큰 선행 발행 (`chat_service.py:331-335`) |

### 3.4 ✅ [기능] `legal_general` RAG 성공 시 `sources` SSE 이벤트 발행 + 토큰 스트리밍

| | 내용 |
|---|------|
| **계획** | RAG 성공 → `{"type":"sources","sources":[...]}` 구조화된 출처 이벤트 발행 |
| **수정 전** | `RagService.query()`가 단순 문자열만 반환. 전체 답변이 단일 `token` 이벤트로 전송 |
| **수정 후** | `RagService.retrieve()` 신규 메서드 추가 (`rag_service.py:106-128`) — retriever 별도 호출 → `(docs, sources)` 반환. `_handle_legal_response()`에서 sources SSE 이벤트 발행 (`chat_service.py:359-361`) + `_llm_stream()` 재활용으로 토큰 단위 스트리밍 (`chat_service.py:377-378`). sources는 DB에도 저장 (`chat_service.py:242`) |

### 3.5 ✅ [프로토콜] `warning` 이벤트에 `code` 필드 추가

| | 내용 |
|---|------|
| **계획** | `{"type":"warning","code":"RAG_FALLBACK","message":"..."}` |
| **수정 전** | `code` 필드 없음 |
| **수정 후** | `"code": "RAG_FALLBACK"` 추가 (`chat_service.py:391`). FE `ChatWarningBadge`에서 `warning.code` 사용 가능 |

### 3.6 ✅ [스키마] `sources_json` 타입 통일

| | 내용 |
|---|------|
| **계획** | `list[dict] | None` (출처 리스트) |
| **수정 전** | DB 모델: `dict | None`, 스키마: `list[dict] | None` — 불일치 |
| **수정 후** | `roadmap_chat.py` 모델 + `roadmap_chat_repository.py` 파라미터 모두 `list[dict] | None`으로 통일. DB 컬럼은 `sa.JSON` 타입이므로 마이그레이션 불필요 |

---

## 4. 허용 가능 편차 (6건, 수정 불필요)

| # | 항목 | 계획 | 구현 | 비고 |
|---|------|------|------|------|
| 1 | `set_auto_title` 길이 | 30자 | 40자 (`_AUTO_TITLE_MAX_LENGTH = 40`) | UX 개선 — 40자가 더 자연스러운 제목 길이 |
| 2 | `SessionService.create_session` 시그니처 | `team_id` 파라미터 포함 | `team_id` 없음 | DB 모델에도 없음. `user_id`로 테넌시 관리하는 설계 |
| 3 | ChatProvider API 이름 | `showHistory()`, `showChat()` | `setHistoryView(boolean)` | 기능 동일, API 표면만 다름 |
| 4 | useChat 메서드명 | `loadHistory(sessionId)` | `loadSession(sessionId)` | 기능 동일, 이름만 다름 |
| 5 | 면책 문구 | "AI 생성 정보 · 정확성 미보장" | 더 상세한 문구 + 전문가 상담 권유 | UX 개선 |
| 6 | SourcesCard 헤더 아이콘 | 📎 이모지 | ChevronDown/Up 아이콘 | 시각적 차이만, 기능 동일 |

> **편차 #7 (RAG 스트리밍)은 3.4 수정 시 함께 해결됨** — `RagService.retrieve()` + `_llm_stream()` 재활용으로 토큰 단위 스트리밍 구현.

---

## 5. 완전 일치 항목 (주요)

### 5.1 백엔드

- **DB 모델**: roadmap_id/step_id nullable, is_deleted, intent_category, UNIQUE 제약 제거 — 5개 필드 전부 일치
- **Alembic 013**: upgrade/downgrade 모두 정상
- **IntentClassifier**: 5카테고리, 3단계 우선순위 (out_of_scope 0.75 → step_related → legal/general 0.7), StepInfo, 키워드 세트 23개 동일
- **SessionService**: CRUD 6개 메서드 전부 구현 (create, list, get, get_messages, update_title, soft_delete, set_auto_title)
- **ChatService**: 세션 resolve, 자동 제목, 사용자 메시지 저장, 의도 분류, 카테고리별 분기 5종, 어시스턴트 응답 저장, 하트비트 15초, 에러 핸들링
- **스키마**: ChatStreamRequest(1~2000자), SessionCreateRequest, SessionUpdateRequest(1~100자), SessionResponse, MessageResponse, 리스트 응답 — 전부 일치
- **DI 팩토리**: get_intent_classifier (singleton), get_session_service, get_chat_service — 전부 일치
- **라우터**: 6개 엔드포인트 (POST /stream, GET/POST /sessions, GET /sessions/{id}/messages, PATCH/DELETE /sessions/{id}) — 전부 일치
- **레포지토리 확장**: list_sessions, update_thread_title, soft_delete_thread, create_session — 전부 일치
- **레거시 정리**: chat_service, unified_chat_service, roadmap_chat_service, chat.py 삭제. rag/deps.py, rag/router.py, schemas.py 정리. test_unified_chat.py 삭제 — 전부 완료

### 5.2 프론트엔드

- **타입**: IntentCategory, ChatMessage, ChatSession, SSEEvent(서브타입 7개), CitationSource — 전부 일치
- **SSE 유틸**: parseSSELine, getAuthHeaders, getApiBaseUrl, tryRefreshToken — 4개 전부 일치
- **API 유틸**: fetchSessions, createSession, fetchMessages, updateSessionTitle, deleteSession + authFetch 래퍼 — 전부 일치
- **ChatProvider**: currentSessionId, roadmapContext(자동 감지), 패널 상태, 히스토리 뷰 — 전부 일치
- **useChat**: messages, isStreaming, sendMessage(SSE 7개 이벤트 처리), loadSession, startNewChat, 401 재시도, AbortController — 전부 일치
- **useSessions**: sessions, loadSessions, createSession, renameSession, deleteSession, 날짜 그룹핑(오늘/어제/이전) — 전부 일치
- **UI 컴포넌트 10개**: ChatWidget, ChatFAB, ChatPanel, ChatMessages, ChatMessage, ChatInput, ChatHistory, ChatEmptyState, SourcesCard, ChatWarningBadge — 전부 일치
- **citations.tsx**: renderCitationLine([법령 N], [서류 N] 인라인 배지) — 일치
- **layout.tsx**: ChatProvider 래핑 + ChatWidget 배치 — 일치
- **레거시 정리**: `features/chatbot/` 전체 삭제, TimelineStepItem "AI에게 물어보기" 버튼 제거, grep `chatbot/useChatContext/GlobalChatbot` = 0건 — 전부 완료

---

## 6. 추가 구현 (계획에 없으나 유용한 기능)

프론트엔드에서 계획에 명시되지 않았으나 추가 구현된 항목:

| # | 항목 | 위치 | 효과 |
|---|------|------|------|
| 1 | SSE 서브타입 인터페이스 | `types/index.ts` | 타입 안전성 강화 |
| 2 | `authFetch` 래퍼 | `utils/api.ts` | 401 재시도 로직 DRY |
| 3 | `hasRoadmapContext` 파생값 | `ChatProvider.tsx` | 조건부 렌더링 간소화 |
| 4 | 글자수 카운터 (200자 이하 표시) | `ChatInput.tsx` | UX 개선 |
| 5 | 자동 높이 조절 textarea | `ChatInput.tsx` | UX 개선 |
| 6 | 바운싱 도트 스트리밍 대기 표시 | `ChatMessages.tsx` | UX 개선 |
| 7 | 인라인 이름 변경 편집 | `ChatHistory.tsx` | UX 개선 |
| 8 | 삭제 확인 다이얼로그 | `ChatHistory.tsx` | UX 안전장치 |
| 9 | `React.memo` on ChatMessage | `ChatMessage.tsx` | 스트리밍 중 리렌더 최적화 |
| 10 | `isLoading` / `error` 상태 | `useChat.ts` | 필수 UX 상태 관리 |

---

## 7. 수정 이력

| 날짜 | 항목 | 수정 파일 |
|------|------|----------|
| 2026-03-03 | 핫픽스 2건 (2.1, 2.2) | `useChat.ts`, `router.py` |
| 2026-03-03 | 미구현 6건 + 편차7 일괄 수정 (3.1~3.6) | `chat_service.py`, `rag_service.py`, `roadmap_chat.py`, `roadmap_chat_repository.py` |
