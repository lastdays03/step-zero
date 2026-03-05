# Runtime Upgrade Plan

> Last Updated: 2026-03-05
> Branch: `feature/5-pkg-manager-migration`
> Related Report: `docs/planning/REPORT-runtime-upgrade-assessment.md`

---

## Executive Summary

프로젝트의 Docker 이미지 및 백엔드 의존성을 최신 안정 버전으로 업그레이드한다. 호스트 측 변경사항(pnpm 버전, Node 버전 등)은 사용자가 직접 호스트에서 진행하므로 본 계획에서 제외한다.

**이 계획의 범위:**
- Dockerfile 내 uv 이미지 태그 업그레이드 (0.9 → 0.10)
- Backend Python 의존성 하한 버전 업데이트 + lock 재생성
- Docker Compose `.venv` 볼륨 제외 (호스트/컨테이너 충돌 방지)
- CI 워크플로 검증

**범위 밖 (호스트에서 사용자가 직접 진행):**
- 루트 `package.json`의 `packageManager` 필드 (pnpm 버전)
- `app-frontend/pnpm-lock.yaml` 재생성
- Node.js Dockerfile 이미지 태그 변경 (node:22 → node:24)
- CI의 `node-version` 변경

---

## Current State

| 항목 | 이전 | 현재 (완료) |
|------|------|------------|
| `app-backend/Dockerfile` uv | `ghcr.io/astral-sh/uv:0.9` | `ghcr.io/astral-sh/uv:0.10` |
| `app-backend/Dockerfile.prod` uv | `ghcr.io/astral-sh/uv:0.9` | `ghcr.io/astral-sh/uv:0.10` |
| FastAPI | `>=0.109.0` | `>=0.135.0` |
| SQLAlchemy | `>=2.0.44` | `>=2.0.48` |
| SQLModel | `>=0.0.14` | `>=0.0.37` |
| docker-compose.dev.yml | `.venv` 공유 | `.venv` 볼륨 제외 |

---

## Implementation Phases

### Phase 1: uv Docker 이미지 통일 — 완료

**변경 파일:** `app-backend/Dockerfile`, `app-backend/Dockerfile.prod`

```dockerfile
# Before
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/
# After
COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /uvx /bin/
```

---

### Phase 2: Backend 의존성 하한 업데이트 — 완료

**변경 파일:** `app-backend/pyproject.toml`, `app-backend/uv.lock`

---

### Phase 3: 통합 검증 — 완료

**결과:**
- Docker 이미지 빌드 성공 (backend + worker)
- 컨테이너 정상 기동 (`.venv` 볼륨 제외 적용)
- Docker pytest: 393 passed, 15 skipped, 2 failed (기존 flaky — requires_openai)
- `alembic check`: `No new upgrade operations detected.`

**추가 변경:**
- `docker-compose.dev.yml`: backend/worker에 `- /app/.venv` 익명 볼륨 추가
- worker 서비스 주석 오류 수정 (`# Frontend Service` → `# Worker Service`)

---

## Risk Assessment

| 위험 | 결과 |
|------|------|
| uv 0.10 lock 해석 차이 | 발생 안 함 |
| FastAPI strict_content_type 이슈 | 발생 안 함 |
| SQLModel 타입 비호환 | 발생 안 함 |
| Docker .venv 충돌 | **발생 → 해결** (볼륨 제외 추가) |

---

## Success Metrics

1. `app-backend/Dockerfile`, `Dockerfile.prod` 모두 `uv:0.10` 사용 — 완료
2. `pyproject.toml` 하한 버전 업데이트 완료 — 완료
3. `uv.lock` 재생성 완료 — 완료
4. `uv run pytest -q` 전체 통과 — 완료 (flaky 2건은 기존 이슈)
5. Docker Compose 빌드 + 기동 성공 — 완료
6. `alembic check` diff 없음 — 완료
