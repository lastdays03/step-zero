# AI 코치 MVP 기술 설계 및 실현 가능성 검증

> **통합일**: 2026-02-28
> **원본 문서**:
> - `ai-coach-technical-design.md` (기술 아키텍처 상세 설계)
> - `technical-validation-ai-coach-mvp.md` (기술적 실현 가능성 검증 보고서)
>
> **근거 문서**: ai-coach-benchmark-analysis.md, benchmark-application-report.md (섹션 4), brainstorm-result.md (사이클 2)
> **코드베이스 기준**: `/config/workspace/step-zero/app-backend/`, `/config/workspace/step-zero/app-frontend/`

---

## Executive Summary

기존 코드베이스 분석 결과, **AI 코치 MVP의 약 80%를 기존 인프라 재활용**으로 구현 가능하다.

**설계 측면 ("What to build"):**
`ChatService` + `RagService` + `SemanticRouter`의 LLM 클라이언트/벡터스토어 인프라,
`ChatPanel`/`ChatMessageList`/`ChatInput`의 UI 컴포넌트를 그대로 재활용하고,
컨텍스트 빌더 + SSE 스트리밍 + 대화 이력 DB 모델만 신규 구현하면 된다.

**검증 측면 ("Proof it's feasible"):**
실제 코드 라인 수 기반 분석에서 전체 재활용율 78%를 확인했다.
신규 작성 코드는 약 931줄로 추정되며, 기존 인프라(LangChain, SQLModel, FastAPI)가 안정적으로
동작하고 있어 새로운 외부 라이브러리 없이 구현이 가능하다.

**최종 판단**: 80% 재활용, 2-3주 개발 가능 (현실적)

---

## 1. 아키텍처 설계

### 1.1 시스템 프롬프트 컨텍스트 빌더: Jasper IQ 패턴 3-레이어 구조

```
+-------------------------------------------------------------+
|  LAYER 1: 불변 팩트 레이어 (LLM 수정 불가)                      |
|  -----------------------------------------------------      |
|  - 업종, 지역, 창업형태, 오픈시기, 예산                         |
|  - 현재 단계 제목, 위상(phase), 목표(objective)                 |
|  - LEGAL_BASIS 액션 (법령명 + ActionKit ID + source_url)       |
|  - DOCUMENT 액션 (서류명 + source_url)                         |
|  -> AI가 이 데이터를 생성/변형/추론할 수 없음                    |
+-------------------------------------------------------------+
          | 주입
+-------------------------------------------------------------+
|  LAYER 2: 실행 상태 레이어 (현재 진행 상태)                      |
|  -----------------------------------------------------      |
|  - 완료된 CHECKLIST 액션 목록                                   |
|  - 미완료 CHECKLIST 액션 목록                                   |
|  - estimated_days, step status                                |
|  - risk_notes (유의사항)                                       |
+-------------------------------------------------------------+
          | 주입
+-------------------------------------------------------------+
|  LAYER 3: 안내 레이어 (AI 행동 규칙)                            |
|  -----------------------------------------------------      |
|  - 이전 대화 요약 (최근 5개 메시지)                              |
|  - 4가지 안전장치 규칙 (섹션 3 참조)                             |
|  - 응답 포맷 규칙 (인용 형식, 면책 고지)                         |
+-------------------------------------------------------------+
```

### 1.2 컨텍스트 직렬화 포맷 (토큰 효율 최적화)

기존 `roadmap.md` 스키마 기반으로 다음 포맷을 사용한다.
최대 약 800~1,200 토큰 사용 (Claude claude-sonnet-4-6 200k 컨텍스트 윈도우 기준 여유).

```python
# RoadmapContextBuilder.build_system_prompt() 내부 직렬화
SYSTEM_PROMPT_TEMPLATE = """당신은 Step Zero의 창업 준비 AI 코치입니다.

## [절대 불변 팩트 -- 이 정보를 절대 수정/추론/생성하지 마세요]
- 업종: {business_type}
- 지역: {location}
- 창업형태: {startup_type}
- 목표 오픈시기: {open_timeline}
- 예산: {budget_range}
- 현재 단계: [{step_order}] {step_title}
- 단계 위상: {phase}
- 단계 목표: {objective}
- 예상 소요일: {estimated_days}일

### 이 단계의 법적 근거 (ActionKit DB 출처)
{legal_bases}

### 이 단계의 필수 서류
{documents}

## [실행 현황]
### 완료된 항목
{completed_actions}

### 미완료 항목
{pending_actions}

### 유의사항
{risk_notes}

## [AI 코치 행동 규칙]
1. 법령명/조문번호/파일경로는 위 팩트 레이어에 제공된 데이터 이외의 것을 생성하지 마세요.
2. 법령 정보를 언급할 때는 반드시 "[출처 N]" 형식으로 위 법적 근거를 인용하세요.
3. ActionKit DB에 없는 정보는 "이 부분은 해당 기관에 직접 확인이 필요합니다"라고 답하세요.
4. 세금신고/소송/특허/의료/투자 등 이 단계 범위 밖의 질문은 전문가 상담을 안내하세요.
5. "~해야 합니다" 대신 "~가 필요합니다/권고됩니다" 어조를 사용하세요 (법적 조언 프레이밍 회피).
6. 모든 답변 마지막에 면책 고지를 반드시 포함하세요.

## [이전 대화 요약]
{recent_chat_summary}
"""
```

법적 근거 직렬화 예시 (토큰 효율):
```
[출처 1] 식품위생법 제37조 (영업허가 등) | actionkit_id:1247 | URL: https://...
[출처 2] 식품위생법 제41조 (위생교육) | actionkit_id:1248 | URL: https://...
```

### 1.3 SSE 스트리밍 엔드포인트 설계

#### 엔드포인트 스펙

```
POST /api/v1/roadmaps/{roadmap_id}/steps/{step_id}/chat/stream
```

| 항목 | 값 |
|------|-----|
| 인증 | JWT 필수 (기존 `deps.get_current_user` 재활용) |
| 권한 | roadmap이 current_team에 속하는지 검증 |
| Content-Type 응답 | `text/event-stream` |
| 타임아웃 | 30초 (HeartBeat 15초마다 전송) |

#### 요청 스키마

```python
class StepChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    thread_id: UUID | None = None  # None이면 새 thread 생성
```

#### SSE 이벤트 포맷

```
# 토큰 스트림
data: {"type": "token", "token": "위생교육은"}\n\n
data: {"type": "token", "token": " 영업"}\n\n

# 출처 블록 (스트리밍 완료 후 한 번에 전송)
data: {"type": "sources", "sources": [
  {"n": 1, "title": "식품위생법 제41조", "url": "https://...", "actionkit_id": 1248}
]}\n\n

# thread_id 전달 (새 thread 생성 시)
data: {"type": "meta", "thread_id": "uuid-...", "message_id": 42}\n\n

# 완료
data: {"type": "done"}\n\n

# 에러
data: {"type": "error", "code": "OUT_OF_SCOPE", "message": "세무 질문은 전문가 상담을 권합니다"}\n\n

# 하트비트 (연결 유지)
: heartbeat\n\n
```

#### FastAPI StreamingResponse 구조

```python
# app/api/v1/roadmaps/chat.py (신규)

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from uuid import UUID

router = APIRouter()

@router.post("/{roadmap_id}/steps/{step_id}/chat/stream")
async def step_chat_stream(
    roadmap_id: UUID,
    step_id: int,
    request: StepChatRequest,
    current_user: User = Depends(deps.get_current_user),
    current_team: Team = Depends(deps.get_current_team),
    db: AsyncSession = Depends(get_write_session_dependency),
    read_db: AsyncSession = Depends(get_read_session_dependency),
    chat_service: RoadmapChatService = Depends(get_roadmap_chat_service),
):
    # 1. roadmap 권한 검증
    roadmap = await repo.get_by_id_for_team(roadmap_id, current_team.id)

    # 2. step 조회 (read_db)
    step_data = await repo.get_step_with_full_context(step_id, roadmap_id)

    # 3. thread 조회/생성 (write_db)
    thread = await chat_repo.get_or_create_thread(
        roadmap_id=roadmap_id,
        step_id=step_id,
        user_id=current_user.id,
        thread_id=request.thread_id,
    )

    # 4. 메시지 저장 (user)
    await chat_repo.add_message(thread.id, role="user", content=request.message)

    # 5. 스트리밍 응답
    return StreamingResponse(
        chat_service.stream(
            roadmap=roadmap,
            step_data=step_data,
            thread=thread,
            user_message=request.message,
            write_db=db,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # nginx 버퍼링 비활성화
        },
    )
```

#### 에러 처리 및 연결 끊김 처리

```python
# RoadmapChatService.stream() 내부 제너레이터

async def stream(...) -> AsyncIterator[str]:
    full_response = ""
    try:
        # 스코프 필터: SemanticRouter 재활용
        if await scope_filter.is_out_of_scope(user_message, step_context):
            yield make_sse_event("error", {
                "code": "OUT_OF_SCOPE",
                "message": "이 질문은 현재 단계 범위를 벗어납니다. 전문가 상담을 권합니다.",
                "redirect_to": current_step_title,
            })
            return

        # LLM 스트리밍 (기존 ChatOpenAI 재활용, streaming=True)
        async for chunk in llm.astream(messages):
            token = chunk.content
            full_response += token
            yield make_sse_event("token", {"token": token})

        # 출처 블록 전송
        sources = extract_cited_sources(full_response, step_data.legal_bases)
        yield make_sse_event("sources", {"sources": sources})

        # thread_id, message_id 전달
        msg = await chat_repo.add_message(thread.id, "assistant", full_response)
        yield make_sse_event("meta", {"thread_id": str(thread.id), "message_id": msg.id})

        yield make_sse_event("done", {})

    except asyncio.CancelledError:
        # 클라이언트 연결 끊김 처리
        if full_response:
            # 부분 응답이라도 저장
            await chat_repo.add_message(
                thread.id, "assistant", full_response + " [연결 끊김]"
            )
        raise

    except asyncio.TimeoutError:
        yield make_sse_event("error", {
            "code": "TIMEOUT",
            "message": "응답 생성 시간이 초과되었습니다. 다시 시도해 주세요.",
        })
```

### 1.4 대화 이력 테이블 설계

#### 설계 결정: curai와 별도, roadmap 도메인에 신규 생성

브레인스토밍 합의(사이클 5, 기술 현실주의자):
> "로드맵 컨텍스트 주입이 curai와 완전히 다른 구조이므로, 결합하면 복잡도만 증가한다. 별도 생성을 권장한다."

#### RoadmapChatThread 스키마

```python
# app/models/roadmap_chat.py (신규)

class RoadmapChatThread(SQLModel, table=True):
    __tablename__ = "roadmap_chat_threads"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    roadmap_id: UUID = Field(foreign_key="roadmap.id", index=True)
    step_id: int = Field(foreign_key="roadmapstep.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow)

    # 인덱스: (roadmap_id, step_id, user_id) -- 특정 단계의 thread 조회
    __table_args__ = (
        sa.Index("ix_chat_thread_lookup", "roadmap_id", "step_id", "user_id"),
    )
```

#### RoadmapChatMessage 스키마

```python
class RoadmapChatMessage(SQLModel, table=True):
    __tablename__ = "roadmap_chat_messages"

    id: int = Field(default=None, primary_key=True)
    thread_id: UUID = Field(foreign_key="roadmap_chat_threads.id", index=True)
    role: str  # "user" | "assistant"
    content: str = Field(sa_column=sa.Column(sa.Text, nullable=False))
    sources_json: list[dict] = Field(
        default_factory=list,
        sa_column=sa.Column(sa.JSON, nullable=False),
    )
    # sources_json 구조:
    # [{"n": 1, "title": "식품위생법 제41조", "url": "https://...", "actionkit_id": 1248}]
    created_at: datetime = Field(default_factory=utcnow, index=True)
    is_truncated: bool = Field(default=False)  # 연결 끊김으로 부분 저장된 경우
```

#### ER 다이어그램 (추가 관계)

```
Roadmap (1) ---- (*) RoadmapChatThread
                          |
RoadmapStep (1) ----------+
                          |
                          +-- (*) RoadmapChatMessage
```

#### Alembic 마이그레이션 위치

```
app-backend/alembic/versions/
  001_initial.py (기존)
  002_roadmap.py (기존)
  003_roadmap_chat.py (신규 -- 이 파일)
```

### 1.5 할루시네이션 방지 4가지 안전장치

#### 1.5.1 Harvey AI 패턴: 팩트-지능 분리

기존 `llm_personalizer.py`의 "ActionKit 법률명/파일 경로 절대 수정 불가" 규칙을
AI 코치 시스템 프롬프트의 **LAYER 1 (불변 팩트 레이어)**에 동일하게 적용한다.

구체적 구현 방법:
- 시스템 프롬프트 최상단에 `## [절대 불변 팩트]` 섹션 배치
- 섹션 내 데이터는 DB에서 직접 조회한 RoadmapStepAction 레코드 (title, source_url, metadata_json.actionkit_item_id)
- 시스템 프롬프트 내 명시적 지시: "이 섹션의 법령명/조문번호/URL은 절대 변형하거나 추론으로 생성하지 마세요"

#### 1.5.2 Perplexity 패턴: 출처 강제 인용

```python
# 시스템 프롬프트 규칙 (LAYER 3)
CITATION_RULE = """
법령/규정/서류 정보를 언급할 때는 반드시 [출처 N] 형식으로 인용하세요.

올바른 예:
"위생교육은 영업 시작 전 이수해야 합니다 [출처 1]."

잘못된 예 (출처 없는 법령 언급):
"식품위생법 제41조에 따르면..." (<- 출처 표기 없음)

출처 목록에 없는 법령명을 생성하는 것은 금지합니다.
"""
```

SSE 스트리밍 후처리에서 `[출처 N]` 패턴 파싱 -> `sources` 이벤트로 전송:
```python
def extract_cited_sources(
    response: str,
    legal_bases: list[LegalBasisContext],
) -> list[dict]:
    """[출처 N] 패턴 파싱 -> ActionKit 메타데이터 매핑"""
    cited = re.findall(r'\[출처 (\d+)\]', response)
    result = []
    for n in set(cited):
        idx = int(n) - 1
        if 0 <= idx < len(legal_bases):
            lb = legal_bases[idx]
            result.append({
                "n": int(n),
                "title": lb.title,
                "url": lb.source_url,
                "actionkit_id": lb.actionkit_item_id,
            })
    return result
```

#### 1.5.3 Ada Health 패턴: 범위 외 질문 거부

스코프 필터는 기존 `SemanticRouter`를 확장하여 구현한다.

```python
# OUT_OF_SCOPE 키워드/카테고리 목록
OUT_OF_SCOPE_PATTERNS = {
    "tax": ["세금신고", "부가세", "종합소득세", "세무사", "세금 환급"],
    "legal_dispute": ["소송", "판례", "법원", "변호사", "행정심판"],
    "medical": ["의료", "건강보험", "산재", "질병"],
    "investment": ["투자", "VC", "엔젤", "주식", "상장"],
    "intellectual_property": ["특허", "상표권", "저작권"],
}

OUT_OF_SCOPE_RESPONSE_TEMPLATE = """\
{topic}은(는) 현재 [{step_title}] 단계의 범위를 벗어납니다.

정확한 안내를 위해 다음 전문가 상담을 권합니다:
{specialist_recommendation}

현재 [{step_title}] 단계에서 도움이 필요한 사항이 있으신가요?"""
```

#### 1.5.4 면책 고정 문구 설계

모든 AI 코치 응답 말미에 **프론트엔드**에서 고정 렌더링 (백엔드 응답에 포함하지 않음 -> 스트리밍 속도 영향 없음):

```tsx
// StepChatPanel.tsx 내부 고정 렌더링
const DISCLAIMER = `이 정보는 일반 정보 안내이며 법적 조언이 아닙니다.
개별 상황에 따라 다를 수 있으므로, 복잡한 경우 행정사/변호사 상담을 권합니다.
(AI 기본법 제00조에 따라 AI 생성 콘텐츠임을 명시합니다)`;
```

### 1.6 프론트엔드 채팅 UI 설계

#### "AI에게 물어보기" 버튼 삽입 위치

`TimelineStepItem.tsx`의 **ACTIVE 상태 섹션** (현재 단계가 `IN_PROGRESS`일 때만 표시)

```
+-----------------------------------------------------+
|  [2] 영업허가 신청           IN_PROGRESS              |
|  -------------------------------------------------- |
|  [v] 식품위생법 제37조 확인                            |
|  [v] 위생교육 수료증 발급                              |
|  [ ] 영업허가 신청서 작성    <- 미완료                  |
|  [ ] 현장 검사 예약          <- 미완료                  |
|                                                      |
|  +------------------------------------------+        |
|  |  이 단계에 대해 AI에게 물어보기              |  <- 버튼 |
|  +------------------------------------------+        |
|                                                      |
|  [단계 완료] 버튼                                     |
+-----------------------------------------------------+
```

버튼 위치: 체크리스트 목록 바로 아래, "단계 완료" 버튼 위

```tsx
// TimelineStepItem.tsx 수정 위치 (state === "ACTIVE" 섹션)
<button
  onClick={() => setStepChatOpen(true)}
  className="w-full flex items-center gap-2 px-3 py-2 text-sm
             text-[#36a4f2] border border-[#36a4f2]/30 rounded-lg
             hover:bg-[#36a4f2]/5 transition-colors"
>
  <MessageSquare className="w-4 h-4" />
  이 단계에 대해 AI 코치에게 물어보기
</button>
```

#### 슬라이드아웃 패널 (우측 고정)

이유:
1. 기존 `GlobalChatbot`/`ChatPanel` 컴포넌트를 80% 재활용 가능
2. 타임라인 뷰를 가리지 않아 단계 정보 참조 가능
3. `GlobalChatbot`과 UI 일관성 유지

```
+--------------------------+---------------------------+
|  타임라인 (로드맵 뷰)      |  [x] AI 코치 채팅 패널     |
|                          |  ------------------------ |
|  [1] 시장조사 [v]          |  영업허가 신청 단계         |
|  [2] 영업허가 -> ACTIVE   |                          |
|      [ ] 신청서 작성       |  사용자: 신청서 어떻게 써요? |
|                          |  AI: 식품위생법 제37조에     |
|      AI에게 물어보기       |  따라... [출처 1]          |
|      [단계 완료]          |                          |
|  [3] 세무사 선정 (잠금)    |  ------------------------ |
|                          |  메시지 입력...  [전송]    |
+--------------------------+---------------------------+
                                     ^
                           400px 고정 폭 (desktop)
                           full-width (mobile)
```

#### SSE 스트리밍 클라이언트 구현 패턴

기존 `useChatbot` hook 구조를 참고하여 `useStepChat` hook 신규 구현:

```typescript
// app-frontend/src/features/roadmap/hooks/useStepChat.ts

interface StepChatState {
  messages: StepChatMessage[];
  isStreaming: boolean;
  currentToken: string;     // 스트리밍 중 현재 누적 토큰
  error: string | null;
  threadId: string | null;
}

interface StepChatMessage {
  id: number | null;
  role: "user" | "assistant";
  content: string;
  sources: CitationSource[];
  isPartial: boolean;        // 스트리밍 진행 중 여부
}

function useStepChat(roadmapId: string, stepId: number) {
  const [state, setState] = useState<StepChatState>({...});

  const sendMessage = async (userMessage: string) => {
    // 1. 낙관적 UI 업데이트 (사용자 메시지 즉시 표시)
    addUserMessage(userMessage);

    // 2. SSE 연결
    const response = await fetch(
      `/api/v1/roadmaps/${roadmapId}/steps/${stepId}/chat/stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${getAuthToken()}`,
        },
        body: JSON.stringify({
          message: userMessage,
          thread_id: state.threadId,
        }),
      }
    );

    if (!response.ok) throw new Error("API 오류");

    // 3. ReadableStream으로 SSE 파싱
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let assistantContent = "";
    let sources: CitationSource[] = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6).trim();
        if (!data || data === "") continue;

        const event = JSON.parse(data);

        switch (event.type) {
          case "token":
            assistantContent += event.token;
            updatePartialAssistantMessage(assistantContent);
            break;

          case "sources":
            sources = event.sources;
            break;

          case "meta":
            // thread_id 저장 (다음 메시지에 재사용)
            setState(prev => ({...prev, threadId: event.thread_id}));
            finalizeAssistantMessage(assistantContent, sources, event.message_id);
            break;

          case "error":
            setError(event.message);
            break;

          case "done":
            setStreaming(false);
            break;
        }
      }
    }
  };

  return { ...state, sendMessage };
}
```

### 1.7 데이터 흐름 요약

```
사용자: "영업허가 신청서 어떻게 써요?" 클릭
                |
                v
[Frontend] useStepChat.sendMessage()
  -> POST /api/v1/roadmaps/{id}/steps/{step_id}/chat/stream
                |
                v
[Backend] step_chat_stream()
  -> 1. JWT 검증 + team 권한 확인
  -> 2. roadmap 메타데이터 조회 (read_db)
  -> 3. step + step_detail + step_actions 조회 (read_db)
  -> 4. thread get_or_create (write_db)
  -> 5. user 메시지 저장 (write_db)
  -> 6. RoadmapContextBuilder.build_system_prompt() 호출
       +-- LAYER 1: roadmap 메타 + step LEGAL_BASIS/DOCUMENT actions
       +-- LAYER 2: CHECKLIST 완료/미완료 상태
       +-- LAYER 3: 4가지 안전장치 규칙 + 최근 대화 요약
                |
                v
[Backend] RoadmapChatService.stream()
  -> 1. SemanticRouter로 스코프 체크 (OUT_OF_SCOPE -> 즉시 에러 이벤트)
  -> 2. ChatOpenAI(streaming=True).astream() 호출
  -> 3. 토큰마다 SSE "token" 이벤트 전송
  -> 4. 완료 후: [출처 N] 파싱 -> "sources" 이벤트
  -> 5. assistant 메시지 DB 저장 -> "meta" 이벤트
  -> 6. "done" 이벤트
                |
                v
[Frontend] ReadableStream 파싱
  -> token 이벤트: 실시간 타이핑 효과 UI 업데이트
  -> sources 이벤트: 출처 블록 렌더링
  -> meta 이벤트: thread_id 저장
  -> 면책 고지 고정 렌더링 (항상)
```

---

## 2. 코드 재활용 분석 (실현 가능성 검증)

### 2.1 검증 결과 요약

| 항목 | 평가 | 재활용율 | 난이도 |
|------|------|--------|--------|
| ChatService/RagService | 양호 | 85% | 2/5 |
| LLM & SemanticRouter | 양호 | 80% | 2/5 |
| SSE 스트리밍 | 부분 | 30% | 3/5 |
| Roadmap 모델 | 양호 | 90% | 1/5 |
| Notification 모델 | 양호 | 75% | 1/5 |
| 프론트엔드 컴포넌트 | 양호 | 80% | 2/5 |
| DB 세션 관리 | 우수 | 95% | 1/5 |
| 인증/권한 미들웨어 | 우수 | 100% | 1/5 |

### 2.2 백엔드 재활용 상세

#### ChatService / RagService

**파일 위치:**
- ChatService: `/app-backend/app/features/rag/application/chat_service.py` (127줄)
- RAGService: `/app-backend/app/features/rag/application/rag_service.py` (122줄)

**재활용 가능 부분 (85%)**:
- LLM 클라이언트 초기화: ChatOpenAI 직접 사용 가능
- 비동기 처리: `asyncio.wait_for()`, `run_in_threadpool()` 패턴 동일
- 에러 핸들링: TimeoutError, Exception 처리 로직
- 프롬프트 템플릿: 기존 시스템/사용자 프롬프트 재사용 가능
- 타임아웃 설정: 25초 타임아웃이 AI 코치에도 적용 가능

**수정 필요 부분 (15%)**:
- 채팅 히스토리 관리: 현재 단일 메시지 기반 -> AI 코치는 대화 컨텍스트 필요
- 스트리밍 응답: 현재 완전한 응답만 반환 -> SSE로 변경 필요
- 문맥 인식: AI 코치는 사용자 맥락 (학습 목표, 진행도) 필요

#### SemanticRouter

**파일 위치:** `/app-backend/app/features/rag/application/semantic_router.py` (114줄)

현재 `legal`/`general` 두 카테고리 분류를 수행하며, AI 코치에서는 `out_of_scope` 앵커만 추가하면 범위 외 질문 필터링이 가능하다.

SemanticRouter 확장 예시:
```python
self.anchors: dict[str, list[str]] = {
    "legal": [...existing...],
    "general": [...existing...],
    "out_of_scope": [  # 신규 추가
        "세금 신고 방법",
        "소송 절차",
        "특허 출원",
        "투자 유치 전략",
    ]
}
```

#### LLMPersonalizer

**파일 위치:** `/app-backend/app/features/roadmaps/application/llm_personalizer.py` (404줄)

AI 코치 재활용성은 60%로 제한적이다. LLM 호출 패턴, JSON 파싱/검증 로직, Fallback 처리는 재활용 가능하나, ActionKit 데이터 구조와 개인화 영역 7가지는 AI 코치 용으로 재설계가 필요하다.

참고: "법령명 절대 수정 불가" 규칙은 AI 코치에서 **동일하게 적용**하며 (섹션 1.5.1 Harvey AI 패턴), LLMPersonalizer의 ActionKit 검증 로직(`_validate_references()`)은 AI 코치와 구조적으로 무관하다.

#### Roadmap 모델

**파일 위치:** `/app-backend/app/models/roadmap.py` (84줄)

RoadmapStepAction의 `metadata_json` 필드를 통해 actionkit_item_id 역추적이 가능하며, 기존 모델을 90% 그대로 사용할 수 있다:

```python
class RoadmapStepAction(SQLModel, table=True):
    action_type: str  # CHECKLIST | LEGAL_BASIS | DOCUMENT
    metadata_json: dict = Field(
        default_factory=dict,
        sa_column=sa.Column(sa.JSON, nullable=False)
    )
    # metadata_json 내 actionkit_item_id로 역추적 가능
```

#### DB 세션 관리 및 인증 미들웨어

**파일 위치:**
- DB 세션: `/app-backend/app/core/db.py` (19줄)
- 인증: `/app-backend/app/api/deps.py` (198줄), `/app-backend/app/core/security.py` (44줄)

두 영역 모두 기존 패턴을 **100% 그대로** 사용한다. `get_current_user`, `get_current_team` 의존성 주입과 `get_session` 팩토리를 AI 코치 엔드포인트에 동일하게 적용한다.

#### SSE 스트리밍

현재 코드베이스에 **FastAPI StreamingResponse 미사용** 상태이며, 모든 응답이 완전한 텍스트 반환 방식이다. 기본 비동기 인프라는 완비되어 있으므로 SSE 엔드포인트를 신규 작성해야 한다. 재활용율 30%.

### 2.3 프론트엔드 재활용 상세

| 기존 코드 | 파일 경로 | 재활용 방법 |
|----------|-----------|------------|
| `ChatPanel` | `chatbot/components/ChatPanel.tsx` (87줄) | `StepChatPanel`의 베이스로 직접 재활용 |
| `ChatMessageList` | `chatbot/components/ChatMessageList.tsx` (43줄) | 출처 렌더링 UI만 추가 |
| `ChatInput` | `chatbot/components/ChatInput.tsx` | 그대로 재활용 |
| `ChatBubble` | `chatbot/components/ChatBubble.tsx` | 그대로 재활용 |
| `useChatbot` hook | `chatbot/hooks/useChatbot.ts` | `useStepChat` hook의 베이스로 참고 |
| `ChatMessage` 타입 | `chatbot/types/chat.ts` | 확장하여 `sources` 필드 추가 |

TimelineStepItem (`/app-frontend/src/features/roadmap/components/TimelineStepItem.tsx`, 200줄+)에는 step이 `IN_PROGRESS`일 때 "AI 코칭" 버튼만 추가하면 된다 (약 3줄).

### 2.4 전체 재활용율 정량 분석

| 영역 | 코드량 | 재활용율 | 신규 개발량 | 난이도 |
|------|--------|---------|-----------|--------|
| 백엔드 API (RAG/Chat) | 250줄 | 85% | 37줄 | 2/5 |
| LLM & Routing | 518줄 | 80% | 104줄 | 2/5 |
| 데이터 모델 | 200줄 | 90% | 20줄 | 1/5 |
| DB & ORM | 217줄 | 95% | 10줄 | 1/5 |
| 인증 미들웨어 | 242줄 | 100% | 0줄 | 1/5 |
| 프론트엔드 | 300줄+ | 80% | 60줄 | 2/5 |
| **SSE 스트리밍** | - | 30% | **150줄** | **3/5** |
| **AI 코치 로직** | - | 0% | **200줄** | **3/5** |
| **메모리/히스토리** | - | 0% | **100줄** | **2/5** |
| **프롬프트 엔지니어링** | - | 0% | **50줄** | **1/5** |
| **테스트** | - | 20% | **200줄** | **2/5** |
| **총합** | ~1,727줄 | **78%** | **931줄** | **평균 2/5** |

### 2.5 신규 구현 필요 항목 (설계 문서 기준)

| 신규 항목 | 파일 경로 (제안) | 복잡도 |
|---------|----------------|--------|
| `RoadmapContextBuilder` | `features/roadmaps/application/context_builder.py` | 3/5 |
| `RoadmapChatService` | `features/roadmaps/application/roadmap_chat_service.py` | 3/5 |
| SSE 스트리밍 엔드포인트 | `api/v1/roadmaps/chat.py` | 2/5 |
| `RoadmapChatThread`, `RoadmapChatMessage` 모델 | `models/roadmap_chat.py` | 1/5 |
| `RoadmapChatRepository` | `repositories/roadmap_chat_repository.py` | 2/5 |
| `003_roadmap_chat.py` 마이그레이션 | `alembic/versions/` | 1/5 |
| `useStepChat` hook (SSE 클라이언트) | `features/roadmap/hooks/useStepChat.ts` | 3/5 |
| `StepChatPanel` 컴포넌트 | `features/roadmap/components/StepChatPanel.tsx` | 2/5 |
| `TimelineStepItem.tsx` 버튼 추가 | 기존 파일 수정 | 1/5 |

---

## 3. 구현 계획

### Phase 1: 백엔드 기반 (1주)

- [ ] `models/roadmap_chat.py` - RoadmapChatThread, RoadmapChatMessage 모델
- [ ] `alembic/versions/003_roadmap_chat.py` - DB 마이그레이션
- [ ] `repositories/roadmap_chat_repository.py` - CRUD 레포지토리
- [ ] `features/roadmaps/application/context_builder.py` - 시스템 프롬프트 빌더
- [ ] SemanticRouter에 `out_of_scope` 카테고리 추가

### Phase 2: 스트리밍 엔드포인트 + 코어 서비스 (1주)

- [ ] `features/roadmaps/application/roadmap_chat_service.py` - 스트리밍 서비스
- [ ] `api/v1/roadmaps/chat.py` - SSE 라우터
- [ ] `api/v1/roadmaps/router.py` - chat 라우터 등록
- [ ] AI 코칭 프롬프트 엔지니어링 (1차)
- [ ] 메모리 관리 (대화 히스토리, 사용자 진도)

### Phase 3: 프론트엔드 UI (0.5주)

- [ ] `features/roadmap/hooks/useStepChat.ts` - SSE 클라이언트 hook
- [ ] `features/roadmap/components/StepChatPanel.tsx` - 채팅 패널
- [ ] `features/roadmap/components/TimelineStepItem.tsx` - 버튼 삽입
- [ ] 면책 고지 고정 렌더링

### Phase 4: 통합 테스트 및 QA (0.5주)

- [ ] `tests/api/test_roadmap_chat_stream.py`
- [ ] 할루시네이션 방지 4가지 안전장치 동작 확인
- [ ] SSE 메모리 누수 확인
- [ ] E2E 테스트

**총 기간: 14-18일 (약 2-3주)**

---

## 4. 리스크 평가

### 낮은 리스크 (높은 확신)

| 항목 | 근거 |
|------|------|
| 기존 코드 재사용 (JWT, DB 세션, RAG 파이프라인) | 100% 호환 확인 완료 |
| Roadmap 모델 구조 호환성 | metadata_json으로 확장 가능 |
| 인증 미들웨어 적용 | 기존 get_current_user, get_current_team 그대로 사용 |
| 기존 배포 파이프라인 활용 | Docker, ECR, ECS, CI/CD 자동화 이미 구성 |
| 기술 부채 최소화 | 새로운 외부 라이브러리 불필요, 마이그레이션 리스크 없음 |

### 중간 리스크

| 항목 | 위험 요소 | 대응 방안 |
|------|----------|----------|
| SSE 스트리밍 | 메모리 누수, 브라우저 연결 종료 처리 | 연결 timeout 30초, heartbeat 15초, CancelledError 처리 (섹션 1.3) |
| 메모리/히스토리 관리 | 대화 내용 저장 및 조회 성능 | RoadmapChatThread/Message 별도 테이블 (섹션 1.4), 복합 인덱스 적용 |
| 프롬프트 엔지니어링 | AI 코칭 품질 불확실 | 초안 프롬프트 후 반복 개선, 테스트 유저 피드백 |
| 할루시네이션 | 법령명/조문번호 생성 위험 | 4가지 안전장치 적용 (섹션 1.5): 팩트-지능 분리, 출처 강제 인용, 범위 외 거부, 면책 고지 |

### 해당 없는 리스크

- LLM이나 모델 아키텍처 변경 불필요
- 기존 API 호환성 유지 (신규 엔드포인트만 추가)

---

*본 문서는 기술 아키텍처 상세 설계와 기술적 실현 가능성 검증 보고서를 통합한 문서입니다.*
*벤치마크 분석, 브레인스토밍 합의, 코드베이스 실사를 기반으로 작성되었습니다.*
*코드 구조는 실제 구현 시 팀 컨벤션에 따라 조정될 수 있습니다.*
