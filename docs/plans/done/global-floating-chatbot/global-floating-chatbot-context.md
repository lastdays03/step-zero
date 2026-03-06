# Global Floating Chatbot - Context & Dependencies

> Last Updated: 2026-02-23
> **Status: COMPLETE - 모든 Phase(1~4) 구현 및 브라우저 검증 완료. 커밋 미완료.**

## Implementation State

### 현재 상태: 구현 완료, 커밋 대기
- Phase 1~4 모두 완료
- 브라우저 테스트(Playwright) 통과
- TypeScript 타입 체크 통과 (기존 PostCard.tsx 에러만 존재, 챗봇 무관)
- **git commit이 아직 안 된 상태** - 모든 변경사항이 unstaged

### Git 변경 파일 목록
```
Modified:
  app-backend/app/api/v1/rag/router.py        # POST /chat 엔드포인트 추가
  app-backend/app/api/v1/schemas.py            # ChatRequest/ChatResponse 스키마
  app-backend/app/features/rag/application/deps.py  # get_chat_service() DI
  app-frontend/src/app/layout.tsx              # GlobalChatbot 배치
  app-frontend/src/features/dashboard/components/DashboardView.tsx  # 챗봇 코드 제거

New:
  app-backend/app/features/rag/application/chat_service.py  # ChatService
  app-frontend/src/features/chatbot/           # 전체 챗봇 모듈 (11개 파일)
```

---

## Key Files

### Backend - 수정/생성 완료
| 파일 | 작업 | 비고 |
|------|------|------|
| `app-backend/app/api/v1/schemas.py` | ChatRequest/ChatResponse 추가 | 기존 RagQuery 스키마 유지 |
| `app-backend/app/features/rag/application/chat_service.py` | **새 파일** | RagService 래핑, 키워드 분류 |
| `app-backend/app/features/rag/application/deps.py` | get_chat_service() 추가 | lru_cache 패턴 |
| `app-backend/app/api/v1/rag/router.py` | POST /chat 엔드포인트 추가 | 인증 불필요 |

### Frontend - 새 파일 (전부 생성 완료)
| 파일 | 역할 |
|------|------|
| `app-frontend/src/features/chatbot/index.ts` | barrel exports |
| `app-frontend/src/features/chatbot/types/chat.ts` | ChatMessage 타입 |
| `app-frontend/src/features/chatbot/hooks/useChatbot.ts` | 핵심 상태/API 훅 |
| `app-frontend/src/features/chatbot/utils/renderAnswerLine.tsx` | URL 감지 유틸 |
| `app-frontend/src/features/chatbot/components/GlobalChatbot.tsx` | 컨테이너 |
| `app-frontend/src/features/chatbot/components/ChatFAB.tsx` | 플로팅 버튼 |
| `app-frontend/src/features/chatbot/components/ChatPanel.tsx` | 슬라이드 패널 |
| `app-frontend/src/features/chatbot/components/ChatMessageList.tsx` | 메시지 목록 |
| `app-frontend/src/features/chatbot/components/ChatBubble.tsx` | 메시지 버블 |
| `app-frontend/src/features/chatbot/components/ChatInput.tsx` | 입력 영역 |
| `app-frontend/src/features/chatbot/components/index.ts` | 컴포넌트 barrel |

### Frontend - 수정 완료
| 파일 | 작업 |
|------|------|
| `app-frontend/src/app/layout.tsx` | GlobalChatbot import 및 배치 (AuthProvider 내부, 양쪽 분기 모두) |
| `app-frontend/src/features/dashboard/components/DashboardView.tsx` | 챗봇 코드 완전 제거 (FAB, Dialog, 상태 5개, handleAskLegal, renderAnswerLine, 불필요 import) |

---

## Key Decisions (구현 중 확정)

### 1. 질문 분류 방식: 키워드 기반
- **키워드:** 법, 허가, 등록, 신고, 인가, 규정, 법률, 법령, 조례, 면허, 신청, 영업, 위생
- `frozenset`으로 O(1) 조회

### 2. 대화 이력: React state (세션 내 유지)
- 페이지 이동 시 유지 (Root Layout의 state이므로)
- 새로고침 시 초기화

### 3. Root Layout 배치
- `AuthProvider` 내부, `{children}` 아래에 `<GlobalChatbot />`
- GoogleOAuthProvider 분기 양쪽 모두에 추가

### 4. RefObject 타입 호환성 해결
- React 19 + 기존 @types/react 버전 차이로 `RefObject<HTMLDivElement | null>` 타입 에러 발생
- `Ref<HTMLDivElement>`로 변경하여 해결 (ChatMessageList, ChatPanel)

### 5. ChatService의 general chain
- `ChatPromptTemplate.from_messages()` + `ainvoke()` (비동기) 사용
- RagService의 `run_in_threadpool` 패턴과 달리 LangChain 네이티브 async 사용

---

## Browser Test Results (Playwright)

| 검증 항목 | 결과 |
|-----------|------|
| 일반 질의 분류 | PASS - "스타트업 창업 절차" → general |
| 법률 질의 분류 | PASS - "음식점 영업 허가 신청" → legal_rag |
| 전역 FAB 표시 | PASS - 대시보드, 로드맵 페이지 |
| 패널 토글 | PASS - Sparkles/X 아이콘 전환 |
| 대화 이력 유지 | PASS - 닫기/열기, 페이지 이동 후 |
| 대화 초기화 | PASS - 빈 상태 복원 |
| 모바일 반응형 | PASS - 375px 풀너비 패널 |
| 로딩 상태 | PASS - 타이핑 인디케이터, 입력 비활성화 |
| 콘솔 에러 | PASS - 챗봇 관련 0건 |
| 기존 /query 하위호환 | PASS - curl 200 OK |

---

## Next Steps

1. **git commit** - 변경사항 커밋 (사용자 요청 시)
2. **기존 빌드 에러 수정** - `PostCard.tsx:43` author_id 에러 (챗봇 무관, 기존 이슈)
3. **향후 개선 고려사항:**
   - Rate limiting (비인증 API 남용 방지)
   - GlobalChatbot lazy import (번들 최적화)
   - LLM 기반 질문 분류 업그레이드
   - 대화 이력 DB 저장

---

## Dependencies (모두 기존 설치됨, 신규 패키지 없음)

### 백엔드
- `langchain`, `langchain-openai`, `langchain-core`, `openai`, `pgvector`

### 프론트엔드
- `axios`, `lucide-react` (Sparkles, X, Send, Loader2, Bot, Trash2), `tailwindcss-animate`

### 환경 변수 (기존)
- `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `NEXT_PUBLIC_API_BASE_URL`

---

## API Contract

### POST /api/v1/rag/chat (신규)
```json
Request:  { "message": "음식점 창업 시 위생 허가 절차는?" }
Response: { "answer": "...", "source": "legal_rag" }  // or "general"
```
- 인증: 불필요
- 에러: 503

### POST /api/v1/rag/query (기존 유지)
```json
Request:  { "question": "..." }
Response: { "answer": "..." }
```
