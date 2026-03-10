# REPORT: LangChain → PydanticAI 마이그레이션 분석 보고서

> 작성일: 2026-03-08
> 프로젝트: StepZero Backend (app-backend)
> 대상: LangChain 의존성 전체 → PydanticAI 대체 가능성 분석

---

## 1. Executive Summary

StepZero 백엔드는 **LangChain 5개 패키지**를 사용하며, **LangGraph는 사용하지 않는다**.
LangChain 사용은 **LLM 호출 래퍼 + 벡터 스토어 어댑터** 수준으로 비교적 얕은 통합이다.

PydanticAI로의 마이그레이션은 **기술적으로 충분히 가능**하며, 코드 간결성·타입 안전성·유지보수성 측면에서 개선이 기대된다. 단, 벡터 스토어(PGVector)와 텍스트 스플리터는 PydanticAI 범위 밖이므로 별도 대체 전략이 필요하다.

**권장 결론: 마이그레이션 진행 (3 Phase, 약 3~5일)**

---

## 2. 현재 LangChain 의존성 분석

### 2.1 pyproject.toml 의존성

```toml
"langchain>=0.1.0",
"langchain-openai>=0.0.5",
"langchain-core>=0.1.20",
"langchain-community>=0.0.20",
"langchain-postgres>=0.0.3",
```

5개 패키지 → 이들의 전이 의존성까지 포함하면 **수십 개의 하위 패키지**가 설치된다.

### 2.2 LangGraph 사용 여부

**사용하지 않음.** pyproject.toml에도 없고, 코드에서도 import하지 않는다.
멀티스텝 워크플로우는 Python 순수 코드(서비스 컴포지션, async/await)로 구현되어 있다.

### 2.3 LangChain Import 전수 조사

| Import | 사용 클래스/함수 | 사용 파일 수 |
|--------|-----------------|-------------|
| `langchain_openai` | `ChatOpenAI`, `OpenAIEmbeddings` | 7 |
| `langchain_core.prompts` | `ChatPromptTemplate` | 2 |
| `langchain_core.output_parsers` | `StrOutputParser`, `JsonOutputParser` | 2 |
| `langchain_core.runnables` | `RunnablePassthrough` | 1 |
| `langchain_core.messages` | `AIMessage`, `HumanMessage`, `SystemMessage` | 1 |
| `langchain_core.documents` | `Document` | 2 |
| `langchain_postgres` | `PGVector` | 2 |
| `langchain_text_splitters` | `RecursiveCharacterTextSplitter` | 2 |

**총 고유 Import: 11개 클래스, 13개 파일에서 사용**

---

## 3. 파일별 LangChain 사용 상세 분석

### 3.1 핵심 서비스 (6개 파일)

#### ① `app/features/rag/application/rag_service.py` — 핵심, LCEL 체인 사용

```python
# 사용: ChatOpenAI, OpenAIEmbeddings, PGVector, ChatPromptTemplate,
#       StrOutputParser, RunnablePassthrough
self.chain = (
    {"context": self.retriever | format_docs_with_metadata,
     "question": RunnablePassthrough()}
    | self.prompt | self.llm | StrOutputParser()
)
```

- **유일한 LCEL 체인** — 프로젝트 내 가장 깊은 LangChain 통합
- PGVector `.as_retriever()` → similarity search (k=5)
- `run_in_threadpool`로 동기 invoke 실행
- **마이그레이션 영향: 높음** (체인 해체 + 벡터 검색 분리 필요)

#### ② `app/features/chat/application/chat_service.py` — SSE 스트리밍

```python
# 사용: ChatOpenAI, AIMessage, HumanMessage, SystemMessage
self._llm = ChatOpenAI(model=..., api_key=..., timeout=20, max_retries=2)
messages = [SystemMessage(content=...), HumanMessage(content=...)]
async for chunk in self._llm.astream(messages):
    token = chunk.content if isinstance(chunk, AIMessage) else ""
```

- `astream()` 비동기 토큰 스트리밍
- 메시지 타입 3종 사용 (SystemMessage, HumanMessage, AIMessage)
- **마이그레이션 영향: 중간** (스트리밍 패턴 변경 필요)

#### ③ `app/features/roadmaps/application/llm_personalizer.py` — 로드맵 개인화

```python
# 사용: ChatOpenAI (주입받음)
response = await run_in_threadpool(self.llm.invoke, messages)
raw_text = response.content
# 수동 JSON 파싱 + hallucination repair
```

- ChatOpenAI를 DI로 주입받아 invoke() 호출
- LangChain 기능 거의 미사용 — 수동 JSON 파싱, 자체 검증/복구 로직
- **마이그레이션 영향: 낮음** (output_type으로 대폭 간소화 가능)

#### ④ `app/services/law_etl.py` — 법률 문서 ETL

```python
# 사용: ChatOpenAI, ChatPromptTemplate, JsonOutputParser
chain = self.prompt | self.llm | self.parser
result = await run_in_threadpool(chain.invoke, {...})
```

- 3단계 체인: 프롬프트 → LLM → JSON 파서
- `JsonOutputParser(pydantic_object=ProcessedLawData)` — Pydantic 모델 기반 파싱
- **마이그레이션 영향: 낮음** (PydanticAI의 핵심 장점 영역)

#### ⑤ `app/services/vector_store.py` — 벡터 임베딩/저장

```python
# 사용: OpenAIEmbeddings, RecursiveCharacterTextSplitter, Document, PGVector
chunks = self.splitter.split_text(content)
documents.append(Document(page_content=chunk, metadata=metadata))
vector_store = PGVector(embeddings=..., collection_name=..., connection=...)
vector_store.add_documents(documents)
```

- 텍스트 청킹 + 임베딩 + PGVector 저장 파이프라인
- LangChain의 `Document` 타입에 의존
- **마이그레이션 영향: 높음** (PGVector + Document 타입 대체 필요)

#### ⑥ `app/features/rag/application/semantic_router.py` — 의도 분류

```python
# 사용: OpenAIEmbeddings
embeddings = await self.embeddings.aembed_documents(texts)
query_embedding = await self.embeddings.aembed_query(query)
```

- OpenAIEmbeddings만 사용 (임베딩 생성 + 코사인 유사도)
- 나머지는 numpy 기반 순수 Python 로직
- **마이그레이션 영향: 낮음** (openai SDK 직접 호출로 대체)

### 3.2 의존성 주입 (2개 파일)

#### ⑦ `app/features/roadmaps/application/deps.py`

```python
from langchain_openai import ChatOpenAI
ChatOpenAI(model="gpt-4-turbo-preview", timeout=30, max_retries=2)
```

#### ⑧ `app/features/rag/application/deps.py`

```python
from langchain_openai import OpenAIEmbeddings
OpenAIEmbeddings(model=..., api_key=...)
```

- 둘 다 LangChain 클래스 인스턴스화 팩토리
- **마이그레이션 영향: 낮음** (초기화 코드 교체)

### 3.3 스크립트 (3개 파일)

| 파일 | 사용 | 영향 |
|------|------|------|
| `scripts/seed_rag_vectors.py` | Document, RecursiveCharacterTextSplitter, PGVector | 중간 |
| `scripts/eval/run_evaluation.py` | ChatOpenAI (평가 judge) | 낮음 |
| `scripts/eval/generate_golden_dataset.py` | ChatOpenAI, OpenAIEmbeddings, PGVector | 낮음 |

### 3.4 기타

| 파일 | 관련 | 영향 |
|------|------|------|
| `alembic/env.py` | langchain_pg_* 테이블 autogenerate 제외 | 유지 필요 |
| `scripts/backup_law_vectors.py` | SQLAlchemy로 langchain_pg_* 테이블 직접 조회 | 스키마 변경 시 수정 필요 |

---

## 4. PydanticAI 대체 가능성 매핑

### 4.1 직접 대체 가능 (PydanticAI 내장)

| LangChain 컴포넌트 | PydanticAI 대체 | 개선점 |
|---|---|---|
| `ChatOpenAI(model=...)` | `Agent(model="openai:gpt-4o")` | 모델 교체 1줄, 타입 안전 |
| `ChatPromptTemplate` | `Agent(system_prompt=...)` 또는 f-string | 불필요한 추상화 제거 |
| `JsonOutputParser(pydantic_object=X)` | `Agent(output_type=X)` | **네이티브 Pydantic 검증**, 파싱 실패 시 자동 재시도 |
| `StrOutputParser` | `Agent(output_type=str)` 기본값 | 불필요해짐 |
| `RunnablePassthrough` | 직접 파라미터 전달 | LCEL 불필요 |
| `AIMessage/HumanMessage/SystemMessage` | PydanticAI 내부 메시지 처리 | 수동 메시지 구성 불필요 |
| `ChatOpenAI.astream()` | `agent.run_stream()` | 스트리밍 + 검증 동시 가능 |
| `ChatOpenAI.invoke()` | `agent.run()` (async 기본) | `run_in_threadpool` 불필요 |

### 4.2 별도 대체 필요 (PydanticAI 범위 밖)

| LangChain 컴포넌트 | 대체 방안 | 비고 |
|---|---|---|
| `PGVector` (langchain-postgres) | **Option A:** `pgvector-python` + `asyncpg` 직접 사용 | 프로젝트가 이미 asyncpg 사용 중 |
| | **Option B:** `langchain-postgres` 단독 유지 | 최소 변경, 하이브리드 |
| `RecursiveCharacterTextSplitter` | **Option A:** `langchain-text-splitters` 단독 유지 | 경량, 다른 LangChain 의존 없음 |
| | **Option B:** 자체 구현 (100줄 미만) | 완전한 LangChain 탈피 |
| `Document` | `dataclass` 또는 Pydantic BaseModel로 교체 | 간단한 데이터 컨테이너 |
| `OpenAIEmbeddings` | `openai.AsyncOpenAI().embeddings.create()` 직접 호출 | 프로젝트가 이미 openai SDK 의존 |

### 4.3 대체 불필요 (미사용)

- LangGraph (미사용)
- LangChain Agents/Tools (미사용)
- LangChain Memory (미사용)
- LangChain Document Loaders (미사용)

---

## 5. 마이그레이션 전략 (3 Phase)

### Phase 1: LLM 호출 계층 전환 (영향: 높음, 위험: 낮음)

**대상 파일:** 6개
**예상 소요:** 1~2일

#### 5.1.1 law_etl.py — 구조화된 출력의 교과서적 전환

**Before (LangChain):**
```python
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0, api_key=...)
prompt = ChatPromptTemplate.from_messages([("system", "..."), ("human", "{content}")])
parser = JsonOutputParser(pydantic_object=ProcessedLawData)
chain = prompt | llm | parser
result = await run_in_threadpool(chain.invoke, {"category": ..., "title": ..., "content": ...})
```

**After (PydanticAI):**
```python
from pydantic_ai import Agent

class ProcessedLawOutput(BaseModel):
    """JsonOutputParser 대체 — 네이티브 Pydantic 검증"""
    title: str
    summary: str
    guide_text: str
    law_reference: str
    category: str

law_etl_agent = Agent(
    model="openai:gpt-4-turbo-preview",
    output_type=ProcessedLawOutput,
    system_prompt="You are a legal expert assistant for startup founders...",
    model_settings={"temperature": 0},
)

result = await law_etl_agent.run(
    f"Category: {category}\nTitle: {title}\nRaw Content:\n{content}"
)
processed = result.output  # ProcessedLawOutput 타입, IDE 자동완성 지원
```

**개선점:**
- `JsonOutputParser` + 수동 `result.get()` 패턴 제거
- 파싱 실패 시 PydanticAI가 자동 재시도 (LangChain은 예외 발생)
- `run_in_threadpool` 불필요 (PydanticAI는 기본 async)

#### 5.1.2 llm_personalizer.py — 가장 큰 개선 효과

**Before:**
```python
from langchain_openai import ChatOpenAI

response = await run_in_threadpool(self.llm.invoke, messages)
raw_text = response.content
parsed = self._parse_json_array(raw_text)  # 수동 JSON 파싱 50줄
details = self._convert_to_details(parsed)  # 수동 변환 25줄
```

**After:**
```python
from pydantic_ai import Agent

class RoadmapStepOutput(BaseModel):
    phase: str
    title: str
    objective: str
    estimated_days: int
    checklist: list[str]
    legal_basis: list[LegalBasisItem]
    documents: list[DocumentItem]
    risk_notes: list[str]
    actionkit_items: list[int]

personalizer_agent = Agent(
    model="openai:gpt-4-turbo-preview",
    output_type=list[RoadmapStepOutput],  # list 타입 직접 지원
    system_prompt=_SYSTEM_PROMPT,
)

result = await personalizer_agent.run(user_prompt)
details = result.output  # list[RoadmapStepOutput] — 파싱/변환 코드 75줄 제거
```

**개선점:**
- `_parse_json_array()` (30줄) + `_convert_to_details()` (25줄) + `ensure_string()` 등 **~75줄 삭제**
- JSON 파싱 실패 자동 복구 (PydanticAI의 retry with validation feedback)
- 타입 안전한 출력 → `_validate_and_repair_references()`의 dict 접근도 typed 속성으로 변경 가능

#### 5.1.3 chat_service.py — SSE 스트리밍 전환

**Before:**
```python
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
async for chunk in self._llm.astream(messages):
    token = chunk.content if isinstance(chunk, AIMessage) else ""
```

**After (Option A — PydanticAI 스트리밍):**
```python
from pydantic_ai import Agent

chat_agent = Agent(model="openai:gpt-4o", system_prompt=system_prompt)

async with chat_agent.run_stream(user_message) as stream:
    async for text in stream.stream_text(delta=True):
        tokens.append(text)
        yield _sse_event("token", {"token": text})
```

**After (Option B — openai SDK 직접 스트리밍, 더 간단):**
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=...)
stream = await client.chat.completions.create(
    model="gpt-4o", stream=True,
    messages=[{"role": "system", "content": system_prompt},
              {"role": "user", "content": user_message}],
)
async for chunk in stream:
    delta = chunk.choices[0].delta.content or ""
    if delta:
        tokens.append(delta)
        yield _sse_event("token", {"token": delta})
```

**권장:** Option A (PydanticAI) — 일관성 유지, 향후 structured streaming 확장 가능

#### 5.1.4 rag_service.py — LCEL 체인 해체

**Before:**
```python
self.chain = (
    {"context": self.retriever | format_docs_with_metadata,
     "question": RunnablePassthrough()}
    | self.prompt | self.llm | StrOutputParser()
)
answer = await run_in_threadpool(self.chain.invoke, question)
```

**After:**
```python
from pydantic_ai import Agent

rag_agent = Agent(
    model="openai:gpt-4o",
    system_prompt=RAG_SYSTEM_PROMPT_TEMPLATE,  # {context}, {question} 플레이스홀더
)

async def query(self, question: str) -> str:
    # 1. 검색 (PGVector 직접 또는 래퍼)
    docs, _ = await self.retrieve(question)
    context = format_docs_with_metadata(docs)

    # 2. LLM 호출
    result = await rag_agent.run(
        f"[컨텍스트]\n{context}\n\n[질문]\n{question}"
    )
    return result.output
```

**개선점:**
- LCEL 체인 해체 → 명시적 2단계 (검색 → 생성)
- `run_in_threadpool` 제거 (PydanticAI 네이티브 async)
- 검색/생성 사이에 로직 삽입 용이 (re-ranking, 필터링 등)

#### 5.1.5 deps.py 파일들

```python
# Before
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
llm = ChatOpenAI(model="gpt-4-turbo-preview", timeout=30, max_retries=2)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=...)

# After
from pydantic_ai import Agent
from openai import AsyncOpenAI

openai_client = AsyncOpenAI(api_key=..., timeout=30, max_retries=2)
# Agent는 각 서비스에서 직접 생성하거나 공유 인스턴스 사용
```

### Phase 2: 벡터 스토어 + 임베딩 전환 (영향: 중간, 위험: 중간)

**대상 파일:** 4개
**예상 소요:** 1~2일

#### 5.2.1 OpenAIEmbeddings → openai SDK 직접 호출

```python
# Before (LangChain)
from langchain_openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=...)
vecs = await embeddings.aembed_documents(texts)
query_vec = await embeddings.aembed_query(query)

# After (openai SDK)
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key=...)

async def embed_texts(texts: list[str]) -> list[list[float]]:
    response = await client.embeddings.create(
        model="text-embedding-3-small", input=texts
    )
    return [item.embedding for item in response.data]

async def embed_query(query: str) -> list[float]:
    response = await client.embeddings.create(
        model="text-embedding-3-small", input=[query]
    )
    return response.data[0].embedding
```

#### 5.2.2 PGVector — 두 가지 선택지

**Option A: `langchain-postgres` 유지 (권장, Phase 2)**

- PGVector는 langchain-postgres 패키지에 있지만, LangChain 코어와 독립적
- `langchain-postgres` 단독 유지 → `langchain`, `langchain-core`, `langchain-openai`, `langchain-community` 제거 가능
- 기존 `langchain_pg_collection`, `langchain_pg_embedding` 테이블 스키마 유지
- **장점:** DB 마이그레이션 불필요, 최소 변경
- **단점:** langchain 의존 완전 제거 불가

**Option B: asyncpg + pgvector 직접 사용 (Phase 3 선택적)**

```python
# 직접 벡터 검색
async def similarity_search(query_embedding: list[float], k: int = 5):
    async with get_session() as session:
        result = await session.execute(
            text("""
                SELECT document, cmetadata,
                       embedding <=> :query_vec AS distance
                FROM langchain_pg_embedding
                WHERE collection_id = :collection_id
                ORDER BY embedding <=> :query_vec
                LIMIT :k
            """),
            {"query_vec": str(query_embedding), "collection_id": ..., "k": k}
        )
        return result.fetchall()
```

- **장점:** LangChain 완전 제거, async 네이티브, 쿼리 최적화 가능
- **단점:** 기존 langchain_pg_* 스키마 맞춤 쿼리 필요, 또는 자체 테이블 설계 필요

#### 5.2.3 RecursiveCharacterTextSplitter — 대체 방안

**Option A: `langchain-text-splitters` 단독 유지 (권장)**
- 독립 패키지, LangChain 코어 불필요
- `pip install langchain-text-splitters` 하나만 유지

**Option B: 자체 구현**
```python
class TextSplitter:
    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100,
                 separators: list[str] | None = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ".", " "]

    def split_text(self, text: str) -> list[str]:
        chunks = self._split_recursive(text, self.separators)
        return self._merge_chunks(chunks)

    def _split_recursive(self, text: str, separators: list[str]) -> list[str]:
        if not text: return []
        if len(text) <= self.chunk_size: return [text]

        sep = separators[0] if separators else ""
        remaining_seps = separators[1:] if len(separators) > 1 else []

        parts = text.split(sep) if sep else list(text)
        result = []
        for part in parts:
            if len(part) > self.chunk_size and remaining_seps:
                result.extend(self._split_recursive(part, remaining_seps))
            else:
                result.append(part)
        return result

    def _merge_chunks(self, splits: list[str]) -> list[str]:
        chunks, current = [], ""
        for split in splits:
            if len(current) + len(split) > self.chunk_size:
                if current: chunks.append(current.strip())
                # Overlap: 이전 청크 끝부분 유지
                current = current[-self.chunk_overlap:] + split if self.chunk_overlap else split
            else:
                current += split
        if current: chunks.append(current.strip())
        return chunks
```

#### 5.2.4 Document → Pydantic BaseModel

```python
# Before
from langchain_core.documents import Document
doc = Document(page_content=chunk, metadata=metadata)

# After
from pydantic import BaseModel

class VectorDocument(BaseModel):
    content: str
    metadata: dict
```

### Phase 3: 스크립트 + 평가 전환 (영향: 낮음, 위험: 낮음)

**대상 파일:** 3개
**예상 소요:** 0.5~1일

- `seed_rag_vectors.py` — Phase 2 결과에 따라 Document/PGVector 교체
- `run_evaluation.py` — ChatOpenAI → PydanticAI Agent 교체
- `generate_golden_dataset.py` — ChatOpenAI + OpenAIEmbeddings 교체

---

## 6. 의존성 변경 요약

### Before (pyproject.toml)
```toml
"langchain>=0.1.0",
"langchain-openai>=0.0.5",
"langchain-core>=0.1.20",
"langchain-community>=0.0.20",
"langchain-postgres>=0.0.3",
```

### After — Option A (하이브리드, 권장)
```toml
"pydantic-ai>=1.0.0",         # LLM Agent 프레임워크
"langchain-postgres>=0.0.3",   # PGVector 어댑터 유지
"langchain-text-splitters>=0.0.1",  # 텍스트 청킹 유지
# langchain, langchain-core, langchain-openai, langchain-community 제거
```

### After — Option B (완전 제거)
```toml
"pydantic-ai>=1.0.0",         # LLM Agent 프레임워크
"pgvector>=0.2.0",            # 이미 의존 중, 직접 사용
# LangChain 관련 패키지 전부 제거
```

---

## 7. 위험 분석 및 완화 전략

### 7.1 높은 위험

| 위험 | 영향 | 완화 |
|------|------|------|
| RAG 체인 해체 시 검색 품질 저하 | RAG 응답 정확도 | 마이그레이션 전후 Tier 2 평가 비교 실행 |
| PGVector 스키마 호환성 | 기존 벡터 데이터 손실 | Option A(유지) 우선, 데이터 백업 필수 |
| SSE 스트리밍 동작 변경 | 프론트엔드 채팅 UX | 브라우저 테스트 + 토큰 단위 비교 |

### 7.2 중간 위험

| 위험 | 영향 | 완화 |
|------|------|------|
| PydanticAI output_type 검증 실패 | LLM 응답 파싱 | retry 메커니즘 활용, 기존 fallback 로직 유지 |
| openai SDK 직접 사용 시 에러 핸들링 | 런타임 안정성 | 기존 graceful degradation 패턴 보존 |
| 전이 의존성 충돌 | 빌드 실패 | `uv lock` 검증, CI 확인 |

### 7.3 낮은 위험

| 위험 | 영향 | 완화 |
|------|------|------|
| API 호환성 (PydanticAI v1 안정) | 장기 유지보수 | V1 stable API, 하위 호환 보장 |
| 팀원 학습 곡선 | 개발 속도 | PydanticAI가 더 단순, 학습 비용 낮음 |

---

## 8. 마이그레이션 이점 정량 분석

### 8.1 코드량 변화 (추정)

| 영역 | Before (줄) | After (줄) | 변화 |
|------|------------|-----------|------|
| law_etl.py LLM 호출 | 40 | 15 | -62% |
| llm_personalizer.py 파싱/변환 | 85 | 10 | -88% |
| rag_service.py 체인 | 50 | 25 | -50% |
| chat_service.py 메시지/스트리밍 | 35 | 20 | -43% |
| deps.py (2개) | 30 | 15 | -50% |
| **합계** | **~240** | **~85** | **-65%** |

### 8.2 의존성 변화

| 항목 | Before | After (Option A) | After (Option B) |
|------|--------|-----------------|-----------------|
| LangChain 패키지 수 | 5 | 2 | 0 |
| 전이 의존성 (추정) | ~40 | ~10 | ~5 |
| 전체 설치 크기 (추정) | ~200MB | ~60MB | ~30MB |

### 8.3 품질 개선

- **타입 안전성:** `result.output`이 Pydantic 모델 타입 → IDE 자동완성, mypy 검증
- **에러 복구:** PydanticAI의 자동 retry + validation feedback (LangChain JsonOutputParser는 1회 시도 후 예외)
- **async 네이티브:** `run_in_threadpool` 래퍼 제거 (현재 5곳에서 사용)
- **디버깅:** PydanticAI Logfire 통합 지원 (옵션)

---

## 9. 마이그레이션 실행 체크리스트

### Phase 1 (LLM 계층)
- [ ] `pydantic-ai` 의존성 추가, 버전 확인
- [ ] `law_etl.py` — Agent + output_type 전환
- [ ] `llm_personalizer.py` — Agent + list[RoadmapStepOutput] 전환
- [ ] `chat_service.py` — Agent.run_stream() 전환
- [ ] `rag_service.py` — LCEL 체인 해체, Agent 전환
- [ ] `semantic_router.py` — openai SDK 직접 임베딩
- [ ] `deps.py` 2개 — 팩토리 업데이트
- [ ] 기존 pytest 전체 통과 확인
- [ ] Tier 2 RAG 평가 실행 (before/after 비교)

### Phase 2 (벡터 스토어)
- [ ] `langchain-postgres` 유지 여부 결정
- [ ] `OpenAIEmbeddings` → openai SDK 직접 호출 전환
- [ ] `Document` → VectorDocument BaseModel 전환
- [ ] `vector_store.py` 업데이트
- [ ] `seed_rag_vectors.py` 업데이트
- [ ] 벡터 데이터 백업 (`backup_law_vectors.py` 실행)
- [ ] langchain, langchain-core, langchain-openai, langchain-community 제거
- [ ] `uv sync` + 전체 테스트

### Phase 3 (스크립트 + 정리)
- [ ] `run_evaluation.py` — Agent 전환
- [ ] `generate_golden_dataset.py` — Agent + openai SDK 전환
- [ ] `alembic/env.py` — langchain_pg_* 제외 로직 유지 확인
- [ ] pyproject.toml 최종 정리
- [ ] CI 빌드/테스트 통과
- [ ] 프론트엔드 E2E 채팅 테스트

---

## 10. 결론 및 권장사항

### 10.1 마이그레이션 적합성: ⭐⭐⭐⭐⭐ (매우 높음)

StepZero의 LangChain 사용은 **얕은 통합** 수준이다:
- LCEL 체인 1개, Agent/Tool 미사용, Memory 미사용, LangGraph 미사용
- 주로 `ChatOpenAI` 래퍼 + `PGVector` 어댑터로 사용
- 대부분의 비즈니스 로직은 순수 Python으로 구현됨

이는 PydanticAI의 **"less is more"** 철학과 정확히 일치한다.

### 10.2 권장 접근

1. **Phase 1 먼저 실행** — LLM 호출 계층만 전환 (위험 낮음, 효과 높음)
2. **Phase 2는 Phase 1 안정화 후** — 벡터 스토어는 하이브리드(Option A) 우선
3. **Phase 3은 선택적** — 완전한 LangChain 제거는 ROI 대비 판단

### 10.3 예상 효과

- **코드 -65%** (LLM 관련 코드)
- **의존성 -60~100%** (LangChain 패키지)
- **타입 안전성 대폭 향상** (IDE + mypy 지원)
- **async 성능 개선** (`run_in_threadpool` 5곳 제거)
- **유지보수성 향상** (LangChain 버전 업데이트 추적 부담 제거)
