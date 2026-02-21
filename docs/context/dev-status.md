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
- 공통 규칙 원천은 `team-standards`(Git)로 고정 운영
- `/ops` 권한 가드(플랫폼 운영자 기준) 프론트+백엔드 최소 구현 진행 중

## Risks And Blockers
- 실제 데이터 연동 전 placeholder 제거 범위가 커질 수 있음
- `/ops` 하위 화면은 기본 골격만 구현되어 실제 운영 데이터 지표 정의가 필요

## Next 3 Actions
1. ActionKit DB 스키마(`actionkit_*`) 마이그레이션 생성 및 적용
2. ActionKit repository/application service 구현 후 v1 API를 service 기반으로 전환
3. `domain/data.py` -> DB seed 스크립트 분리 및 다운로드 경로 정합성 검증

## Test Status
- Backend pytest: 실행 실패(`app-backend/.venv/bin/pytest` 없음)
- Frontend lint: 실행 실패(`eslint` 미설치, `node_modules` 없음)
- Migration check: 미해당

## Sync Notes
- 2026-02-15: Linear MCP 핸드셰이크 이슈 재점검 결과, 실호출 정상으로 상태 전환
- 2026-02-15: 새 프로젝트 일괄 적용용 래퍼 스크립트 `scripts/bootstrap-from-standards.sh` 추가, `/tmp/team-standards` 초기 커밋 완료
- 2026-02-15: 외부 공통 규칙 채널 제거, 공통 규칙은 `team-standards`(Git) 단일 원천으로 재정의
- 2026-02-15: NotebookLM 연동(MCP/문서)을 운영 범위에서 제거
- 2026-02-15: `/ops` 권한 모델을 팀 단위에서 플랫폼 운영자(`User.is_superuser`) 단일 모델로 확정
- 2026-02-15: `app-frontend/src/lib` 누락 복구(`api-client.ts`, `api-types.ts`, `utils.ts`)로 모듈 해석 오류 정리
- 2026-02-16: 백엔드 실행 필수값 누락 방지를 위해 `app-backend/.env.example` 추가 및 `.gitignore` 예외 반영
- 2026-02-20: ActionKit 로컬 스토리지 경로를 `STORAGE_LOCAL_ROOT` 단일 변수 + fallback(`app-backend/uploads`)로 단순화
- 2026-02-20: ActionKit 데이터/파일 관리 전환 플랜 문서 `docs/planning/PLAN-actionkit-data-file-management.md` 추가
- 2026-02-20: 운영 콘솔에 `액션 키트 관리` 카드 및 `/ops/actionkit` 화면 추가
