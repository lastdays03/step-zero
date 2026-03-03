# 글로벌 챗봇 + AI 코치 통합 계획

> **Last Updated**: 2026-03-02
> **Status**: 구현 완료
> **Branch**: `feature/4-ai-coach-chatbot`

---

## 1. Executive Summary

기존 글로벌 챗봇(Stateless JSON)과 AI 코치 챗봇(SSE 스트리밍, 로드맵 전용)을 **단일 글로벌 챗봇**으로 통합한다. 선택된 로드맵의 IN_PROGRESS 단계 컨텍스트가 모든 화면에서 자동 주입되어, 하나의 챗봇에서 코치 + 일반 AI 기능을 모두 제공한다.

### 핵심 설계 결정

| 항목 | 결정 |
|------|------|
| 스트리밍 | **전체 SSE 스트리밍** — 일반/코치 모두 토큰 단위 실시간 응답 |
| 컨텍스트 선택 | 로드맵 상세 페이지에서 선택된 로드맵의 IN_PROGRESS 단계 (localStorage `stepzero_active_roadmap_id`) |
| 모드 전환 | **불필요** — SemanticRouter가 질문 유형 자동 분류 (legal/general/out_of_scope) |
| StepChatPanel | **제거** → 글로벌 챗봇으로 완전 대체 |
| 다른 화면 | 로드맵 컨텍스트 전역 자동 유지 |
| 로드맵 없는 사용자 | 기존 일반 모드(RAG + 일반 AI)로 동작 |

---

## 2. Current State Analysis

### 글로벌 챗봇 (`features/chatbot/`)
- **엔드포인트**: `POST /api/v1/rag/chat` → JSON 응답
- **아키텍처**: Stateless, 메모리 기반 메시지 (DB 저장 없음)
- **분류**: SemanticRouter → legal(RAG) / general(LLM) / out_of_scope
- **프론트엔드**: `useChatbot()` + `GlobalChatbot` + `ChatPanel` + `ChatBubble`

### AI 코치 챗봇 (`features/roadmap/`)
- **엔드포인트**: `POST /api/v1/roadmaps/{id}/steps/{sid}/chat/stream` → SSE
- **아키텍처**: Stateful, Thread/Message DB 저장, 3레이어 시스템 프롬프트
- **분류**: SemanticRouter → out_of_scope 차단 후 LLM 스트리밍
- **프론트엔드**: `useStepChat()` + `StepChatPanel` (로드맵 화면 전용)

### 핵심 차이
| 항목 | 글로벌 | AI 코치 |
|------|--------|---------|
| 응답 방식 | JSON 일괄 | SSE 토큰 스트리밍 |
| DB 저장 | 없음 | Thread + Message |
| 프롬프트 | 기본 시스템 프롬프트 | 3레이어 (FACTS + STATUS + RULES) |
| 출처 인용 | 없음 | [법령 N], [서류 N] 파싱 |
| 접근 범위 | 전체 페이지 | 로드맵 화면만 |

---

## 3. Proposed Future State

### 통합 아키텍처

```
사용자 → 글로벌 챗봇 (모든 페이지)
         │
         ├─ ChatContextProvider (localStorage 감지)
         │   └─ stepzero_active_roadmap_id → IN_PROGRESS 단계 자동 선택
         │
         └─ POST /api/v1/rag/chat/stream (통합 SSE 엔드포인트)
             │
             ├─ roadmap_id + step_id 있음?
             │   ├─ legal 질문 → RoadmapChatService.stream() (3레이어 + DB + 출처)
             │   └─ general 질문 → ChatService.stream() (일반 SSE)
             │
             └─ 컨텍스트 없음
                 └─ ChatService.stream() (기존 일반 모드 SSE)
```

---

## 4. Implementation Phases

### Phase 1: 백엔드 — 통합 SSE 엔드포인트 (Section A)

**A-1. UnifiedChatRequest 스키마** — `schemas.py`
- `message`, `thread_id`, `roadmap_id`, `step_id` 필드
- `roadmap_id`와 `step_id`는 쌍으로 존재하거나 둘 다 없어야 함 (validator)

**A-2. ChatService.stream() 메서드** — `chat_service.py`
- 기존 `chat()` 메서드는 유지 (하위호환)
- 새 `stream()` 메서드: SSE 토큰 단위 스트리밍 (일반 + legal)
- legal: RAG 응답 전체를 단일 token 이벤트로 전송
- general: `llm.astream()` 토큰 단위

**A-3. UnifiedChatService 디스패처** — 새 파일
- `ChatService`와 `RoadmapChatService`를 조합(compose)
- roadmap 컨텍스트 유무에 따라 분기
- 로드맵/단계 소유권 검증 + 스레드 get_or_create

**A-4. DI 팩토리** — `deps.py`
- `get_unified_chat_service(session)` 추가

**A-5. SSE 라우터** — `rag/router.py`
- `POST /rag/chat/stream` 엔드포인트 추가
- 기존 `POST /rag/chat` 유지

**A-6. 백엔드 테스트**

### Phase 2: 프론트엔드 기반 — 공유 유틸 추출 (Section B-1)

**B-1. SSE 유틸리티** — 새 파일 `sseClient.ts`
- `useStepChat.ts`에서 공통 로직 추출: URL, auth, SSE 파싱

**B-2. ChatMessage 타입 확장** — `chat.ts`
- `CitationSource`, `isStreaming`, `sources` 필드 추가

**B-3. 출처 렌더링 추출** — `renderCitationLine.tsx`, `SourcesCard.tsx`
- `StepChatPanel.tsx`에서 공유 컴포넌트 추출

**B-4. ChatContextProvider** — 새 파일
- localStorage 기반 로드맵 컨텍스트 전역 관리

### Phase 3: 프론트엔드 통합 — 시각적 변경 (Section B-2)

**B-5. useChatbot 리팩토링** — SSE + 코치 모드
**B-6. ChatBubble 업그레이드** — 출처 인용 + 스트리밍 커서
**B-7. ChatPanel 업그레이드** — 코치 헤더 + 면책 문구
**B-8. ChatMessageList 업그레이드** — 모드별 빈 상태
**B-9. GlobalChatbot + layout.tsx** — Provider 래핑

### Phase 4: 정리 (Section C)

**C-1. TimelineStepItem** — StepChatPanel → ChatContext 전환
**C-2. StepChatPanel + useStepChat 삭제**
**C-3. lint + build + 기존 테스트 통과 확인**

---

## 5. Risk Assessment

| 리스크 | 영향 | 완화 |
|--------|------|------|
| SSE 연결 끊김 | 부분 응답 유실 | heartbeat + 재연결 로직 (useStepChat 패턴 재사용) |
| 로드맵 컨텍스트 stale | 잘못된 단계 가이드 | localStorage 변경 감지 + 로드맵 detail API 재조회 |
| 기존 챗봇 사용자 경험 변화 | 혼란 | 로드맵 없으면 기존과 100% 동일 동작 보장 |
| StepChatPanel 삭제 후 누락 | 기존 기능 접근 불가 | 글로벌 챗봇에 동일 기능 완전 이식 확인 후 삭제 |
| 백엔드 테스트 깨짐 | CI 실패 | 기존 엔드포인트 변경 없이 새 엔드포인트만 추가 |

---

## 6. Success Metrics

- [ ] 기존 `POST /rag/chat` 엔드포인트 동작 유지 (하위호환)
- [ ] 새 `POST /rag/chat/stream` SSE 스트리밍 정상 동작
- [ ] 로드맵 컨텍스트 없이 일반 모드 SSE 스트리밍
- [ ] 로드맵 컨텍스트 있을 때 3레이어 프롬프트 + [법령 N] 출처
- [ ] 모든 페이지에서 코치 컨텍스트 유지
- [ ] 대화 이력 DB 저장 + 로드 (코치 모드)
- [ ] OUT_OF_SCOPE 질문 차단
- [ ] 기존 백엔드 테스트 전체 통과
- [ ] 프론트엔드 lint 0 errors + build 성공
