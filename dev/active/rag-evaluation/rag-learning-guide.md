# RAG 기초부터 평가까지 - 학습 가이드

> Last Updated: 2026-02-24
> 대상: RAG를 처음 구축하는 개발자
> 목표: StepZero 프로젝트의 RAG 코드를 완전히 이해하고, 왜 그렇게 만들었는지, 어떻게 개선하는지 판단할 수 있는 수준

---

## 목차

1. [LLM의 한계와 RAG가 필요한 이유](#1-llm의-한계와-rag가-필요한-이유)
2. [RAG 전체 구조 한눈에 보기](#2-rag-전체-구조-한눈에-보기)
3. [임베딩(Embedding) 이해하기](#3-임베딩embedding-이해하기)
4. [벡터 데이터베이스 이해하기](#4-벡터-데이터베이스-이해하기)
5. [문서 전처리와 청킹(Chunking)](#5-문서-전처리와-청킹chunking)
6. [검색(Retrieval) 전략](#6-검색retrieval-전략)
7. [프롬프트와 생성(Generation)](#7-프롬프트와-생성generation)
8. [LangChain 체인 구조 읽는 법](#8-langchain-체인-구조-읽는-법)
9. [RAG 평가 메트릭 완전 정복](#9-rag-평가-메트릭-완전-정복)
10. [우리 코드와 1:1 대응 해설](#10-우리-코드와-11-대응-해설)
11. [자주 묻는 질문 (FAQ)](#11-자주-묻는-질문-faq)
12. [추천 학습 자료](#12-추천-학습-자료)

---

## 1. LLM의 한계와 RAG가 필요한 이유

### LLM만으로는 안 되는 이유

ChatGPT 같은 LLM은 학습 데이터에 포함된 정보만 알고 있다. 문제가 되는 상황:

| 문제 | 예시 | 결과 |
|---|---|---|
| **지식 마감일** | "2025년 개정된 식품위생법은?" | 학습 이후 정보라 모름 |
| **사내 데이터** | "우리 회사 취업규칙은?" | 학습 데이터에 없음 |
| **환각(Hallucination)** | "식품위생법 제127조는?" | 없는 조항을 그럴듯하게 지어냄 |
| **출처 부재** | "이 답변의 근거는?" | 어디서 왔는지 알 수 없음 |

### RAG의 핵심 아이디어

> "LLM에게 시험 볼 때 참고 자료(오픈북)를 주자"

```
일반 LLM:
  질문 → [LLM의 기억만으로 답변] → 답변 (환각 위험)

RAG:
  질문 → [관련 문서를 찾아서] → [문서와 함께 LLM에게 전달] → 답변 (근거 있음)
```

비유하자면:
- **일반 LLM** = 교과서 없이 시험 보기 (기억에만 의존)
- **RAG** = 오픈북 시험 (교과서를 찾아보고 답 쓰기)

### 우리 프로젝트에서 RAG가 필요한 이유

StepZero는 한국 스타트업 창업자를 위한 법률 가이드 챗봇이다.
- 한국 식품위생법, 상법 등 **한국 법률 특수 지식** 필요
- 법률 내용은 **자주 개정**되어 LLM 학습 데이터와 불일치 가능
- 법률 답변에서 **환각은 치명적** (잘못된 법적 조언)
- **출처 제시**가 필수 ("식품위생법 제37조에 따르면...")

---

## 2. RAG 전체 구조 한눈에 보기

RAG는 크게 **두 단계**로 나뉜다:

### (A) 인덱싱 단계 (Indexing) - 사전 준비, 한 번만

```
┌─────────────────────────────────────────────────────────────┐
│                    인덱싱 (오프라인, 한 번)                    │
│                                                              │
│  [법률 PDF/MD 파일들]                                        │
│        │                                                     │
│        ▼                                                     │
│  ① 문서 로드 (law_fetcher.py)                               │
│     PDF → 텍스트 추출 (pdfplumber)                           │
│        │                                                     │
│        ▼                                                     │
│  ② ETL 변환 (law_etl.py)                                    │
│     원본 법률 텍스트 → 창업자 친화적 가이드                    │
│     (gpt-4-turbo-preview가 변환)                              │
│        │                                                     │
│        ▼                                                     │
│  ③ 임베딩 (vector_store.py)                                  │
│     텍스트 → 숫자 벡터 (text-embedding-3-small)              │
│        │                                                     │
│        ▼                                                     │
│  ④ 저장 (PostgreSQL + pgvector)                              │
│     벡터 + 원본 텍스트 + 메타데이터 저장                      │
└─────────────────────────────────────────────────────────────┘
```

### (B) 쿼리 단계 (Querying) - 사용자 질문마다 실행

```
┌─────────────────────────────────────────────────────────────┐
│                    쿼리 (온라인, 매 질문)                     │
│                                                              │
│  [사용자 질문: "영업신고는 어디서 해요?"]                     │
│        │                                                     │
│        ▼                                                     │
│  ① 질문 임베딩                                              │
│     "영업신고는 어디서 해요?" → [0.023, -0.157, 0.089, ...]   │
│        │                                                     │
│        ▼                                                     │
│  ② 유사도 검색 (pgvector)                                    │
│     질문 벡터와 가장 가까운 문서 3개 검색                     │
│        │                                                     │
│        ▼                                                     │
│  ③ 프롬프트 조립                                             │
│     "다음 컨텍스트를 기반으로 답하세요:                       │
│      [검색된 문서 3개]                                        │
│      질문: 영업신고는 어디서 해요?"                           │
│        │                                                     │
│        ▼                                                     │
│  ④ LLM 생성 (gpt-4o-mini)                                   │
│     "관할 시·군·구청에 영업신고를 해야 합니다..."             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 임베딩(Embedding) 이해하기

### 임베딩이란?

텍스트를 **숫자 배열(벡터)**로 바꾸는 것이다. 이 벡터는 텍스트의 **의미**를 숫자로 표현한다.

```
"영업신고"    → [0.023, -0.157, 0.089, ..., 0.042]  (1536차원)
"영업허가"    → [0.021, -0.148, 0.091, ..., 0.039]  (비슷한 벡터!)
"양자역학"    → [-0.312, 0.204, -0.067, ..., 0.188]  (매우 다른 벡터)
```

**핵심**: 의미가 비슷한 텍스트는 벡터도 비슷하다 → 벡터 간 거리를 재면 의미적 유사도를 알 수 있다.

### 우리가 쓰는 임베딩 모델

```python
# rag_service.py:23-26
self.embeddings = OpenAIEmbeddings(
    model=settings.OPENAI_EMBED_MODEL,  # "text-embedding-3-small"
    api_key=settings.OPENAI_API_KEY,
)
```

| 모델 | 차원 수 | 최대 토큰 | 비용 | 특징 |
|---|---|---|---|---|
| `text-embedding-3-small` | 1536 | 8,191 | $0.02/1M 토큰 | 가성비 좋음, 우리가 사용 |
| `text-embedding-3-large` | 3072 | 8,191 | $0.13/1M 토큰 | 더 정확하지만 비쌈 |
| `text-embedding-ada-002` | 1536 | 8,191 | $0.10/1M 토큰 | 구세대, 사용하지 말 것 |

**왜 small을 선택했나?**: 비용이 large의 1/6이면서 성능 차이가 크지 않아 시작 단계에 적합.

### 토큰이란?

LLM과 임베딩 모델은 텍스트를 **토큰** 단위로 처리한다.

```
한국어 대략적 환산:
  한국어 1글자 ≈ 1~3 토큰
  "식품위생법" (5글자) ≈ 약 5~8 토큰
  "8,191 토큰" ≈ 한국어 약 3,000~5,000자
```

**주의**: 우리 시스템은 문서를 통째로 임베딩하는데, 문서가 8,191 토큰을 넘으면 **잘린다**. 이게 청킹이 필요한 이유 중 하나.

---

## 4. 벡터 데이터베이스 이해하기

### 벡터 DB의 역할

일반 DB는 `WHERE name = '식품위생법'` 같은 **정확한 매칭**을 한다.
벡터 DB는 "이 벡터와 **가장 비슷한** 벡터 3개를 찾아줘" 같은 **유사도 검색**을 한다.

```
일반 DB:   "영업" 검색 → "영업" 단어가 정확히 있는 행만 반환
벡터 DB:   "영업" 벡터 검색 → "영업신고", "영업허가", "사업등록" 등 의미 유사한 것도 반환
```

### pgvector (우리가 사용)

PostgreSQL에 벡터 검색 기능을 추가하는 **확장(extension)**이다.

```python
# vector_store.py:71-76
vector_store = PGVector(
    embeddings=self.embeddings,          # 임베딩 모델
    collection_name=self.collection_name, # "law_vectors" (테이블명과 유사)
    connection=self.db_url,               # PostgreSQL 접속 정보
    use_jsonb=True,                       # 메타데이터를 JSONB로 저장
)
```

실제 DB에 저장되는 것:

| id | embedding (벡터) | document (원본 텍스트) | cmetadata (메타데이터) |
|---|---|---|---|
| 1 | [0.023, -0.157, ...] | "휴게음식점 영업신고\n\n..." | {"title": "...", "category": "휴게음식점"} |
| 2 | [0.045, -0.089, ...] | "일반음식점 영업허가\n\n..." | {"title": "...", "category": "일반음식점"} |

### 다른 벡터 DB 선택지

| 이름 | 특징 | 비유 |
|---|---|---|
| **pgvector** | PostgreSQL 확장, 별도 DB 불필요 | 기존 집에 방 하나 추가 (우리 선택) |
| **Chroma** | 가벼운 인메모리 DB | 간이 창고, 프로토타입에 좋음 |
| **Pinecone** | 클라우드 전용 관리형 | 풀옵션 물류센터, 비용 있음 |
| **Weaviate** | 오픈소스, 기능 풍부 | 대형 자체 물류센터 |
| **FAISS** | Facebook 라이브러리, 로컬 전용 | 초고속 인메모리 검색, 서버 내장 |

**pgvector를 선택한 이유**: 이미 PostgreSQL을 쓰고 있으므로 별도 인프라 없이 벡터 검색 추가 가능.

---

## 5. 문서 전처리와 청킹(Chunking)

### 청킹이란?

긴 문서를 **작은 조각(chunk)**으로 나누는 것이다.

```
[10페이지 법률 PDF]
        │
        ▼  청킹
[조각1: 제1조~제5조] [조각2: 제6조~제10조] [조각3: 제11조~제15조] ...
```

### 왜 청킹이 필요한가?

**비유**: 도서관에서 책을 찾는 상황

- **청킹 없음** = 도서관에 책이 10권 있고, 질문과 가장 관련 있는 **책 전체**를 3권 빌려줌
  - 문제: 해당 조항은 책의 한 페이지에 있는데 책 전체를 다 읽어야 함
  - 문제: 임베딩이 책 **전체**의 평균 의미를 표현 → 특정 조항 검색 정밀도 저하

- **청킹 있음** = 각 책을 챕터별로 분리해서 100개 챕터가 있고, 가장 관련 있는 **챕터** 3개를 빌려줌
  - 장점: 딱 필요한 부분만 찾을 수 있음
  - 장점: 임베딩이 해당 챕터의 의미를 정확히 표현

### 우리 시스템의 현재 상태: 청킹 없음

```python
# vector_store.py:60-64
doc = Document(
    page_content=f"{item.title}\n\n{item.guide_text}\n\n[Reference]\n{item.law_reference}",
    # ↑ 문서 전체를 1개 Document로 저장 (청킹 없음)
    metadata=metadata
)
```

**현재 방식의 문제점**:
1. 문서가 길면 임베딩 토큰 한도(8,191) 초과 → 뒷부분 손실
2. 한 문서에 여러 주제가 있으면 임베딩이 평균화 → 검색 정밀도 하락
3. LLM에 전달되는 컨텍스트가 너무 길면 핵심 정보를 놓칠 수 있음

### 청킹 전략 종류

| 전략 | 방식 | 장점 | 단점 |
|---|---|---|---|
| **고정 크기** | 1000자마다 자르기 | 단순, 예측 가능 | 문장 중간에서 잘릴 수 있음 |
| **재귀 분할** | 문단→문장→단어 순으로 분할 | 의미 단위 보존 | 설정 필요 |
| **의미 기반** | 임베딩 유사도 변화 지점에서 분할 | 가장 정확 | 느리고 비쌈 |
| **구조 기반** | 제1조, 제2조 등 법률 구조로 분할 | 법률 도메인에 최적 | 도메인 의존 |

**향후 개선 시 추천**: `RecursiveCharacterTextSplitter` (재귀 분할)

```python
# 개선 예시 (아직 미적용)
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,    # 각 조각 최대 1000자
    chunk_overlap=200,  # 조각 간 200자 겹침 (문맥 유지)
    separators=["\n\n", "\n", ".", " "]  # 분할 우선순위
)
chunks = splitter.split_documents(documents)
```

**chunk_overlap은 왜 필요한가?**

```
원본: "제37조 ① 영업을 하려면 신고해야 한다. ② 신고 기한은 영업 개시 3일 전이다."

overlap 없이:
  조각1: "제37조 ① 영업을 하려면 신고해야"  (잘림)
  조각2: "한다. ② 신고 기한은 영업 개시 3일 전이다."  (앞문맥 없음)

overlap 있으면:
  조각1: "제37조 ① 영업을 하려면 신고해야 한다. ② 신고 기한은"
  조각2: "신고해야 한다. ② 신고 기한은 영업 개시 3일 전이다."
  → 겹치는 부분이 있어서 문맥 유지!
```

---

## 6. 검색(Retrieval) 전략

### 유사도 검색 (우리가 사용)

질문 벡터와 저장된 문서 벡터 사이의 **코사인 유사도(cosine similarity)**를 계산하여 가장 비슷한 k개를 반환.

```python
# rag_service.py:36
self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
# → 가장 유사한 문서 3개 반환
```

**코사인 유사도란?**: 두 벡터가 가리키는 방향이 얼마나 비슷한지 측정. -1(정반대)~1(동일).

```
"영업신고 방법"과 "영업신고 절차"  → 유사도 0.95 (매우 유사)
"영업신고 방법"과 "법인 설립"      → 유사도 0.45 (약간 관련)
"영업신고 방법"과 "양자역학"       → 유사도 0.05 (무관)
```

### 다른 검색 전략들

#### (1) MMR (Maximal Marginal Relevance)

**문제**: 유사도만으로 검색하면 비슷한 문서 3개가 올 수 있음
**해결**: 관련성도 높으면서 서로 **다양한** 문서를 선택

```
유사도 검색:  [영업신고-가이드1(0.95), 영업신고-가이드2(0.93), 영업신고-FAQ(0.91)]
              → 비슷한 내용 3개, 다양성 부족

MMR 검색:     [영업신고-가이드1(0.95), 영업신고-처벌(0.82), 영업신고-서류(0.78)]
              → 관련 있으면서 서로 다른 관점
```

```python
# MMR 적용 예시 (아직 미적용)
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 3, "fetch_k": 10, "lambda_mult": 0.7}
    # fetch_k: 후보 10개 가져온 뒤, 다양성 고려해 3개 선택
    # lambda_mult: 0=최대 다양성, 1=최대 관련성 (0.7은 관련성 우선)
)
```

#### (2) Hybrid Search (키워드 + 의미)

**문제**: 의미 검색만으로는 "제37조"같은 정확한 키워드 매칭이 약함
**해결**: 전통적 키워드 검색(BM25)과 의미 검색을 결합

```
질문: "식품위생법 제37조"

의미 검색만: [식품 안전 가이드, 위생 관리 방법, ...] → "제37조" 못 찾을 수 있음
키워드 검색만: [제37조 포함 문서들] → 의미는 무시
하이브리드: 두 결과를 합쳐서 최적 선택 → "제37조"도 찾고 의미도 고려
```

#### (3) Reranking (재순위화)

**문제**: 임베딩 기반 검색은 대략적 유사도만 측정
**해결**: 후보 문서를 가져온 뒤, 더 정교한 모델로 재평가

```
1단계: 빠른 벡터 검색 → 후보 20개
2단계: Cross-encoder (또는 Cohere reranker) → 상위 3개 재선택
```

비유: 서류 전형(빠르지만 대략적)으로 20명 뽑고, 면접(느리지만 정확)으로 3명 최종 선발.

---

## 7. 프롬프트와 생성(Generation)

### RAG 프롬프트의 구조

RAG 프롬프트의 핵심은 **"이 자료만 보고 답해라"**는 제약이다.

```python
# rag_service.py:44-55
self.prompt = ChatPromptTemplate.from_template("""
    You are an AI assistant for startup founders in Korea.
    Answer the question based ONLY on the following context.
    If the answer is not in the context, say "제공된 법령 문서에서는 해당 정보를 찾을 수 없습니다."

    Context:
    {context}        ← 검색된 문서 3개가 여기 들어감

    Question: {question}  ← 사용자 질문

    Answer (in Korean):
""")
```

### 프롬프트의 각 부분이 하는 역할

| 부분 | 목적 | 우리 코드 |
|---|---|---|
| **역할 지정** | LLM에게 전문가 페르소나 부여 | "AI assistant for startup founders" |
| **제약 조건** | 컨텍스트만 사용하도록 강제 (환각 방지) | "based ONLY on the following context" |
| **거부 지시** | 모를 때 솔직하게 모른다고 답하게 | "If the answer is not in the context, say..." |
| **컨텍스트 삽입** | 검색된 문서를 여기 넣음 | `{context}` |
| **질문 삽입** | 사용자 질문 원문 | `{question}` |
| **출력 지시** | 한국어로 답변 | "Answer (in Korean)" |

### 현재 프롬프트의 개선 포인트

1. **영어 프롬프트**: "You are an AI assistant..." → 한국어 법률 용어 정확성에 영향 가능
2. **Few-shot 없음**: 예시 Q&A를 보여주면 답변 형식이 일관됨
3. **출처 지시 없음**: "관련 법령을 인용하시오" 같은 지시가 없음

```
개선 예시 (아직 미적용):

당신은 한국 스타트업 창업자를 위한 법률 전문 AI입니다.
아래 참고 자료만을 근거로 답변하세요.

규칙:
- 참고 자료에 없는 내용은 답하지 마세요
- 관련 법령명과 조항을 반드시 인용하세요
- 한국어로 답변하세요

예시:
Q: 영업신고 기한은?
A: 식품위생법 시행규칙에 따르면, 영업 개시 전에 관할 관청에 신고해야 합니다.

참고 자료:
{context}

질문: {question}
답변:
```

---

## 8. LangChain 체인 구조 읽는 법

### 파이프(`|`) 연산자

LangChain에서 `|`는 "이 결과를 다음 단계의 입력으로 넘겨라"는 뜻이다.

```python
# rag_service.py:62-67
self.chain = (
    {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
    | self.prompt
    | self.llm
    | StrOutputParser()
)
```

이것을 단계별로 풀어보면:

```
사용자 입력: "영업신고는 어디서 해요?"
        │
        ▼
┌─ 단계 1: 입력 분배 ─────────────────────────────────────────┐
│                                                              │
│  "context" ← self.retriever | format_docs                    │
│    1) retriever가 질문으로 유사 문서 3개 검색                  │
│    2) format_docs가 3개 문서를 하나의 텍스트로 합침            │
│    → "휴게음식점 영업신고\n\n...\n\n일반음식점 영업허가\n\n..." │
│                                                              │
│  "question" ← RunnablePassthrough()                          │
│    → 입력 그대로 통과: "영업신고는 어디서 해요?"               │
│                                                              │
│  결과: {"context": "문서 3개 텍스트", "question": "원래 질문"} │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
┌─ 단계 2: 프롬프트 조립 ─────────────────────────────────────┐
│  self.prompt                                                 │
│  → {context}와 {question}에 값을 채워 완성된 프롬프트 생성    │
│  → "You are an AI assistant... Context: [문서들] Question:..." │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
┌─ 단계 3: LLM 호출 ─────────────────────────────────────────┐
│  self.llm (gpt-4o-mini)                                      │
│  → 프롬프트를 받아 답변 생성                                  │
│  → AIMessage(content="관할 시·군·구청에 영업신고를...")         │
└──────────────────────────────────────────────────────────────┘
        │
        ▼
┌─ 단계 4: 문자열 추출 ──────────────────────────────────────┐
│  StrOutputParser()                                           │
│  → AIMessage 객체에서 .content 문자열만 꺼냄                  │
│  → "관할 시·군·구청에 영업신고를 해야 합니다..."               │
└──────────────────────────────────────────────────────────────┘
```

### ETL 체인도 같은 패턴

```python
# law_etl.py:67
chain = self.prompt | self.llm | self.parser
# prompt: 법률 텍스트를 가이드로 변환해달라는 지시
# llm: gpt-4-turbo-preview가 변환 실행
# parser: JSON 결과를 Python dict로 파싱
```

---

## 9. RAG 평가 메트릭 완전 정복

### 왜 평가가 필요한가?

RAG는 **여러 단계**가 연결된 파이프라인이다. 최종 답변이 나쁠 때 **어디가 문제**인지 알아야 고칠 수 있다.

```
검색이 잘못됨?  → 엉뚱한 문서를 가져옴         → 검색 메트릭 확인
생성이 잘못됨?  → 문서는 맞는데 답을 잘못 씀    → 생성 메트릭 확인
둘 다?          → 문서도 틀리고 답도 틀림         → E2E 메트릭 확인
```

### 비유로 이해하는 핵심 메트릭

도서관에서 시험 답안을 작성하는 학생에 비유:

| 메트릭 | 비유 | 질문 |
|---|---|---|
| **Hit Rate** | "도서관에서 관련 책을 찾았나?" | 3권 중 1권이라도 관련 있음? |
| **Context Precision** | "빌린 3권 중 실제로 쓸모있는 건 몇 권?" | 3권 다 관련? 1권만? |
| **Context Recall** | "정답에 필요한 정보가 빌린 책에 다 있나?" | 빠진 정보 없이 다 포함? |
| **Faithfulness** | "책에 있는 내용만 답안에 썼나?" | 본인 생각(환각) 안 섞었나? |
| **Answer Relevancy** | "질문에 대한 답을 썼나?" | 엉뚱한 답 아닌가? |
| **Answer Correctness** | "답안이 정답과 일치하나?" | 실제 정답과 비교 |

### 메트릭 상세 해설

#### (1) Hit Rate@K (검색 적중률)

```
질문: "영업신고 기한은?"
검색된 문서 3개:
  [1] 영업신고 관련 가이드  ← 관련 있음!
  [2] 위생 교육 안내        ← 관련 없음
  [3] 음식점 시설 기준      ← 관련 없음

Hit Rate = 관련 문서가 1개 이상 있으므로 → 1 (적중!)
```

**계산**: 질문 N개 중 관련 문서가 Top-K에 1개 이상 있는 질문 수 / N

**이 수치가 낮으면**: 벡터 검색 자체가 실패. 임베딩 모델 변경이나 청킹 도입 필요.

#### (2) Faithfulness (충실도, 환각 방지)

**가장 중요한 메트릭**. 답변이 검색된 컨텍스트에 근거하는지 측정.

```
검색된 컨텍스트: "식품위생법에 따라 영업 개시 전 관할 관청에 신고해야 한다."

답변 A (높은 Faithfulness):
  "식품위생법에 따라 영업 개시 전에 관할 관청에 신고해야 합니다."
  → 컨텍스트에 있는 내용만 사용 ✓

답변 B (낮은 Faithfulness):
  "영업 개시 7일 전까지 신고해야 하며, 위반 시 500만원 벌금입니다."
  → "7일 전", "500만원 벌금"은 컨텍스트에 없음 = 환각! ✗
```

**측정 방법 (LLM-as-Judge)**:
1. 답변을 개별 주장(claim)으로 분리
2. 각 주장이 컨텍스트에 의해 뒷받침되는지 LLM이 판단
3. 비율 = 뒷받침 주장 수 / 전체 주장 수

#### (3) Answer Relevancy (답변 관련성)

답변이 질문에 실제로 응답하는지 측정.

```
질문: "영업신고는 어디서 하나요?"

답변 A (높은 Relevancy):
  "관할 시·군·구청에 영업신고를 하시면 됩니다." → 질문에 직접 답변 ✓

답변 B (낮은 Relevancy):
  "영업신고에는 건강진단서와 교육이수증이 필요합니다."
  → 관련은 있지만 "어디서"에 답하지 않음 ✗
```

#### (4) Answer Correctness (답변 정확도)

골든 데이터셋의 정답(ground truth)과 RAG 답변을 비교.

```
질문: "법인세 신고 기한은?"
정답: "사업연도 종료 후 3개월 이내"
RAG 답변: "사업연도 종료일로부터 3개월 이내에 신고해야 합니다."
→ 핵심 사실 일치 → 점수 3/3

RAG 답변: "2개월 이내에 신고해야 합니다."
→ 기한 오류 → 점수 0/3
```

### Faithfulness vs Relevancy vs Correctness 관계

```
                   Faithfulness 높음          Faithfulness 낮음
                ┌────────────────────────┬────────────────────────┐
Relevancy 높음  │ 최상: 컨텍스트 근거,     │ 위험: 질문에 잘 답하나   │
                │ 질문에도 잘 답함         │ 환각이 섞여 있음         │
                │ → 이상적 상태           │ → 프롬프트 강화 필요     │
                ├────────────────────────┼────────────────────────┤
Relevancy 낮음  │ 검색 문제: 컨텍스트     │ 최악: 질문과 무관하고     │
                │ 내용은 맞지만 질문과     │ 환각까지 있음             │
                │ 다른 부분을 답함         │ → 전체 파이프라인 점검   │
                │ → 검색 전략 개선 필요    │                          │
                └────────────────────────┴────────────────────────┘
```

### LLM-as-Judge란?

평가도 LLM에게 맡기는 것이다. 사람이 100개 답변을 일일이 채점하는 대신, GPT-4o에게 채점을 시킨다.

```
프롬프트:
  "다음 답변이 컨텍스트에만 근거하는지 0.0~1.0으로 평가하세요.
   컨텍스트: [검색된 문서]
   답변: [RAG 답변]
   숫자만 응답:"

GPT-4o 응답: "0.85"
```

**장점**: 의미적 판단 가능, 한국어도 잘 처리, 확장성 좋음
**단점**: 비용 발생, 완벽하지 않음 (사람과 80~85% 일치), 자기 편향(자기 답변에 후한 점수)

---

## 10. 우리 코드와 1:1 대응 해설

### 전체 데이터 흐름과 코드 매핑

```
[법률 PDF 파일]
     │
     │  law_fetcher.py - LocalFileSource
     │  └ pdfplumber로 텍스트 추출
     │  └ 디렉토리명에서 카테고리 추출
     ▼
[LawData 객체]  ← title, category, content_body
     │
     │  law_etl.py - LawETLProcessor
     │  └ gpt-4-turbo-preview가 법률 텍스트 → 가이드로 변환
     │  └ JSON 출력 → ProcessedLawData 파싱
     ▼
[ProcessedLawData]  ← title, summary, guide_text, law_reference
     │
     │  vector_store.py - VectorStoreService
     │  └ Document(page_content=title+guide+reference, metadata=...)
     │  └ text-embedding-3-small로 임베딩
     │  └ pgvector에 저장
     ▼
[PostgreSQL law_vectors 테이블]  ← embedding + document + metadata
     │
     │  === 여기부터 쿼리 단계 ===
     │
[사용자 질문 수신]  ← POST /api/v1/rag/chat
     │
     │  chat_service.py - classify_query()
     │  └ 키워드 13개 체크: 법, 허가, 등록, 신고...
     │  └ "legal" → RAG 파이프라인
     │  └ "general" → 일반 LLM
     ▼
[RagService.query()]
     │
     │  rag_service.py - self.chain.invoke()
     │  ├ retriever: 질문 임베딩 → pgvector 유사도 검색 → Top-3 문서
     │  ├ format_docs: 문서 3개를 하나의 텍스트로 결합
     │  ├ prompt: 컨텍스트 + 질문을 프롬프트 템플릿에 삽입
     │  ├ llm: gpt-4o-mini가 답변 생성
     │  └ parser: 문자열 추출
     ▼
[답변 반환]  ← {"answer": "...", "source": "legal_rag"}
```

### 각 파일의 핵심 라인 해설

#### `rag_service.py` - 심장

```python
# 23-26행: 임베딩 모델 초기화
self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small", ...)
# → 모든 텍스트를 1536차원 벡터로 변환하는 도구

# 30-35행: 벡터 DB 연결
self.vector_store = PGVector(
    embeddings=self.embeddings,       # 위에서 만든 임베딩 모델
    collection_name="law_vectors",     # PostgreSQL 테이블
    connection=sync_db_url,           # DB 접속 정보
    use_jsonb=True,                   # 메타데이터를 JSONB로 저장
)

# 36행: 검색기 생성 (이 한 줄이 "검색" 전략의 전부)
self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
# → 유사도 기준 상위 3개 문서 반환

# 62-67행: 체인 조립 (이 한 블록이 RAG의 핵심 로직)
self.chain = (
    {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
    | self.prompt
    | self.llm
    | StrOutputParser()
)
```

#### `chat_service.py` - 교통 정리

```python
# 14-30행: 법률 키워드 목록
LEGAL_KEYWORDS = frozenset(["법", "허가", "등록", ...])
# → 이 키워드가 질문에 있으면 RAG으로 라우팅

# 39-43행: 분류 함수 (단 5줄로 구현)
def classify_query(message: str) -> Literal["legal", "general"]:
    for keyword in LEGAL_KEYWORDS:
        if keyword in message:  # 단순 포함 체크
            return "legal"
    return "general"
# → "4대보험 의무?"는 키워드 없어서 general로 감 (한계)

# 74-79행: 라우팅 실행
async def chat(self, message: str):
    source = classify_query(message)
    if source == "legal":
        answer = await self.rag_service.query(message)  # RAG 파이프라인
        return answer, "legal_rag"
    # else: 일반 LLM으로...
```

---

## 11. 자주 묻는 질문 (FAQ)

### Q: 임베딩 모델을 바꾸면 기존 벡터를 다시 만들어야 하나?

**A: 네.** 임베딩 모델마다 벡터 차원과 의미 표현이 다르다. 모델을 바꾸면 모든 문서를 새 모델로 다시 임베딩해야 한다. 질문 벡터와 문서 벡터는 **같은 모델**로 만들어야 유사도 비교가 의미 있다.

### Q: k=3이면 항상 3개 문서를 가져오나?

**A: 네.** 관련 없어도 3개를 가져온다. pgvector는 "관련성 임계값" 같은 필터가 기본 적용되지 않는다. 그래서 무관한 문서가 섞일 수 있고, 이를 걸러내려면 **score threshold** 설정이나 **reranking**이 필요하다.

### Q: RAG이 "모른다"고 답하는 건 어떻게 작동하나?

**A**: 프롬프트에 명시적으로 지시하고 있다:
```
If the answer is not in the context, say "제공된 법령 문서에서는 해당 정보를 찾을 수 없습니다."
```
하지만 실제로 LLM이 항상 이 지시를 따르지는 않는다. 특히 질문이 일반적일수록 LLM이 자체 지식으로 답하려는 경향이 있다. 이것이 **Faithfulness 메트릭**을 측정해야 하는 이유이다.

### Q: 평가 메트릭 중 가장 중요한 건?

**A**: 법률 도메인에서는 **Faithfulness**(환각 방지)가 가장 중요하다.
- 틀린 법률 정보 제공은 사용자에게 실질적 피해를 줄 수 있음
- "모르겠습니다"가 "틀린 답"보다 항상 나음
- 그 다음으로 Hit Rate (검색 실패하면 나머지 다 무의미)

### Q: RAGAS와 우리가 만든 Custom Judge의 차이는?

**A**:
- **RAGAS**: 학술 표준 프레임워크. claim-level 분석으로 정교하지만, 라이브러리 의존성이 무겁고 breaking change 잦음
- **Custom Judge**: 우리 도메인(한국 법률)에 특화된 프롬프트. 가볍고 제어 가능. 법률 용어, 조항 인용 등 도메인 특수 평가 가능
- 둘 다 사용하되 Custom Judge를 주력으로, RAGAS는 교차 검증용

### Q: 골든 데이터셋은 몇 개가 적당한가?

**A**: 단계별로:
- **첫 시작**: 20~30개 (현재 20개) - 파이프라인 검증용
- **안정화**: 50~100개 - 통계적으로 의미 있는 패턴 발견
- **프로덕션**: 100~200개 - 카테고리/난이도별 충분한 커버리지
- 핵심은 개수보다 **다양성**. factual/procedural/interpretive/edge case 골고루.

### Q: temperature=0이면 같은 질문에 항상 같은 답이 나오나?

**A**: 거의 같지만 100% 동일하지는 않다. OpenAI API는 temperature=0에서도 미세한 변동이 있을 수 있다. 평가의 재현성을 위해 temperature=0을 사용하되, 완벽한 재현은 기대하지 않는 것이 좋다.

---

## 12. 추천 학습 자료

### 입문 (개념 잡기)

| 자료 | 형태 | 핵심 내용 | 링크 키워드 |
|---|---|---|---|
| LangChain RAG Tutorial | 공식 문서 | RAG 기초부터 구현까지 | `langchain rag tutorial` 검색 |
| LCEL (LangChain Expression Language) | 공식 문서 | 파이프(`\|`) 연산자, 체인 구성 | `langchain lcel` 검색 |
| OpenAI Embedding Guide | 공식 문서 | 임베딩 개념, 모델 비교 | `openai embeddings guide` 검색 |
| pgvector GitHub README | GitHub | pgvector 설치/사용법 | `pgvector/pgvector` GitHub |

### 중급 (심화)

| 자료 | 형태 | 핵심 내용 |
|---|---|---|
| LangChain: Text Splitters | 공식 문서 | 청킹 전략 총정리 |
| Pinecone: Chunking Strategies | 블로그 | 청킹의 Why/How 상세 설명 |
| LangChain: Retrievers | 공식 문서 | 검색 전략 (MMR, Ensemble, Parent Document 등) |
| RAGAS Documentation | 공식 문서 | 평가 메트릭 이론 및 사용법 |

### 고급 (평가/최적화)

| 자료 | 형태 | 핵심 내용 |
|---|---|---|
| RAGAS 논문 (EACL 2024) | 학술 논문 | Faithfulness/Relevancy 측정 이론 |
| Databricks: LLM Eval Best Practices | 블로그 | LLM-as-Judge 실전 가이드 (0-3 스케일 근거) |
| DeepEval Documentation | 공식 문서 | pytest 통합 RAG 평가 |
| TruLens RAG Triad | 블로그 | RAG 평가의 3축 프레임워크 |
| Ko-LongRAG (EMNLP 2025) | 학술 논문 | 한국어 RAG 벤치마크 |

### 실습 추천 순서

```
1주차: 임베딩 체험
  └ OpenAI Embedding API로 텍스트 벡터화 해보기
  └ 두 문장의 코사인 유사도 직접 계산해보기
  └ "영업신고"와 "영업허가"의 유사도 vs "영업신고"와 "양자역학"의 유사도 비교

2주차: 검색 체험
  └ pgvector에 직접 SQL로 유사도 검색 쿼리 날려보기
  └ k를 1, 3, 5, 10으로 바꿔보며 결과 차이 관찰
  └ MMR 검색 결과와 유사도 검색 결과 비교

3주차: 프롬프트 실험
  └ 영어 프롬프트 vs 한국어 프롬프트 답변 품질 비교
  └ few-shot 예시 추가 전/후 답변 형식 비교
  └ "모른다고 답하라" 지시 강화 전/후 환각 비율 비교

4주차: 평가 실습
  └ Tier 1 테스트 실행하고 결과 해석
  └ Tier 2 테스트 실행하고 메트릭별 의미 파악
  └ 점수가 낮은 케이스를 분석하여 원인 추정
```

---

## 용어 사전

| 용어 | 영어 | 설명 |
|---|---|---|
| RAG | Retrieval-Augmented Generation | 검색 증강 생성. 외부 문서를 검색하여 LLM 답변 품질 향상 |
| 임베딩 | Embedding | 텍스트를 의미를 담은 숫자 벡터로 변환하는 것 |
| 벡터 | Vector | 숫자 배열. 예: [0.023, -0.157, 0.089] |
| 코사인 유사도 | Cosine Similarity | 두 벡터의 방향 유사도 (-1~1) |
| 청킹 | Chunking | 긴 문서를 작은 조각으로 나누는 것 |
| 토큰 | Token | LLM이 처리하는 텍스트의 최소 단위 |
| 환각 | Hallucination | LLM이 사실이 아닌 내용을 그럴듯하게 생성하는 현상 |
| 충실도 | Faithfulness | 답변이 제공된 컨텍스트에 근거하는 정도 |
| 골든 데이터셋 | Golden Dataset | 정답이 포함된 평가용 Q&A 모음 |
| Ground Truth | Ground Truth | 평가 기준이 되는 정답 |
| LLM-as-Judge | LLM-as-Judge | LLM을 평가자로 사용하는 방법 |
| MMR | Maximal Marginal Relevance | 관련성과 다양성을 동시에 고려하는 검색 전략 |
| Reranking | Reranking | 1차 검색 결과를 더 정교한 모델로 재순위화 |
| k (Top-K) | Top-K | 검색 결과 중 상위 K개를 사용 |
| BM25 | Best Matching 25 | 전통적 키워드 기반 문서 검색 알고리즘 |
| 하이브리드 검색 | Hybrid Search | 키워드 검색 + 의미 검색을 결합 |
| ETL | Extract, Transform, Load | 데이터 추출-변환-적재 파이프라인 |
| RAGAS | Retrieval Augmented Generation Assessment | RAG 평가 표준 프레임워크 |
