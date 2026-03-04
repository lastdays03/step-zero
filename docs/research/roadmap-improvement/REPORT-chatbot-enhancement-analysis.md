# AI 코치 챗봇 개선 — 현재 시스템 분석 및 계획 검증 리포트

> 작성일: 2026-03-01 (링크 오류 분석 추가: 2026-03-01)
> 목적: 마스터 플랜(REPORT-01-master-plan.md) Section 3 "AI 코치 대화 MVP"의 실현 가능성을 현재 코드베이스 기준으로 정밀 검증 + 법적근거/필수서류 링크 오류 근본 원인 분석
> 방법: 백엔드 RAG/Chat, 프론트엔드 ChatBot, 데이터 모델, LLM 파이프라인, 링크 생성/렌더링 흐름 총 7개 영역 병렬 코드 분석

---

## 1. 현재 시스템 현황 (AS-IS)

### 1.1 백엔드 채팅 아키텍처

```
app-backend/app/features/rag/
├── application/
│   ├── deps.py              # 싱글톤 DI (lru_cache)
│   ├── chat_service.py      # 하이브리드 채팅 (legal/general 분기)
│   ├── rag_service.py       # PGVector RAG 파이프라인
│   └── semantic_router.py   # 임베딩 기반 쿼리 분류
└── domain/
    └── __init__.py          # 비어있음 (DB 모델 없음)
```

**핵심 발견:**

| 항목 | 현재 상태 | 마스터 플랜 요구 |
|------|----------|----------------|
| API 엔드포인트 | `POST /rag/chat` (JSON 응답) | `POST /roadmaps/{id}/steps/{id}/chat/stream` (SSE) |
| 응답 방식 | **일괄 응답** (chain.invoke → 전체 텍스트 대기) | **SSE 스트리밍** (token 단위 전송) |
| 인증 | **없음** (public API) | JWT 필수 (`get_current_user`) |
| 대화 이력 | **없음** (stateless, DB 모델 자체가 없음) | `RoadmapChatThread` + `RoadmapChatMessage` 테이블 |
| 컨텍스트 | RAG 검색 문서 5개만 | 3레이어 (불변 팩트 + 실행 상태 + 안내 규칙) |
| 쿼리 분류 | 2카테고리 (legal/general) | + OUT_OF_SCOPE 카테고리 필요 |
| LLM 모델 | `gpt-4o-mini` | 동일 (재활용 가능) |
| 안전장치 | RAG 프롬프트 5개 규칙만 | 4가지 구조적 안전장치 |

### 1.2 프론트엔드 채팅 아키텍처

```
app-frontend/src/features/chatbot/
├── components/
│   ├── GlobalChatbot.tsx     # 최상위 진입점 (FAB 토글)
│   ├── ChatPanel.tsx         # 패널 컨테이너 (400×600px)
│   ├── ChatMessageList.tsx   # 메시지 목록 + 스크롤
│   ├── ChatBubble.tsx        # 개별 메시지 (User/Assistant)
│   ├── ChatInput.tsx         # textarea + 엔터 전송
│   └── ChatFAB.tsx           # 플로팅 액션 버튼
├── hooks/
│   └── useChatbot.ts         # 상태 + API 호출
├── types/
│   └── chat.ts               # ChatMessage 인터페이스
└── utils/
    └── renderAnswerLine.tsx   # URL 자동 링크화
```

**핵심 발견:**

| 항목 | 현재 상태 | 마스터 플랜 요구 |
|------|----------|----------------|
| 채팅 위치 | **글로벌 FAB** (모든 페이지) | **단계별 슬라이드아웃 패널** (TimelineStepItem 내) |
| 스트리밍 표시 | **없음** (로딩 → 전체 텍스트) | SSE 토큰 단위 실시간 렌더링 |
| 출처 표시 | `"법률 RAG"` / `"일반 AI"` 배지만 | `[출처 N]` 인라인 인용 + 출처 카드 |
| 면책 문구 | **없음** | FE 하단 고정 렌더링 (AI 기본법 준수) |
| 컨텍스트 인식 | 없음 (어떤 단계인지 모름) | 현재 단계/로드맵 정보 주입 |
| 대화 기록 | 메모리만 (새로고침 시 소멸) | 서버 저장 + 이전 대화 로드 |

### 1.3 데이터 모델 — AI 코치 컨텍스트 빌더 필요 데이터

**Roadmap → Step → StepDetail → StepAction** 체인이 이미 완성되어 있음:

```
Roadmap (UUID)
├── business_type, location, startup_type, open_timeline, budget_range  ← LAYER 1 팩트
├── RoadmapStep (int)
│   ├── step_order, title, status                                      ← LAYER 2 실행 상태
│   ├── RoadmapStepDetail (1:1)
│   │   ├── phase, objective, estimated_days, risk_notes               ← LAYER 1 + 2
│   │   └── mapping_source, source_count, has_fallback                 ← 출처 추적
│   └── RoadmapStepAction[] (1:N)
│       ├── action_type: CHECKLIST | LEGAL_BASIS | DOCUMENT            ← LAYER 1 팩트
│       ├── title, description, source_url                             ← LAYER 1 팩트
│       └── metadata_json:
│           ├── actionkit_item_id                                      ← ActionKit 역추적 키
│           ├── actionkit_domain, actionkit_category                   ← 분류 정보
│           ├── actionkit_file_id, actionkit_highlight_id              ← 세부 참조
│           └── mapping_source                                         ← 출처 추적
```

**ActionKit 원본 데이터 접근 경로:**
```
metadata_json.actionkit_item_id → ActionKitItem
  ├── .name (법령명), .summary (요약)
  ├── .highlights[] → 체크리스트 항목
  ├── .related_laws[] → 관련 법령명 + 요약
  ├── .files[] → 서류 파일 (object_key, original_filename)
  └── .checklists[] → 체크리스트 (v8 추가)
```

**평가**: 마스터 플랜 LAYER 1(불변 팩트)에 필요한 모든 데이터가 이미 DB에 존재.
`RoadmapContextBuilder`는 기존 `RoadmapRepository` + `ActionKitRepository` 메서드를 조합하면 구현 가능.

### 1.4 LLM/프롬프트 파이프라인

**현재 LLM 인스턴스 생성 위치 (4곳):**

| 위치 | 모델 | 용도 | 재활용 가능성 |
|------|------|------|-------------|
| `rag_service.py` | gpt-4o-mini, timeout=20 | RAG 답변 생성 | **높음** — streaming=True 추가만 |
| `chat_service.py` | gpt-4o-mini, timeout=20 | 일반 대화 | **높음** — 동일 패턴 |
| `llm_personalizer.py` | gpt-4o-mini, timeout=30 | 로드맵 개인화 | 참고용 (프롬프트 구조) |
| `law_etl.py` | gpt-4-turbo-preview, temp=0 | 법령 ETL | 미관련 |

**현재 프롬프트 설계 패턴 (재활용 가능):**
- "절대 규칙" 섹션으로 행동 범위 제한
- `[컨텍스트]` / `[질문]` / `[답변]` 구분 마커
- JSON 출력 강제 시 예시 포함
- ActionKit 데이터 수정 금지 규칙 (LLMPersonalizer에서 검증됨)

---

## 2. 마스터 플랜 vs 현실 — GAP 분석

### 2.1 재활용률 검증 (마스터 플랜 주장 vs 실제)

| 기존 코드 | 마스터 플랜 재활용률 | **실제 평가** | 근거 |
|----------|:------------------:|:-----------:|------|
| `ChatOpenAI` 인스턴스 | 100% | **90%** | `streaming=True` 추가 + `ainvoke` → `astream` 변경 필요. 거의 동일하나 호출 패턴이 다름 |
| `SemanticRouter` | 90% | **70%** | 현재 2카테고리(legal/general)만 존재. OUT_OF_SCOPE 앵커 + threshold 재조정 + 로드맵 컨텍스트 내 분류 로직 추가 필요 |
| `PGVector` 벡터스토어 | 80% | **50%** | 현재 `law_vectors` 컬렉션은 법령 전체 검색용. AI 코치는 특정 단계의 ActionKit 아이템 기반이므로 벡터 검색보다 **관계형 조회가 주력**. PGVector 재활용은 보충적 |
| `format_docs_with_metadata()` | 90% | **60%** | 현재 함수는 RAG 문서 포맷팅용. AI 코치는 ActionKit 아이템 + 법령 + 체크리스트를 LAYER별로 구조화해야 함. 포맷 구조가 근본적으로 다름 |
| 인증/DB 세션 미들웨어 | 100% | **100%** | `get_current_user`, `get_session` 그대로 사용 가능 |
| `ChatPanel`/UI 컴포넌트 | 80% | **40%** | 글로벌 FAB 채팅 → 단계별 슬라이드아웃 패널로 구조 변경. SSE 스트리밍 처리, 출처 인용 파싱, 면책 문구 등 새 기능이 상당. 컴포넌트 구조(ChatBubble, ChatInput)는 참고 가능하나 대부분 재작성 |

**종합 재활용률 평가:**
- 마스터 플랜 주장: **~80%**
- **실제 평가: ~55-60%** (보수적 분석 A의 시각에 더 가까움)
- 핵심 차이: "동일 패턴 재활용"과 "동일 코드 재활용"은 다름. 패턴은 재활용 가능하나 구현은 상당 부분 신규

### 2.2 신규 구현 필요 항목 상세

#### BE 신규 (예상 공수 포함)

| # | 항목 | 복잡도 | 예상 공수 | 의존성 |
|---|------|:------:|:--------:|--------|
| 1 | `RoadmapChatThread` + `RoadmapChatMessage` DB 모델 | 낮음 | 1일 | Alembic 마이그레이션 |
| 2 | Alembic 마이그레이션 (테이블 2개 + 인덱스) | 낮음 | 0.5일 | #1 |
| 3 | `RoadmapContextBuilder` (3레이어 직렬화) | **높음** | 3일 | RoadmapRepository + ActionKitRepository |
| 4 | `RoadmapChatService` (SSE 스트리밍 + 대화 이력) | **높음** | 4일 | #1, #3, ChatOpenAI |
| 5 | SSE 라우터 (`/roadmaps/{id}/steps/{id}/chat/stream`) | 중간 | 2일 | #4, FastAPI StreamingResponse |
| 6 | SemanticRouter 확장 (OUT_OF_SCOPE 앵커) | 낮음 | 1일 | 기존 SemanticRouter |
| 7 | 4가지 안전장치 시스템 프롬프트 설계 | **높음** | 3일 | #3 |
| 8 | 응답 내 출처 파싱 로직 | 중간 | 1일 | #4 |
| | **BE 합계** | | **~15.5일 (약 3주)** | |

#### FE 신규

| # | 항목 | 복잡도 | 예상 공수 | 의존성 |
|---|------|:------:|:--------:|--------|
| 1 | `useStepChat` hook (SSE EventSource + 상태 관리) | **높음** | 3일 | BE SSE 엔드포인트 |
| 2 | `StepChatPanel` (슬라이드아웃 패널) | 중간 | 2일 | #1 |
| 3 | SSE 토큰 스트리밍 렌더링 | 중간 | 2일 | #1 |
| 4 | 출처 인용 파싱 + 출처 카드 UI | 중간 | 1.5일 | #3 |
| 5 | "AI에게 물어보기" 버튼 (`TimelineStepItem` 통합) | 낮음 | 1일 | #2 |
| 6 | 면책 문구 고정 렌더링 | 낮음 | 0.5일 | — |
| 7 | 모바일 풀스크린 대응 | 낮음 | 1일 | #2 |
| | **FE 합계** | | **~11일 (약 2주)** | |

**총 예상**: BE 3주 + FE 2주 (병렬 시 ~3주, 직렬 시 ~5주)

### 2.3 마스터 플랜 일정 평가

| 마스터 플랜 일정 | 낙관적 평가 | 보수적 평가 | 판단 |
|:-------------:|:--------:|:--------:|:----:|
| BE 10일 (Week 4-5) | 가능하지만 빡빡 | 15일 필요 | **약간 낙관적** |
| FE 5일 (Week 6) | 가능하지만 빡빡 | 11일 필요 | **상당히 낙관적** |
| 총 2-3주 | 최소 3주 | 4-5주 | **2주 버퍼 필요** |

---

## 3. 컴포넌트별 상세 구현 분석

### 3.1 RoadmapContextBuilder (핵심 신규 컴포넌트)

마스터 플랜의 3레이어 구조를 현재 데이터 모델로 매핑:

```python
# 구현 계획

class RoadmapContextBuilder:
    """3레이어 시스템 프롬프트 컨텍스트 빌더"""

    async def build(
        self,
        roadmap: Roadmap,
        step: RoadmapStep,
        step_detail: RoadmapStepDetail,
        actions: list[RoadmapStepAction],
        recent_messages: list[RoadmapChatMessage],  # 최근 5개
    ) -> str:
        layer1 = self._build_fact_layer(roadmap, step, step_detail, actions)
        layer2 = self._build_state_layer(step, step_detail, actions)
        layer3 = self._build_instruction_layer(recent_messages)
        return f"{layer1}\n\n{layer2}\n\n{layer3}"
```

**LAYER 1 데이터 소스 매핑:**

| 마스터 플랜 요구 | 데이터 소스 | 접근 방법 |
|:---------------:|-----------|----------|
| 업종, 지역, 창업형태, 오픈시기, 예산 | `Roadmap` 테이블 | `roadmap.business_type`, `.location`, `.startup_type`, `.open_timeline`, `.budget_range` |
| 현재 단계 제목, 위상, 목표 | `RoadmapStep` + `RoadmapStepDetail` | `step.title`, `detail.phase`, `detail.objective` |
| LEGAL_BASIS 액션 (법령명 + ActionKit ID + source_url) | `RoadmapStepAction` where `action_type='LEGAL_BASIS'` | `action.title`, `action.metadata_json['actionkit_item_id']`, `action.source_url` |
| DOCUMENT 액션 (서류명 + source_url) | `RoadmapStepAction` where `action_type='DOCUMENT'` | `action.title`, `action.source_url` |

**LAYER 2 데이터 소스 매핑:**

| 마스터 플랜 요구 | 데이터 소스 |
|:---------------:|-----------|
| 완료/미완료 CHECKLIST 목록 | `RoadmapStepAction` where `action_type='CHECKLIST'` + `metadata_json.completed` |
| estimated_days | `RoadmapStepDetail.estimated_days` |
| step status | `RoadmapStep.status` |
| risk_notes | `RoadmapStepDetail.risk_notes` (JSON 배열) |

**LAYER 3 구현:**

| 요구 | 구현 방법 |
|------|----------|
| 이전 대화 요약 (최근 5개) | `RoadmapChatMessage` 테이블에서 `thread_id` + `ORDER BY created_at DESC LIMIT 5` |
| 4가지 안전장치 규칙 | 정적 텍스트 (시스템 프롬프트에 하드코딩) |
| 응답 포맷 규칙 | 정적 텍스트 |

**토큰 예산 검증:**

현재 데이터 구조로 시뮬레이션:
```
LAYER 1 (팩트):
- 사용자 입력 5필드: ~50토큰
- 단계 정보 (title + phase + objective): ~80토큰
- LEGAL_BASIS 액션 3개: ~150토큰
- DOCUMENT 액션 2개: ~60토큰
소계: ~340토큰

LAYER 2 (실행 상태):
- CHECKLIST 10개 (완료/미완료): ~200토큰
- estimated_days + status + risk_notes: ~80토큰
소계: ~280토큰

LAYER 3 (안내):
- 최근 5개 메시지 요약: ~200토큰
- 안전장치 + 포맷 규칙: ~300토큰
소계: ~500토큰

총합: ~1,120토큰 (마스터 플랜 800-1,200 범위 내)
```

**평가**: 토큰 예산 현실적. 단, CHECKLIST가 많은 단계(20개+)에서는 1,200토큰 초과 가능 → 동적 트리밍 로직 필요.

### 3.2 SSE 스트리밍 엔드포인트

**현재 코드에 SSE 구현 없음**. 신규 구현 필요 항목:

```python
# 필요한 FastAPI 패턴

from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI

async def stream_chat(roadmap_id, step_id, request, user, session):
    # 1. 컨텍스트 빌드
    context = await context_builder.build(...)

    # 2. LLM 스트리밍
    llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)

    async def event_generator():
        async for chunk in llm.astream(messages):
            token = chunk.content
            yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**기술적 고려사항:**

| 항목 | 설명 | 결정 필요 |
|------|------|----------|
| LangChain `astream` | `ChatOpenAI`에서 `astream()` 메서드 사용 | LangChain 버전 호환성 확인 필요 |
| 하트비트 | 15초마다 빈 이벤트 전송 | `asyncio.create_task`로 백그라운드 |
| 타임아웃 | 30초 | `asyncio.wait_for` 래핑 |
| 연결 끊김 | `is_truncated=True`로 메시지 저장 | `try/except asyncio.CancelledError` |
| CORS | SSE에 대한 CORS 설정 | 기존 CORS 미들웨어 확인 |

### 3.3 안전장치 구현 분석

| # | 안전장치 | 현재 코드 활용 | 신규 구현 |
|---|---------|:------------:|:--------:|
| 1 | 팩트-지능 분리 | LLMPersonalizer의 "ActionKit 수정 금지" 규칙 패턴 재활용 | LAYER 1을 `<FACT>` 태그로 명시적 분리 |
| 2 | 출처 강제 인용 | `format_docs_with_metadata`의 `[출처 N]` 패턴 | 시스템 프롬프트에 "반드시 [출처 N] 형식 인용" 규칙 추가 |
| 3 | 범위 외 거부 | SemanticRouter의 분류 로직 | OUT_OF_SCOPE 앵커 추가 (세금, 소송, 의료, 투자 키워드) |
| 4 | 면책 고정 문구 | **없음** | FE에서 하단 고정 텍스트 렌더링 |

**안전장치 #3 세부 설계:**

현재 SemanticRouter anchors:
```python
# 현재: 2카테고리
"legal": [8개 앵커], "general": [4개 앵커]

# 확장 필요: 3카테고리
"in_scope": [로드맵 단계 관련 질문 앵커],
"out_of_scope": [
    "세금 절감 방법", "소송 절차", "의료 보험 청구",
    "주식 투자", "부동산 투자", "이혼 절차",
    "형사 사건", "의료 과실", ...
],
"general": [일상 대화 앵커]
```

### 3.4 프론트엔드 SSE 처리

**현재 코드에 EventSource 사용 없음.** 신규 구현:

```typescript
// useStepChat hook 핵심 구조

function useStepChat(roadmapId: string, stepId: number) {
  const [messages, setMessages] = useState<StepChatMessage[]>([])
  const [streamingText, setStreamingText] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)

  const sendMessage = async (content: string) => {
    // 1. user 메시지 추가
    // 2. EventSource 또는 fetch + ReadableStream 연결
    // 3. SSE 이벤트 파싱:
    //    - token → streamingText에 append
    //    - sources → 출처 카드 렌더링
    //    - done → assistant 메시지 확정 + streamingText 리셋
  }
}
```

**SSE 클라이언트 선택지:**

| 방식 | 장점 | 단점 | 추천 |
|------|------|------|:----:|
| `EventSource` API | 브라우저 네이티브, 자동 재연결 | GET만 지원, 헤더 커스텀 불가 | X |
| `fetch` + `ReadableStream` | POST 지원, 헤더 자유, JWT 전송 가능 | 수동 파싱, 재연결 로직 필요 | **O** |
| `@microsoft/fetch-event-source` | POST+헤더+자동 재연결 | 외부 의존성 | O (대안) |

**추천**: `fetch` + `ReadableStream` (외부 의존성 없이 JWT 헤더 전송 가능)

### 3.5 "AI에게 물어보기" 버튼 삽입 위치

현재 `TimelineStepItem.tsx` 구조 분석:

```
ACTIVE 상태 렌더링:
┌────────────────────────────────────────┐
│ ● [step.title]                         │  ← 헤더
│   [detail.objective]                   │  ← 목표 설명
│                                        │
│ 체크리스트:                              │
│   ☐ 체크리스트 항목 1                    │  ← CHECKLIST actions
│   ☐ 체크리스트 항목 2                    │
│                                        │
│ 서류:                                   │
│   ☐ 서류 1 (다운로드)                    │  ← DOCUMENT actions
│                                        │
│ 법적 근거:                               │
│   📖 법령명 (링크)                       │  ← LEGAL_BASIS actions
│                                        │
│ [단계 완료]                              │  ← 상태 변경 버튼
└────────────────────────────────────────┘
```

**마스터 플랜 삽입 위치**: 체크리스트 바로 아래, "단계 완료" 버튼 위

```
│ 법적 근거:                               │
│   📖 법령명 (링크)                       │
│                                        │
│   💬 AI에게 물어보기                     │  ← 여기에 삽입
│                                        │
│ [단계 완료]                              │
```

---

## 4. 기존 코드와의 관계 — 구체적 재활용/수정/신규 분류

### 4.1 완전 재활용 (수정 없이 사용)

| 코드 | 위치 | 용도 |
|------|------|------|
| `get_current_user` | `app/api/deps.py` | JWT 인증 |
| `get_current_team` | `app/api/deps.py` | 팀 컨텍스트 |
| `get_session` | `app/core/db.py` | DB 세션 |
| `RoadmapRepository.get_by_id_for_team()` | `app/repositories/roadmap_repository.py` | 로드맵 조회 |
| `RoadmapRepository.list_step_actions()` | 상동 | 액션 목록 |
| `RoadmapRepository.list_step_details()` | 상동 | 단계 상세 |
| `ActionKitRepository.get_item_with_category()` | `app/repositories/actionkit_repository.py` | ActionKit 아이템 조회 |
| `ChatMessage` 타입 | `src/features/chatbot/types/chat.ts` | 메시지 타입 참고 |

### 4.2 수정 후 재활용

| 코드 | 수정 내용 | 공수 |
|------|----------|:----:|
| `SemanticRouter` | OUT_OF_SCOPE 앵커 추가, threshold 재조정 | 1일 |
| `ChatBubble` 컴포넌트 | 출처 인용 `[출처 N]` 파싱 + 출처 카드 추가 | 1.5일 |
| `ChatInput` 컴포넌트 | 동일 구조, props 약간 변경 | 0.5일 |
| `renderAnswerLine` 유틸 | 출처 번호 파싱 추가 | 0.5일 |
| `ChatOpenAI` 인스턴스 설정 | `streaming=True` 추가 | 0.5일 |

### 4.3 신규 구현 필수

| 코드 | 위치 | 공수 |
|------|------|:----:|
| **BE: `RoadmapContextBuilder`** | `app/features/roadmaps/application/` | 3일 |
| **BE: `RoadmapChatService`** | `app/features/roadmaps/application/` | 4일 |
| **BE: SSE 라우터** | `app/api/v1/roadmaps/` | 2일 |
| **BE: DB 모델 2개** | `app/models/` | 1일 |
| **BE: Alembic 마이그레이션** | `alembic/versions/` | 0.5일 |
| **BE: 안전장치 시스템 프롬프트** | `app/features/roadmaps/application/` | 3일 |
| **FE: `useStepChat` hook** | `src/features/roadmap/hooks/` | 3일 |
| **FE: `StepChatPanel`** | `src/features/roadmap/components/` | 2일 |
| **FE: SSE 스트리밍 렌더링** | `StepChatPanel` 내부 | 2일 |
| **FE: 출처 카드 + 인용 UI** | `src/features/roadmap/components/` | 1.5일 |
| **FE: 면책 문구** | `StepChatPanel` 하단 | 0.5일 |
| **FE: TimelineStepItem 통합** | 기존 파일 수정 | 1일 |

---

## 5. 리스크 및 주의사항

### 5.1 기술적 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| **SSE + JWT 인증** | EventSource API는 커스텀 헤더 불가 → JWT 전송 문제 | `fetch` + `ReadableStream` 사용 또는 쿼리 파라미터 토큰 (보안 주의) |
| **LangChain astream 호환성** | 현재 LangChain 버전에서 `astream` 지원 여부 | `langchain-openai` 버전 확인, 필요시 OpenAI SDK 직접 사용 |
| **CORS + SSE** | SSE 응답에 대한 CORS preflight | FastAPI CORS 미들웨어에 `text/event-stream` 허용 확인 |
| **동시 연결 수** | 유저당 SSE 연결 1개 유지 → 서버 리소스 | 타임아웃 30초 + 하트비트로 관리 |
| **토큰 예산 초과** | 큰 단계(CHECKLIST 20개+)에서 컨텍스트 오버플로우 | 동적 트리밍: CHECKLIST 15개 초과 시 미완료 우선, 나머지 요약 |

### 5.2 제품 리스크

| 리스크 | 영향 | 마스터 플랜 대응 | 추가 대응 필요 |
|--------|------|:-------------:|:------------:|
| **변호사법 제109조** | AI 코치가 "법률 사무" 영역 진입 시 법적 리스크 | 법률 자문 50-150만원 | 출시 전 필수 — **일정에 반영 안됨** |
| **AI 기본법 라벨링** | 2026.01 시행, AI 생성 콘텐츠 표시 의무 | FE 하단 면책 문구 | 법무 검토로 요건 충족 확인 필요 |
| **할루시네이션** | 잘못된 법률 정보 → 사용자 피해 → 신뢰 붕괴 | 4가지 안전장치 | **출시 전 QA 시나리오 100건+ 필요** |
| **NYC MyCity 사례** | 잘못된 인허가 안내 → 사용자 실제 피해 | ActionKit 외 정보 차단 | 시스템 프롬프트 레드팀 테스트 필수 |

### 5.3 일정 리스크

| 항목 | 마스터 플랜 | 현실적 예상 | 차이 |
|------|:--------:|:--------:|:----:|
| BE 개발 | 10일 | 14-16일 | +4-6일 |
| FE 개발 | 5일 | 10-12일 | +5-7일 |
| 프롬프트 설계 + 테스트 | (BE에 포함) | 5-7일 (별도) | +5-7일 |
| QA + 안전장치 검증 | (미명시) | 3-5일 | +3-5일 |
| **총합** | **~15일 (3주)** | **~32-40일 (6-8주)** | **2배** |

**주의**: 마스터 플랜 Phase 2에 2주 버퍼 포함(부록 B 언급)이 있으나, 법률 자문 일정(4-6주)은 별도로 병행 필요.

---

## 6. 구현 순서 권장 (의존성 기반)

```
Phase 2-A: 기반 구축 (Week 1-2)
├── [1] DB 모델 + 마이그레이션 (1.5일)
├── [2] RoadmapContextBuilder (3일) ← 가장 중요, 먼저 완성
├── [3] SemanticRouter OUT_OF_SCOPE 확장 (1일)
└── [4] 안전장치 시스템 프롬프트 초안 (2일)

Phase 2-B: 백엔드 핵심 (Week 2-3)
├── [5] RoadmapChatService + SSE 스트리밍 (4일) ← #1, #2, #3 의존
└── [6] SSE 라우터 + 인증 (2일) ← #5 의존

Phase 2-C: 프론트엔드 (Week 3-4, BE와 병렬 가능 일부)
├── [7] useStepChat hook + SSE 클라이언트 (3일) ← #6 의존
├── [8] StepChatPanel + 스트리밍 렌더링 (3일) ← #7 의존
├── [9] 출처 인용 + 면책 문구 (2일) ← #8 의존
└── [10] TimelineStepItem 통합 (1일) ← #8 의존

Phase 2-D: 품질 검증 (Week 4-5)
├── [11] 안전장치 QA (3일) ← #5, #7 의존
├── [12] 프롬프트 튜닝 + A/B 시나리오 (3일)
└── [13] 통합 테스트 + 성능 (2일)
```

---

## 7. 핵심 결론

### 마스터 플랜 대비 현실 평가

| 항목 | 마스터 플랜 주장 | 실제 평가 |
|------|:------------:|:--------:|
| 코드 재활용률 | 80% | **55-60%** |
| 개발 기간 | 2-3주 | **5-8주** (QA 포함) |
| BE/FE 병렬화 | Week 4-5 BE → Week 6 FE | BE 2주 선행 후 FE 가능 |
| 주요 병목 | (미식별) | **RoadmapContextBuilder** + **안전장치 프롬프트 설계** |

### 실현 가능성 판단

**결론: 기술적으로 완전히 실현 가능하나, 일정은 마스터 플랜 대비 약 2배 소요 예상.**

1. **데이터 준비 완료**: LAYER 1/2에 필요한 모든 데이터가 이미 DB에 존재 (Roadmap + StepDetail + StepAction + ActionKit)
2. **패턴 재활용 가능**: LLM 호출, 프롬프트 구조, DI 패턴, 인증 미들웨어 모두 검증된 패턴 존재
3. **핵심 신규 작업**: `RoadmapContextBuilder`, SSE 스트리밍, 안전장치 프롬프트 — 이 3개가 전체 공수의 60%
4. **최대 리스크**: 법률 자문 일정(4-6주) 미반영, 안전장치 QA 부족 시 NYC MyCity 사태 재현 가능

### 즉시 시작 가능한 작업

1. DB 모델 정의 + Alembic 마이그레이션 (외부 의존성 없음)
2. `RoadmapContextBuilder` 프로토타입 (기존 Repository 메서드 조합)
3. 안전장치 시스템 프롬프트 초안 작성 (LLMPersonalizer 패턴 참고)

### 병행 필수 작업 (비개발)

1. **법률 자문 착수** (변호사법 + AI 기본법, 4-6주 전)
2. **안전장치 QA 시나리오** 100건+ 작성 (경계 케이스 포함)
3. **프롬프트 레드팀 테스트** 계획 수립

---
---

# Part 2: 법적근거/필수서류 링크 오류 — 근본 원인 분석 및 개선 방안

> AI 코치 개선 전 **선행 해결 필수** 항목. 현재 로드맵의 핵심 가치(법령 기반 신뢰성)를 훼손하는 문제.

---

## 8. 링크 생성 전체 파이프라인 추적

### 8.1 source_url 생성 흐름도

```
ActionKitMatcher.match()
  ↓ MatchedActionKit[] (item + files + highlights + related_laws)

LLMPersonalizer.personalize()
  ↓ PersonalizedStepDetail[] (LLM이 JSON 배열 생성)
  ↓ legal_basis: [{title, snippet, actionkit_item_id}]
  ↓ documents:   [{name, file_url, actionkit_item_id, actionkit_file_id}]

RoadmapGenerationService._personalized_to_steps_payload()
  ↓ Step 1: item_id → file_url 맵 구성
  ↓   item_file_urls[item_id] = f"/api/v1/actionkits/files/{object_key}"
  ↓
  ↓ Step 2: LEGAL_BASIS source_url 보강
  ↓   LLM source_url 있음? → 사용
  ↓   없음? → actionkit_item_id로 item_file_urls 룩업
  ↓   룩업 실패? → source_url = None  ★ 문제 발생 지점
  ↓
  ↓ Step 3: DOCUMENT source_url 보강
  ↓   file_url 있음? → /api/v1/actionkits/files/ 프리픽스 추가
  ↓   없음? → actionkit_item_id로 룩업
  ↓   룩업 실패? → source_url = None  ★ 문제 발생 지점

RoadmapRepository.create_steps_with_details()
  ↓ RoadmapStepAction.source_url에 저장 (DB)

프론트엔드 TimelineStepItem.tsx
  ↓ source_url 있음? → <a href={source_url}> "근거/원문 보기"
  ↓ 없음 + LEGAL_BASIS? → "상세 법령 정보 준비 중" (회색 텍스트)
  ↓ 없음 + DOCUMENT? → 아무것도 표시 안 함
```

### 8.2 파일 서빙 아키텍처

```
FastAPI main.py:
  app.mount(
    "/api/v1/actionkits/files",
    StaticFiles(directory=str(actionkit_storage_dir)),  # uploads/actionkit/
  )

DB에 저장된 source_url:
  /api/v1/actionkits/files/laws/chapter-1/42/v1/식품위생법.pdf

실제 파일 경로:
  {STORAGE_ROOT}/actionkit/laws/chapter-1/42/v1/식품위생법.pdf

대안 엔드포인트 (별도 존재하지만 로드맵에서 미사용):
  GET /api/v1/actionkits/items/{item_id}/download
```

---

## 9. 발견된 링크 오류 — 근본 원인 5가지

### 문제 #1: LLM이 actionkit_item_id를 누락/변조 [심각도: HIGH]

**원인**: LLM이 JSON 출력 시 `actionkit_item_id` 필드를 생략하거나 존재하지 않는 ID를 생성

**코드 경로**:
```python
# llm_personalizer.py — LLM 출력 파싱
for lb in detail.legal_basis:
    item_id = lb.get("actionkit_item_id")  # → None 또는 잘못된 ID
    # item_file_urls에서 룩업 실패 → source_url = None
```

**검증 현황**: `_validate_references()`가 존재하지만 **debug 로그만 출력하고 데이터를 수정하지 않음**
```python
# llm_personalizer.py:303-328
if title not in original_law_names:
    logger.debug("LLM modified law: '%s'", title)  # 경고만, 수정 없음
```

**영향**: LEGAL_BASIS 액션의 source_url = None → "상세 법령 정보 준비 중" 표시

**발생 빈도**: LLM 특성상 비결정적 — 동일 입력이라도 때때로 누락 발생

---

### 문제 #2: ActionKit 아이템에 파일이 없는 경우 [심각도: HIGH]

**원인**: ActionKit 아이템(법령)은 있지만 첨부된 파일(PDF 등)이 없는 경우

**코드 경로**:
```python
# roadmap_generation_service.py:312-322
item_file_urls: dict[int, str] = {}
for m in matched_items:
    if m.item.id is not None and m.files:  # ← m.files가 빈 리스트면 스킵
        for f in m.files:
            item_file_urls[m.item.id] = f"/api/v1/actionkits/files/{f.object_key}"
            break
```

**조건**: `ActionKitFile` 테이블에 해당 item의 `is_current=True` 레코드 없음

**영향**: 해당 item_id가 `item_file_urls` 맵에 등록 안 됨 → 모든 관련 법적근거/서류의 source_url = None

---

### 문제 #3: 한 아이템에 여러 파일 — 첫 번째만 사용 [심각도: MEDIUM]

**원인**: `break` 문으로 첫 번째 파일만 `item_file_urls`에 저장

**코드**:
```python
for f in m.files:
    item_file_urls[m.item.id] = f"/api/v1/actionkits/files/{f.object_key}"
    break  # ← 2번째 이후 파일 무시
```

**영향**: 서류(DOCUMENT)가 여러 파일을 참조해야 하는 경우, 첫 번째 파일 URL만 사용. 나머지 서류는 다른 file_id인데도 같은 URL을 받거나 None.

---

### 문제 #4: RAG 폴백 모드 — 모든 링크 없음 [심각도: MEDIUM]

**원인**: ActionKit 매칭 실패 시 순수 LLM 생성으로 폴백. 이 경우 ActionKit 데이터 자체가 없음.

**코드**:
```python
# llm_personalizer.py — 폴백 템플릿
LegalBasisItem(
    title="업종별 개별법",
    snippet="업종에 따른 인허가 근거...",
    source_url=None,  # ← 하드코딩 None
)
```

**폴백 조건**: `_MIN_ACTIONKIT_MATCHES = 1` (매칭 1건 미만이면 폴백)

**영향**: 폴백 로드맵의 **모든** LEGAL_BASIS가 "상세 법령 정보 준비 중", 모든 DOCUMENT에 링크 없음

---

### 문제 #5: 한글 파일명 URL 인코딩 [심각도: LOW-MEDIUM]

**원인**: object_key에 한글이 포함된 경우 URL 인코딩 문제 가능

**예시**:
```
object_key: laws/chapter-1/42/v1/식품위생법(법률)(제21299호)(20261231).pdf
source_url: /api/v1/actionkits/files/laws/chapter-1/42/v1/식품위생법(법률)(제21299호)(20261231).pdf
```

**FastAPI StaticFiles**: Starlette StaticFiles가 URL 디코딩을 처리하지만, 특수문자(괄호 등)와 한글 조합에서 불일치 발생 가능

**영향**: 특정 파일에서만 404 발생 — 재현이 불규칙적이라 디버깅 어려움

---

## 10. 프론트엔드 렌더링 문제 분석

### 10.1 현재 렌더링 로직 (TimelineStepItem.tsx)

```typescript
// source_url 처리 (라인 243-257)
{item.source_url ? (
    <a href={item.source_url} target="_blank" rel="noreferrer"
       className="text-xs text-[#36a4f2] hover:underline">
        근거/원문 보기
        <ExternalLink className="w-3 h-3" />
    </a>
) : item.action_type === "LEGAL_BASIS" ? (
    <span className="text-xs text-slate-400">
        상세 법령 정보 준비 중
    </span>
) : null}
```

### 10.2 프론트엔드 문제점

| 문제 | 설명 | 영향 |
|------|------|------|
| **DOCUMENT 링크 없음 시 무표시** | source_url=null인 DOCUMENT는 링크 영역 자체가 렌더링 안 됨 | 사용자가 서류가 있는지 없는지 구분 불가 |
| **404 에러 무처리** | `<a href>` 클릭 시 404 → 새 탭에서 에러 페이지 표시 | 사용자 경험 손상, 신뢰도 하락 |
| **metadata_json 미활용** | `actionkit_item_id`가 metadata에 있지만 대안 링크 생성 안 함 | 폴백 경로 없음 |
| **LEGAL_BASIS vs DOCUMENT 불일치** | LEGAL_BASIS는 "준비 중" 표시, DOCUMENT는 완전 무표시 | 일관성 없음 |

---

## 11. 개선 방안 — 우선순위별

### 11.1 [P0] 즉시 수정 — LLM actionkit_item_id 검증 강화

**현재**: 경고만 → **개선**: 자동 복구

```python
# llm_personalizer.py — _validate_references() 개선

def _validate_and_repair_references(
    details: list[dict],
    matched_items: list[MatchedActionKit],
) -> list[dict]:
    """LLM 출력의 actionkit_item_id를 검증하고 누락 시 자동 복구"""

    # 원본 데이터 인덱스 구성
    valid_item_ids = {m.item.id for m in matched_items}
    law_name_to_item_id = {
        law.law_name: m.item.id
        for m in matched_items
        for law in m.related_laws
    }
    item_name_to_id = {m.item.name: m.item.id for m in matched_items}

    for detail in details:
        for lb in detail.get("legal_basis", []):
            item_id = lb.get("actionkit_item_id")

            # Case 1: item_id 없음 → 법령명으로 역매핑
            if not item_id:
                title = lb.get("title", "")
                item_id = law_name_to_item_id.get(title) or item_name_to_id.get(title)
                if item_id:
                    lb["actionkit_item_id"] = item_id
                    logger.info("Repaired missing item_id for '%s' → %d", title, item_id)

            # Case 2: item_id가 유효 범위 밖 → 제거
            elif item_id not in valid_item_ids:
                lb["actionkit_item_id"] = None
                logger.warning("Invalid item_id %d removed for '%s'", item_id, lb.get("title"))

    return details
```

**예상 효과**: source_url = None 케이스 50-70% 감소

---

### 11.2 [P0] 즉시 수정 — DOCUMENT 링크 폴백 추가

**프론트엔드**: metadata_json의 actionkit_item_id를 활용한 대안 링크

```typescript
// TimelineStepItem.tsx — source_url 없을 때 대안 경로

{item.source_url ? (
    <a href={item.source_url} target="_blank" rel="noreferrer" ...>
        근거/원문 보기
    </a>
) : item.metadata_json?.actionkit_item_id ? (
    // 대안: item_id 기반 다운로드 엔드포인트 사용
    <a href={`/api/v1/actionkits/items/${item.metadata_json.actionkit_item_id}/download`}
       target="_blank" rel="noreferrer" ...>
        원문 보기 (대안)
    </a>
) : item.action_type === "LEGAL_BASIS" ? (
    <span className="text-xs text-slate-400">상세 법령 정보 준비 중</span>
) : item.action_type === "DOCUMENT" ? (
    <span className="text-xs text-slate-400">서류 준비 중</span>
) : null}
```

**핵심**: `/api/v1/actionkits/items/{item_id}/download` 엔드포인트가 **이미 구현되어 있으나** 로드맵에서 사용하지 않고 있음. 이를 폴백 경로로 활용.

**예상 효과**: metadata에 item_id가 있는 모든 케이스에서 링크 복구

---

### 11.3 [P0] 즉시 수정 — 다중 파일 매핑

**현재**: 첫 번째 파일만 사용 → **개선**: 모든 파일 매핑

```python
# roadmap_generation_service.py — item_file_urls 구성 개선

# Before:
item_file_urls: dict[int, str] = {}
for m in matched_items:
    if m.item.id is not None and m.files:
        for f in m.files:
            item_file_urls[m.item.id] = f"/api/v1/actionkits/files/{f.object_key}"
            break  # ← 문제

# After:
item_file_urls: dict[int, str] = {}      # item_id → 대표 파일 URL (첫 번째)
item_all_files: dict[int, list[dict]] = {}  # item_id → 전체 파일 목록

for m in matched_items:
    if m.item.id is not None and m.files:
        files_list = []
        for f in m.files:
            url = f"/api/v1/actionkits/files/{f.object_key}"
            files_list.append({"url": url, "file_id": f.id, "filename": f.original_filename})
            if m.item.id not in item_file_urls:
                item_file_urls[m.item.id] = url  # 첫 번째만 대표
        item_all_files[m.item.id] = files_list
```

---

### 11.4 [P1] source_url 생성 전략 변경 — item_id 기반 URL로 통일

**근본적 해결**: object_key 기반 StaticFiles URL 대신 **item_id 기반 동적 URL** 사용

```python
# Before (현재):
item_file_urls[m.item.id] = f"/api/v1/actionkits/files/{f.object_key}"
# → 한글 파일명 인코딩 문제, 파일 경로 변경 시 깨짐

# After (개선):
item_file_urls[m.item.id] = f"/api/v1/actionkits/items/{m.item.id}/download"
# → item_id는 불변, 파일 버전 변경에도 안전, 한글 인코딩 무관
```

**장점**:
- item_id는 정수 → URL 인코딩 문제 없음
- 파일 버전 업데이트해도 URL 불변 (항상 최신 is_current=True 서빙)
- 기존 `/items/{item_id}/download` 엔드포인트 그대로 활용

**단점**:
- 기존 로드맵의 source_url 마이그레이션 필요 (data migration)
- StaticFiles 직접 서빙보다 약간 느림 (DB 조회 1회 추가)

---

### 11.5 [P1] RAG 폴백 모드 개선

**현재**: 매칭 실패 → 모든 링크 없음

**개선 방안**:

```python
# 부분 매칭 hybrid 모드 추가
if len(matched_items) < _MIN_ACTIONKIT_MATCHES:
    # 기존: 전체 폴백 → source_url 전부 None
    # 개선: 매칭된 아이템이 있으면 부분 활용
    if matched_items:
        # 매칭된 단계: ActionKit 데이터 사용
        # 미매칭 단계: LLM 생성 + source_url = None (기존 동작)
        generation_mode = "HYBRID"
    else:
        generation_mode = "RAG"  # 완전 폴백
```

---

### 11.6 [P2] 기존 데이터 복구 마이그레이션

기존 로드맵에서 source_url=None이지만 metadata_json에 actionkit_item_id가 있는 레코드 복구:

```python
# 마이그레이션 스크립트 (1회성)
UPDATE roadmap_step_actions
SET source_url = CONCAT('/api/v1/actionkits/items/',
                        (metadata_json->>'actionkit_item_id')::int,
                        '/download')
WHERE source_url IS NULL
  AND metadata_json->>'actionkit_item_id' IS NOT NULL
  AND action_type IN ('LEGAL_BASIS', 'DOCUMENT');
```

---

## 12. 문제 — 원인 — 해결 요약 테이블

| # | 사용자 증상 | 근본 원인 | 코드 위치 | 해결 방안 | 우선순위 |
|---|-----------|----------|----------|----------|:-------:|
| 1 | LEGAL_BASIS에 "준비 중" 표시 | LLM이 actionkit_item_id 누락 | `llm_personalizer.py:303-328` | 자동 복구 로직 추가 | **P0** |
| 2 | DOCUMENT에 링크 없음 | ActionKit 아이템에 파일 미등록 | `roadmap_generation_service.py:312-322` | item_id 기반 다운로드 폴백 | **P0** |
| 3 | 클릭 시 404 | 한글 파일명 URL 인코딩 불일치 | `roadmap_generation_service.py:320` | item_id 기반 URL로 통일 | **P1** |
| 4 | 잘못된 서류에 링크 연결 | 첫 번째 파일만 매핑, 나머지 무시 | `roadmap_generation_service.py:319` (break) | 다중 파일 매핑 | **P0** |
| 5 | 폴백 로드맵 전체 링크 없음 | RAG 모드에서 ActionKit 데이터 미사용 | `llm_personalizer.py:495-601` | hybrid 모드 도입 | **P1** |
| 6 | DOCUMENT "준비 중" 미표시 | FE에서 null DOCUMENT 무시 | `TimelineStepItem.tsx:243-257` | 일관된 폴백 텍스트 추가 | **P0** |
| 7 | 과거 로드맵 링크 깨짐 | 파일 버전 변경 (is_current 필터) | `actionkit_matcher.py` | item_id URL + 마이그레이션 | **P1** |

---

## 13. 구현 순서 권장 — 링크 오류 우선 해결

```
선행 작업: 링크 오류 수정 (AI 코치 개선 전 필수)
│
├── [P0-1] FE: DOCUMENT/LEGAL_BASIS 일관된 폴백 표시 (0.5일)
│   └── TimelineStepItem.tsx 수정
│
├── [P0-2] FE: metadata_json.actionkit_item_id 기반 대안 링크 (1일)
│   └── /items/{item_id}/download 엔드포인트 활용
│
├── [P0-3] BE: LLM actionkit_item_id 자동 복구 로직 (2일)
│   └── llm_personalizer.py _validate_and_repair_references()
│
├── [P0-4] BE: 다중 파일 매핑 수정 (0.5일)
│   └── roadmap_generation_service.py break 제거
│
├── [P1-1] BE: source_url을 item_id 기반 URL로 통일 (1일)
│   └── roadmap_generation_service.py URL 생성 패턴 변경
│
├── [P1-2] DB: 기존 데이터 마이그레이션 (0.5일)
│   └── source_url=None → item_id 기반 URL 복구
│
└── [P1-3] BE: hybrid 매칭 모드 (2일)
    └── 부분 매칭 시 ActionKit 데이터 활용

총 예상: P0 = 4일, P1 = 3.5일 → 합계 ~7.5일 (약 1.5주)
```

**이후**: AI 코치 챗봇 개선 진행 (Part 1의 Phase 2-A부터)

---

## 14. 전체 로드맵 (링크 수정 + AI 코치)

```
Week 0-1.5: 링크 오류 P0+P1 수정 (7.5일)
  ↓
Week 2-3:   AI 코치 기반 구축 (DB 모델, ContextBuilder, 안전장치)
  ↓
Week 3-4:   AI 코치 백엔드 핵심 (SSE, 라우터)
  ↓
Week 4-5:   AI 코치 프론트엔드 (StepChatPanel, 스트리밍)
  ↓
Week 5-7:   품질 검증 + 프롬프트 튜닝
```

**총 예상**: 7-9주 (링크 수정 1.5주 + AI 코치 5.5-7.5주)
