# Handoff

## 마지막 업데이트
- Date: 2026-03-03
- Branch: `feature/4-ai-coach-chatbot`

## 이번 세션 완료

### 글로벌 챗봇 + AI 코치 통합 (SSE 스트리밍)
에이전트 팀(backend-dev + frontend-dev) 병렬 처리로 19개 태스크 전체 구현 완료.

**백엔드 (Section A):**
- `UnifiedChatRequest` 스키마 + model_validator (roadmap_id/step_id 쌍 검증)
- `ChatService.stream()` 메서드 추가 (일반 SSE 스트리밍)
- `UnifiedChatService` 디스패처 — 컨텍스트 유무로 코치/일반 자동 분기
- `POST /rag/chat/stream` SSE 엔드포인트 + DI 팩토리
- `problem.py` ValueError 직렬화 버그 수정
- 테스트 8개 추가 → 전체 433 passed, 30 skipped

**프론트엔드 (Section B~D):**
- `sseClient.ts` — SSE 파싱/auth/URL 유틸 추출
- `ChatContextProvider` — localStorage 기반 로드맵 컨텍스트 전역 관리
- `renderCitationLine.tsx` + `SourcesCard.tsx` — 출처 렌더링
- `useChatbot.ts` 전면 리팩토링 — REST→SSE, 코치/일반 모드 분기
- `ChatBubble/ChatPanel/ChatMessageList/GlobalChatbot` 업그레이드
- `TimelineStepItem` — StepChatPanel→ChatContext 전환
- `StepChatPanel.tsx` + `useStepChat.ts` 삭제 (레거시 제거)
- lint 0 errors, build 성공

### 챗봇 완전 통합 설계 논의
- 현재 "AI 어시스턴트" vs "AI 코치" 이중 모드 분리 분석
- 대화 이력 저장 구조별 UX 옵션 3가지 (A: 단일 스트림, B: 대화방 목록, C: 하이브리드)
- 미결정 사항 5개 (Q1~Q5) 정리
- 리서치 문서: `dev/active/unified-chatbot-integration/chatbot-unification-research.md`

## 핵심 기술 결정
- **단일 SSE 엔드포인트**: `/rag/chat/stream` — roadmap_id 유무로 자동 분기
- **UnifiedChatService = 조합 패턴**: 기존 ChatService + RoadmapChatService 변경 최소화
- **기존 엔드포인트 유지**: `/rag/chat`, `/roadmaps/{id}/steps/{sid}/chat/*` 하위호환
- **ChatContextProvider + localStorage**: 페이지 전환해도 로드맵 컨텍스트 유지

## 검증
- Backend pytest: 433 passed, 30 skipped, 0 failed
- Frontend lint: 0 errors
- Frontend build: 성공 (19 static + 2 동적 페이지)

## 커밋된 변경사항
- `cc7d861` feat: 로드맵 단계별 AI 코치 챗봇 구현 (Phase 4 Section A~C)
- `4a7024b` fix: 로드맵 챗봇 코드 리뷰 important 8건 개선
- `be0979d` ~ `8668bfb` docs/test: 테스트 스위트 + 문서
- `3b93f50` feat: 글로벌 챗봇 + AI 코치 통합 SSE 스트리밍
- `aa560bc` docs: 개발 계획 문서 정리

## 다음 세션 시작점
1. **즉시**: 챗봇 완전 통합 설계 논의 이어가기 (Q1~Q5 결정)
   - 리서치 문서: `dev/active/unified-chatbot-integration/chatbot-unification-research.md`
2. **설계 확정 후**: 완전 통합 구현 (대화 이력 통합, UX 일원화)
3. **이후**: `feature/4-ai-coach-chatbot` → `develop` PR 생성

## 커밋 시 주의사항
- 커밋 메시지는 소문자 시작 필수 (commitlint subject-case 규칙)
- `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` 포함
