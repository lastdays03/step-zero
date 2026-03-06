# StepZero AI 챗봇 UX 통합 개선 계획

> **Date**: 2026-03-03
> **Status**: 설계 확정 — 구현 대기
> **Branch**: `feature/4-ai-coach-chatbot`
> **접근 방식**: 클린 재작성 — 기존 챗봇 코드 전체 제거 후 새로 구현 (DB 모델 + 핵심 도메인 로직만 재사용)

---

## 1. Executive Summary

기존 이원화된 챗봇(AI 어시스턴트 + AI 코치)을 **완전히 제거**하고, **"StepZero AI"**라는 단일 정체성의 새 챗봇을 처음부터 구축한다.

- **단일 정체성**: "StepZero AI" — 사용자는 모드를 의식하지 않음
- **모든 대화 DB 저장**: 일반/코치 구분 없이 세션 기반으로 영구 보존
- **ChatGPT식 세션 관리**: 새 대화, 히스토리 목록, 이름 변경/삭제
- **질문 의도 자동 분류**: 5카테고리 IntentClassifier — 자동으로 최적 컨텍스트 적용
- **RAG 실패 시 LLM 폴백 + 경고 배지**

### 핵심 설계 결정 요약

| # | 항목 | 결정 |
|---|------|------|
| D1 | AI 정체성 | **"StepZero AI"** 단일 이름 |
| D2 | 대화 저장 | **모든 대화 DB 저장** — 일반/코치 구분 없이 |
| D3 | 세션 관리 | **ChatGPT식** — 새 대화 버튼, 히스토리 목록, 이름 변경/삭제 |
| D4 | 컨텍스트 주입 | **질문 기반 자동 분류** (5카테고리 IntentClassifier) |
| D5 | 히스토리 UI | **패널 내 슬라이드** — "← 대화 목록" 버튼 |
| D6 | RAG 실패 | **LLM 폴백 + ⚠️ "출처 미확인" 경고 배지** |
| D7 | 로드맵 버튼 | **"AI에게 물어보기" 버튼 제거** — FAB 상시 존재 |
| D8 | 세션 제목 | **첫 질문 기반** — 첫 메시지의 처음 30자 |
| D9 | 구현 방식 | **클린 재작성** — 기존 코드 제거 후 새로 구현 |

---

## 2. 클린 재작성 전략

### 2.1 원칙

**DB는 살리고, 소스는 새로 작성한다.**

- 기존 DB 모델(Thread/Message)을 확장해서 세션 기반으로 활용
- 기존 핵심 도메인 로직(ContextBuilder, SemanticRouter, RagService)은 재사용
- 챗봇 서비스/라우터/프론트엔드 코드는 **전부 새로 작성**

### 2.2 재사용 자산 — 백엔드 도메인 로직만

| 영역 | 파일 | 이유 |
|------|------|------|
| DB 모델 | `app/models/roadmap_chat.py` | 스키마 확장해서 세션 기반 활용 |
| 레포지토리 | `app/repositories/roadmap_chat_repository.py` | DB 접근 로직 재사용 + 새 메서드 추가 |
| 프롬프트 빌더 | `roadmaps/application/context_builder.py` | 3레이어 코치 프롬프트 (잘 만든 도메인 로직) |
| 시맨틱 라우터 | `rag/application/semantic_router.py` | 임베딩 분류기 → IntentClassifier 기반으로 활용 |
| RAG 서비스 | `rag/application/rag_service.py` | 법령 벡터 검색 인프라 |

### 2.3 완전 새로 작성

#### 백엔드 — 새 `features/chat/` + `api/v1/chat/`

| 기존 파일 (제거) | 새 파일 | 설명 |
|----------------|---------|------|
| `rag/application/chat_service.py` | `chat/application/chat_service.py` | 새 통합 채팅 서비스 |
| `rag/application/unified_chat_service.py` | (위에 통합) | 별도 디스패처 불필요 |
| `rag/application/deps.py` (챗봇 관련) | `chat/application/deps.py` | 새 DI 팩토리 |
| `api/v1/rag/router.py` (챗봇 관련) | `api/v1/chat/router.py` | 새 `/chat/*` 라우터 |
| `api/v1/schemas.py` (챗봇 관련) | `chat/application/schemas.py` | 새 세션 기반 스키마 |
| `api/v1/roadmaps/chat.py` | (제거) | 글로벌 챗봇으로 완전 대체 |
| `roadmaps/application/roadmap_chat_service.py` | (로직을 새 서비스에 흡수) | 코치 스트리밍 로직 재구현 |
| (없음) | `chat/application/intent_classifier.py` | **신규** 5카테고리 분류기 |
| (없음) | `chat/application/session_service.py` | **신규** 세션 CRUD 서비스 |

#### 프론트엔드 — 100% 신규 작성 (디자인 포함)

기존 `features/chatbot/` 전체 삭제. 새 `features/chat/` 디렉토리를 **디자인부터 코드까지 완전히 새로 구축**.
기존 컴포넌트 참고 없이 새 UX 요구사항에 맞는 UI를 처음부터 설계한다.

| 새 파일 | 설명 |
|---------|------|
| `components/ChatWidget.tsx` | 메인 래퍼 (FAB + Panel 전환) |
| `components/ChatFAB.tsx` | 플로팅 액션 버튼 (새 디자인) |
| `components/ChatPanel.tsx` | 패널 (세션 관리 + 대화 + 히스토리 슬라이드) |
| `components/ChatMessages.tsx` | 메시지 리스트 (새 레이아웃) |
| `components/ChatMessage.tsx` | 개별 메시지 버블 (새 디자인) |
| `components/ChatInput.tsx` | 입력 필드 (새 디자인) |
| `components/ChatHistory.tsx` | 히스토리 목록 슬라이드 (신규) |
| `components/ChatEmptyState.tsx` | 빈 상태 + 추천 질문 (신규) |
| `components/SourcesCard.tsx` | 출처 카드 (새 디자인) |
| `components/ChatWarningBadge.tsx` | RAG 폴백 경고 (신규) |
| `hooks/useChat.ts` | 핵심 훅 — SSE + 메시지 관리 (신규) |
| `hooks/useSessions.ts` | 세션 관리 훅 (신규) |
| `providers/ChatProvider.tsx` | 통합 컨텍스트 Provider (신규) |
| `utils/sse.ts` | SSE 파싱 + auth 유틸 (신규) |
| `utils/citations.tsx` | 인용 렌더링 유틸 (신규) |
| `utils/api.ts` | 세션 API 클라이언트 (신규) |
| `types/index.ts` | 타입 정의 (신규) |
| `index.ts` | 모듈 export |

### 2.4 새 디렉토리 구조

```
app-backend/app/
├── features/
│   ├── chat/                          ← 새 feature 디렉토리
│   │   ├── application/
│   │   │   ├── __init__.py
│   │   │   ├── chat_service.py        ← 통합 채팅 서비스 (SSE 스트리밍)
│   │   │   ├── intent_classifier.py   ← 5카테고리 분류기
│   │   │   ├── session_service.py     ← 세션 CRUD 서비스
│   │   │   ├── deps.py               ← DI 팩토리
│   │   │   └── schemas.py            ← 요청/응답 스키마
│   │   └── __init__.py
│   ├── rag/                           ← 유지 (RAG 인프라)
│   │   └── application/
│   │       ├── rag_service.py         ← 유지
│   │       └── semantic_router.py     ← 유지 (IntentClassifier 기반)
│   └── roadmaps/                      ← 유지 (로드맵 도메인)
│       └── application/
│           └── context_builder.py     ← 유지 (3레이어 프롬프트)
├── api/v1/
│   ├── chat/                          ← 새 라우터 디렉토리
│   │   ├── __init__.py
│   │   └── router.py                 ← 세션 CRUD + SSE 스트리밍
│   └── rag/
│       └── router.py                 ← 챗봇 관련 엔드포인트 제거 (RAG query만 유지)

app-frontend/src/features/
├── chat/                              ← 새 feature 디렉토리
│   ├── components/
│   │   ├── ChatWidget.tsx             ← 메인 래퍼 (FAB + Panel)
│   │   ├── ChatFAB.tsx               ← 플로팅 버튼
│   │   ├── ChatPanel.tsx             ← 패널 (헤더 + 메시지 + 입력)
│   │   ├── ChatMessages.tsx          ← 메시지 리스트
│   │   ├── ChatMessage.tsx           ← 개별 메시지 버블
│   │   ├── ChatInput.tsx             ← 입력 필드
│   │   ├── ChatHistory.tsx           ← 히스토리 목록 슬라이드
│   │   ├── ChatEmptyState.tsx        ← 빈 상태 + 추천 질문
│   │   ├── SourcesCard.tsx           ← 출처 카드
│   │   └── ChatWarningBadge.tsx      ← RAG 폴백 경고
│   ├── hooks/
│   │   ├── useChat.ts                ← 핵심 훅 (SSE + 메시지 관리)
│   │   └── useSessions.ts           ← 세션 관리 훅
│   ├── providers/
│   │   └── ChatProvider.tsx          ← 통합 컨텍스트 Provider
│   ├── utils/
│   │   ├── sse.ts                    ← SSE 파싱 + auth 유틸
│   │   ├── citations.tsx             ← 인용 렌더링 유틸
│   │   └── api.ts                    ← 세션 API 클라이언트
│   ├── types/
│   │   └── index.ts                  ← 타입 정의
│   └── index.ts                      ← 모듈 export
└── chatbot/                           ← 기존 (전체 삭제 예정)
```

---

## 3. 현재 상태 vs 목표 상태

### Before (현재)

```
┌─ AI 어시스턴트 (일반) ──────┐    ┌─ AI 코치 (로드맵) ──────────┐
│ FAB 진입                    │    │ "AI에게 물어보기" 진입      │
│ 대화 이력: 휘발성            │    │ 대화 이력: DB 저장 (단계별) │
│ 개인화: 없음                │    │ 개인화: 3레이어 프롬프트    │
│ 출처: 없음                  │    │ 출처: [법령 N], [서류 N]   │
│ 별도 정체성                 │    │ 별도 정체성               │
└─────────────────────────────┘    └────────────────────────────┘
```

### After (목표)

```
┌─ StepZero AI ─────────────────────────────────────────────────┐
│ FAB 진입 (모든 페이지)                                        │
│                                                               │
│ ┌─ 세션 관리 ──────────────────────────────────┐              │
│ │ [+ 새 대화]  [☰ 대화 목록]                    │              │
│ │ 히스토리: 모든 대화 DB 저장                    │              │
│ │ 이름 변경 / 삭제 가능                         │              │
│ └───────────────────────────────────────────────┘              │
│                                                               │
│ ┌─ IntentClassifier (자동) ─────────────────────┐             │
│ │ current_step → 현재 단계 3레이어 코치 답변      │             │
│ │ other_step   → 다른 단계 3레이어 + 명시 안내    │             │
│ │ legal_general → RAG 답변 (실패 시 LLM + ⚠️)   │             │
│ │ general      → 일반 LLM 답변                   │             │
│ │ out_of_scope → "전문가 상담 권장" 차단          │             │
│ └────────────────────────────────────────────────┘             │
│                                                               │
│ 출처 인용: 모든 모드에서 조건부 표시                             │
│ 면책 문구: 항상 표시                                           │
└───────────────────────────────────────────────────────────────┘
```

---

## 4. 질문 의도 분류 체계 (IntentClassifier)

### 4.1 5가지 카테고리

| # | 카테고리 | 설명 | 컨텍스트 주입 | 응답 스타일 |
|---|---------|------|-------------|-----------|
| 1 | `current_step` | 현재 IN_PROGRESS 단계 관련 | 현재 단계 3레이어 | 코치 + 출처 인용 |
| 2 | `other_step` | 로드맵의 다른 단계 관련 | 해당 단계 3레이어 | 코치 + 출처 + "N단계 기준" |
| 3 | `legal_general` | 법률/행정 관련, 특정 단계 무관 | RAG 검색 (실패 시 LLM + ⚠️) | RAG 답변 + 출처 |
| 4 | `general` | 일반 창업/비즈니스 질문 | 없음 | 일반 LLM |
| 5 | `out_of_scope` | 전문 영역 (세금 계산, 소송 등) | 없음 | 차단 메시지 |

### 4.2 분류 우선순위 흐름

```
질문 입력
  │
  ├─ [1순위] out_of_scope 체크 (threshold: 0.75)
  │   └─ 투자/세금계산/소송/의료 → 차단
  │
  ├─ [2순위] step_related 매칭 (로드맵 보유 사용자만)
  │   ├─ 현재 단계 ActionKit 키워드 매칭 → current_step
  │   ├─ "이 단계", "지금", "현재", "체크리스트" 키워드 → current_step
  │   ├─ 다른 단계명/번호 언급 → other_step
  │   └─ 다른 단계 ActionKit 키워드 매칭 → other_step
  │
  ├─ [3순위] legal vs general (기존 SemanticRouter)
  │   ├─ legal 유사도 ≥ 0.7 → legal_general
  │   ├─ legal 키워드 폴백 → legal_general
  │   └─ 기본 → general
  │
  └─ [기본값] general
```

### 4.3 RAG 실패 처리 (legal_general)

| 실패 유형 | 처리 |
|----------|------|
| 검색 결과 0건 / 유사도 미달 | LLM 폴백 답변 + ⚠️ "출처 미확인 정보 — 정확한 내용은 전문가 확인 권장" |
| 저신뢰도 결과 (0.5~0.65) | 임계값 미달로 간주 → 위와 동일 처리 |
| 기술적 오류 (DB장애/타임아웃) | LLM 폴백 + "일시적으로 법률 DB 검색이 불가합니다" 안내 |

### 4.4 질문 예시 매핑

```
"이 단계에서 뭘 해야 돼?"           → current_step
"사업자등록 서류 어디서 발급받아?"    → current_step (현재 단계 ActionKit 매칭)
"체크리스트 중에 아직 안 한 거 뭐야?" → current_step

"2단계 영업신고는 뭐가 필요해?"     → other_step
"마지막 단계는 뭐야?"               → other_step
"영업신고 하려면 위생교육 먼저야?"   → other_step

"법인 설립 비용이 얼마야?"           → legal_general
"개인사업자 vs 법인 차이?"           → legal_general
"근로계약서 필수 기재사항?"           → legal_general

"카페 인테리어 추천해줘"             → general
"사업계획서 어떻게 써?"              → general
"초기 마케팅 전략?"                  → general

"세금 얼마나 내야 하나요?"           → out_of_scope
"소송을 진행하고 싶어요"             → out_of_scope
"투자 수익률이 어떻게 돼?"           → out_of_scope
```

---

## 5. UI/UX 설계

### 5.1 FAB (Floating Action Button)

```
모바일: ✨ 원형 버튼
데스크톱: ✨ "StepZero AI에게 물어보기"
```

### 5.2 패널 레이아웃 — 대화 화면 (기본)

```
┌─────────────────────────────────┐
│ ☰ StepZero AI     [+ 새 대화] ✕ │  ← ☰ = 히스토리 목록 전환
│  📍 사업자등록 (자동 감지됨)      │  ← 로드맵 컨텍스트 표시 (있을 때만)
├─────────────────────────────────┤
│                                 │
│  🤖 안녕하세요! 무엇이든         │
│     물어보세요.                  │
│                                 │
│  👤 영업신고 서류가 뭐야?         │
│                                 │
│  🤖 영업신고에 필요한 서류는...   │
│     [법령 1] 식품위생법에 따라... │
│     ┌──────────────────────┐    │
│     │ 📎 출처 2건           │    │
│     └──────────────────────┘    │
│                                 │
│  👤 카페 인테리어 추천해줘        │
│                                 │
│  🤖 카페 인테리어 트렌드는...     │  ← 일반 질문은 컨텍스트 없이 답변
│                                 │
├─────────────────────────────────┤
│ ⚠️ AI 생성 정보 · 정확성 미보장  │
├─────────────────────────────────┤
│ [메시지를 입력하세요...]    [▶]  │
└─────────────────────────────────┘
```

### 5.3 패널 레이아웃 — 히스토리 목록 (슬라이드)

```
┌─────────────────────────────────┐
│ ← 대화 목록               [✕]  │
├─────────────────────────────────┤
│                                 │
│ [+ 새 대화]                     │
│                                 │
│ ── 오늘 ────────────────────── │
│                                 │
│ 📝 영업신고 서류가 뭐야?         │  ← 첫 메시지 기반 제목
│    3분 전 · 4개 메시지           │
│    [⋮] ← 이름 변경 / 삭제       │
│                                 │
│ 📝 카페 인테리어 추천             │
│    1시간 전 · 6개 메시지         │
│    [⋮]                         │
│                                 │
│ ── 어제 ────────────────────── │
│                                 │
│ 📝 사업자등록 절차 문의          │
│    어제 · 8개 메시지             │
│    [⋮]                         │
│                                 │
│ ── 이전 ────────────────────── │
│                                 │
│ 📝 법인 vs 개인사업자            │
│    3일 전 · 2개 메시지           │
│    [⋮]                         │
│                                 │
└─────────────────────────────────┘
```

### 5.4 빈 상태 (새 대화)

```
┌─────────────────────────────────┐
│                                 │
│           ✨                    │
│     StepZero AI                 │
│                                 │
│  창업에 필요한 모든 것을          │
│  물어보세요                      │
│                                 │
│  💡 추천 질문:                   │
│  ┌─────────────────────────┐    │
│  │ "사업자등록 절차 알려줘"  │    │  ← 로드맵 있으면 현재 단계 관련
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │ "법인과 개인사업자 차이?" │    │
│  └─────────────────────────┘    │
│  ┌─────────────────────────┐    │
│  │ "체크리스트 진행 현황"    │    │  ← 로드맵 있으면만 표시
│  └─────────────────────────┘    │
│                                 │
└─────────────────────────────────┘
```

### 5.5 경고 배지 (RAG 실패 시)

```
🤖 법인 설립 시 필요한 서류는 일반적으로...
   (일반 LLM 지식 기반 답변)

   ┌──────────────────────────────────┐
   │ ⚠️ 출처 미확인 정보              │
   │ 정확한 내용은 전문가 확인을 권장  │
   └──────────────────────────────────┘
```

### 5.6 로드맵 타임라인 변경

```
Before:                              After:
┌─ 1단계: 사업자등록 ──┐             ┌─ 1단계: 사업자등록 ──┐
│ [체크리스트]          │             │ [체크리스트]          │
│ [AI에게 물어보기]     │  ← 제거     │ (버튼 없음 — FAB 사용) │
└──────────────────────┘             └──────────────────────┘
```

---

## 6. 데이터 모델 변경

### 6.1 기존 DB 모델 확장

기존 `roadmap_chat_threads` / `roadmap_chat_messages` 테이블을 확장한다.
테이블 이름은 유지하되, nullable 변경 + 새 필드 추가.

```sql
-- roadmap_chat_threads (기존 확장)
ALTER TABLE roadmap_chat_threads
  ALTER COLUMN roadmap_id DROP NOT NULL,    -- 일반 대화는 NULL
  ALTER COLUMN step_id DROP NOT NULL,       -- 일반 대화는 NULL
  ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE,
  DROP CONSTRAINT uq_roadmap_step_user;     -- 세션 기반으로 변경 (1:N 허용)

-- roadmap_chat_messages (기존 확장)
ALTER TABLE roadmap_chat_messages
  ADD COLUMN intent_category VARCHAR(20);   -- current_step/other_step/legal_general/general/out_of_scope
```

### 6.2 필드 활용 변경

| 필드 | 기존 용도 | 새 용도 |
|------|----------|---------|
| `threads.title` | 미사용 (항상 NULL) | **첫 메시지 30자 자동 설정** + 사용자 수정 가능 |
| `threads.roadmap_id` | 필수 (NOT NULL) | **선택** — 일반 대화는 NULL |
| `threads.step_id` | 필수 (NOT NULL) | **선택** — 일반 대화는 NULL |
| `threads.message_count` | 수동 카운터 | **유지** — 히스토리 목록 표시용 |
| `messages.token_count` | 미사용 | **유지** — 향후 비용 분석용 |
| `messages.sources_json` | 코치만 사용 | **모든 모드** — RAG 답변 시에도 저장 |

### 6.3 새 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/api/v1/chat/sessions` | 세션 목록 (페이지네이션, is_deleted=false) |
| `GET` | `/api/v1/chat/sessions/{id}/messages` | 세션 메시지 조회 |
| `POST` | `/api/v1/chat/sessions` | 새 세션 생성 (빈 세션) |
| `PATCH` | `/api/v1/chat/sessions/{id}` | 세션 제목 변경 |
| `DELETE` | `/api/v1/chat/sessions/{id}` | 세션 소프트 삭제 |
| `POST` | `/api/v1/chat/stream` | **통합 SSE 스트리밍** (핵심 엔드포인트) |

### 6.4 SSE 프로토콜

```
-- 기존 이벤트 (유지)
data: {"type":"token","token":"텍스트"}\n\n
data: {"type":"sources","sources":[...]}\n\n
data: {"type":"meta","session_id":"uuid","message_id":42}\n\n
data: {"type":"done"}\n\n
data: {"type":"error","code":"OUT_OF_SCOPE","message":"..."}\n\n
: heartbeat\n\n

-- 새 이벤트 (추가)
data: {"type":"intent","category":"current_step","step_title":"사업자등록"}\n\n
data: {"type":"warning","code":"RAG_FALLBACK","message":"출처 미확인 정보..."}\n\n
```

---

## 7. 구현 단계 (Phases)

### Phase 1: 백엔드 — 새 chat feature 구축 (Section A)

**A-1. DB 모델 확장 + 마이그레이션**
- `roadmap_chat_threads`: roadmap_id/step_id nullable, is_deleted 추가
- `roadmap_chat_messages`: intent_category 추가
- UNIQUE 제약 제거
- Alembic 마이그레이션

**A-2. IntentClassifier 구현** — `chat/application/intent_classifier.py`
- 기존 SemanticRouter를 내부적으로 활용 (직접 확장 X, 조합)
- 5카테고리 분류 로직 (우선순위 기반)
- 로드맵 ActionKit 키워드 풀 구성
- step 매칭 (current vs other) 판단

**A-3. SessionService 구현** — `chat/application/session_service.py`
- 세션 CRUD (목록, 생성, 제목 변경, 소프트 삭제)
- 메시지 조회 (페이지네이션)
- 첫 메시지 기반 자동 제목

**A-4. ChatService 구현** — `chat/application/chat_service.py`
- 통합 SSE 스트리밍 서비스
- IntentClassifier → 카테고리별 분기:
  - current_step/other_step → ContextBuilder + LLM astream
  - legal_general → RagService (실패 시 LLM 폴백 + warning)
  - general → LLM astream
  - out_of_scope → error 이벤트
- 모든 대화 DB 저장 (일반 포함)
- intent/warning SSE 이벤트 발행
- 하트비트 + AbortController

**A-5. 스키마 + DI** — `chat/application/schemas.py`, `deps.py`
- ChatStreamRequest (message, session_id)
- SessionResponse, SessionListResponse
- MessageListResponse (페이지네이션)
- DI 팩토리

**A-6. 라우터** — `api/v1/chat/router.py`
- 세션 CRUD 엔드포인트
- SSE 스트리밍 엔드포인트
- `main.py`에 라우터 등록

**A-7. 기존 챗봇 엔드포인트 정리**
- `/rag/chat`, `/rag/chat/stream` 제거 (또는 deprecated)
- `/roadmaps/{id}/steps/{sid}/chat/*` 제거 (또는 deprecated)
- 기존 테스트 정리

**A-8. 백엔드 테스트**
- 세션 CRUD 테스트
- SSE 스트리밍 테스트 (각 카테고리별)
- IntentClassifier 단위 테스트
- RAG 폴백 테스트

### Phase 2: 프론트엔드 — 새 chat feature 구축 (Section B)

**B-1. 타입 + 유틸** — `types/`, `utils/`
- ChatMessage, Session, SSEEvent 타입
- SSE 파싱 유틸 (sse.ts)
- 인용 렌더링 유틸 (citations.tsx)
- 세션 API 클라이언트 (api.ts)

**B-2. ChatProvider** — `providers/ChatProvider.tsx`
- 세션 상태 관리 (currentSession, sessions[])
- 로드맵 컨텍스트 자동 감지 (localStorage 연동)
- 패널 열기/닫기
- 세션 CRUD 액션

**B-3. useChat 훅** — `hooks/useChat.ts`
- SSE 스트리밍 + 메시지 관리
- 세션 전환 시 메시지 로드
- intent/warning 이벤트 처리
- 토큰 갱신 + 재시도

**B-4. useSessions 훅** — `hooks/useSessions.ts`
- 세션 목록 조회 (페이지네이션)
- 세션 생성/이름 변경/삭제
- 날짜별 그룹핑

**B-5. 컴포넌트 구현**
- ChatWidget — 메인 래퍼 (FAB + Panel)
- ChatFAB — 플로팅 버튼
- ChatPanel — 패널 (헤더 + 슬라이드 전환)
- ChatMessages — 메시지 리스트
- ChatMessage — 개별 버블
- ChatInput — 입력 필드
- ChatHistory — 히스토리 목록
- ChatEmptyState — 빈 상태 + 추천 질문
- SourcesCard — 출처 카드
- ChatWarningBadge — RAG 폴백 경고

**B-6. layout.tsx 연동**
- `<ChatProvider>` 래핑
- `<ChatWidget />` 배치

### Phase 3: 정리 + 전환 (Section C)

**C-1. 기존 chatbot feature 삭제**
- `features/chatbot/` 전체 디렉토리 삭제
- `features/roadmap/components/TimelineStepItem.tsx`에서 "AI에게 물어보기" 버튼 제거
- layout.tsx에서 기존 Provider/GlobalChatbot 제거

**C-2. 기존 백엔드 코드 정리**
- `unified_chat_service.py` 삭제
- `chat_service.py` (기존 rag 내) 챗봇 관련 코드 정리
- `roadmap_chat_service.py` 삭제 (로직이 새 서비스에 흡수됨)
- 기존 챗봇 라우터/스키마 정리

**C-3. 최종 검증**
- `cd app-backend && .venv/bin/pytest -q` — 전체 통과
- `cd app-frontend && npm run lint` — 0 errors
- `cd app-frontend && npm run build` — 성공
- 수동 시나리오 테스트 (Section 8 참조)

---

## 8. 사용자 시나리오 테스트 계획

| # | 시나리오 | 기대 동작 |
|---|---------|----------|
| S1 | 로드맵 없는 사용자가 FAB 클릭 | StepZero AI 빈 상태 + 일반 추천 질문 |
| S2 | 로드맵 있는 사용자가 FAB 클릭 | StepZero AI + 📍 현재 단계 표시 + 단계 관련 추천 |
| S3 | 현재 단계 질문 | current_step 분류 → 3레이어 코치 답변 + 출처 |
| S4 | 다른 단계 질문 | other_step 분류 → 해당 단계 코치 답변 + "N단계 기준" |
| S5 | 일반 법률 질문 | legal_general → RAG 답변 + 법률 출처 |
| S6 | RAG 실패 시 | LLM 폴백 + ⚠️ 경고 배지 |
| S7 | 일반 창업 질문 | general → 일반 LLM 답변 |
| S8 | 전문 영역 질문 | out_of_scope → "전문가 상담 권장" |
| S9 | 새 대화 버튼 | 현재 대화 자동 저장 → 빈 세션 시작 |
| S10 | 히스토리에서 이전 대화 선택 | 해당 세션 메시지 로드 + 이어서 대화 |
| S11 | 세션 이름 변경 | 인라인 에디팅 → PATCH API |
| S12 | 세션 삭제 | 확인 다이얼로그 → DELETE (소프트 삭제) |
| S13 | 페이지 새로고침 후 재진입 | 마지막 세션 자동 로드 |
| S14 | 로드맵 생성 후 첫 대화 | 컨텍스트 자동 감지 → 📍 단계 표시 활성화 |

---

## 9. 리스크 평가

| 리스크 | 영향 | 완화 |
|--------|------|------|
| IntentClassifier 분류 오류 | 잘못된 컨텍스트 답변 | intent SSE 이벤트로 분류 결과 전달 → 피드백 개선 |
| 세션 무한 증가 | 성능 저하 | 페이지네이션 (최근 50개) + 30일 자동 정리 |
| DB 마이그레이션 | 기존 데이터 영향 | nullable 변경만 → 기존 데이터 호환 |
| 클린 재작성 범위 | 구현 시간 증가 | Phase별 독립 완성 → 점진 전환 |
| 기존 엔드포인트 호환 | 외부 연동 깨짐 | Phase 3까지 기존 엔드포인트 유지 후 최종 제거 |
| 패널 공간 제한 | 히스토리 UI 난잡 | 슬라이드 전환으로 공간 재활용 |

---

## 10. 기술 스택

기존 스택 그대로 활용. 새 라이브러리 추가 없음.

- 백엔드: FastAPI + SQLModel + OpenAI + pgvector
- 프론트엔드: Next.js + React + Tailwind + shadcn/ui
- 스트리밍: SSE (프로토콜 확장)
- 인증: JWT (기존 패턴)
