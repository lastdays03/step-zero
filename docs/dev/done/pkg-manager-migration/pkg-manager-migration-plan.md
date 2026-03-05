# 패키지 매니저 마이그레이션 구현 계획

> Last Updated: 2026-03-05

## Executive Summary

Backend를 **uv** 단일 매니저로, Frontend(+Root)를 **pnpm** 단일 매니저로 전환한다.
현재 uv.lock과 pnpm-lock.yaml이 이미 존재하여 기본 호환성이 확보된 상태이므로, Dockerfile/Makefile/스크립트/docker-compose/CI/Hooks/문서의 참조를 일괄 정리하는 작업이 핵심이다.

**추가**: 호환성 검토 결과, Python 3.13 업그레이드를 위한 **인증 패키지 교체**(Phase 0)가 필수 선행 작업으로 식별되었다. 런타임 버전 업그레이드(Phase E)는 패키지 매니저 마이그레이션 완료 후 별도 진행한다.

## Phased Approach

```
Phase 0 ──→ Phase A~D ──→ Phase E
(인증 교체)  (패키지 매니저)  (런타임 업그레이드)
```

- **Phase 0**: passlib/python-jose 교체 (Python 3.13 차단 해제)
- **Phase A~D**: 패키지 매니저 마이그레이션 (기존 계획)
- **Phase E**: Python 3.11→3.13, Node.js 20→22 LTS (EOL 대응)

---

## Phase 0: 인증 패키지 교체 (필수 선행)

Python 3.13에서 **passlib이 완전 동작 불가**하고, **python-jose에 보안 취약점 2건**(CVE-2024-33663, CVE-2024-33664)이 존재한다. 런타임 업그레이드(Phase E) 전에 반드시 해결해야 한다.

**0-1. pyproject.toml 의존성 교체** (Effort: S)
- `passlib[bcrypt]>=1.7.4` 제거
- `bcrypt<4` 제거
- `python-jose[cryptography]>=3.3.0` 제거
- `bcrypt>=4.0.0` 추가
- `PyJWT>=2.8.0` 추가
- 수락 기준: `uv lock` 정상 완료

**0-2. security.py 교체** (Effort: S)
- passlib CryptContext → bcrypt 직접 사용

```python
# Before
from passlib.context import CryptContext
from jose import jwt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

encoded_jwt = jwt.encode(to_encode, key, algorithm=algo)

# After
import bcrypt
import jwt

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )

def get_password_hash(password):
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

encoded_jwt = jwt.encode(to_encode, key, algorithm=algo)
```

- 수락 기준: 기존 해시된 비밀번호로 로그인 성공

**0-3. deps.py JWT 교체** (Effort: S)
- `from jose import JWTError, jwt` → `import jwt` + `from jwt.exceptions import ...`
- `JWTError` → `jwt.exceptions.InvalidTokenError`
- `ExpiredSignatureError` → `jwt.exceptions.ExpiredSignatureError`
- `jwt.decode()` API는 동일 (algorithms 파라미터 호환)
- 수락 기준: JWT 인증 플로우 정상 (encode/decode/만료/무효)

**0-4. 테스트 검증** (Effort: S)
- `make test` 전체 통과
- 인증 관련 테스트 집중 확인 (로그인, 회원가입, 토큰 갱신, 만료)
- 수락 기준: pytest 전체 통과, 기존 bcrypt 해시 호환 확인

---

## Current State Analysis

### Backend
- `pyproject.toml` + `uv.lock` 존재 (uv로 해석 가능)
- `setup_dev.sh`: uv 우선 -> 실패 시 pip fallback (이중 경로, 94줄)
- `Makefile`: `.venv/bin/` 직접 참조 (run, worker, test)
- `Dockerfile`/`Dockerfile.prod`: `pip install` 사용
- `run_alembic.sh`: `.venv/bin/alembic` 직접 참조
- `bootstrap_actionkit.sh`, `bootstrap_rag.sh`: `.venv/bin/python` (local 모드)
- `build-system`: setuptools (-> 유지 가능, uv는 build-system 무관)
- `stepzero_backend.egg-info/` 디렉토리 존재 (정리 필요)

### Frontend
- `package-lock.json` + `pnpm-lock.yaml` 공존 (불일치 위험)
- `Dockerfile`: `npm install`
- `Dockerfile.prod`: `npm ci`
- `docker-compose.dev.yml`: `command: npm run dev`
- `.npmrc`: 없음

### Root
- `package.json`: Husky + commitlint (npm 기반)
- `package-lock.json`: 존재 (git untracked 상태)

### CI/CD & Hooks
- `.github/workflows/ci.yml` backend-tests: `pip install -e ".[dev]"` 사용
- `.github/workflows/ci.yml` frontend-lint: **이미 pnpm 사용** (변경 불필요)
- `.github/pull_request_template.md`: `.venv/bin/pytest`, `npm run lint`
- `.husky/pre-push`: `.venv/bin/pytest -q`, `npm run lint`

### 문서 (활성 파일 중 참조 포함)
- `CLAUDE.md`, `AGENTS.md`, `README.md`: pip/npm/.venv 참조 다수
- `docs/dev-guide/`: junior-playbook, new-work-checklist
- `docs/operations/`: project-operation-rules, linear-github-rules
- `app-backend/app/features/*/AGENTS.md`: 8개 파일 모두 `.venv/bin/pytest`
- `docs/dev/active/r2-storage-migration/`: 활성 태스크에 venv/pip 참조

## Proposed Future State

### Backend
- **uv만 사용** — pip/venv 직접 호출 제거
- Dockerfile: `COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/` + `uv sync`
- Makefile/스크립트: `uv run <cmd>` 패턴
- CI: `astral-sh/setup-uv` action
- `.venv/` 디렉토리: uv가 자동 관리 (프로젝트 내 `.venv`)

### Frontend + Root
- **pnpm만 사용** — npm 참조 완전 제거
- Dockerfile: `corepack enable` + `pnpm install --frozen-lockfile`
- `package-lock.json` 삭제 (root + app-frontend)
- Root `package.json`에 `"packageManager": "pnpm@9.x"` 추가
- CI frontend-lint: 이미 pnpm 사용 (변경 불필요)

### CI/CD & Hooks
- `.github/workflows/ci.yml` backend-tests: uv 사용
- `.husky/pre-push`: `uv run pytest`, `pnpm lint`
- `.github/pull_request_template.md`: `uv run pytest`, `pnpm lint`

---

## Implementation Phases (A~D: 패키지 매니저 마이그레이션)

### Phase A: Backend uv 전면 전환

uv.lock이 이미 존재하고 setup_dev.sh에 uv 경로가 구현되어 있어 난이도 낮음.

**A-1. Dockerfile 전환** (Effort: S)
- `Dockerfile`: pip -> uv sync --extra dev --frozen
- 멀티스테이지 COPY로 uv 바이너리 주입: `COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/`
- `ghcr.io/astral-sh/uv:latest` 사용 금지 — 버전 태그 고정 필수
- 수락 기준: `docker build -f Dockerfile .` 성공

**A-2. Dockerfile.prod 전환** (Effort: S)
- `Dockerfile.prod`: pip -> uv sync --no-dev --frozen
- build-essential 제거 가능 여부 확인
- 수락 기준: `docker build -f Dockerfile.prod .` 성공

**A-3. Makefile 전환** (Effort: S)
- `.venv/bin/uvicorn` -> `uv run uvicorn`
- `.venv/bin/python -m pytest` -> `uv run pytest`
- `.venv/bin/python -m arq` -> `uv run python -m arq`
- 수락 기준: `make run`, `make test`, `make worker` 로컬 정상

**A-4. setup_dev.sh 단순화** (Effort: S)
- pip fallback 경로 제거 (94줄 -> ~20줄로 축소)
- macOS 우회 로직 제거 (uv 0.9는 안정화됨)
- `uv sync --extra dev` 단일 호출
- uv 미설치 시 설치 안내 메시지
- 수락 기준: `make setup` 정상

**A-5. run_alembic.sh 전환** (Effort: S)
- `.venv/bin/alembic` -> `uv run alembic`
- 수락 기준: `make migrate-up`, `make migrate-revision m="test"` 정상

**A-6. bootstrap_actionkit.sh + bootstrap_rag.sh 전환** (Effort: S)
- `run_local()` 내 `.venv/bin/python` -> `uv run python`
- PYTHON_BIN 분기 로직 단순화
- 수락 기준: `ACTIONKIT_BOOTSTRAP_MODE=local ./scripts/bootstrap_actionkit.sh` 정상

**A-7~A-8. docker-compose command 업데이트** (Effort: S)
- `docker-compose.dev.yml`: backend/worker command에 `uv run` 적용
- `docker-compose.prod.yml`: Dockerfile.prod CMD 활용 확인
- 수락 기준: `docker compose up app-backend app-worker` 정상

**A-9. pyproject.toml 정리** (Effort: S)
- `[build-system]` setuptools 유지
- `stepzero_backend.egg-info/` 삭제 + `.gitignore` 추가
- 수락 기준: `uv sync --extra dev` 경고 없이 완료

**A-10. 빌드 검증** (Effort: S)
- Docker dev/prod 빌드 + 서비스 기동
- `make test` 통과
- 수락 기준: 전체 서비스 docker-compose up 정상 + pytest 통과

### Phase B: Frontend pnpm 전환

pnpm-lock.yaml이 이미 존재하므로 기본 호환성 확인됨.

**B-1~B-2. package-lock.json 삭제 + packageManager 설정** (Effort: S)
- `app-frontend/package-lock.json` 삭제
- `package-lock.json` (root) 삭제
- Root `package.json`에 `"packageManager": "pnpm@9.x"` 추가
- 수락 기준: git에서 package-lock.json 완전 제거

**B-3. .npmrc 생성** (Effort: S)
- `app-frontend/.npmrc`: `node-linker=hoisted`
- 수락 기준: `pnpm install` 후 기존 import 호환

**B-4~B-5. Dockerfile 전환** (Effort: S)
- dev/prod 모두: npm -> corepack + pnpm install --frozen-lockfile
- COPY에 `.npmrc` 포함
- 수락 기준: docker build 성공

**B-6. docker-compose command 업데이트** (Effort: S)
- `docker-compose.dev.yml`: `npm run dev` -> `pnpm dev`
- 수락 기준: `docker compose up app-frontend` 정상

**B-7. package.json scripts 수정** (Effort: S)
- `types:sync` 내 `npm run` -> `pnpm` 참조
- 수락 기준: `pnpm types:sync` 정상

**B-8. Root pnpm 초기화** (Effort: S)
- Root에서 `pnpm install` -> pnpm-lock.yaml 생성
- Husky + commitlint 동작 확인
- 수락 기준: `git commit` 시 commitlint 훅 트리거

**B-9. 빌드 검증** (Effort: S)
- Docker dev/prod 빌드 + 서비스 기동
- `pnpm lint` + `pnpm test` 통과
- 수락 기준: 전체 서비스 정상

### Phase C: CI/CD & Hooks 전환

**C-1. GitHub Actions CI workflow** (Effort: S)
- `.github/workflows/ci.yml` backend-tests job:
  - `actions/setup-python` 유지
  - `pip install` -> `astral-sh/setup-uv` + `uv sync --extra dev`
  - `pytest` -> `uv run pytest`
- frontend-lint job: **변경 불필요** (이미 pnpm 사용)
- 수락 기준: PR에서 CI 통과

**C-2. PR 템플릿 업데이트** (Effort: S)
- `.venv/bin/pytest -q` -> `uv run pytest -q`
- `npm run lint` -> `pnpm lint`
- 수락 기준: 참조 갱신 확인

**C-3. Husky pre-push 훅 업데이트** (Effort: S)
- L23: `.venv/bin/pytest -q` -> `uv run pytest -q`
- L26: `npm run lint` -> `pnpm lint`
- 수락 기준: `git push` 시 훅 정상 실행

### Phase D: 문서 & 정리

**D-1. CLAUDE.md** (Effort: M) — 변경량 가장 큼
- Quick Commands: npm -> pnpm, pip/venv -> uv
- Quality Gates: `.venv/bin/pytest` -> `uv run pytest`
- Frontend Architecture: npm 참조 -> pnpm
- Docker Compose, Data Seeding 섹션
- 수락 기준: CLAUDE.md 내 npm/pip/.venv 참조 0건

**D-2. AGENTS.md** (Effort: S)
- L20, L36, L37: npm/pip -> pnpm/uv

**D-3. README.md** (Effort: S)
- Quick Start, Frontend 로컬 실행, 훅 설명: npm -> pnpm
- Backend 스크립트 설명: venv -> uv
- macOS uv 우회 설명 제거/갱신

**D-4~D-7. 운영/가이드 문서** (Effort: S)
- `junior-playbook.md`, `new-work-checklist.md`
- `project-operation-rules.md`, `linear-github-rules.md`
- 모두: `.venv/bin/pytest` -> `uv run pytest`, `npm run lint` -> `pnpm lint`

**D-8. Feature AGENTS.md 8개** (Effort: S)
- `app-backend/app/features/{AGENTS.md,*/AGENTS.md}`: `.venv/bin/pytest` -> `uv run pytest`
- 8개 파일 일괄 sed 가능

**D-9. 활성 태스크 문서 갱신** (Effort: S)
- `docs/dev/active/r2-storage-migration/` 내 venv/pip 참조

**D-10. .gitignore 정리** (Effort: S)
- `stepzero_backend.egg-info/` 추가

**D-11. MEMORY.md 업데이트** (Effort: S)
- 패키지 매니저 결정 기록

---

## Phase E: 런타임 버전 업그레이드 (Phase 0 + A~D 완료 후)

Python 3.11 (EOL: 2026-05)과 Node.js 20 (EOL: 2026-04-30) 모두 2개월 내 지원 종료.
패키지 매니저 마이그레이션 완료 후 즉시 이어서 진행한다.

**E-1. Python 3.11 -> 3.13** (Effort: M)
- Dockerfile: `FROM python:3.11-slim` -> `FROM python:3.13-slim`
- Dockerfile.prod 동일 변경
- CI: `python-version: "3.11"` -> `"3.13"`
- pyproject.toml: `requires-python = ">=3.11"` -> `">=3.13"` (선택)
- `sqlalchemy>=2.0.0` -> `>=2.0.44` 하한 상향 (3.14 greenlet unblock)
- `uv lock` 재실행하여 lock 파일 갱신
- 수락 기준: Docker 빌드 + `make test` 전체 통과
- 주의: Python 3.14는 LangChain 미지원 (Issue #34441), **3.13 권장**

**E-2. Node.js 20 -> 22 LTS** (Effort: S)
- Dockerfile: `FROM node:20-alpine` -> `FROM node:22-alpine`
- Dockerfile.prod 동일 변경
- CI: `node-version: "20"` -> `"22"`
- 수락 기준: Docker 빌드 + `pnpm lint` + `pnpm test` 통과
- 주의: Node 24 LTS도 가능하나 22가 더 안전한 선택

**E-3. @types/node 업데이트** (Effort: S)
- `app-frontend/package.json`: `"@types/node": "^20"` -> `"^22"`
- `pnpm install` 후 타입 체크 통과 확인

**E-4. sqlalchemy 하한 상향** (Effort: S)
- `pyproject.toml`: `sqlalchemy>=2.0.0` -> `sqlalchemy>=2.0.44`
- Python 3.14 greenlet 자동 설치 unblock 버전

**E-5. 전체 빌드/테스트 검증** (Effort: S)
- `docker compose -f docker-compose.dev.yml up -d --build` 전체 정상
- `docker compose -f docker-compose.prod.yml up -d --build` 프로덕션 정상
- `make test` 통과
- `pnpm lint` + `pnpm test` 통과

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Docker 빌드 캐시 전면 무효화 | 확실 | 낮음 (1회성) | lock 파일 먼저 COPY하는 레이어 캐시 전략 |
| uv 버전 드리프트 | 낮음 | 중간 | Dockerfile에서 `ghcr.io/astral-sh/uv:0.9` 태그 고정 |
| pnpm hoisting 호환성 | 낮음 | 중간 | `node-linker=hoisted` + `.npmrc` |
| Husky 훅 깨짐 | 중간 | 낮음 | `pnpm install` 시 `prepare` 자동 실행 |
| 프로덕션 배포 영향 | 낮음 | 높음 | dev 환경 먼저 검증 후 prod 적용 |
| CI workflow 실패 | 중간 | 중간 | feature 브랜치에서 PR로 CI 확인 후 머지 |
| bootstrap 스크립트 깨짐 | 낮음 | 중간 | local/docker 양쪽 모드 테스트 |
| **passlib Python 3.13 비호환** | **확실** | **높음** | **Phase 0에서 선행 교체** |
| **python-jose 보안 취약점** | **확실** | **높음** | **Phase 0에서 PyJWT 전환** |
| **bcrypt 해시 호환성** | 낮음 | 높음 | bcrypt 4.x는 기존 3.x 해시 읽기 호환 |
| Python 3.13 의존성 비호환 | 낮음 | 중간 | uv.lock에 cp313 wheel 존재 확인됨 |
| Node.js 22 의존성 비호환 | 매우 낮음 | 낮음 | 전 의존성 호환 확인됨 |
| langchain Python 3.14 미지원 | 확실 | 중간 | 3.13까지만 업그레이드, 3.14는 보류 |

## Success Metrics

- [ ] Phase 0: passlib/python-jose 완전 제거, pytest 통과
- [ ] Backend: `pip`, `.venv/bin/` 직접 참조 0건 (Dockerfile, Makefile, scripts, CI, hooks)
- [ ] Frontend: `npm` 참조 0건 (Dockerfile, docker-compose, package.json scripts, hooks)
- [ ] `package-lock.json` 파일 저장소 내 0개
- [ ] Docker dev/prod 빌드 + 서비스 기동 성공
- [ ] pytest 384+ passed, lint 0 errors
- [ ] Husky pre-push 훅 정상 (uv run pytest + pnpm lint)
- [ ] GitHub Actions CI 통과
- [ ] 문서 내 실행 명령 일관성 확보
- [ ] Phase E: Python 3.13 + Node.js 22 전환 후 전체 테스트 통과

## Dependencies

- uv >= 0.9.26 (Dockerfile 이미지 태그로 핀)
- pnpm >= 9.x (corepack으로 관리)
- Node.js 20 -> 22 LTS (Phase E)
- Python 3.11-slim -> 3.13-slim (Phase E)
- GitHub Actions: `astral-sh/setup-uv`, `pnpm/action-setup@v4`
- Phase 0 완료 후: `bcrypt>=4.0.0`, `PyJWT>=2.8.0`

## Total Task Count

| Phase | 태스크 수 | 핵심 |
|-------|----------|------|
| 0 (인증 교체) | 4 | pyproject.toml, security.py, deps.py, 테스트 |
| A (Backend uv) | 10 | Dockerfile, Makefile, scripts 5개, compose |
| B (Frontend pnpm) | 9 | lock 삭제, .npmrc, Dockerfile, compose |
| C (CI/Hooks) | 4 | ci.yml, PR template, pre-push, 검증 |
| D (문서) | 11 | CLAUDE.md, AGENTS.md, README.md, feature AGENTS.md x8, 운영 4개 |
| E (런타임) | 5 | Python 3.13, Node 22, @types/node, sqlalchemy, 검증 |
| **합계** | **43** | |
