# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-06
- Branch: `develop` (clean, up-to-date)

## Sprint Focus
- 다음 계획 착수 대기 (legacy-file-cleanup 또는 신규 계획)

## Current State
- ops-file-manager: 전체 완료, PR #24 머지, done/ 아카이브
- dashboard-enhance: 전체 완료 (Phase 1~4), PR #24 머지, done/ 아카이브
- legacy-file-cleanup: 계획 수립 완료, A-2만 완료 (듀얼 라이트), 나머지 미착수

## Completed (최근)
- Ops 파일 관리 콘솔 (PR #24)
  - 백엔드: files API (목록/통계/삭제), 감사 로그 연동, 테스트 306줄
  - 프론트엔드: OpsFilesView 543줄, 타입/API 모듈
- Dashboard Enhance Phase 1~4 (PR #24)
  - 거짓 정보 제거 (프로 플랜, 소셜 프루프, 하드코딩 아바타)
  - 데이터 연동 (founders_online 실제 집계, roadmap_id, error 배너)
  - 알림 SSE 전환 (Redis Pub/Sub + SSE 스트림 + useNotificationSSE 훅)
  - 접근성 + 테스트 보강 (aria-label, sr-only, 키보드, safe-area)
- 알림 링크 해시 라우팅 전환 + 미읽음 UX 개선

## In Progress
- 없음

## Risks And Blockers
- 없음

## Next 3 Actions
1. legacy-file-cleanup 착수 여부 결정 (Phase A: 데이터 정합성 확보)
2. 또는 신규 기능 계획 수립
3. Docker 환경 통합 테스트 (ops-file-manager + dashboard-enhance 변경분)

## Test Status
- Backend pytest: 421 passed, 10 skipped
- Frontend lint: 통과 (warning 1건: ops/files img element)
