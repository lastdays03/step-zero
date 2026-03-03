# Dev Status

## Last Updated
- Date: 2026-03-03
- Branch: `feature/4-ai-coach-chatbot`

## Sprint Focus
- Phase 4: AI 코치 챗봇 + 글로벌 챗봇 통합

## Current State
- Phase 0 전체 완료 (develop 머지 완료)
- Phase 1 전체 완료 (develop 머지 완료)
- Phase 2+3 전체 완료 (develop 머지 완료)
- Phase 4 AI 코치 챗봇: 구현 완료 + 통합 SSE 스트리밍 완료
- 챗봇 완전 통합: **설계 논의 중** (대화 이력 구조 + UX 일원화)

## Completed (Phase 4)

### AI 코치 챗봇 (이전 세션)
- 로드맵 단계별 3레이어 시스템 프롬프트 (FACTS/STATUS/RULES)
- RoadmapChatService SSE 스트리밍 + Thread/Message DB 저장
- 출처 인용 파싱 ([법령 N], [서류 N])
- SemanticRouter OUT_OF_SCOPE 차단
- 품질 검증 테스트 스위트

### 글로벌 챗봇 + AI 코치 통합 (이번 세션)
- UnifiedChatService 디스패처 — 단일 엔드포인트 자동 분기
- ChatService.stream() — 일반 모드 SSE 스트리밍
- ChatContextProvider — 로드맵 컨텍스트 전역 관리
- useChatbot 전면 리팩토링 (REST→SSE)
- StepChatPanel/useStepChat 레거시 제거
- 프론트엔드 컴포넌트 업그레이드 (출처/스트리밍/코치 헤더)

## In Progress
- 챗봇 완전 통합 설계 (UX + 대화 이력 구조)
  - 리서치: `dev/active/unified-chatbot-integration/chatbot-unification-research.md`
  - 미결정: 대화 이력 구조 (단일 스트림 vs 대화방 vs 하이브리드)
  - 미결정: 챗봇 정체성 통합 ("AI 어시스턴트" vs "AI 코치" 일원화)

## Risks And Blockers
- (없음)

## Next 3 Actions
1. 챗봇 완전 통합 설계 확정 (Q1~Q5 결정)
2. 완전 통합 구현
3. `feature/4-ai-coach-chatbot` → `develop` PR 생성

## Test Status
- Backend pytest: 433 passed, 30 skipped
- Frontend lint: 0 errors
- Frontend build: 성공 (19 static + 2 동적 페이지)

## Sync Notes
- 2026-03-01: Phase 0 전체 완료 — develop 머지 완료
- 2026-03-02: Phase 1 완료 — develop 머지 완료
- 2026-03-02: Phase 2+3 완료 — develop 머지 완료
- 2026-03-02: Phase 4 AI 코치 챗봇 구현 완료
- 2026-03-03: 글로벌 챗봇 + AI 코치 통합 SSE 완료, 완전 통합 설계 논의 중
