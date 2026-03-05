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
- CI 워크플로 검증

**범위 밖 (호스트에서 사용자가 직접 진행):**
- 루트 `package.json`의 `packageManager` 필드 (pnpm 버전)
- `app-frontend/pnpm-lock.yaml` 재생성
- Node.js Dockerfile 이미지 태그 변경 (node:22 → node:24)
- CI의 `node-version` 변경

---

## Current State

| 항목 | 현재 | 목표 |
|------|------|------|
| `app-backend/Dockerfile` uv | `ghcr.io/astral-sh/uv:0.9` | `ghcr.io/astral-sh/uv:0.10` |
| `app-backend/Dockerfile.prod` uv | `ghcr.io/astral-sh/uv:0.9` | `ghcr.io/astral-sh/uv:0.10` |
| FastAPI | `>=0.109.0` | `>=0.135.0` |
| SQLAlchemy | `>=2.0.44` | `>=2.0.48` |
| SQLModel | `>=0.0.14` | `>=0.0.37` |

---

## Implementation Phases

### Phase 1: uv Docker 이미지 통일

**목적:** 호스트(0.10.8)와 Docker 컨테이너의 uv 버전 불일치를 해소한다.

**변경 파일:**
- `app-backend/Dockerfile` L3
- `app-backend/Dockerfile.prod` L3

**변경 내용:**
```dockerfile
# Before
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/
# After
COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /uvx /bin/
```

**위험 분석:**
- uv 0.10의 breaking change 중 프로젝트에 영향을 주는 항목 없음
- `uv sync`, `uv run` 패턴만 사용 중 — 인터페이스 변경 없음
- Docker 기본 이미지 변경(Bookworm→Trixie)은 multi-stage copy이므로 무관

**검증:**
- Docker 이미지 빌드 성공
- `uv run pytest -q` 통과

---

### Phase 2: Backend 의존성 하한 업데이트

**목적:** FastAPI, SQLAlchemy, SQLModel의 pyproject.toml 하한 버전을 올리고 lock 파일을 재생성한다.

**변경 파일:**
- `app-backend/pyproject.toml` — 3개 라인 수정
- `app-backend/uv.lock` — `uv lock --upgrade` 재생성

**변경 내용:**
```toml
# Before
"fastapi>=0.109.0"
"sqlalchemy>=2.0.44"
"sqlmodel>=0.0.14"

# After
"fastapi>=0.135.0"
"sqlalchemy>=2.0.48"
"sqlmodel>=0.0.37"
```

**위험 분석:**
- FastAPI `strict_content_type` 기본 활성화 — Axios가 Content-Type 자동 설정하므로 영향 없음
- SQLModel 타입 시스템 리팩토링 — Pydantic v2 + SA 2.x 이미 사용 중이라 호환
- SQLAlchemy 패치 — 버그픽스만 포함

**검증:**
- `uv lock --upgrade` 성공
- `uv run pytest -q` 통과
- `alembic check` diff 없음

---

### Phase 3: 통합 검증

**Docker Compose 빌드 + 기능 테스트:**
```bash
docker compose -f docker-compose.dev.yml build app-backend app-worker
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml exec app-backend uv run pytest -q
docker compose -f docker-compose.dev.yml exec app-backend python -m alembic check
```

---

## Risk Assessment

| 위험 | 확률 | 영향 | 완화 방안 |
|------|------|------|----------|
| uv 0.10 lock 해석 차이 | 낮음 | 중간 | `--frozen` 사용 확인, lock 재생성 |
| FastAPI strict_content_type 이슈 | 매우 낮음 | 중간 | Axios Content-Type 헤더 자동 설정 확인 |
| SQLModel 타입 비호환 | 매우 낮음 | 중간 | pytest 전수 통과로 검증 |
| Docker 빌드 실패 | 낮음 | 낮음 | git revert 2줄로 즉시 롤백 |

---

## Success Metrics

1. `app-backend/Dockerfile`, `Dockerfile.prod` 모두 `uv:0.10` 사용
2. `pyproject.toml` 하한 버전 업데이트 완료
3. `uv.lock` 재생성 완료
4. `uv run pytest -q` 전체 통과
5. Docker Compose 빌드 성공
