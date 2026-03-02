# Phase 4: AI 코치 챗봇 MVP — 작업 체크리스트

> **Last Updated**: 2026-03-02
> **Status**: 계획 완료, 구현 대기

---

## Section A: BE 기반 구축 (5.5일)

### A-1. DB 모델 생성 (1일)

- [ ] `app-backend/app/models/roadmap_chat.py` 생성
  - [ ] `RoadmapChatThread` 모델 (id, roadmap_id, step_id, user_id, title, message_count, created_at, updated_at)
  - [ ] `RoadmapChatMessage` 모델 (id, thread_id, role, content, sources_json, token_count, created_at)
  - [ ] FK 제약조건 (roadmaps.id, roadmap_steps.id, users.id, roadmap_chat_threads.id)
  - [ ] ondelete 설정 (CASCADE)
  - [ ] 복합 인덱스 (roadmap_id, step_id) on threads
  - [ ] thread_id 인덱스 on messages
- [ ] `app-backend/app/models/__init__.py` 수정
  - [ ] `from .roadmap_chat import RoadmapChatThread, RoadmapChatMessage` 추가
  - [ ] `__all__` 리스트에 추가
- [ ] `app-backend/alembic/env.py` 수정
  - [ ] `import app.models.roadmap_chat` 추가

### A-2. Alembic 마이그레이션 (0.5일)

- [ ] `app-backend/alembic/versions/011_roadmap_chat.py` 생성
  - [ ] depends_on: 010 마이그레이션
  - [ ] upgrade: roadmap_chat_threads, roadmap_chat_messages 테이블 생성
  - [ ] downgrade: 양 테이블 삭제
- [ ] Docker 환경에서 마이그레이션 실행 검증
  - [ ] `docker compose exec app-backend python -m alembic upgrade head`
  - [ ] `docker compose exec app-backend python -m alembic check` (diff 없음 확인)

### A-3. RoadmapContextBuilder (3일)

- [ ] `app-backend/app/features/roadmaps/application/context_builder.py` 생성
  - [ ] `RoadmapContextBuilder` 클래스
  - [ ] `build()` 메서드: 3레이어 조합
  - [ ] `_build_fact_layer()`: 불변 팩트 (업종, 지역, 법령, 서류)
  - [ ] `_build_state_layer()`: 실행 상태 (체크리스트 완료/미완료, 위험 요소)
  - [ ] `_build_instruction_layer()`: 안내 규칙 (안전장치 + 최근 대화)
  - [ ] `_trim_to_budget()`: 토큰 예산 초과 시 트리밍
- [ ] RoadmapRepository 기존 메서드 활용
  - [ ] `list_step_details([step_id])` 호출 확인
  - [ ] `list_step_actions([step_id])` 호출 확인
- [ ] 단위 테스트
  - [ ] 각 레이어 독립 생성 검증
  - [ ] 토큰 예산 트리밍 검증
  - [ ] 빈 데이터 (법령 0개, 체크리스트 0개) 처리

### A-4. SemanticRouter OUT_OF_SCOPE 확장 (0.5일)

- [ ] `app-backend/app/features/rag/application/semantic_router.py` 수정
  - [ ] `out_of_scope` 앵커 카테고리 추가 (8-12개 문장)
  - [ ] `classify()` 메서드: out_of_scope 판정 로직
  - [ ] threshold 조정 (0.75 권장)
- [ ] 분류 테스트
  - [ ] "세금 얼마나 내야 하나요?" → out_of_scope
  - [ ] "영업신고 어떻게 해요?" → legal (기존 동작 유지)
  - [ ] "카페 인테리어 추천" → general (기존 동작 유지)

### A-5. RoadmapChatRepository (0.5일)

- [ ] `app-backend/app/repositories/roadmap_chat_repository.py` 생성
  - [ ] `get_or_create_thread(roadmap_id, step_id, user_id)` 구현
  - [ ] `get_thread(thread_id)` 구현
  - [ ] `list_threads(roadmap_id, step_id)` 구현
  - [ ] `add_message(thread_id, role, content, sources_json, token_count)` 구현
  - [ ] `get_recent_messages(thread_id, limit=10)` 구현
  - [ ] `count_messages(thread_id)` 구현
- [ ] 단위 테스트 (CRUD 기본 동작)

---

## Section B: BE 핵심 구현 (7일)

### B-1. RoadmapChatService (4일)

- [ ] `app-backend/app/features/roadmaps/application/roadmap_chat_service.py` 생성
  - [ ] `RoadmapChatService` 클래스
  - [ ] `__init__()`: ContextBuilder, SemanticRouter, ChatRepo, ChatOpenAI(streaming=True)
  - [ ] `stream()` 비동기 제너레이터
    - [ ] SemanticRouter OUT_OF_SCOPE 차단
    - [ ] Thread 생성/조회
    - [ ] user 메시지 DB 저장
    - [ ] ContextBuilder.build() 호출
    - [ ] 대화 이력 구성 (_build_chat_messages)
    - [ ] ChatOpenAI.astream() 토큰 스트리밍
    - [ ] 출처 파싱 (_parse_citations)
    - [ ] assistant 메시지 DB 저장
    - [ ] SSE 이벤트 yield (token, sources, meta, done)
  - [ ] `_build_chat_messages()`: LangChain 메시지 배열 구성
  - [ ] `_parse_citations()`: [법령 N], [서류 N] 패턴 파싱
  - [ ] 하트비트 (15초 간격)
  - [ ] 타임아웃 (30초)
  - [ ] `asyncio.CancelledError` 처리 (부분 응답 저장)
- [ ] 의존성 주입 함수 (`get_roadmap_chat_service`)
- [ ] SSE 이벤트 헬퍼 (`_sse_event(event_type, data)`)
- [ ] 통합 테스트 (모의 LLM)

### B-2. SSE 라우터 (2일)

- [ ] `app-backend/app/api/v1/roadmaps/chat.py` 생성
  - [ ] `POST /{roadmap_id}/steps/{step_id}/chat/stream` (SSE 스트리밍)
    - [ ] JWT 인증 (get_current_user)
    - [ ] Team 권한 (get_current_team)
    - [ ] 로드맵 소유권 검증
    - [ ] Step 상태 검증 (IN_PROGRESS 또는 COMPLETED)
    - [ ] StreamingResponse 반환
    - [ ] CORS 헤더 (text/event-stream)
  - [ ] `GET /{roadmap_id}/steps/{step_id}/chat/threads` (스레드 목록)
    - [ ] 인증 + 권한
    - [ ] ThreadSummary 목록 반환
  - [ ] `GET /{roadmap_id}/steps/{step_id}/chat/threads/{thread_id}/messages` (메시지 목록)
    - [ ] 인증 + Thread 소유권
    - [ ] offset/limit 페이징
    - [ ] ChatMessageResponse 목록 반환
- [ ] 스키마 정의 (`api/v1/roadmaps/schemas.py` 확장)
  - [ ] `StepChatRequest` (message, thread_id)
  - [ ] `ThreadSummary` (thread_id, message_count, created_at, updated_at)
  - [ ] `ChatMessageResponse` (id, role, content, sources, created_at)
- [ ] 라우터 등록 (`api/v1/roadmaps/router.py` 수정)
  - [ ] `router.include_router(chat_router)` 추가
- [ ] API 테스트
  - [ ] curl로 SSE 스트리밍 확인
  - [ ] 인증 실패 → 401
  - [ ] 소유권 실패 → 403
  - [ ] Step 상태 PENDING → 400

### B-3. 안전장치 시스템 프롬프트 설계 (1일)

- [ ] 시스템 프롬프트 텍스트 작성
  - [ ] LAYER 1 팩트 태그 (`<FACTS>`) 템플릿
  - [ ] LAYER 2 상태 태그 (`<STATUS>`) 템플릿
  - [ ] LAYER 3 규칙 태그 (`<RULES>`) 내용
    - [ ] 팩트-지능 분리 규칙
    - [ ] 출처 강제 인용 규칙 + few-shot 예시
    - [ ] 범위 제한 규칙
    - [ ] 전문가 권고 규칙
    - [ ] 불확실성 표현 규칙
- [ ] 테스트 시나리오 20건 준비 (초안)
  - [ ] 법령 변형 시도 5건
  - [ ] 없는 법령 생성 유도 5건
  - [ ] 범위 외 질문 5건
  - [ ] 정상 질문 5건

---

## Section C: FE 구현 (8일)

### C-1. useStepChat Hook (3일)

- [ ] `app-frontend/src/features/roadmap/hooks/useStepChat.ts` 생성
  - [ ] `StepChatMessage` 인터페이스 정의
  - [ ] `CitationSource` 인터페이스 정의
  - [ ] `useStepChat(roadmapId, stepId)` 훅 구현
    - [ ] messages 상태 관리
    - [ ] isStreaming / isLoading / error 상태
    - [ ] threadId 관리
    - [ ] `sendMessage()` — fetch + ReadableStream SSE 파싱
    - [ ] `loadHistory()` — GET 이력 API 호출
    - [ ] `clearError()` — 에러 초기화
  - [ ] SSE 파싱 로직
    - [ ] buffer 기반 라인 파싱
    - [ ] token 이벤트 → 실시간 메시지 업데이트
    - [ ] sources 이벤트 → 출처 저장
    - [ ] meta 이벤트 → thread_id 저장
    - [ ] done 이벤트 → 스트리밍 완료
    - [ ] error 이벤트 → 에러 표시
    - [ ] 하트비트 무시 (`: heartbeat`)
  - [ ] AbortController 취소 지원
  - [ ] 컴포넌트 언마운트 시 정리 (cleanup)
- [ ] `features/roadmap/hooks/index.ts` 수정 — export 추가
- [ ] 토큰 접근 (localStorage.getItem("token"))
- [ ] 리렌더 최적화 (배치 처리)

### C-2. StepChatPanel 컴포넌트 (2일)

- [ ] `app-frontend/src/features/roadmap/components/StepChatPanel.tsx` 생성
  - [ ] Props: roadmapId, stepId, stepTitle, isOpen, onClose
  - [ ] 레이아웃
    - [ ] 데스크톱: 우측 슬라이드아웃 (420px)
    - [ ] 모바일: 하단 풀스크린 시트 (85vh)
    - [ ] 슬라이드인/아웃 애니메이션
  - [ ] 헤더: 단계 제목 + 닫기 버튼
  - [ ] 메시지 영역
    - [ ] 빈 상태 (첫 대화 안내)
    - [ ] 메시지 목록 (user/assistant 분류)
    - [ ] 스트리밍 중 타이핑 인디케이터 (커서 깜빡임)
    - [ ] 자동 스크롤 (새 메시지 시)
  - [ ] 입력 영역 (ChatInput 패턴 차용)
    - [ ] textarea + 전송 버튼
    - [ ] Enter 키 전송 (Shift+Enter 줄바꿈)
    - [ ] disabled 상태 (isStreaming)
  - [ ] useStepChat 훅 연결
  - [ ] 마운트 시 loadHistory() 호출
- [ ] `features/roadmap/components/index.ts` 수정 — export 추가

### C-3. 출처 인용 파싱 + 출처 카드 UI (1.5일)

- [ ] 출처 파싱 유틸
  - [ ] `[법령 N]`, `[서류 N]` 패턴 정규식
  - [ ] 인라인 텍스트 → React 노드 변환 (링크 삽입)
  - [ ] 소스 매칭 (N → sources 배열 인덱스)
- [ ] 출처 카드 UI
  - [ ] 메시지 하단 접이식 목록 (기본 접힘)
  - [ ] 아이콘: Gavel (법령) / FileText (서류)
  - [ ] 제목 + 외부 링크 (ExternalLink 아이콘)
  - [ ] "출처 N개" 토글 버튼
- [ ] 인라인 인용 링크
  - [ ] 클릭 시 출처 카드 하이라이트

### C-4. TimelineStepItem 통합 (0.5일)

- [ ] `TimelineStepItem.tsx` 수정
  - [ ] ACTIVE 상태에 "AI에게 물어보기" 버튼 추가
  - [ ] 위치: 체크리스트 목록 아래, "완료" 버튼 위
  - [ ] 버튼 스타일: 보조 (gradient border, MessageSquare 아이콘)
  - [ ] `stepChatOpen` 상태 추가
  - [ ] StepChatPanel 렌더링 (조건부)
  - [ ] 버튼 표시 조건: step.status === "IN_PROGRESS" 또는 "COMPLETED"

### C-5. 면책 문구 고정 렌더링 (0.5일)

- [ ] StepChatPanel 입력 영역 위에 면책 문구 영역 추가
  - [ ] 텍스트: "AI가 생성한 정보이며, 정확성을 보장하지 않습니다. 중요한 결정은 전문가와 상담하세요."
  - [ ] Info 아이콘 (lucide-react)
  - [ ] 스타일: text-xs, text-slate-400, border-t, bg-slate-50
  - [ ] 항상 표시 (스크롤 무관)

### C-6. 모바일 풀스크린 대응 (0.5일)

- [ ] 반응형 브레이크포인트 적용
  - [ ] md 이상: 슬라이드아웃 패널
  - [ ] md 미만: 하단 풀스크린 시트 (85vh)
- [ ] 뒤로가기 버튼으로 닫기 (모바일)
- [ ] 키보드 올라올 때 입력 영역 가시성 확보
- [ ] 모바일 Safari + Chrome 테스트

---

## Section D: 품질 검증 (8일)

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
  - [ ] `cd app-backend && .venv/bin/pytest -q`
  - [ ] `cd app-frontend && npm run lint`
  - [ ] `cd app-frontend && npm run build`

---

## 비개발 병행 작업

### 법률 자문 (Phase 4 출시 전 필수)

- [ ] 변호사법 제109조 검토 의뢰
- [ ] AI 기본법 (2026.01 시행) 준수 사항 확인
- [ ] 면책 문구 법률적 적정성 검토
- [ ] AI 코치 서비스 범위 법적 판단

### 안전장치 QA 시나리오 작성 (Week 2부터)

- [ ] 시나리오 100건+ 초안 작성
- [ ] 카테고리별 분류 (법령 변형, 범위 외, 인젝션 등)
- [ ] 기대 결과 정의

---

## 완료 기준

모든 아래 조건 충족 시 Phase 4 완료:

- [ ] 모든 Section A-D 체크리스트 완료
- [ ] `pytest -q` 전체 통과
- [ ] `npm run lint` 통과
- [ ] `npm run build` 성공
- [ ] `alembic check` diff 없음
- [ ] SSE 스트리밍 정상 동작 (수동 확인)
- [ ] 안전장치 QA 100건+ 통과 (할루시네이션 < 5%)
- [ ] 면책 문구 모든 응답에 표시
- [ ] 모바일 반응형 동작 확인
- [ ] feature 브랜치에서 develop으로 PR 생성 + 머지
