# 패키지 매니저 마이그레이션 컨텍스트

> Last Updated: 2026-03-05

## Related Planning Doc

- `docs/planning/PLAN-package-manager-migration.md` — 배경/목표/리스크 상세

## Prerequisite: 인증 패키지 교체 (Phase 0)

> Python 3.13 업그레이드를 위한 **필수 선행 작업**. 패키지 매니저 마이그레이션(Phase A~D)과 독립적이지만, 런타임 업그레이드(Phase E) 전에 반드시 완료해야 함.

### 차단 요소 상세

| 패키지 | 문제 | 영향 |
|--------|------|------|
| `passlib[bcrypt]>=1.7.4` | (1) Python 3.13에서 `crypt` stdlib 제거 (PEP 594) → 내부 의존 깨짐<br>(2) bcrypt 5.x가 `__about__.__version__` 제거 → 버전 감지 실패<br>(3) 마지막 릴리스 2020년, 유지보수 중단 | `security.py:7,21,26,30` — `CryptContext`, `verify()`, `hash()` |
| `bcrypt<4` | passlib 호환을 위한 제약이나 보안 패치 차단 | `pyproject.toml` 제약 |
| `python-jose[cryptography]>=3.3.0` | CVE-2024-33663 (ECDSA 혼동), CVE-2024-33664 (JWT bomb)<br>2021년 이후 유지보수 중단 | `security.py:6,58`, `deps.py:6-7,34,128,173` |

### 교체 대상 파일

| 파일 | 현재 | 변경 |
|------|------|------|
| `app-backend/pyproject.toml` | `passlib[bcrypt]>=1.7.4`, `bcrypt<4`, `python-jose[cryptography]>=3.3.0` | `bcrypt>=4.0.0`, `PyJWT>=2.8.0` |
| `app-backend/app/core/security.py` | `from passlib.context import CryptContext`<br>`from jose import jwt` | `import bcrypt` 직접 사용<br>`import jwt` (PyJWT) |
| `app-backend/app/api/deps.py` | `from jose import JWTError, jwt`<br>`from jose.exceptions import ExpiredSignatureError` | `import jwt`<br>`from jwt.exceptions import InvalidTokenError, ExpiredSignatureError` |

## Key Files

### Backend (uv 전환 대상) — 실행 파일

| 파일 | 역할 | 현재 참조 | 변경 유형 |
|------|------|----------|----------|
| `app-backend/Dockerfile` | 개발 Docker 이미지 | `pip install .[dev]` | pip -> uv sync |
| `app-backend/Dockerfile.prod` | 프로덕션 Docker 이미지 | `pip install .` | pip -> uv sync --no-dev |
| `app-backend/Makefile` | 로컬 명령 단축 | `.venv/bin/uvicorn`, `.venv/bin/python -m pytest` | uv run |
| `app-backend/scripts/setup_dev.sh` | 로컬 개발환경 초기화 | `.venv/bin/python`, pip fallback 이중 경로 | uv 단일 |
| `app-backend/scripts/run_alembic.sh` | Alembic 래퍼 | `.venv/bin/alembic` | uv run alembic |
| `app-backend/scripts/bootstrap_actionkit.sh` | ActionKit 시드 | `.venv/bin/python` (local 모드) | uv run python |
| `app-backend/scripts/bootstrap_rag.sh` | RAG 벡터 시드 | `.venv/bin/python` (local 모드) | uv run python |
| `app-backend/pyproject.toml` | 프로젝트 정의 | `[build-system]` setuptools | 유지 |
| `app-backend/uv.lock` | uv lock 파일 | 이미 존재 | 유지 |

### Frontend (pnpm 전환 대상) — 실행 파일

| 파일 | 역할 | 현재 참조 | 변경 유형 |
|------|------|----------|----------|
| `app-frontend/Dockerfile` | 개발 Docker 이미지 | `npm install` | corepack + pnpm |
| `app-frontend/Dockerfile.prod` | 프로덕션 Docker 이미지 | `npm ci` | pnpm install --frozen-lockfile |
| `app-frontend/package.json` | 프로젝트 정의 | `types:sync` 내 `npm run` | pnpm 참조 |
| `app-frontend/package-lock.json` | npm lock | 존재 | **삭제** |
| `app-frontend/pnpm-lock.yaml` | pnpm lock | 이미 존재 | 유지 |
| `app-frontend/.npmrc` | pnpm 설정 | 없음 | **신규 생성** |

### Root

| 파일 | 역할 | 현재 참조 | 변경 유형 |
|------|------|----------|----------|
| `package.json` | Husky + commitlint | npm 기반 | packageManager 필드 추가 |
| `package-lock.json` | npm lock | 존재 (untracked) | **삭제** |

### CI/CD

| 파일 | 현재 참조 | 변경 유형 |
|------|----------|----------|
| `.github/workflows/ci.yml` (L152-153) | `pip install --upgrade pip` + `pip install -e ".[dev]"` | uv로 전환 |
| `.github/workflows/ci.yml` (L165-178) | pnpm 이미 사용 중 | 변경 불필요 (이미 pnpm) |
| `.github/pull_request_template.md` (L10-11) | `.venv/bin/pytest -q`, `npm run lint` | `uv run pytest`, `pnpm lint` |

### Husky Hooks

| 파일 | 현재 참조 | 변경 유형 |
|------|----------|----------|
| `.husky/pre-push` (L23) | `.venv/bin/pytest -q` | `uv run pytest -q` |
| `.husky/pre-push` (L26) | `npm run lint` | `pnpm lint` |

### Docker Compose

| 파일 | 변경 내용 |
|------|----------|
| `docker-compose.dev.yml` (L48) | backend command: `uv run uvicorn ...` |
| `docker-compose.dev.yml` (L74) | worker command: `uv run python -m arq ...` |
| `docker-compose.dev.yml` (L98) | frontend command: `pnpm dev` |
| `docker-compose.prod.yml` | Dockerfile CMD 활용, command 명시 불필요 |

### 문서 (pip/npm/.venv 참조 포함)

| 파일 | 참조 내용 | 변경 유형 |
|------|----------|----------|
| `CLAUDE.md` | Quick Commands, Quality Gates 전반 | npm/pip -> pnpm/uv |
| `AGENTS.md` (L20, L36-37) | `npm run dev`, `npm run lint`, `.venv/bin/pytest` | pnpm/uv |
| `README.md` (L158-162, L300) | `npm install`, `npm run dev`, `npm run types:sync` | pnpm |
| `docs/dev-guide/junior-playbook.md` (L11-12) | `.venv/bin/pytest`, `npm run lint` | uv/pnpm |
| `docs/dev-guide/new-work-checklist.md` (L21) | `pytest -q / npm run lint` | uv/pnpm |
| `docs/operations/project-operation-rules.md` (L44, L61, L66-68, L74) | `.venv/bin/pytest`, `npm run dev/lint/types:sync` | uv/pnpm |
| `docs/operations/linear-github-rules.md` (L84-85) | `.venv/bin/pytest`, `npm run lint` | uv/pnpm |
| `app-backend/app/features/AGENTS.md` (L19) | `.venv/bin/pytest -q` | uv run pytest |
| `app-backend/app/features/*/AGENTS.md` (7개) | `.venv/bin/pytest -q` | uv run pytest |
| `docs/dev/active/r2-storage-migration/` (3곳) | `.venv/bin/pytest`, `pip install` | uv 참조로 갱신 |

### 문서 (done/ 아카이브) — 변경 제외

`docs/dev/done/`, `docs/planning/completed/`, `docs/dev-guide/phase4-*.md` 내 참조는 **역사적 기록이므로 변경하지 않는다**. 단, 현재 활성 문서(`active/`)는 갱신한다.

## Key Decisions

| 결정 | 근거 |
|------|------|
| uv 버전 0.9.26 고정 | Dockerfile에서 `ghcr.io/astral-sh/uv:0.9` 태그로 핀 |
| `.uv-version` 파일은 참고용 | uv가 공식 지원하지 않음, Dockerfile 이미지 태그가 실제 버전 관리 수단 |
| Dockerfile에서 `COPY --from` 패턴 사용 | 시스템 패키지 설치 불필요, 바이너리 복사만으로 충분 |
| `[build-system]` setuptools 유지 | uv는 build-system 무관하게 sync 가능, 불필요한 변경 회피 |
| pnpm `node-linker=hoisted` 사용 | npm 호환 flat node_modules 구조 유지, Next.js 호환성 보장 |
| corepack으로 pnpm 관리 | Node 20에 내장, 별도 설치 불필요, 버전 고정 가능 |
| `--frozen-lockfile` Docker에서 사용 | 재현 가능한 빌드 보장, lock 변경 방지 |
| done/ 아카이브 문서는 변경 안 함 | 역사적 기록 보존, 현재 활성 문서만 갱신 |
| CI backend-tests job도 uv 전환 | pip -> `astral-sh/setup-uv` action + `uv sync` |
| passlib/python-jose 교체 선행 | Python 3.13 EOL 대응 필수, 보안 취약점 해소 |
| 런타임 업그레이드는 패키지 매니저 마이그레이션 완료 후 별도 진행 | 동시 변경 시 원인 파악 곤란 |

## Version Compatibility Matrix

### 현재 버전 vs 최신 안정 버전

| 항목 | 현재 사용 | 최신 안정 | EOL | 권장 |
|------|----------|----------|-----|------|
| Python | 3.11 | 3.14.3 | **2026-05 (2개월 후)** | 3.13 |
| Node.js | 20 | 24.14.0 LTS | **2026-04-30 (2개월 후)** | 22 LTS |
| React | ^18 | 19.2.4 | 18 LTS 지원 중 | 유지 가능 |
| Next.js | ^16.1.6 | 16.1.6 | 최신 | 유지 |
| TypeScript | ^5 | 5.8 / 6.0 beta | 5.x 지원 중 | 유지 |
| uv | 0.9.26 | 0.10.8 | — | 0.9.26 유지 후 점진 업그레이드 |
| pnpm | 9.x (CI) | 10.30.3 | — | 9.x 유지 후 점진 업그레이드 |

### Python 3.13 업그레이드 호환성

| 패키지 | 판정 | 비고 |
|--------|------|------|
| **passlib[bcrypt] + bcrypt<4** | 비호환 | Phase 0에서 교체 필수 |
| **python-jose[cryptography]** | 비호환(보안) | Phase 0에서 교체 필수 |
| sqlalchemy | 주의 | `>=2.0.44`로 하한 상향 권장 |
| langchain 계열 | 주의 | 3.13 호환, 3.14는 미완성 (Issue #34441) |
| arq | 주의 | maintenance-only 선언, 동작은 함 |
| fastapi, uvicorn, asyncpg, sqlmodel | 호환 | — |
| psycopg2-binary, greenlet, numpy, tiktoken | 호환 | cp313/cp314 wheel 확인됨 |
| openai, redis, alembic, pdfplumber | 호환 | — |
| pytest, black, mypy 등 dev | 호환 | — |

### Node.js 22 LTS 업그레이드 호환성

| 패키지 | 판정 | 비고 |
|--------|------|------|
| `@types/node ^20` | 변경 필요 | `^22`로 업데이트 |
| ts-node ^10.9.2 | 주의 | 현재 직접 실행 경로 없음, 장기적으로 tsx 교체 권고 |
| next, react, jest, eslint, tailwindcss | 호환 | — |
| 나머지 전부 | 호환 | browser-only / pure JS |

### pnpm 10 업그레이드 시 주의 (향후)

| 항목 | 비고 |
|------|------|
| Lifecycle scripts 기본 차단 | `onlyBuiltDependencies`에 husky, esbuild, @next/swc-* 추가 필요 |
| `.npmrc` -> `pnpm-workspace.yaml` | pnpm 10에서 설정 파일 위치 이동 |
| Corepack 호환 | corepack 0.31.0 미만에서 pnpm 10 설치 실패 사례 보고 |

### uv 0.10 업그레이드 시 주의 (향후)

| 항목 | 비고 |
|------|------|
| `uv venv` 재생성 | `--clear` 플래그 필요 |
| Docker 이미지 태그 | `ghcr.io/astral-sh/uv:0.10`으로 변경 |

## Dependencies Between Tasks

```
Phase 0 (인증 패키지 교체 — 선행 필수):
0-1 (pyproject.toml) ──┐
0-2 (security.py)    ──┼─→ 0-4 (테스트 검증)
0-3 (deps.py)        ──┘

Phase A (Backend):
A-1 (Dockerfile) ──┐
A-2 (Dockerfile.prod)┤
A-3 (Makefile)   ──┤
A-4 (setup_dev)  ──┤
A-5 (run_alembic)──┼─→ A-11 (빌드 검증)
A-6 (bootstrap_*) ┤
A-7 (compose dev)──┤
A-8 (compose prod)─┤
A-9 (pyproject)  ──┘

Phase B (Frontend):
B-1 (lock 삭제)  ──┐
B-2 (packageMgr) ──┤
B-3 (.npmrc)     ──┤
B-4 (Dockerfile) ──┼─→ B-11 (빌드 검증)
B-5 (Dockerfile.prod)┤
B-6 (compose)    ──┤
B-7 (scripts)    ──┤
B-8 (root init)  ──┘

Phase C (CI/Hooks):
C-1 (ci.yml)     ──┐
C-2 (PR template)──┼─→ C-4 (검증)
C-3 (pre-push)   ──┘

Phase D (문서):
A-11 + B-11 + C-4 ─→ D-1~D-11 (문서 일괄)

Phase E (런타임 업그레이드 — Phase 0 + Phase A~D 완료 후):
E-1 (Python 3.11 -> 3.13) ──┐
E-2 (Node.js 20 -> 22)    ──┼─→ E-5 (전체 빌드/테스트 검증)
E-3 (@types/node ^22)     ──┤
E-4 (sqlalchemy>=2.0.44)  ──┘
```

## Rollback Strategy

전환 실패 시:
1. Dockerfile의 pip/npm 라인 복원 (git revert)
2. package-lock.json 복원 (git checkout)
3. Makefile의 .venv/bin/ 경로 복원
4. .husky/pre-push 복원
5. CI workflow 복원
6. 모든 변경은 단일 feature 브랜치에서 진행하므로 develop에 영향 없음
