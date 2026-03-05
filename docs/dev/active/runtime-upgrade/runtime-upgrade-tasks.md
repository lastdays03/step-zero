# Runtime Upgrade Tasks

> Last Updated: 2026-03-05
> Branch: `feature/5-pkg-manager-migration`

---

## Phase 1: uv Docker 이미지 통일

- [ ] **T1.1** `app-backend/Dockerfile` L3: `ghcr.io/astral-sh/uv:0.9` → `ghcr.io/astral-sh/uv:0.10`
  - Effort: S
  - Acceptance: Dockerfile 빌드 성공

- [ ] **T1.2** `app-backend/Dockerfile.prod` L3: `ghcr.io/astral-sh/uv:0.9` → `ghcr.io/astral-sh/uv:0.10`
  - Effort: S
  - Acceptance: Dockerfile 빌드 성공

---

## Phase 2: Backend 의존성 하한 업데이트

- [ ] **T2.1** `app-backend/pyproject.toml` FastAPI 하한 변경: `>=0.109.0` → `>=0.135.0`
  - Effort: S
  - Acceptance: pyproject.toml 수정 완료

- [ ] **T2.2** `app-backend/pyproject.toml` SQLAlchemy 하한 변경: `>=2.0.44` → `>=2.0.48`
  - Effort: S
  - Acceptance: pyproject.toml 수정 완료

- [ ] **T2.3** `app-backend/pyproject.toml` SQLModel 하한 변경: `>=0.0.14` → `>=0.0.37`
  - Effort: S
  - Acceptance: pyproject.toml 수정 완료

- [ ] **T2.4** `uv lock --upgrade` 실행하여 lock 파일 재생성
  - Effort: S
  - Depends: T2.1, T2.2, T2.3
  - Acceptance: `uv.lock` 정상 생성, 의존성 충돌 없음

---

## Phase 3: 검증

- [ ] **T3.1** 호스트에서 `cd app-backend && uv run pytest -q` 통과
  - Depends: T2.4
  - Acceptance: 전체 테스트 통과 (requires_openai 제외)

- [ ] **T3.2** Docker Compose 빌드 테스트
  - Depends: T1.1, T1.2, T2.4
  - Acceptance: `docker compose -f docker-compose.dev.yml build app-backend app-worker` 성공

- [ ] **T3.3** Docker 내 pytest 통과 (선택 — Docker 환경 가용 시)
  - Depends: T3.2
  - Acceptance: `docker compose exec app-backend uv run pytest -q` 통과

- [ ] **T3.4** Alembic 스키마 정합성 확인 (선택 — Docker DB 가용 시)
  - Depends: T3.2
  - Acceptance: `alembic check` diff 없음

---

## Phase 4: 커밋 및 정리

- [ ] **T4.1** 변경사항 커밋
  - Depends: T3.1 (최소), T3.2 (권장)
  - Acceptance: commitlint 통과하는 conventional commit

---

## Scope Out (호스트에서 사용자 직접 진행)

아래 항목은 이 태스크 범위 밖. 사용자가 호스트에서 직접 처리:

- [ ] 루트 `package.json` `packageManager` 필드 pnpm 버전 변경
- [ ] `app-frontend/pnpm-lock.yaml` 재생성
- [ ] Frontend Dockerfile Node.js 이미지 태그 변경 (선택)
- [ ] CI `node-version` 변경 (선택)
- [ ] React 19 마이그레이션 (별도 기획)
- [ ] Tailwind CSS 4 마이그레이션 (별도 기획)
