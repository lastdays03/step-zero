# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

**Advanced Harness** — Claude Code 스킬/에이전트/훅/커맨드 모음 모노레포.

이 레포는 두 가지 역할을 한다:
1. **Claude Code 인프라 템플릿**: 스킬(14개), 에이전트(11개), 훅(8개), 커맨드(3개)를 다른 프로젝트에 이식 가능
2. **실제 작동 앱**: FastAPI 백엔드 + Next.js 15 프론트엔드 (QWarty 프로젝트)

## Quick Commands

### Backend

```bash
cd backend
uv venv && source .venv/bin/activate
uv pip install -e .[dev]
uvicorn backend.main:app --reload --port 28080  # 주의: backend.main (app.main 아님)
```

```bash
# Code quality
cd backend
black . && isort . --profile black && ruff check --fix . && mypy .
pre-commit run --all-files
```

```bash
# Tests (asyncio_mode=auto)
cd backend
pytest                          # 전체
pytest tests/test_specific.py   # 단일 파일
pytest -k "test_name"           # 이름 매칭
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev          # Turbopack dev server (localhost:3000)
pnpm build        # Production build
pnpm lint         # ESLint
```

```bash
# E2E tests (Playwright)
cd frontend
pnpm exec playwright test
pnpm exec playwright test tests/specific.spec.ts  # 단일 파일
```

```bash
# Lighthouse CI
cd frontend
pnpm build && npx lhci autorun
```

### Claude Code 설정 설치 (다른 프로젝트에)

```bash
curl -fsSL https://raw.githubusercontent.com/lastdays03/team-standards/main/scripts/install-claude-env.sh | bash
curl -fsSL https://raw.githubusercontent.com/lastdays03/team-standards/main/scripts/install-claude-env.sh | bash -s -- ~/target-project
```

## Monorepo Structure

```
.claude/
  agents/       # 11 autonomous agents (auth-route-debugger, code-refactor-master, planner, etc.)
  commands/     # 3 slash commands (/dev-docs, /dev-docs-update, /route-research-for-testing)
  hooks/        # 7 hooks (skill-activation-prompt, post-tool-use-tracker, tsc-check, etc.)
  skills/       # 14 skills + skill-rules.json (auto-activation config)
  settings.json # Hook bindings & permissions
docs/
  context/      # 세션 운영 (상태/결정/핸드오프/규칙)
  plans/        # 기획 + 구현 통합 (active/, reports/, done/)
  architecture/ # 시스템 아키텍처
  operations/   # 팀 협업 프로세스
  dev-guide/    # 개발자 가이드
  archive/      # 역할 완료 문서
backend/        # Python 3.12.3, FastAPI, SQLModel, PostgreSQL
frontend/       # Next.js 15, React 19, TypeScript, Tailwind CSS 4, shadcn/ui
scripts/        # install-claude-env.sh (설정만 타 프로젝트에 이식)
```

## Claude Code Infrastructure

### Skills Auto-Activation

스킬은 `.claude/skills/skill-rules.json`의 트리거 규칙에 따라 자동 활성화된다. `skill-activation-prompt` 훅(UserPromptSubmit)이 사용자 프롬프트와 파일 컨텍스트를 매칭하여 관련 스킬을 주입한다.

주요 스킬:
- `fastapi-backend-guidelines` — DDD, SQLModel, async/await 패턴
- `nextjs-frontend-guidelines` — App Router, shadcn/ui, Tailwind CSS 4, 한국어 i18n
- `pytest-backend-testing` — FastAPI 테스트 패턴 (유닛/통합/비동기/목킹)
- `skill-developer` — 새 스킬 생성 메타가이드 (트리거, 훅, 500줄 룰)
- `error-tracking` — Sentry v8 통합 패턴

### Slash Commands

- `/dev-docs <설명>` — `docs/plans/active/{task-name}/`에 plan/context/tasks 문서 구조 생성
- `/dev-docs-update` — 컨텍스트 컴팩션 전 진행 상태 업데이트, 완료 작업 아카이브. docs/context 연동하여 세션 상태 동기화
- `/route-research-for-testing` — 편집된 라우트 자동 감지 후 auth-route-tester로 테스트

### Hooks

- **UserPromptSubmit**: `skill-activation-prompt` — 스킬 자동 활성화
- **PostToolUse**: `post-tool-use-tracker` — Edit/Write/MultiEdit 추적
- **Stop**: `tsc-check`, `trigger-build-resolver` — TypeScript 컴파일 검증 및 에러 자동 수정

### Agents

에이전트는 `.claude/agents/*.md`에 정의된 자율 실행 서브태스크 전문가. 주요:
- `planner` / `plan-reviewer` — 개발 계획 수립 및 리뷰
- `code-architecture-reviewer` — 아키텍처 일관성/품질 리뷰
- `code-refactor-master` — 종합 리팩토링 (파일 재구성, 의존성 추적)
- `auth-route-tester` / `auth-route-debugger` — JWT 인증 라우트 테스트/디버깅
- `frontend-error-fixer` — 빌드타임/런타임 프론트엔드 에러 진단
- `web-research-specialist` — GitHub Issues, Reddit, SO 기술 리서치

## Document Management

### 문서 구조
- `docs/plans/active/{topic}/` — 기획(PLAN) + 구현(tasks/context)이 같은 폴더에 공존
- `docs/plans/reports/` — 독립 리서치 보고서 (REPORT-*.md)
- `docs/plans/done/` — 완료 아카이브 (폴더째 이동)
- PLAN 파일에 구현 상세를 작성하지 않는다 (별도 tasks/context 파일 사용)

### 세션 체크리스트
- **시작**: `docs/context/` 4개 파일 순서대로 읽기 (dev-status → decisions → handoff → ops-rules)
- **종료**: dev-status 상태 갱신 → decisions 확정사항 기록 → handoff 다음 시작점 작성

### 네이밍 규칙
- 계획: `PLAN-<topic>.md`, 보고서: `REPORT-<topic>.md`
- 영문 + 케밥케이스, 파일명 버전 접미사(`_v2`) 지양

### 크기 가이드
- `dev-status.md`: 50줄 이내
- `handoff.md`: 40줄 이내

## Backend Architecture

**Framework:** FastAPI + SQLModel + SQLAlchemy (async/await, asyncpg)

**Database — Read/Write Separation:**
- `backend/db/orm.py`에서 이벤트 루프별 엔진/세션 캐싱
- 쓰기: `get_write_session()` / `get_write_session_dependency()`
- 읽기: `get_read_session()` / `get_read_session_dependency()`
- PostgreSQL + asyncpg, 비개발 환경 SSL 필수

**Domain-Driven Design:**
- `backend/domain/{entity}/` — model.py (SQLModel), service.py, repository.py
- 도메인: user, auth, artist, artwork, admin, curai, exhibition, message, notification, subscription, shared
- API: `/api/v1/` 프리픽스, 라우터는 `backend/api/v1/routers/`
- DTO: `backend/dtos/` (Pydantic 기반 request/response)
- 앱 생성: `backend/main.py` → `create_application()`

**AI Agent (Curai):** Pydantic AI, SSE 스트리밍, 스레드 기반 대화 + DB 도구 검색

## Frontend Architecture

**Framework:** Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS 4

**핵심 파일:**
- `src/lib/api.ts` — 백엔드 API 클라이언트 (모든 API 호출 여기 집중)
- `src/lib/serverAuth.ts` — 서버사이드 JWT 인증
- `src/lib/s3Upload.ts` — S3 presigned POST + 클라이언트 WebP 압축 + 썸네일

**S3 업로드 플로우:**
Client → `POST /api/v1/upload/presigned-url` → presigned POST 생성 → 클라이언트가 S3 직접 업로드 (최대 50MB)

**i18n:** next-intl, 로케일은 `src/locales/`

## Deployment

- Backend: AWS ECS (`qwarty-backend-cluster`), main 브랜치 push 시 GitHub Actions 자동 배포
  - ECR: `206404754787.dkr.ecr.ap-northeast-2.amazonaws.com/qwarty-backend:latest`
  - Task def: `backend/prod-apne2-qwarty-backend-task-def.json`
- Workflow: `.github/workflows/deploy-real.yaml`

## Critical Gotchas

- **Backend 모듈 경로**: `uvicorn backend.main:app` (~~app.main:app~~ 아님)
- **DB 세션 선택**: 읽기 전용 엔드포인트는 반드시 `get_read_session_dependency()` 사용
- **프론트엔드 API**: 반드시 `src/lib/api.ts` 경유, 직접 fetch 금지
- **이미지 업로드**: S3 presigned POST 방식, 클라이언트 사이드 압축 후 업로드
- **성능 기준**: LCP <2000ms, FCP <1000ms, CLS <0.1, TTI <2500ms, TBT <300ms
- **Pre-commit**: backend에서 black, isort, ruff, mypy 자동 실행 (`.pre-commit-config.yaml`)

