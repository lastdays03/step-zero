# Dev Status

## Last Updated
- Date: 2026-02-15
- Branch: `develop`

## Sprint Focus
- 소셜로그인 전용 운영 플로우에 맞춘 `/ops` 접근 정책 구현
- 피처별 실제 기능 구현(placeholder 제거)

## Current State
- Backend API 구조를 `app/api/v2/<feature>/<function>.py`로 통일했다.
- Frontend 피처 패키지 경계를 정리했고 `/`는 `/dashboard`로 리다이렉트된다.
- 사이드/모바일 메뉴는 주요 진입점(`/roadmap`, `/actionkit`, `/growth-club`, `/settings`, `/profile`, `/billing`)까지 연결됐다.
- Linear MCP는 실조회 기준 정상 동작(팀/프로젝트/이슈 조회 성공).

## In Progress
- Context memory upgrade Phase 1 문서 고정 적용 완료, Phase 1 운영 검증 준비 중
- `/ops` 권한 가드(프론트+백엔드) 최소 구현 착수 예정

## Risks And Blockers
- 실제 데이터 연동 전 placeholder 제거 범위가 커질 수 있음
- `/ops` 권한 가드 구현 시 프론트/백엔드 정책 불일치 가능성

## Next 3 Actions
1. `/ops` 권한 가드(프론트+백엔드) 최소 구현
2. `roadmap`/`actionkit` 페이지 placeholder를 실제 데이터 로딩 화면으로 교체
3. 메뉴/라우트 규칙을 e2e 또는 통합 테스트로 1차 검증

## Test Status
- Backend pytest: 미실행(이번 변경은 문서 작업)
- Frontend lint: 미실행(이번 변경은 문서 작업)
- Migration check: 미해당

## Sync Notes
- 2026-02-15: Linear MCP 핸드셰이크 이슈 재점검 결과, 실호출 정상으로 상태 전환
