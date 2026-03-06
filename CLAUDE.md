# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**StepZero** - AI 기반 스타트업 창업자 액셀러레이팅 플랫폼. 사용자 입력으로 개인화 로드맵을 생성하고, RAG 기반 법률/창업 상담을 제공.

## Monorepo Structure

```
step-zero/
├── app-backend/       # FastAPI backend (Python 3.11, port 8000)
├── app-frontend/      # Next.js 16 frontend (React 18, port 3000)
├── docs/              # 기획/설계/컨텍스트 문서
│   ├── context/       # 세션 운영 (상태/결정/핸드오프/규칙)
│   ├── plans/         # 기획 + 구현 통합 (active/, reports/, done/)
│   ├── architecture/  # 시스템 아키텍처 설계
│   ├── operations/    # 팀 협업 프로세스 규칙
│   ├── dev-guide/     # 개발자 가이드/체크리스트
│   └── archive/       # 역할 완료 문서 보관
├── scripts/           # 루트 유틸리티 스크립트
├── docker-compose.dev.yml   # 개발 환경 (5 services)
├── docker-compose.prod.yml  # 프로덕션 환경
├── AGENTS.md          # AI 에이전트 프로젝트 규칙
└── CLAUDE.md          # 이 파일
```

## Quick Commands

### Backend (`cd app-backend`)

```bash
make setup            # 개발환경 초기화 (uv sync + .env)
make run              # uv run uvicorn app.main:app --reload --port 8000
make worker           # ARQ 비동기 워커 (로드맵 생성용)
make test             # uv run pytest -q (eval 제외, ~30초)
make test-eval        # RAG 평가 전체 (OpenAI API + PostgreSQL 필요)
make test-eval-t2     # Tier 2 평가만 (~5분, ~$2-5)
make test-eval-t3     # Tier 3 전체 평가 (~15분, ~$15-25)
make migrate-up       # alembic upgrade head
make migrate-revision m="description"  # 새 마이그레이션 생성
make migrate-verify   # 모델 ↔ DB 스키마 diff 검증
make rag-bootstrap    # RAG 벡터 시드 적재
```

### Frontend (`cd app-frontend`)

```bash
pnpm install          # 의존성 설치
pnpm dev              # next dev --webpack (localhost:3000)
pnpm build            # 프로덕션 빌드
pnpm lint             # ESLint
pnpm test             # Jest
pnpm types:sync       # OpenAPI → TypeScript 타입 자동 생성
```

### Code Quality (Backend)

```bash
cd app-backend
black .               # 코드 포맷
isort . --profile black  # import 정렬
flake8 .              # 린트
mypy .                # 타입 체크
```

### Docker Compose (전체 스택)

```bash
docker compose -f docker-compose.dev.yml up -d --build     # 전체 실행
docker compose -f docker-compose.dev.yml up -d app-db app-redis  # DB+Redis만
docker compose -f docker-compose.dev.yml logs -f app-backend app-worker  # 로그
```

### Quality Gates (변경 완료 전 반드시 실행)

```bash
cd app-backend && uv run pytest -q             # 백엔드 변경 시
cd app-frontend && pnpm lint                   # 프론트엔드 변경 시
```

## Git Workflow

- **`develop`**: 기본 브랜치 (개발 통합)
- **`main`**: 프로덕션 (직접 push 금지, `develop`에서만 PR 머지)
- **`feature/*`**: 기능 브랜치 → `develop`으로 PR
- 브랜치 명명: `feature/<issue-number>-<short-slug>`
- 커밋: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `perf:`, `ci:`, `build:`, `revert:`)
- PR 제목/설명: 한국어
- 루트에서 `pnpm install` 1회 실행 → Husky + commitlint 훅 활성화

## Backend Architecture

**Framework:** FastAPI + SQLModel/SQLAlchemy + asyncpg (async)

### Feature-Based Structure

비즈니스 로직은 `app-backend/app/features/{feature}/`에 위치. 각 feature는 `domain/`(모델)과 `application/`(서비스) 레이어로 분리.

| Feature | 역할 |
|---------|------|
| `auth` | 이메일/Google OAuth 로그인, JWT 토큰, 팀 자동 생성 |
| `profile` | 사용자 프로필 CRUD |
| `dashboard` | 대시보드 통계 |
| `roadmaps` | 핵심 - AI 로드맵 생성/관리 (비동기 파이프라인) |
| `rag` | RAG + 시맨틱 라우팅 기반 법률/일반 AI 채팅 |
| `actionkit` | 법률 행정 키트 (파일 + 체크리스트) |
| `growth_club` | 커뮤니티 게시판 |
| `ops` | 관리자 콘솔 (superuser only) |

### Shared Layers

- `app/repositories/` - 공유 데이터 접근 (user, team, roadmap, actionkit)
- `app/models/` - SQLModel ORM 모델
- `app/services/` - 공통 서비스 (vector_store, law_etl, actionkit_etl)
- `app/api/v1/{feature}/` - HTTP 라우터 (`/api/v1` prefix)
- `app/api/problem.py` - RFC 7807 에러 응답 (`application/problem+json`)

### Key Subsystems

**로드맵 생성 파이프라인 (비동기):**
1. `POST /api/v1/roadmaps/jobs` → Job 생성 (status: QUEUED)
2. Redis/ARQ로 `app-worker` 서비스에 enqueue
3. `RoadmapGenerationService` → ActionKitMatcher + LLMPersonalizer
4. 프론트엔드가 `GET /api/v1/roadmaps/jobs/{id}` 폴링

**RAG 시스템:**
- `RagService` - PGVector + OpenAI 임베딩 검색
- `ChatService` - 법률 쿼리 → RAG, 일반 쿼리 → LLM 직접 (SemanticRouter로 분류)
- 벡터 스토어: pgvector `law_vectors` 컬렉션

**인증:**
- JWT Bearer 토큰 (access + refresh)
- 프론트엔드: localStorage 저장, Axios 인터셉터로 silent refresh
- 팀 컨텍스트: `X-Team-Id` 헤더
- 관리자: `is_superuser=True`, `require_platform_admin` 의존성

### Multi-Tenancy

모든 비즈니스 데이터는 `Team` (UUID) 스코프. 가입 시 개인 팀 자동 생성. `TeamMember` 테이블로 역할 관리 (`owner`, `admin`, `member`).

### Database

- PostgreSQL 16 + pgvector
- 단일 세션 (`get_session()`) - Read/Write 분리 없음
- Alembic 마이그레이션 (`app-backend/alembic/versions/` 8개 파일)
- 테스트: SQLite in-memory (`sqlite+aiosqlite`)

### ARQ Worker

로드맵 비동기 생성 전용. 별도 Docker 서비스 `app-worker`로 실행:
```bash
cd app-backend && make worker
```

## Frontend Architecture

**Framework:** Next.js 16 (App Router) + React 18 + TypeScript + Tailwind CSS 3.3

### UI Stack

- **컴포넌트:** Radix UI + shadcn/ui 패턴 (`src/components/ui/`)
- **스타일링:** Tailwind CSS 3.3
- **아이콘:** Lucide React
- **DnD:** @hello-pangea/dnd (로드맵 단계 재정렬)
- **HTTP:** Axios (`src/lib/api-client.ts`) + 토큰 인터셉터
- **인증:** AuthProvider (`src/providers/`) + `useSyncExternalStore` (탭 간 동기화)
- **OAuth:** Google (@react-oauth/google)

### Feature Structure

`app-frontend/src/features/{feature}/`로 모듈화. 각 feature는 `index.ts`로만 export. 크로스 feature 내부 경로 import 금지. 공유 타입은 `features/shared/contracts/index.ts`.

### Route Groups (`src/app/`)

- `(dashboard)/` - 대시보드, 로드맵, 액션킷, 커뮤니티, 프로필, 관리자, 공지, 설정
- `/login` - 로그인 페이지

### API Type Generation

```bash
pnpm types:sync     # 백엔드 OpenAPI → src/lib/api-types.ts 자동 생성
```
`api-types.ts`는 자동 생성 파일. 수동 편집 금지.

## Docker Compose Services

| 서비스 | 이미지/역할 | 포트 |
|--------|------------|------|
| `app-db` | pgvector/pgvector:pg16 | 5432 |
| `app-redis` | redis:alpine | 6379 |
| `app-backend` | FastAPI API 서버 | 8000 |
| `app-worker` | ARQ 비동기 워커 | - |
| `app-frontend` | Next.js | 3000 |

## Testing

### Backend (Pytest)

```bash
cd app-backend && make test
```
- `pytest-asyncio` (asyncio_mode = "auto")
- 테스트 DB: SQLite (`sqlite+aiosqlite`)
- `tests/conftest.py`에서 테스트 유저/팀 시드
- 디렉토리: `tests/api/`, `tests/integration/`, `tests/services/`
- 마커: `@pytest.mark.requires_openai` - OPENAI_API_KEY 필요 테스트

### Frontend (Jest)

```bash
cd app-frontend && pnpm test
```
- `@testing-library/react` + `jest-environment-jsdom`
- 테스트: `src/features/{feature}/__tests__/`

## Environment Files

| 파일 | 용도 |
|------|------|
| `app-backend/.env` | 공유 기본값 (비밀키 금지) |
| `app-backend/.env.local` | 로컬 비밀값 (Git 제외) |
| `app-backend/.env.docker.local` | Docker Compose override |
| `app-frontend/.env` | `NEXT_PUBLIC_*` 기본값 |
| `app-frontend/.env.local` | 로컬 비밀값 |

우선순위: `.env` → `.env.local` → `.env.docker.local` (후자가 덮어씀)

## Data Seeding

```bash
# ActionKit 마이그레이션 + 시드
cd app-backend && ACTIONKIT_BOOTSTRAP_MODE=docker ./scripts/bootstrap_actionkit.sh

# RAG 벡터 시드
cd app-backend && RAG_BOOTSTRAP_MODE=docker ./scripts/bootstrap_rag.sh
```

## Document Management

### 문서 구조
- `docs/plans/active/{topic}/` — 기획(PLAN) + 구현(tasks/context)이 같은 폴더에 공존
- `docs/plans/reports/` — 독립 리서치 보고서 (REPORT-*.md)
- `docs/plans/done/` — 완료 아카이브 (폴더째 이동)
- PLAN 파일에 구현 상세를 작성하지 않는다 (별도 tasks/context 파일 사용)
- `/dev-docs` 커맨드로 `docs/plans/active/{topic}/` 하위에 3파일 세트 생성

### 네이밍 규칙
- 계획: `PLAN-<topic>.md`, 보고서: `REPORT-<topic>.md`
- 영문 + 케밥케이스, 파일명 버전 접미사(`_v2`) 지양

### 크기 가이드
- `dev-status.md`: 50줄 이내
- `handoff.md`: 40줄 이내

## Context Continuity

세션 시작 시 반드시 읽을 파일 (순서대로):
1. `docs/context/dev-status.md` - 현재 개발 상태/다음 액션
2. `docs/context/decisions.md` - 확정된 기술 결정
3. `docs/context/handoff.md` - 세션 핸드오프 요약
4. `docs/context/ops-rules.md` - 운영 규칙

사용자가 `핸드오프`/`마무리`/`종료` 요청 시:
1. `dev-status.md` 상태 갱신
2. `decisions.md` 확정사항 기록
3. `handoff.md` 다음 시작점 작성 후 커밋 대기

## Browser Testing (Chrome DevTools MCP)

프론트엔드 브라우저 테스트/성능 측정 시 **chrome-devtools MCP** 사용:

```
1. mcp__chrome-devtools__navigate_page({ url: "http://localhost:3000" })
2. mcp__chrome-devtools__take_snapshot({ verbose: false })
3. mcp__chrome-devtools__list_console_messages()
4. mcp__chrome-devtools__performance_start_trace({ reload: true, autoStop: true })
5. mcp__chrome-devtools__take_screenshot({ fullPage: true })
```

Core Web Vitals 목표: LCP <2000ms, FCP <1000ms, CLS <0.1, TTI <2500ms, TBT <300ms

## Code Search Strategy

- **정의/참조 추적**: LSP 우선 (`goToDefinition`, `findReferences`) — Grep보다 정확하고 오탐 없음
- **텍스트/패턴 검색**: Grep 사용 — TODO/FIXME, 에러 메시지, 환경변수, `.md`/`.yml`/`.env` 등 비코드 파일
- **리팩토링 영향 분석**: LSP `findReferences` → `incomingCalls` 순서로 호출 체인 파악
- **대규모 탐색**: Grep으로 후보 좁히기 → LSP로 정확한 참조 확인 (2단계 전략)
- **파일 구조 파악**: LSP `documentSymbol` 우선 — 전체 Read 없이 함수/클래스 목록 확인

## Important Notes

- **모듈 경로:** `app.main:app` (uvicorn 실행 시)
- **API 포트:** 백엔드 8000, 프론트엔드 3000
- **DB 세션:** `get_session()` 단일 팩토리 사용 (Read/Write 분리 없음)
- **파일 저장:** 로컬 파일시스템 (`STORAGE_LOCAL_ROOT` 환경변수), S3 아님
- **`app-worker` 필수:** 로드맵 비동기 생성은 워커 서비스 실행 필요
- **임시 파일:** `.temp/artifacts/`에 저장, 커밋 금지
