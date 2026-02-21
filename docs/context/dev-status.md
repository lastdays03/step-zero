# Dev Status

## Last Updated
- Date: 2026-02-21
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
- 2026-02-21: 팀 공통 ActionKit 동기화용 `app-backend/scripts/bootstrap_actionkit.sh` 추가 및 README 실행 절차 반영
- 2026-02-21: `bootstrap_actionkit.sh`를 Docker 우선(auto) 실행으로 보강해 팀원 로컬 Python/pip 의존 없이 컨테이너 내부 마이그레이션+시드 가능하게 개선
- 2026-02-21: README에 ActionKit 동기화를 `docker compose up` 후 `docker compose exec app-backend`로 마이그레이션/시드 수행하는 절차로 명시
- 2026-02-21: README에 컨테이너 기동 후 필요 시 `docker compose exec`로 마이그레이션/시드를 선택 실행하는 운영 절차(방법 A/B) 추가
- 2026-02-21: README ActionKit 운영 명령을 `docker compose exec`에서 `docker exec stepzero-backend` 기준으로 통일
- 2026-02-21: OS 호환성 강화를 위해 `.gitattributes`에 LF 정책(`*.sh`, `*.yml`, `Dockerfile*`) 추가 및 프론트 `types:backend-openapi`를 Docker exec 기반으로 전환
- 2026-02-21: README 2-4 섹션의 중복 실행 예시를 정리하고 ActionKit 동기화 절차를 단일 흐름(준비/마이그레이션/시드 + 옵션)으로 재구성
- 2026-02-21: `docker-compose.prod.yml` + `Dockerfile.prod`(백/프론트) 추가, 루트 `.env.local` 기반 배포 변수 관리 절차와 `app-backend/.env.local`(로컬 백엔드) 역할 분리 문서화
- 2026-02-21: 환경 템플릿 파일 규격을 `.env.example`로 통일(루트 템플릿 파일명 변경 및 `.gitignore` 예외 반영)
- 2026-02-21: 컨테이너별 env 분리 정책 적용(백/워커=`app-backend/.env*`, 프론트=`app-frontend/.env*`) 및 dev/prod compose를 `env_file` 기반으로 전환
- 2026-02-21: Ops 운영관리 플랜을 마스터+상세 구조로 재편(`PLAN-ops-admin-menu-master` + users/reports/announcements/audit-logs)하고 기존 actionkit/growth 플랜을 감사로그 선행 게이트 기준으로 보강
- 2026-02-21: `docs/planning/` 레거시/참조 문서 9개를 `docs/planning/completed/`로 이동해 실행 문서 범위를 현재 플랜 중심으로 정리
