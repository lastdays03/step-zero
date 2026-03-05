# PLAN: 패키지 매니저 마이그레이션 (Backend: uv, Frontend: pnpm)

> 작성일: 2026-03-05
> 상태: 계획 수립
> 구현 문서: `docs/dev/active/pkg-manager-migration/`

## 1. 배경 및 목표

### 현재 상태

| 영역 | 현재 도구 | Lock 파일 | 비고 |
|------|----------|-----------|------|
| Backend | pip + venv (uv 부분 도입) | `uv.lock` 존재 | `setup_dev.sh`에서 uv 감지 시 사용, 실패 시 pip fallback |
| Frontend | npm | `package-lock.json` + `pnpm-lock.yaml` (공존) | Dockerfile은 `npm install`/`npm ci` 사용 |
| Root | npm (Husky/commitlint) | `package-lock.json` | `npm run prepare`로 Husky 활성화 |

### 문제점

1. **Backend**: uv가 이미 부분 도입(`uv.lock` 존재, `setup_dev.sh`에서 uv 우선 사용)되었으나 Dockerfile과 Makefile은 여전히 pip/venv 기반
2. **Frontend**: `package-lock.json`과 `pnpm-lock.yaml`이 공존하여 lock 파일 불일치 위험
3. **일관성 부재**: 도구 혼용으로 개발자 온보딩 혼란, CI/CD 파이프라인 복잡성 증가
4. **보안 취약점**: `python-jose`에 CVE 2건 (CVE-2024-33663, CVE-2024-33664), `passlib` 유지보수 중단
5. **런타임 EOL 임박**: Python 3.11 (2026-05), Node.js 20 (2026-04-30) 모두 2개월 내 지원 종료

### 목표

- Backend: **uv를 단일 패키지 매니저로 확정** (pip fallback 제거)
- Frontend: **pnpm을 단일 패키지 매니저로 확정** (npm 제거)
- Docker, Makefile, 문서 전반 일관성 확보
- 인증 패키지 보안 취약점 해소 (passlib/python-jose 교체)
- 런타임 EOL 대응 (Python 3.13, Node.js 22 LTS)

---

## 2. 변경 범위 분석

### 2.1 Phase 0: 인증 패키지 교체 (필수 선행)

> Python 3.13 업그레이드 시 **passlib이 완전 동작 불가** — `crypt` stdlib 제거 (PEP 594) + bcrypt 5.x API 변경

| 파일 | 현재 | 변경 내용 |
|------|------|----------|
| `app-backend/pyproject.toml` | `passlib[bcrypt]>=1.7.4`, `bcrypt<4`, `python-jose[cryptography]>=3.3.0` | `bcrypt>=4.0.0`, `PyJWT>=2.8.0` |
| `app-backend/app/core/security.py` | passlib CryptContext + jose jwt | bcrypt 직접 + PyJWT |
| `app-backend/app/api/deps.py` | `from jose import JWTError, jwt` | `import jwt` (PyJWT) |

**코드 변경 예시:**

```python
# security.py — Before
from passlib.context import CryptContext
from jose import jwt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# security.py — After
import bcrypt
import jwt

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
```

```python
# deps.py — Before
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

# deps.py — After
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
# JWTError -> InvalidTokenError
```

### 2.2 Backend (pip/venv -> uv 전면 전환)

| 파일 | 현재 | 변경 내용 |
|------|------|----------|
| `app-backend/Dockerfile` | `pip install .[dev]` | `uv sync --extra dev` |
| `app-backend/Dockerfile.prod` | `pip install .` | `uv sync --no-dev` |
| `app-backend/Makefile` | `.venv/bin/uvicorn`, `.venv/bin/python -m pytest` | `uv run uvicorn`, `uv run pytest` |
| `app-backend/scripts/setup_dev.sh` | uv/pip 이중 경로 | uv 단일 경로로 단순화 |
| `app-backend/pyproject.toml` | `[build-system]` setuptools | 유지 (uv는 build-system 무관) |
| `docker-compose.dev.yml` | — | command에서 `uv run` 사용 |
| `docker-compose.prod.yml` | — | Dockerfile.prod CMD 활용 |

**Dockerfile (dev)**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# uv 설치 — 반드시 버전 태그 고정 (latest 금지)
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

# 의존성 캐시 레이어
COPY pyproject.toml uv.lock ./
RUN uv sync --extra dev --frozen

COPY . .
ENV PYTHONPATH=/app
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile.prod**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY . .
ENV PYTHONPATH=/app
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2.3 Frontend (npm -> pnpm)

| 파일 | 현재 | 변경 내용 |
|------|------|----------|
| `app-frontend/Dockerfile` | `npm install` | `corepack enable && pnpm install --frozen-lockfile` |
| `app-frontend/Dockerfile.prod` | `npm ci` | `corepack enable && pnpm install --frozen-lockfile` |
| `app-frontend/package.json` | `scripts` 내 `npm run` 참조 | `pnpm` 참조 |
| `docker-compose.dev.yml` | `npm run dev` | `pnpm dev` |
| `app-frontend/package-lock.json` | 존재 | **삭제** |

**Dockerfile (dev)**
```dockerfile
FROM node:20-alpine
WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml .npmrc ./
RUN pnpm install --frozen-lockfile

COPY . .
CMD ["pnpm", "dev"]
```

### 2.4 Root (Husky/commitlint)

| 파일 | 현재 | 변경 내용 |
|------|------|----------|
| `package.json` (root) | `npm` 기반 | `pnpm` 기반 + `"packageManager": "pnpm@9.x"` |
| `package-lock.json` (root) | 존재 | **삭제**, `pnpm-lock.yaml` 생성 |

### 2.5 Phase E: 런타임 업그레이드

| 파일 | 현재 | 변경 내용 |
|------|------|----------|
| Backend Dockerfile/Dockerfile.prod | `python:3.11-slim` | `python:3.13-slim` |
| Frontend Dockerfile/Dockerfile.prod | `node:20-alpine` | `node:22-alpine` |
| CI workflow | `python-version: "3.11"`, `node-version: "20"` | `"3.13"`, `"22"` |
| `app-frontend/package.json` | `@types/node: "^20"` | `"^22"` |
| `app-backend/pyproject.toml` | `sqlalchemy>=2.0.0` | `sqlalchemy>=2.0.44` |

---

## 3. 실행 계획

### Phase 0: 인증 패키지 교체 (예상 작업량: 소)

| 순서 | 태스크 | 파일 |
|------|--------|------|
| 0-1 | pyproject.toml 의존성 교체 | `pyproject.toml` |
| 0-2 | security.py passlib->bcrypt, jose->PyJWT | `app/core/security.py` |
| 0-3 | deps.py JWT 임포트 교체 | `app/api/deps.py` |
| 0-4 | 인증 플로우 전체 테스트 | — |

### Phase A: Backend uv 전면 전환 (예상 작업량: 소)

| 순서 | 태스크 | 파일 |
|------|--------|------|
| A-1~2 | Dockerfile에 uv 설치 + `uv sync` 적용 | `Dockerfile`, `Dockerfile.prod` |
| A-3 | Makefile에서 `.venv/bin/` -> `uv run` 전환 | `Makefile` |
| A-4 | `setup_dev.sh` 단순화 (pip fallback 제거) | `scripts/setup_dev.sh` |
| A-5~7 | 스크립트 전환 (alembic, bootstrap) | `scripts/*.sh` |
| A-8~9 | docker-compose + pyproject.toml 정리 | compose 파일, `pyproject.toml` |
| A-10 | 빌드 테스트 (Docker + 로컬) | — |

### Phase B: Frontend pnpm 전환 (예상 작업량: 소~중)

| 순서 | 태스크 | 파일 |
|------|--------|------|
| B-1~2 | `package-lock.json` 삭제 + packageManager 설정 | 삭제 대상 2개, `package.json` |
| B-3 | `.npmrc` 생성 (node-linker=hoisted) | `.npmrc` |
| B-4~5 | Dockerfile + Dockerfile.prod 전환 | `Dockerfile`, `Dockerfile.prod` |
| B-6~7 | compose + scripts 업데이트 | compose 파일, `package.json` |
| B-8~10 | Root pnpm 초기화 + Husky 확인 | — |
| B-11 | 빌드 테스트 | — |

### Phase C: CI/Hooks 전환

| 순서 | 태스크 | 파일 |
|------|--------|------|
| C-1 | CI workflow uv 전환 | `.github/workflows/ci.yml` |
| C-2 | PR 템플릿 업데이트 | `.github/pull_request_template.md` |
| C-3 | Husky pre-push 전환 | `.husky/pre-push` |
| C-4 | 검증 | — |

### Phase D: 문서 & 정리

| 순서 | 태스크 | 파일 |
|------|--------|------|
| D-1~3 | CLAUDE.md, AGENTS.md, README.md | 루트 문서 3개 |
| D-4~7 | 운영/가이드 문서 | docs/ 4개 |
| D-8 | Feature AGENTS.md (8개) | `app-backend/app/features/*/AGENTS.md` |
| D-9~11 | 활성 태스크 문서, .gitignore, MEMORY.md | 기타 |

### Phase E: 런타임 업그레이드 (예상 작업량: 중)

| 순서 | 태스크 | 파일 |
|------|--------|------|
| E-1 | Python 3.11 -> 3.13 | Dockerfile 2개, CI, pyproject.toml |
| E-2 | Node.js 20 -> 22 LTS | Dockerfile 2개, CI |
| E-3 | @types/node ^20 -> ^22 | `package.json` |
| E-4 | sqlalchemy 하한 상향 | `pyproject.toml` |
| E-5 | 전체 빌드/테스트 검증 | — |

---

## 4. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| Docker 빌드 캐시 무효화 | 최초 빌드 시간 증가 | lock 파일을 먼저 COPY하는 레이어 캐시 전략 유지 |
| uv 버전 호환성 | 예기치 않은 동작 변경 | Dockerfile에서 `ghcr.io/astral-sh/uv:0.9` 태그 고정 (latest 금지) |
| pnpm의 node_modules 구조 차이 | 일부 패키지 해석 문제 가능 | `node-linker=hoisted` 설정으로 npm 호환 구조 유지 (`.npmrc`) |
| macOS 개발자 uv 이슈 | `setup_dev.sh`에 macOS 우회 존재 | uv 0.9 안정화됨; 문제 시 설치 가이드 제공 |
| Root Husky 훅 | pnpm 전환 후 훅 재설치 필요 | `pnpm install` 시 `prepare` 스크립트로 자동 실행 |
| **passlib Python 3.13 비호환** | **인증 시스템 완전 마비** | **Phase 0에서 선행 교체 (bcrypt 직접 사용)** |
| **python-jose 보안 취약점** | **CVE 2건 (ECDSA 혼동, JWT bomb)** | **Phase 0에서 PyJWT 전환** |
| bcrypt 해시 호환성 | 기존 비밀번호 로그인 불가 가능 | bcrypt 4.x는 3.x 해시 읽기 완전 호환 (검증됨) |
| Python 3.13 의존성 비호환 | 일부 패키지 설치 실패 | uv.lock에 cp313 wheel 존재 확인, langchain 3.13 호환 확인 |
| Python 3.14 langchain 미지원 | 런타임 오류 | **3.14 보류, 3.13까지만 업그레이드** |
| Node.js 22 호환성 | 의존성 오류 | 전 의존성 호환 확인됨, @types/node ^22 업데이트 필요 |

---

## 5. 완료 기준

- [ ] Phase 0: passlib/python-jose 완전 제거, bcrypt>=4.0.0 + PyJWT>=2.8.0 전환, pytest 통과
- [ ] `docker compose -f docker-compose.dev.yml up -d --build` 전체 서비스 정상 기동
- [ ] `docker compose -f docker-compose.prod.yml up -d --build` 프로덕션 빌드 성공
- [ ] `cd app-backend && make test` 통과
- [ ] `cd app-frontend && pnpm lint` 통과
- [ ] `cd app-frontend && pnpm test` 통과
- [ ] Husky pre-commit + commit-msg 훅 정상 동작
- [ ] `package-lock.json` 파일 저장소에서 완전 제거
- [ ] CLAUDE.md 문서 최신화
- [ ] Phase E: Python 3.13 + Node.js 22 전환 후 전체 서비스 정상
- [ ] 저장소 내 실행 파일에서 pip/npm/.venv/bin/passlib/jose 참조 0건
