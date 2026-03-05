# 패키지 매니저 마이그레이션 태스크 체크리스트

> Last Updated: 2026-03-05

## Phase 0: 인증 패키지 교체 (필수 선행)

> Python 3.13 업그레이드 차단 해제 + 보안 취약점 해소

- [ ] 0-1. `app-backend/pyproject.toml` — 의존성 교체
  - `passlib[bcrypt]>=1.7.4` 제거
  - `bcrypt<4` 제거
  - `python-jose[cryptography]>=3.3.0` 제거
  - `bcrypt>=4.0.0` 추가
  - `PyJWT>=2.8.0` 추가
  - `uv lock` 재실행
- [ ] 0-2. `app-backend/app/core/security.py` — passlib -> bcrypt 직접 사용
  - `from passlib.context import CryptContext` 제거
  - `from jose import jwt` -> `import jwt` (PyJWT)
  - `CryptContext` -> `bcrypt.checkpw()` / `bcrypt.hashpw()` 직접 호출
  - `jwt.encode()` API 호환 확인 (PyJWT와 python-jose 시그니처 동일)
- [ ] 0-3. `app-backend/app/api/deps.py` — JWT 임포트 교체
  - `from jose import JWTError, jwt` -> `import jwt`
  - `from jose.exceptions import ExpiredSignatureError` -> `from jwt.exceptions import ExpiredSignatureError`
  - `JWTError` -> `jwt.exceptions.InvalidTokenError`
  - `jwt.decode()` API 호환 확인 (algorithms 파라미터 동일)
- [ ] 0-4. **검증**: 인증 플로우 전체 테스트
  - `make test` 전체 통과
  - 기존 bcrypt 해시 비밀번호 로그인 성공 확인 (bcrypt 4.x는 3.x 해시 읽기 호환)
  - JWT 토큰 encode/decode/만료/무효 시나리오 테스트
  - issuer 검증 정상 동작 확인

## Phase A: Backend uv 전면 전환

- [ ] A-1. `app-backend/Dockerfile` — pip -> uv sync --extra dev --frozen
  - COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/
  - `ghcr.io/astral-sh/uv:latest` 사용 금지 — 버전 태그 고정
  - COPY pyproject.toml uv.lock 레이어 분리
  - docker build 성공 확인
- [ ] A-2. `app-backend/Dockerfile.prod` — pip -> uv sync --no-dev --frozen
  - build-essential 제거 가능 여부 확인 (uv는 wheel 우선)
  - docker build 성공 확인
- [ ] A-3. `app-backend/Makefile` — .venv/bin/ -> uv run
  - run, worker, test 타겟 변경
  - migrate-up, migrate-revision은 run_alembic.sh 경유
- [ ] A-4. `app-backend/scripts/setup_dev.sh` — uv 단일 경로
  - pip fallback 제거
  - macOS 우회 제거
  - uv 미설치 시 설치 안내 메시지
- [ ] A-5. `app-backend/scripts/run_alembic.sh` — uv run alembic
  - .venv/bin/alembic 참조 제거
- [ ] A-6. `app-backend/scripts/bootstrap_actionkit.sh` — .venv/bin/python -> uv run python
  - run_local() 함수 내 PYTHON_BIN 로직 변경
- [ ] A-7. `app-backend/scripts/bootstrap_rag.sh` — .venv/bin/python -> uv run python
  - run_local() 함수 내 PYTHON_BIN 로직 변경
- [ ] A-8. `docker-compose.dev.yml` — backend/worker command
  - L48: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
  - L74: `uv run python -m arq app.workers.roadmap_worker.WorkerSettings`
- [ ] A-9. `docker-compose.prod.yml` — Dockerfile.prod CMD 활용 확인
- [ ] A-10. `pyproject.toml` 정리
  - egg-info 디렉토리 삭제
  - .gitignore에 `stepzero_backend.egg-info/` 추가
- [ ] A-11. **검증**: Docker dev 빌드 + make test 통과

## Phase B: Frontend pnpm 전환

- [ ] B-1. `app-frontend/package-lock.json` 삭제
- [ ] B-2. Root `package-lock.json` 삭제
- [ ] B-3. Root `package.json`에 `"packageManager": "pnpm@9.x"` 추가
- [ ] B-4. `app-frontend/.npmrc` 생성 (`node-linker=hoisted`)
- [ ] B-5. `app-frontend/Dockerfile` — npm -> corepack + pnpm
  - corepack enable + pnpm install --frozen-lockfile
  - COPY package.json pnpm-lock.yaml .npmrc ./
- [ ] B-6. `app-frontend/Dockerfile.prod` — npm ci -> pnpm install --frozen-lockfile
  - COPY package.json pnpm-lock.yaml .npmrc ./
- [ ] B-7. `docker-compose.dev.yml` — frontend command: `pnpm dev`
  - L98: `command: pnpm dev`
- [ ] B-8. `app-frontend/package.json` scripts 수정
  - `types:sync` 내 `npm run` -> `pnpm` 참조
- [ ] B-9. Root `pnpm install` 실행 -> pnpm-lock.yaml 생성
- [ ] B-10. Husky 훅 동작 확인 (commit-msg + pre-commit)
- [ ] B-11. **검증**: Docker dev 빌드 + pnpm lint + pnpm test 통과

## Phase C: CI/CD & Hooks 전환

- [ ] C-1. `.github/workflows/ci.yml` — backend-tests job
  - `pip install` -> `astral-sh/setup-uv` + `uv sync --extra dev`
  - 또는 `uv pip install -e ".[dev]"` (간단 전환)
- [ ] C-2. `.github/pull_request_template.md` — 검증 체크리스트
  - L10: `.venv/bin/pytest -q` -> `uv run pytest -q`
  - L11: `npm run lint` -> `pnpm lint`
- [ ] C-3. `.husky/pre-push` — 실행 명령 전환
  - L23: `.venv/bin/pytest -q` -> `uv run pytest -q`
  - L26: `npm run lint` -> `pnpm lint`
- [ ] C-4. **검증**: `git commit` + `git push` 시 훅 정상 트리거

## Phase D: 문서 업데이트

### D-1~D-3: 루트 문서

- [ ] D-1. `CLAUDE.md` 업데이트
  - Quick Commands: npm -> pnpm, pip -> uv
  - Quality Gates (L77): `.venv/bin/pytest` -> `uv run pytest`
  - Frontend Architecture: npm 참조 -> pnpm
  - Docker Compose 섹션 command 업데이트
  - Data Seeding 섹션 `.venv/bin/` 참조 갱신
- [ ] D-2. `AGENTS.md` 업데이트
  - L20: `npm run dev` -> `pnpm dev`
  - L36: `.venv/bin/pytest -q` -> `uv run pytest -q`
  - L37: `npm run lint` -> `pnpm lint`
- [ ] D-3. `README.md` 업데이트
  - L158-159: `npm install` / `npm run dev` -> `pnpm install` / `pnpm dev`
  - L162: `npm run types:sync` -> `pnpm types:sync`
  - L300: `npm install` -> `pnpm install`
  - L64: `Python venv + 의존성` -> `uv + 의존성`
  - L192: macOS uv 우회 설명 제거/갱신

### D-4~D-7: 운영/가이드 문서

- [ ] D-4. `docs/dev-guide/junior-playbook.md`
  - L11: `.venv/bin/pytest -q` -> `uv run pytest -q`
  - L12: `npm run lint` -> `pnpm lint`
- [ ] D-5. `docs/dev-guide/new-work-checklist.md`
  - L21: `pytest -q / npm run lint` -> `uv run pytest -q / pnpm lint`
- [ ] D-6. `docs/operations/project-operation-rules.md`
  - L44: `npm run lint` -> `pnpm lint`
  - L61: `.venv/bin/pytest -q` -> `uv run pytest -q`
  - L66-68: `npm run dev`, `npm run types:sync`, `npm run lint` -> pnpm
  - L74: `npm run lint` -> `pnpm lint`
- [ ] D-7. `docs/operations/linear-github-rules.md`
  - L84: `.venv/bin/pytest -q` -> `uv run pytest -q`
  - L85: `npm run lint` -> `pnpm lint`

### D-8: Feature AGENTS.md (8개)

- [ ] D-8. Backend feature AGENTS.md 일괄 변경
  - `app-backend/app/features/AGENTS.md` (L19)
  - `app-backend/app/features/auth/AGENTS.md` (L21)
  - `app-backend/app/features/dashboard/AGENTS.md` (L21)
  - `app-backend/app/features/profile/AGENTS.md` (L21)
  - `app-backend/app/features/rag/AGENTS.md` (L21)
  - `app-backend/app/features/roadmaps/AGENTS.md` (L21)
  - `app-backend/app/features/ops/AGENTS.md` (L21)
  - `app-backend/app/features/actionkit/AGENTS.md` (L21)
  - 모두: `.venv/bin/pytest -q` -> `uv run pytest -q`

### D-9~D-11: 기타

- [ ] D-9. `docs/dev/active/r2-storage-migration/` 활성 문서 갱신
  - `r2-storage-migration-tasks.md` L92, L103, L274: venv/pip -> uv 참조
- [ ] D-10. `.gitignore` 정리
  - `stepzero_backend.egg-info/` 추가
- [ ] D-11. MEMORY.md 업데이트
  - 패키지 매니저 결정 기록

## Phase E: 런타임 버전 업그레이드 (Phase 0 + A~D 완료 후)

> Python 3.11 EOL: 2026-05, Node.js 20 EOL: 2026-04-30 — 2개월 내 지원 종료

- [ ] E-1. Python 3.11 -> 3.13 업그레이드
  - `app-backend/Dockerfile`: `FROM python:3.11-slim` -> `FROM python:3.13-slim`
  - `app-backend/Dockerfile.prod`: 동일 변경
  - `.github/workflows/ci.yml`: `python-version: "3.11"` -> `"3.13"`
  - `pyproject.toml`: `requires-python = ">=3.11"` -> `">=3.13"` (선택)
  - `uv lock` 재실행
  - 주의: Python 3.14는 LangChain 미지원, **3.13 권장**
- [ ] E-2. Node.js 20 -> 22 LTS 업그레이드
  - `app-frontend/Dockerfile`: `FROM node:20-alpine` -> `FROM node:22-alpine`
  - `app-frontend/Dockerfile.prod`: 동일 변경
  - `.github/workflows/ci.yml`: `node-version: "20"` -> `"22"`
- [ ] E-3. `app-frontend/package.json` — `@types/node` 업데이트
  - `"@types/node": "^20"` -> `"^22"`
  - `pnpm install` 후 타입 체크 확인
- [ ] E-4. `app-backend/pyproject.toml` — sqlalchemy 하한 상향
  - `sqlalchemy>=2.0.0` -> `sqlalchemy>=2.0.44`
  - Python 3.14 greenlet 자동 설치 unblock 버전
- [ ] E-5. **검증**: 전체 빌드/테스트
  - `docker compose -f docker-compose.dev.yml up -d --build` 전체 서비스 정상
  - `docker compose -f docker-compose.prod.yml up -d --build` 프로덕션 빌드 성공
  - `cd app-backend && make test` 통과
  - `cd app-frontend && pnpm lint` 통과
  - `cd app-frontend && pnpm test` 통과

## Final Verification (전체 마이그레이션 완료 후)

- [ ] `docker compose -f docker-compose.dev.yml up -d --build` 전체 서비스 정상
- [ ] `docker compose -f docker-compose.prod.yml up -d --build` 프로덕션 빌드 성공
- [ ] `cd app-backend && make test` 통과
- [ ] `cd app-frontend && pnpm lint` 통과
- [ ] `cd app-frontend && pnpm test` 통과
- [ ] Husky pre-push 훅 정상 (uv run pytest + pnpm lint)
- [ ] Husky commit-msg 훅 정상 (commitlint)
- [ ] GitHub Actions CI 통과 (backend-tests + frontend-lint)
- [ ] 저장소 내 `package-lock.json` 0개
- [ ] 저장소 내 실행 파일에서 pip/npm/.venv/bin/ 직접 참조 0건
- [ ] grep 검증: `grep -rn "\.venv/bin/\|pip install\|npm run\|npm install\|npm ci" --include="*.sh" --include="*.yml" --include="Makefile" --include="Dockerfile*" .`
- [ ] passlib, python-jose 완전 제거 확인: `grep -rn "passlib\|from jose" app-backend/`
- [ ] Python 3.13 + Node.js 22 LTS에서 전체 서비스 정상 기동
