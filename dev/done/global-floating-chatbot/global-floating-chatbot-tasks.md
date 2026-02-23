# Global Floating Chatbot - Task Checklist

> Last Updated: 2026-02-23

## Phase 1: Backend - 하이브리드 Chat 엔드포인트

- [x] **1-1** ChatRequest/ChatResponse 스키마 추가 `[S]`
  - 파일: `app-backend/app/api/v1/schemas.py`
  - AC: 스키마 정의 완료, 기존 RagQuery 영향 없음

- [x] **1-2** ChatService 생성 `[L]`
  - 파일: `app-backend/app/features/rag/application/chat_service.py` (새 파일)
  - AC: 키워드 분류 동작, 법률→RAG / 일반→LLM 분기 확인

- [x] **1-3** DI 등록 (get_chat_service) `[S]`
  - 파일: `app-backend/app/features/rag/application/deps.py`
  - AC: lru_cache 싱글턴 등록 확인

- [x] **1-4** POST /chat 엔드포인트 추가 `[S]`
  - 파일: `app-backend/app/api/v1/rag/router.py`
  - AC: curl 법률/일반 질의 올바른 source 반환, 기존 /query 정상

---

## Phase 2: Frontend - 챗봇 컴포넌트 모듈

- [x] **2-1** 폴더 구조 + barrel exports 생성 `[S]`
- [x] **2-2** ChatMessage 타입 정의 `[S]`
- [x] **2-3** renderAnswerLine 유틸리티 추출 `[S]`
- [x] **2-4** useChatbot 핵심 훅 `[M]`
- [x] **2-5** ChatFAB 컴포넌트 `[S]`
- [x] **2-6** ChatBubble 컴포넌트 `[S]`
- [x] **2-7** ChatMessageList 컴포넌트 `[S]`
- [x] **2-8** ChatInput 컴포넌트 `[S]`
- [x] **2-9** ChatPanel 컴포넌트 `[M]`
- [x] **2-10** GlobalChatbot 컨테이너 `[S]`

---

## Phase 3: Integration & Cleanup

- [x] **3-1** Root Layout에 GlobalChatbot 배치 `[S]`
- [x] **3-2** DashboardView 챗봇 코드 제거 `[M]`

---

## Phase 4: Polish & Verification

- [x] **4-1** 모바일 반응형 테스트 `[M]`
  - 결과: 모바일(375px) 풀너비 패널 정상, MobileNav 위에 z-50 표시, FAB 아이콘 전환 정상

- [x] **4-2** 에러/로딩 상태 검증 `[S]`
  - 결과: 콘솔 에러 0건 (favicon.ico 404만 기존 이슈), 타이핑 인디케이터 정상, 입력 비활성화 정상

- [x] **4-3** End-to-End 검증 `[M]`
  - [x] 일반 질의 → source: "general" (일반 AI) 정상
  - [x] 법률 질의 (영업/허가/신청 키워드) → source: "legal_rag" (법률 RAG) 정상
  - [x] 전역 표시: 대시보드, 로드맵 페이지 모두 FAB 표시
  - [x] 세션 유지: 패널 닫기/열기, 페이지 이동 후 대화 이력 유지
  - [x] 대화 초기화: 휴지통 버튼 클릭 시 빈 상태로 복원
  - [x] 하위호환: POST /api/v1/rag/query 정상 동작 (curl 200 OK)
  - [x] 네트워크: POST /api/v1/rag/chat 200 OK 확인
