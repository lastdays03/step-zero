# StepZero AI 챗봇 클린 재작성 — 구현 계획

> **Last Updated**: 2026-03-03
> **Status**: 구현 대기
> **Branch**: `feature/4-ai-coach-chatbot`
> **설계 문서**: `dev/active/unified-chatbot-integration/chatbot-ux-improvement-plan.md`

---

## 1. Executive Summary

기존 이원화된 챗봇(AI 어시스턴트 + AI 코치)을 **완전히 제거**하고, **"StepZero AI"** 단일 정체성의 새 챗봇을 **클린 재작성** 방식으로 구축한다.

- DB 모델(Thread/Message)을 확장 재사용하고, 핵심 도메인 로직(ContextBuilder, SemanticRouter, RagService)을 조합
- 챗봇 서비스·라우터·프론트엔드는 **100% 신규 작성** (디자인 포함)
- 3개 Phase로 구분: BE 신규 → FE 신규 → 레거시 정리

### 핵심 신규 기능

| 기능 | 설명 |
|------|------|
| IntentClassifier | 5카테고리 자동 분류 (current_step / other_step / legal_general / general / out_of_scope) |
| 세션 관리 | ChatGPT식 — 새 대화, 히스토리, 이름 변경/삭제 |
| 모든 대화 DB 저장 | 일반 질문도 세션으로 영구 보존 |
| RAG 폴백 + 경고 | RAG 실패 시 LLM 답변 + "출처 미확인" 경고 배지 |
| 단일 SSE 스트리밍 | `/api/v1/chat/stream` 하나로 모든 모드 통합 |

---

## 2. Current State Analysis

### 2.1 기존 아키텍처 문제점

| 문제 | 현상 | 영향 |
|------|------|------|
| 이원화된 정체성 | "AI 어시스턴트" vs "AI 코치" 별도 UI/진입점 | 사용자 혼란 — "어디서 물어봐야 하지?" |
| 일반 대화 소실 | 일반 모드 대화는 새로고침 시 사라짐 | "아까 물어본 거 어디 갔지?" |
| 맥락 오염 | 코치 모드에서 일반 질문 시 단계 프롬프트에 끌려감 | 부정확한 답변 |
| 이력 접근 불가 | 단계 전환 시 이전 대화 접근 경로 없음 | 1단계 대화를 다시 보려면 타임라인 탐색 필요 |
| 코드 중복 | SSE 로직이 2곳(useChatbot, useStepChat)에 분산 | 유지보수 부담 |

### 2.2 기존 코드 규모

| 영역 | 파일 수 | 총 라인 | 비고 |
|------|---------|---------|------|
| BE 챗봇 서비스 | 4 | ~600 | chat_service, unified_chat, roadmap_chat, deps |
| BE 라우터/스키마 | 3 | ~450 | rag/router, roadmaps/chat, schemas |
| FE chatbot feature | 12+ | ~1200 | hooks, providers, components, utils, types |
| 합계 | ~19 | ~2250 | 전부 교체 대상 |

### 2.3 재사용 자산

| 자산 | 파일 (라인) | 재사용 방식 |
|------|------------|-----------|
| DB 모델 | `models/roadmap_chat.py` (62) | 스키마 확장 (nullable, is_deleted, intent_category) |
| 레포지토리 | `repositories/roadmap_chat_repository.py` (143) | 기존 메서드 재사용 + 새 메서드 추가 |
| 프롬프트 빌더 | `roadmaps/application/context_builder.py` (401) | 그대로 재사용 (`build()` 호출) |
| 시맨틱 라우터 | `rag/application/semantic_router.py` (142) | IntentClassifier 내부에서 조합 활용 |
| RAG 서비스 | `rag/application/rag_service.py` (123) | `query()` 메서드 직접 호출 |

---

## 3. Proposed Future State

### 3.1 새 아키텍처

```
사용자 → ChatFAB (모든 페이지)
         │
         └─ ChatPanel (세션 기반)
             │
             ├─ ChatHistory (슬라이드 전환)
             │   └─ GET /api/v1/chat/sessions
             │
             └─ POST /api/v1/chat/stream
                 │
                 ├─ IntentClassifier.classify(query, roadmap_steps)
                 │   ├─ out_of_scope → SSE error 이벤트
                 │   ├─ current_step → ContextBuilder.build() + LLM astream
                 │   ├─ other_step  → ContextBuilder.build(해당단계) + LLM astream
                 │   ├─ legal_general → RagService.query() (실패→LLM+warning)
                 │   └─ general → LLM astream
                 │
                 └─ 모든 대화 DB 저장 (SessionService)
```

### 3.2 새 엔드포인트 체계

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `POST` | `/api/v1/chat/stream` | 통합 SSE 스트리밍 (핵심) |
| `GET` | `/api/v1/chat/sessions` | 세션 목록 (페이지네이션) |
| `GET` | `/api/v1/chat/sessions/{id}/messages` | 세션 메시지 조회 |
| `POST` | `/api/v1/chat/sessions` | 새 세션 생성 |
| `PATCH` | `/api/v1/chat/sessions/{id}` | 세션 제목 변경 |
| `DELETE` | `/api/v1/chat/sessions/{id}` | 세션 소프트 삭제 |

### 3.3 SSE 프로토콜

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

### 3.4 새 디렉토리 구조

```
app-backend/app/
├── features/chat/                     ← 새 feature
│   ├── application/
│   │   ├── __init__.py
│   │   ├── chat_service.py            ← 통합 SSE 스트리밍
│   │   ├── intent_classifier.py       ← 5카테고리 분류기
│   │   ├── session_service.py         ← 세션 CRUD
│   │   ├── deps.py                    ← DI 팩토리
│   │   └── schemas.py                 ← 요청/응답 스키마
│   └── __init__.py
├── api/v1/chat/                       ← 새 라우터
│   ├── __init__.py
│   └── router.py

app-frontend/src/features/chat/        ← 새 feature (100% 신규)
├── components/
│   ├── ChatWidget.tsx
│   ├── ChatFAB.tsx
│   ├── ChatPanel.tsx
│   ├── ChatMessages.tsx
│   ├── ChatMessage.tsx
│   ├── ChatInput.tsx
│   ├── ChatHistory.tsx
│   ├── ChatEmptyState.tsx
│   ├── SourcesCard.tsx
│   └── ChatWarningBadge.tsx
├── hooks/
│   ├── useChat.ts
│   └── useSessions.ts
├── providers/
│   └── ChatProvider.tsx
├── utils/
│   ├── sse.ts
│   ├── citations.tsx
│   └── api.ts
├── types/
│   └── index.ts
└── index.ts
```

---

## 4. Implementation Phases

### Phase 1: 백엔드 — 새 chat feature 구축 (Section A)

**목표**: 새 `/api/v1/chat/*` 엔드포인트가 독립적으로 동작. 기존 엔드포인트와 병행.

| ID | 태스크 | 크기 | 의존성 | 수용 기준 |
|----|--------|------|--------|----------|
| A-1 | DB 모델 확장 + Alembic 마이그레이션 | M | 없음 | roadmap_id/step_id nullable, is_deleted, intent_category 추가. `alembic check` diff 0 |
| A-2 | IntentClassifier 구현 | L | 없음 | 5카테고리 분류, SemanticRouter 조합, ActionKit 키워드 풀 매칭 |
| A-3 | SessionService 구현 | M | A-1 | 세션 CRUD + 페이지네이션 + 자동 제목 (첫 메시지 30자) |
| A-4 | ChatService 구현 (SSE 스트리밍) | XL | A-1, A-2 | 카테고리별 분기, DB 저장, intent/warning 이벤트, 하트비트 |
| A-5 | 스키마 + DI 팩토리 | S | A-2, A-3, A-4 | ChatStreamRequest, SessionResponse 등 + DI 함수 |
| A-6 | 라우터 + main.py 등록 | M | A-3, A-4, A-5 | 6개 엔드포인트 동작, 인증/팀 검증 포함 |
| A-7 | 백엔드 테스트 | L | A-6 | 세션 CRUD, SSE 스트리밍(5카테고리), IntentClassifier, RAG 폴백 테스트 전체 통과 |

### Phase 2: 프론트엔드 — 새 chat feature 구축 (Section B)

**목표**: 새 `features/chat/` 디렉토리가 독립적으로 동작. 기존 `features/chatbot/`과 병행.

| ID | 태스크 | 크기 | 의존성 | 수용 기준 |
|----|--------|------|--------|----------|
| B-1 | 타입 정의 + SSE 유틸 + API 클라이언트 | M | A-6 (BE API 완성) | ChatMessage, Session, SSEEvent 타입. parseSSE, auth 헤더, 세션 API 함수 |
| B-2 | ChatProvider 구현 | L | B-1 | 세션 상태, 로드맵 컨텍스트 자동 감지, 패널 열기/닫기, 세션 CRUD 액션 |
| B-3 | useChat 훅 구현 | XL | B-1, B-2 | SSE 스트리밍, 메시지 관리, intent/warning 처리, 토큰 갱신, AbortController |
| B-4 | useSessions 훅 구현 | M | B-1, B-2 | 세션 목록 조회, 생성/이름 변경/삭제, 날짜별 그룹핑 |
| B-5 | UI 컴포넌트 — 코어 | XL | B-2, B-3 | ChatWidget, ChatFAB, ChatPanel, ChatMessages, ChatMessage, ChatInput (새 디자인) |
| B-6 | UI 컴포넌트 — 부가 | L | B-3, B-4 | ChatHistory, ChatEmptyState, SourcesCard, ChatWarningBadge (새 디자인) |
| B-7 | layout.tsx 연동 + 인용 유틸 | S | B-5, B-6 | ChatProvider 래핑, ChatWidget 배치, citations 렌더링 |
| B-8 | FE 검증 | M | B-7 | `npm run lint` 0 errors, `npm run build` 성공 |

### Phase 3: 정리 + 전환 (Section C)

**목표**: 기존 챗봇 코드 완전 제거. 새 chat feature만 유지.

| ID | 태스크 | 크기 | 의존성 | 수용 기준 |
|----|--------|------|--------|----------|
| C-1 | FE 기존 chatbot feature 삭제 | M | B-8 | `features/chatbot/` 전체 삭제, layout.tsx 기존 import 제거, 프로젝트 전체에서 `chatbot` import 0건 |
| C-2 | FE TimelineStepItem 정리 | S | C-1 | "AI에게 물어보기" 버튼 + `useChatContext` 제거 |
| C-3 | BE 기존 챗봇 코드 정리 | M | A-7 | unified_chat_service, roadmap_chat_service 삭제. rag/router에서 /chat, /chat/stream 제거. roadmaps/chat.py 삭제 |
| C-4 | BE 기존 테스트 정리 | S | C-3 | 삭제된 엔드포인트 관련 테스트 제거 또는 수정 |
| C-5 | 최종 통합 검증 | L | C-1~C-4 | pytest 전체 통과, lint 0, build 성공, 14개 시나리오 수동 테스트 |

---

## 5. Risk Assessment

| 리스크 | 확률 | 영향 | 완화 전략 |
|--------|------|------|----------|
| IntentClassifier 분류 정확도 미달 | 중 | 높음 | SSE intent 이벤트로 분류 결과 투명하게 전달. 키워드 폴백 + 임계값 조정 가능. 향후 사용자 피드백 루프 |
| DB 마이그레이션 기존 데이터 손상 | 낮음 | 높음 | nullable 변경만 수행 → 기존 데이터 호환. 마이그레이션 전 DB 백업 |
| Phase 1-2 병행 기간 동안 코드 충돌 | 중 | 중 | 새 feature는 별도 디렉토리(`chat/`)에 구축 → 기존 코드와 물리적 분리 |
| SSE 연결 안정성 | 중 | 중 | 하트비트(15초) + 재연결 로직 + AbortController |
| 패널 공간 내 히스토리 UI 복잡도 | 낮음 | 중 | 슬라이드 전환으로 대화/히스토리 뷰 분리 |
| 세션 데이터 무한 증가 | 낮음 | 중 | 페이지네이션(50개) + 소프트 삭제 + 향후 30일 자동 정리 |
| 클린 재작성 범위로 인한 일정 초과 | 중 | 중 | Phase별 독립 완성 → Phase 1 완료 시점에 BE 단독으로도 유효 |

---

## 6. Success Metrics

### 6.1 기능 완성도

- [ ] 6개 API 엔드포인트 정상 동작
- [ ] 5카테고리 IntentClassifier 분류 정확 (예시 매핑 기준)
- [ ] 모든 대화 DB 저장 + 재방문 시 복원
- [ ] 세션 CRUD (생성, 목록, 이름 변경, 삭제)
- [ ] SSE 스트리밍 (token, sources, meta, intent, warning, done, error)
- [ ] RAG 실패 시 LLM 폴백 + 경고 배지
- [ ] 로드맵 컨텍스트 자동 감지 (localStorage 연동)

### 6.2 코드 품질

- [ ] `cd app-backend && .venv/bin/pytest -q` — 전체 통과 (0 failed)
- [ ] `cd app-frontend && npm run lint` — 0 errors
- [ ] `cd app-frontend && npm run build` — 성공
- [ ] 기존 `features/chatbot/` 디렉토리 완전 삭제
- [ ] 프로젝트 전체에서 `chatbot` import 0건

### 6.3 UX 시나리오 (14개)

| # | 시나리오 | 기대 동작 |
|---|---------|----------|
| S1 | 로드맵 없는 사용자 FAB 클릭 | 빈 상태 + 일반 추천 질문 |
| S2 | 로드맵 있는 사용자 FAB 클릭 | 📍 현재 단계 + 단계 관련 추천 |
| S3 | 현재 단계 질문 | current_step → 코치 + 출처 |
| S4 | 다른 단계 질문 | other_step → "N단계 기준" |
| S5 | 일반 법률 질문 | legal_general → RAG + 출처 |
| S6 | RAG 실패 | LLM 폴백 + ⚠️ 경고 |
| S7 | 일반 창업 질문 | general → LLM 답변 |
| S8 | 전문 영역 질문 | out_of_scope → 차단 |
| S9 | 새 대화 | 자동 저장 → 빈 세션 |
| S10 | 히스토리 선택 | 세션 메시지 로드 |
| S11 | 세션 이름 변경 | PATCH API |
| S12 | 세션 삭제 | 소프트 삭제 |
| S13 | 새로고침 | 마지막 세션 자동 로드 |
| S14 | 로드맵 생성 후 | 컨텍스트 자동 활성화 |

---

## 7. Required Resources & Dependencies

### 7.1 외부 의존성

| 서비스 | 용도 | 필수 |
|--------|------|------|
| OpenAI API (`OPENAI_API_KEY`) | LLM 스트리밍 + 임베딩 | 필수 |
| PostgreSQL 16 + pgvector | DB + 벡터 검색 | 필수 |
| Redis | 직접 사용 안 함 (워커 전용) | 불필요 |

### 7.2 내부 의존성

| 의존 대상 | 어떤 모듈에서 | 용도 |
|----------|-------------|------|
| `RoadmapContextBuilder` | 새 ChatService | 코치 모드 3레이어 프롬프트 |
| `SemanticRouter` | 새 IntentClassifier | 임베딩 유사도 분류 |
| `RagService` | 새 ChatService | legal_general 법령 검색 |
| `RoadmapChatRepository` | 새 SessionService | 스레드/메시지 CRUD |
| `RoadmapRepository` | 새 ChatService | 로드맵/단계 조회 (소유권 검증) |

### 7.3 기존 인프라 (변경 없음)

- JWT 인증 (`get_current_user`, `get_current_team`)
- API 클라이언트 (Axios + 토큰 인터셉터)
- Tailwind CSS 3.3 + shadcn/ui
