# Phase 4: AI 코치 챗봇 MVP — 작업 체크리스트

> **Last Updated**: 2026-03-02
> **Status**: Section A~C 구현 완료 + Critical/Important 수정 완료, Section D 미착수
> **Branch**: `feature/4-ai-coach-chatbot`

---

## Section A: BE 기반 구축 (5.5일) — **완료**

### A-1. DB 모델 생성 (1일) — **완료**

- [x] `app-backend/app/models/roadmap_chat.py` 생성
  - [x] `RoadmapChatThread` 모델 (id, roadmap_id, step_id, user_id, title, message_count, created_at, updated_at)
  - [x] `RoadmapChatMessage` 모델 (id, thread_id, role, content, sources_json, token_count, created_at)
  - [x] FK 제약조건 (roadmaps.id, roadmap_steps.id, users.id, roadmap_chat_threads.id)
  - [x] ondelete 설정 (CASCADE)
  - [x] UniqueConstraint (roadmap_id, step_id, user_id) on threads — C-6/I-3 적용
  - [x] thread_id 인덱스 on messages
- [x] `app-backend/app/models/__init__.py` 수정
  - [x] `from .roadmap_chat import RoadmapChatThread, RoadmapChatMessage` 추가
  - [x] `__all__` 리스트에 추가
- [x] `app-backend/alembic/env.py` 수정
  - [x] `import app.models.roadmap_chat` 추가

### A-2. Alembic 마이그레이션 (0.5일) — **완료**

- [x] `app-backend/alembic/versions/012_roadmap_chat.py` 생성 (번호 012로 확정)
  - [x] depends_on: 011_template_startup_type
  - [x] upgrade: roadmap_chat_threads, roadmap_chat_messages 테이블 생성
  - [x] downgrade: 양 테이블 삭제
  - [x] UniqueConstraint (roadmap_id, step_id, user_id) 포함
- [ ] Docker 환경에서 마이그레이션 실행 검증
  - [ ] `docker compose exec app-backend python -m alembic upgrade head`
  - [ ] `docker compose exec app-backend python -m alembic check` (diff 없음 확인)

### A-3. RoadmapContextBuilder (3일) — **완료**

- [x] `app-backend/app/features/roadmaps/application/context_builder.py` 생성
  - [x] `RoadmapContextBuilder` 클래스
  - [x] `build()` 메서드: 3레이어 조합 + actions 반환 (I-2)
  - [x] `_build_fact_layer()`: 불변 팩트 (업종, 지역, 법령, 서류)
  - [x] `_build_state_layer()`: 실행 상태 (체크리스트 완료/미완료, 위험 요소)
  - [x] `_build_instruction_layer()`: 안내 규칙 (안전장치 5가지 + few-shot) — I-1 적용 (대화 맥락 중복 제거)
  - [x] `_trim_to_budget()`: 토큰 예산 초과 시 트리밍
  - [x] I-5: 미사용 session 파라미터 제거
- [x] RoadmapRepository 기존 메서드 활용
  - [x] `list_step_details([step_id])` 호출 확인
  - [x] `list_step_actions([step_id])` 호출 확인
- [x] 단위 테스트 (`tests/services/test_context_builder.py`)
  - [x] 각 레이어 독립 생성 검증
  - [x] 토큰 예산 트리밍 검증
  - [x] 빈 데이터 (법령 0개, 체크리스트 0개) 처리
  - [x] 안전장치 프롬프트 20건 시나리오

### A-4. SemanticRouter OUT_OF_SCOPE 확장 (0.5일) — **완료**

- [x] `app-backend/app/features/rag/application/semantic_router.py` 수정
  - [x] `out_of_scope` 앵커 카테고리 추가 (10개 문장)
  - [x] `classify()` 메서드: out_of_scope 판정 로직 (threshold 0.75)
  - [x] 기존 ChatService에도 out_of_scope 처리 추가 (I-7)
- [x] 분류 테스트 (`tests/services/test_semantic_router.py`)

### A-5. RoadmapChatRepository (0.5일) — **완료**

- [x] `app-backend/app/repositories/roadmap_chat_repository.py` 생성
  - [x] `get_or_create_thread(roadmap_id, step_id, user_id)` 구현 + IntegrityError 핸들링 (C-6)
  - [x] `get_thread(thread_id)` 구현
  - [x] `list_threads(roadmap_id, step_id, user_id)` 구현 — DB 레벨 필터 (C-4)
  - [x] `add_message(thread_id, role, content, sources_json, token_count)` 구현 — SQL UPDATE 최적화 (I-6)
  - [x] `get_recent_messages(thread_id, limit=10, offset=0)` 구현 — offset 지원 (C-5)
  - [x] `count_messages(thread_id)` 구현
- [x] 단위 테스트 (`tests/repositories/test_roadmap_chat_repository.py`)

---

## Section B: BE 핵심 구현 (7일) — **완료**

### B-1. RoadmapChatService (4일) — **완료**

- [x] `app-backend/app/features/roadmaps/application/roadmap_chat_service.py` 생성
  - [x] `RoadmapChatService` 클래스
  - [x] `__init__()`: ContextBuilder, SemanticRouter, ChatRepo, ChatOpenAI(streaming=True)
  - [x] `stream()` 비동기 제너레이터
    - [x] SemanticRouter OUT_OF_SCOPE 차단
    - [x] user 메시지 DB 저장
    - [x] ContextBuilder.build() 호출 + actions 활용 (I-2)
    - [x] 대화 이력 구성 (_build_chat_messages)
    - [x] ChatOpenAI.astream() 토큰 스트리밍
    - [x] 출처 파싱 (_parse_citations)
    - [x] assistant 메시지 DB 저장
    - [x] SSE 이벤트 yield (token, sources, meta, done)
  - [x] `_build_chat_messages()`: LangChain 메시지 배열 구성
  - [x] `_parse_citations()`: [법령 N], [서류 N] 패턴 파싱
  - [x] asyncio.Queue 기반 하트비트 (15초 간격) — C-2 수정
  - [x] 타임아웃 (30초)
  - [x] `asyncio.CancelledError` 처리 (부분 응답 저장)
  - [x] session.commit() 제너레이터 최종단 이동 — C-3 수정
- [x] 의존성 주입 함수 (`deps.py` — `get_roadmap_chat_service`) — C-1 통합
- [x] SSE 이벤트 헬퍼 (`_sse_event(event_type, data)`)
- [x] 통합 테스트 (`tests/services/test_roadmap_chat_service.py`)

### B-2. SSE 라우터 (2일) — **완료**

- [x] `app-backend/app/api/v1/roadmaps/chat.py` 생성
  - [x] `POST /{roadmap_id}/steps/{step_id}/chat/stream` (SSE 스트리밍)
    - [x] JWT 인증 (get_current_user)
    - [x] Team 권한 (get_current_team)
    - [x] 로드맵 소유권 검증
    - [x] Step 상태 검증 (IN_PROGRESS 또는 COMPLETED)
    - [x] StreamingResponse 반환
    - [x] CORS 헤더 (text/event-stream)
  - [x] `GET /{roadmap_id}/steps/{step_id}/chat/threads` (스레드 목록)
    - [x] 인증 + 권한
    - [x] DB 레벨 user_id 필터 (C-4)
    - [x] ThreadSummary 목록 반환
  - [x] `GET /{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages` (메시지 목록)
    - [x] 인증 + Thread 소유권
    - [x] offset/limit 페이징 (C-5)
    - [x] ChatMessageResponse 목록 반환
- [x] 스키마 정의 (`api/v1/schemas.py`)
  - [x] `StepChatRequest` (message, thread_id)
  - [x] `ThreadSummary` (thread_id, message_count, created_at, updated_at)
  - [x] `ChatMessageResponse` (id, role: Literal, content, sources, created_at) — I-4 적용
- [x] 라우터 등록 (`api/v1/roadmaps/router.py` 수정)
  - [x] `router.include_router(chat_router)` 추가
- [ ] API 테스트
  - [ ] curl로 SSE 스트리밍 확인
  - [ ] 인증 실패 → 401
  - [ ] 소유권 실패 → 403
  - [ ] Step 상태 PENDING → 400

### B-3. 안전장치 시스템 프롬프트 설계 (1일) — **완료**

- [x] 시스템 프롬프트 텍스트 작성
  - [x] LAYER 1 팩트 태그 (`<FACTS>`) 템플릿
  - [x] LAYER 2 상태 태그 (`<STATUS>`) 템플릿
  - [x] LAYER 3 규칙 태그 (`<RULES>`) 내용
    - [x] 팩트-지능 분리 규칙
    - [x] 출처 강제 인용 규칙 + few-shot 예시
    - [x] 범위 제한 규칙
    - [x] 전문가 권고 규칙
    - [x] 불확실성 표현 규칙
- [x] 테스트 시나리오 20건 (test_context_builder.py 내 `TestSafetyGuardPrompts`)

---

## Section C: FE 구현 (8일) — **완료**

### C-1. useStepChat Hook (3일) — **완료**

- [x] `app-frontend/src/features/roadmap/hooks/useStepChat.ts` 생성
  - [x] SSE 타입 정의 (SSETokenEvent, SSESourcesEvent, SSEMetaEvent, SSEDoneEvent, SSEErrorEvent)
  - [x] `useStepChat(roadmapId, stepId)` 훅 구현
    - [x] messages 상태 관리
    - [x] isStreaming / isLoading / error 상태
    - [x] threadId 관리
    - [x] `sendMessage()` — fetch + ReadableStream SSE 파싱
    - [x] `loadHistory()` — GET 이력 API 호출
    - [x] `clearError()` — 에러 초기화
  - [x] SSE 파싱 로직
    - [x] buffer 기반 라인 파싱
    - [x] token 이벤트 → 실시간 메시지 업데이트
    - [x] sources 이벤트 → 출처 저장
    - [x] meta 이벤트 → thread_id 저장 + 서버 메시지 ID ref (I-8)
    - [x] done 이벤트 → 스트리밍 완료 (serverMessageId 안전 탐색, I-8)
    - [x] error 이벤트 → 에러 표시
    - [x] 하트비트 무시 (`: heartbeat`)
  - [x] AbortController 취소 지원
  - [x] 컴포넌트 언마운트 시 정리 (cleanup)
  - [x] Silent Refresh for SSE: tryRefreshToken() + 401 재시도 (C-7)
- [x] `features/roadmap/hooks/index.ts` 수정 — export 추가
- [x] 토큰 접근 (localStorage.getItem("token"))

### C-2. StepChatPanel 컴포넌트 (2일) — **완료**

- [x] `app-frontend/src/features/roadmap/components/StepChatPanel.tsx` 생성
  - [x] Props: roadmapId, stepId, stepTitle, isOpen, onClose
  - [x] 레이아웃
    - [x] 데스크톱: 우측 슬라이드아웃 (420px)
    - [x] 모바일: 하단 풀스크린 시트 (85vh)
    - [x] 슬라이드인/아웃 애니메이션
  - [x] 헤더: 단계 제목 + 닫기 버튼
  - [x] 메시지 영역
    - [x] 빈 상태 (첫 대화 안내)
    - [x] 메시지 목록 (user/assistant 분류)
    - [x] 스트리밍 중 타이핑 인디케이터 (커서 깜빡임)
    - [x] 자동 스크롤 (새 메시지 시)
  - [x] 입력 영역
    - [x] textarea + 전송 버튼
    - [x] Enter 키 전송 (Shift+Enter 줄바꿈)
    - [x] disabled 상태 (isStreaming)
  - [x] useStepChat 훅 연결
  - [x] 마운트 시 loadHistory() 호출
- [x] `features/roadmap/components/index.ts` 수정 — export 추가

### C-3. 출처 인용 파싱 + 출처 카드 UI (1.5일) — **완료**

- [x] 출처 파싱 유틸 (StepChatPanel 내 renderCitationLine)
  - [x] `[법령 N]`, `[서류 N]` 패턴 정규식
  - [x] 인라인 텍스트 → React 노드 변환 (링크 삽입)
  - [x] 소스 매칭 (N → sources 배열 인덱스)
- [x] 출처 카드 UI (SourcesCard 컴포넌트)
  - [x] 메시지 하단 접이식 목록 (기본 접힘)
  - [x] 아이콘: Gavel (법령) / FileText (서류)
  - [x] 제목 + 외부 링크 (ExternalLink 아이콘)
  - [x] "출처 N개" 토글 버튼

### C-4. TimelineStepItem 통합 (0.5일) — **완료**

- [x] `TimelineStepItem.tsx` 수정
  - [x] ACTIVE/DONE 상태에 "AI에게 물어보기" 버튼 추가
  - [x] 버튼 스타일: MessageSquare 아이콘
  - [x] `stepChatOpen` 상태 추가
  - [x] StepChatPanel 렌더링 (조건부)
  - [x] 버튼 표시 조건: step.status === "IN_PROGRESS" 또는 "COMPLETED"

### C-5. 면책 문구 고정 렌더링 (0.5일) — **완료**

- [x] StepChatPanel 입력 영역 위에 면책 문구 영역 추가
  - [x] Info 아이콘 (lucide-react)
  - [x] 스타일: text-xs, text-slate-400
  - [x] 항상 표시 (스크롤 무관)

### C-6. 모바일 풀스크린 대응 (0.5일) — **완료**

- [x] 반응형 브레이크포인트 적용
  - [x] md 이상: 슬라이드아웃 패널
  - [x] md 미만: 하단 풀스크린 시트 (85vh)
- [x] 모바일 드래그 핸들
- [x] 키보드 올라올 때 입력 영역 가시성 확보 (virtualKeyboard API + fallback)

---

## Section D: 품질 검증 (8일) — **미착수**

### D-1. 프롬프트 엔지니어링 + 튜닝 (3일)

- [ ] 시스템 프롬프트 반복 개선 (5-10회)
  - [ ] 음식점 업종 시나리오
  - [ ] 카페 업종 시나리오
  - [ ] 온라인 쇼핑몰 시나리오
  - [ ] 기타 업종 (데이터 부족 케이스)
- [ ] 토큰 예산 최적화
  - [ ] 불필요한 정보 제거
  - [ ] CHECKLIST 20개+ 트리밍 검증
- [ ] 한국어 응답 품질 조정
  - [ ] 자연스러운 존댓말
  - [ ] 전문 용어 설명 수준

### D-2. 안전장치 QA (3일)

- [ ] 테스트 시나리오 100건+ 실행
  - [ ] 법령명 변형 시도 (20건)
  - [ ] 없는 법령 생성 유도 (15건)
  - [ ] 범위 외 질문 (20건)
  - [ ] 출처 없는 답변 유도 (15건)
  - [ ] 프롬프트 인젝션 (10건)
  - [ ] 경계 케이스 (20건)
- [ ] 결과 분석
  - [ ] 할루시네이션 비율 < 5% 확인
  - [ ] OUT_OF_SCOPE 분류 정확도 > 90% 확인
  - [ ] 출처 인용 정확도 > 95% 확인
- [ ] 실패 케이스 → 프롬프트 수정 → 재검증

### D-3. 통합 테스트 (2일)

- [ ] E2E 플로우 테스트
  - [ ] 로드맵 생성 → 단계 진행 → AI 코치 대화
  - [ ] 대화 이력 저장 → 페이지 새로고침 → 이력 복원
  - [ ] 여러 단계에서 각각 대화 → 컨텍스트 격리 확인
- [ ] 동시 연결 테스트
  - [ ] 3-5명 동시 SSE 연결
  - [ ] 메모리/CPU 모니터링
- [ ] 에러 시나리오
  - [ ] 네트워크 끊김 → 재연결
  - [ ] 토큰 만료 → 401 처리
  - [ ] Step PENDING 상태 → 차단 확인
- [ ] Quality Gates 통과
  - [x] `cd app-backend && .venv/bin/pytest -q` — 260 passed
  - [x] `cd app-frontend && npm run lint` — 0 errors
  - [x] `cd app-frontend && npm run build` — 성공

---

## 비개발 병행 작업

### 법률 자문 (Phase 4 출시 전 필수)

- [ ] 변호사법 제109조 검토 의뢰
- [ ] AI 기본법 (2026.01 시행) 준수 사항 확인
- [ ] 면책 문구 법률적 적정성 검토
- [ ] AI 코치 서비스 범위 법적 판단

### 안전장치 QA 시나리오 작성 (Week 2부터)

- [x] 시나리오 110건 초안 작성 (`qa-safety-scenarios.md`)
- [x] 카테고리별 분류 (법령 변형, 범위 외, 인젝션 등)
- [x] 기대 결과 정의

---

## 코드 리뷰 수정 이력

### Critical 7건 — **전체 완료** (2026-03-02)

| # | 이슈 | 상태 |
|---|------|------|
| C-1 | 중복 팩토리 함수 → deps.py 통합 | **완료** |
| C-2 | 하트비트 미작동 → asyncio.Queue 패턴 | **완료** |
| C-3 | 서비스 레이어 커밋 → 제너레이터 최종단 이동 | **완료** |
| C-4 | user_id 필터 누락 → DB 레벨 필터 | **완료** |
| C-5 | offset 미동작 → Repository 파라미터 추가 | **완료** |
| C-6 | Race condition → UniqueConstraint + IntegrityError | **완료** |
| C-7 | SSE Silent Refresh 부재 → tryRefreshToken + 401 재시도 | **완료** |

### Important 8건 — **전체 완료** (2026-03-02)

| # | 이슈 | 상태 |
|---|------|------|
| I-1 | 컨텍스트 중복 → 시스템 프롬프트에서 대화 맥락 제거 | **완료** |
| I-2 | 중복 DB 쿼리 → build()가 actions 반환 | **완료** |
| I-3 | 인덱스 비효율 → 중복 복합 인덱스 제거 | **완료** |
| I-4 | role 필드 제약 없음 → Literal 타입 적용 | **완료** |
| I-5 | 미사용 session 파라미터 → 제거 | **완료** |
| I-6 | add_message 재조회 → SQL UPDATE | **완료** |
| I-7 | out_of_scope 기존 서비스 미처리 → ChatService 추가 | **완료** |
| I-8 | done 이벤트 ID 비교 → serverMessageId ref | **완료** |

---

## 완료 기준

모든 아래 조건 충족 시 Phase 4 완료:

- [x] Section A 체크리스트 완료
- [x] Section B 체크리스트 완료
- [x] Section C 체크리스트 완료
- [ ] Section D 체크리스트 완료
- [x] `pytest -q` 전체 통과 (260 passed)
- [x] `npm run lint` 통과
- [x] `npm run build` 성공
- [ ] `alembic check` diff 없음 (Docker 환경 검증 필요)
- [ ] SSE 스트리밍 정상 동작 (수동 확인)
- [ ] 안전장치 QA 100건+ 통과 (할루시네이션 < 5%)
- [x] 면책 문구 모든 응답에 표시
- [x] 모바일 반응형 동작 구현
- [ ] feature 브랜치에서 develop으로 PR 생성 + 머지
