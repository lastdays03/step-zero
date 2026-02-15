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
- Context memory 운영 검증 Day 1 기록 완료(`context-memory-validation-log.md`)
- Context memory는 `Phase 1` 진행 중이며 `Phase 2`는 게이트 조건 충족 전 잠금 상태
- Phase 3 운영 모델 조정: 공통 규칙은 `team-standards`(Git), 프로젝트 자료 탐색/분석은 NotebookLM으로 역할 분리
- NotebookLM MCP 런타임/인증 검증 완료(질의 호출 성공, 소스 미등록 노트북 응답 확인)
- `/ops` 권한 가드(프론트+백엔드) 최소 구현 착수 예정

## Risks And Blockers
- 실제 데이터 연동 전 placeholder 제거 범위가 커질 수 있음
- `/ops` 권한 가드 구현 시 프론트/백엔드 정책 불일치 가능성

## Next 3 Actions
1. `team-standards` 기준 공통 규칙을 현재 프로젝트 문서와 동기화
2. `/ops` 권한 가드(프론트+백엔드) 최소 구현
3. `roadmap`/`actionkit` 페이지 placeholder를 실제 데이터 로딩 화면으로 교체

## Test Status
- Backend pytest: 미실행(이번 변경은 문서 작업)
- Frontend lint: 미실행(이번 변경은 문서 작업)
- Migration check: 미해당

## Sync Notes
- 2026-02-15: Linear MCP 핸드셰이크 이슈 재점검 결과, 실호출 정상으로 상태 전환
- 2026-02-15: 새 프로젝트 일괄 적용용 래퍼 스크립트 `scripts/bootstrap-from-standards.sh` 추가, `/tmp/team-standards` 초기 커밋 완료
- 2026-02-15: 외부 공통 규칙 채널 제거, 공통 규칙은 `team-standards`(Git) 단일 원천으로 재정의
