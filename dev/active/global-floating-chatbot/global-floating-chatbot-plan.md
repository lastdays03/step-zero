# Global Floating Chatbot - Implementation Plan

> Last Updated: 2026-02-23

## Executive Summary

대시보드에만 존재하는 법률 AI 챗봇(모달 방식)을 **모든 페이지에서 접근 가능한 플로팅 슬라이드 패널 챗봇**으로 공통화한다. 동시에 백엔드를 법률 RAG 전용에서 **일반 질문도 응답 가능한 하이브리드 방식**으로 확장한다.

## Current State Analysis

### 백엔드
- `POST /api/v1/rag/query` 단일 엔드포인트 (법률 RAG 전용)
- `RagService`: LangChain + PGVector 기반, gpt-4o-mini 사용
- 인증 불필요, stateless 단건 질의

### 프론트엔드
- `DashboardView.tsx`에 챗봇 하드코딩 (FAB 버튼 + Dialog 모달)
- 대시보드 페이지에서만 접근 가능
- 단건 질의 후 응답 표시, 대화 이력 없음

## Proposed Future State

### 백엔드
- `POST /api/v1/rag/chat` 하이브리드 엔드포인트 추가
- 키워드 기반 분류: 법률 질문 → RAG / 일반 질문 → LLM 직접
- 기존 `/query` 하위호환 유지

### 프론트엔드
- `features/chatbot/` 공통 모듈 (7개 컴포넌트 + 훅 + 타입)
- Root Layout에 배치 → 모든 페이지에서 표시
- 우측 하단 슬라이드업 패널 UI
- 세션 내 대화 이력 유지 (새로고침 시 초기화)

---

## Phase 1: Backend - 하이브리드 Chat 엔드포인트

### 1-1. ChatRequest/ChatResponse 스키마 추가
- **파일:** `app-backend/app/api/v1/schemas.py`
- **내용:** `ChatRequest(message: str)`, `ChatResponse(answer: str, source: str)`
- **Effort:** S
- **AC:** 스키마 정의 완료, 기존 Rag 스키마 영향 없음

### 1-2. ChatService 생성
- **새 파일:** `app-backend/app/features/rag/application/chat_service.py`
- **내용:**
  - `RagService` 래핑, 하이브리드 분류
  - 키워드 기반 분류 (법, 허가, 등록, 신고, 인가, 규정, 법률, 법령, 조례, 면허, 신청, 영업, 위생 → legal)
  - Legal → `RagService.query()` / General → `ChatOpenAI` 직접 호출
  - 시스템 프롬프트: 한국 스타트업 파운더를 돕는 AI 어시스턴트
  - 에러 처리: timeout 25s, graceful fallback
- **재사용:** `RagService`, `get_settings()`, `get_logger()`, LangChain 의존성
- **Effort:** L
- **AC:** 법률 질문은 RAG 경로, 일반 질문은 LLM 직접 경로로 분기 확인

### 1-3. DI 등록
- **파일:** `app-backend/app/features/rag/application/deps.py`
- **내용:** `get_chat_service()` (`@lru_cache(maxsize=1)`)
- **Effort:** S
- **Depends:** 1-2
- **AC:** DI 함수 등록, 싱글턴 캐싱 확인

### 1-4. Chat 엔드포인트 추가
- **파일:** `app-backend/app/api/v1/rag/router.py`
- **내용:** `POST /chat` 엔드포인트, 인증 불필요
- **Effort:** S
- **Depends:** 1-1, 1-3
- **AC:** curl 법률/일반 질의 시 올바른 source 반환, 기존 `/query` 정상 동작

---

## Phase 2: Frontend - 챗봇 컴포넌트 모듈

### 2-1. 폴더 구조 생성
```
app-frontend/src/features/chatbot/
├── index.ts
├── types/chat.ts
├── hooks/useChatbot.ts
├── utils/renderAnswerLine.tsx
└── components/
    ├── index.ts
    ├── GlobalChatbot.tsx
    ├── ChatFAB.tsx
    ├── ChatPanel.tsx
    ├── ChatMessageList.tsx
    ├── ChatBubble.tsx
    └── ChatInput.tsx
```
- **Effort:** S
- **AC:** 폴더 + barrel export 파일 생성

### 2-2. ChatMessage 타입 정의
- **파일:** `types/chat.ts`
- **내용:** `id`, `role`, `content`, `source?`, `timestamp`
- **Effort:** S
- **AC:** 타입 export 확인

### 2-3. renderAnswerLine 유틸리티 추출
- **파일:** `utils/renderAnswerLine.tsx`
- **내용:** DashboardView L17-37의 URL 감지 + 링크 렌더링 함수 이동
- **Effort:** S
- **AC:** DashboardView에서 import 경로 변경 후 정상 동작

### 2-4. useChatbot 핵심 훅
- **파일:** `hooks/useChatbot.ts`
- **내용:**
  - 상태: `messages`, `isOpen`, `isLoading`, `error`, `input`
  - API: `apiClient.post("/rag/chat", { message })`
  - 액션: `sendMessage()`, `togglePanel()`, `clearHistory()`
  - 자동 스크롤
- **재사용:** `apiClient` (`app-frontend/src/lib/api-client.ts`)
- **Effort:** M
- **Depends:** 2-2, Phase 1 완료
- **AC:** 메시지 전송/응답 동작, 에러 처리, 비인증 시에도 동작

### 2-5. ChatFAB (플로팅 버튼)
- **파일:** `components/ChatFAB.tsx`
- **내용:** DashboardView L303-315 추출, `fixed bottom-28 md:bottom-8 right-6 md:right-8 z-50`
- 열림: `Sparkles` → `X` 전환, 데스크톱 텍스트 "AI에게 물어보기"
- **재사용:** `Button`, `Sparkles`, `X` (lucide-react)
- **Effort:** S
- **AC:** 버튼 클릭 시 패널 토글, 아이콘 전환 동작

### 2-6. ChatPanel (슬라이드업 패널)
- **파일:** `components/ChatPanel.tsx`
- **내용:**
  - 모바일: `inset-x-0 bottom-0 h-[70vh] pb-28 rounded-t-2xl`
  - 데스크톱: `right-8 bottom-20 w-[400px] h-[600px] max-h-[80vh] rounded-2xl`
  - 애니메이션: `tailwindcss-animate` `animate-in slide-in-from-bottom`
  - 구조: Header → MessageList → Input
- **Effort:** M
- **Depends:** 2-7, 2-8, 2-9
- **AC:** 슬라이드 애니메이션 동작, 모바일/데스크톱 반응형

### 2-7. ChatBubble (메시지 버블)
- **파일:** `components/ChatBubble.tsx`
- **내용:**
  - AI: 좌측, 봇 아이콘, `bg-white border rounded-xl rounded-tl-none`
  - User: 우측, `bg-blue-600 text-white rounded-xl rounded-tr-none`
  - `renderAnswerLine()`으로 URL 자동 링크
- **Effort:** S
- **Depends:** 2-3
- **AC:** 역할별 버블 스타일 분리, URL 자동 링크

### 2-8. ChatMessageList (메시지 목록)
- **파일:** `components/ChatMessageList.tsx`
- **내용:** 스크롤 컨테이너, 타이핑 인디케이터, 자동 스크롤
- **Effort:** S
- **Depends:** 2-7
- **AC:** 메시지 추가 시 자동 스크롤, 로딩 시 타이핑 인디케이터

### 2-9. ChatInput (입력 영역)
- **파일:** `components/ChatInput.tsx`
- **내용:** Enter 전송, Shift+Enter 줄바꿈, 로딩 시 비활성화
- **Effort:** S
- **AC:** 키보드 동작, 전송 버튼 비활성화/스피너

### 2-10. GlobalChatbot (컨테이너)
- **파일:** `components/GlobalChatbot.tsx`
- **내용:** `"use client"`, `useChatbot` 훅 사용, FAB + Panel 조합
- **Effort:** S
- **Depends:** 2-4, 2-5, 2-6
- **AC:** FAB 클릭으로 패널 토글, 전체 채팅 플로우 동작

---

## Phase 3: Integration & Cleanup

### 3-1. Root Layout에 GlobalChatbot 배치
- **파일:** `app-frontend/src/app/layout.tsx`
- **내용:** `<AuthProvider>` 내부, `{children}` 아래에 `<GlobalChatbot />` 추가
- **Effort:** S
- **Depends:** Phase 2 완료
- **AC:** 모든 페이지에서 플로팅 버튼 표시

### 3-2. DashboardView 챗봇 코드 제거
- **파일:** `app-frontend/src/features/dashboard/components/DashboardView.tsx`
- **제거:** URL 유틸(→공유 유틸 import), 챗봇 상태 5개, handleAskLegal, FAB+Dialog 전체, 불필요 import
- **Effort:** M
- **Depends:** 3-1
- **AC:** DashboardView에 챗봇 코드 없음, 대시보드 기능 정상

---

## Phase 4: Polish & Verification

### 4-1. 모바일 반응형 테스트
- MobileNav(z-40) 위에 ChatFAB/Panel(z-50) 정상 표시
- 패널 풀너비, 키보드 열림 시 레이아웃 유지
- **Effort:** M

### 4-2. 에러/로딩 상태 검증
- 네트워크 오류, API 503, 타임아웃 각 시나리오 테스트
- 타이핑 인디케이터, 자동 스크롤 동작
- **Effort:** S

### 4-3. End-to-End 검증
- 검증 항목: 법률 질의(RAG), 일반 질의(LLM), 플로팅 버튼 전역 표시, 대화 이력 세션 유지, 새로고침 초기화, 기존 `/query` 하위호환
- **Effort:** M

---

## Risk Assessment

| 리스크 | 영향 | 완화 |
|--------|------|------|
| 키워드 분류 정확도 부족 | 법률 질문이 일반으로 분류될 수 있음 | 보수적 키워드 세트 + 추후 LLM 분류 업그레이드 가능 |
| 비인증 사용자 API 남용 | OpenAI 비용 증가 | Rate limiting 추후 추가 고려 |
| 모바일 키보드 레이아웃 충돌 | 패널 UI 깨짐 | fixed 포지셔닝으로 대응, 실기기 테스트 |
| Root Layout에 client 컴포넌트 추가 | 번들 사이즈 증가 | GlobalChatbot lazy import 검토 |

## Success Metrics

- 모든 페이지(로그인/대시보드/프로필 등)에서 챗봇 버튼 접근 가능
- 법률 질문은 `source: "legal_rag"`, 일반 질문은 `source: "general"` 분류
- 페이지 이동 시 대화 이력 유지
- 기존 `POST /api/v1/rag/query` 하위호환 100%
- DashboardView에서 챗봇 코드 완전 제거

## z-index 계층

| 요소 | z-index | 위치 |
|------|---------|------|
| Header | z-30 | `(dashboard)/layout.tsx` |
| MobileNav | z-40 | `(dashboard)/layout.tsx` |
| ChatFAB | z-50 | Root layout |
| ChatPanel | z-50 | Root layout |
