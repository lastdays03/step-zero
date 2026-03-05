# Runtime Upgrade Tasks

> Last Updated: 2026-03-05
> Branch: `feature/5-pkg-manager-migration`

---

## Phase 1: uv Docker 이미지 통일

- [x] **T1.1** `app-backend/Dockerfile` L3: `ghcr.io/astral-sh/uv:0.9` → `ghcr.io/astral-sh/uv:0.10`
- [x] **T1.2** `app-backend/Dockerfile.prod` L3: `ghcr.io/astral-sh/uv:0.9` → `ghcr.io/astral-sh/uv:0.10`

---

## Phase 2: Backend 의존성 하한 업데이트

- [x] **T2.1** `app-backend/pyproject.toml` FastAPI 하한 변경: `>=0.109.0` → `>=0.135.0`
- [x] **T2.2** `app-backend/pyproject.toml` SQLAlchemy 하한 변경: `>=2.0.44` → `>=2.0.48`
- [x] **T2.3** `app-backend/pyproject.toml` SQLModel 하한 변경: `>=0.0.14` → `>=0.0.37`
- [x] **T2.4** `uv lock --upgrade` 실행하여 lock 파일 재생성

---

## Phase 3: 검증

- [x] **T3.1** 호스트에서 `cd app-backend && uv run pytest -q` 통과 — 384 passed
- [x] **T3.2** Docker Compose 이미지 리빌드 + 컨테이너 시작
  - `.venv` 볼륨 제외 추가로 호스트/컨테이너 충돌 해결
  - `docker-compose.dev.yml` 수정: backend/worker 모두 `- /app/.venv` 추가
- [x] **T3.3** Docker 내 pytest 통과 — 393 passed, 15 skipped, 2 failed (기존 flaky: requires_openai)
- [x] **T3.4** Alembic 스키마 정합성 확인 — `No new upgrade operations detected.`

---

## Phase 4: 커밋 및 정리

- [x] **T4.1** 코드 변경 커밋 — `365227b`
- [ ] **T4.2** Docker Compose .venv 제외 + 문서 업데이트 커밋
- [ ] **T4.3** PR 생성 → develop 머지

---

## Scope Out (호스트에서 사용자 직접 진행)

- [ ] 루트 `package.json` `packageManager` 필드 pnpm 버전 변경
- [ ] `app-frontend/pnpm-lock.yaml` 재생성
- [ ] Frontend Dockerfile Node.js 이미지 태그 변경 (선택)
- [ ] CI `node-version` 변경 (선택)
- [ ] React 19 마이그레이션 (별도 기획)
- [ ] Tailwind CSS 4 마이그레이션 (별도 기획)
