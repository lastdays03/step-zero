# Runtime Upgrade Context

> Last Updated: 2026-03-05

---

## Related Planning Doc

- `docs/planning/REPORT-runtime-upgrade-assessment.md` — 전체 버전 분석 보고서

---

## Current Implementation State

**Phase 1~3 완료. Phase 4 커밋 + PR 생성 대기.**

모든 코드 변경과 검증이 완료되었다:
- Dockerfile uv 0.10 업그레이드 (dev + prod)
- pyproject.toml 의존성 하한 업데이트 + uv.lock 재생성
- docker-compose.dev.yml `.venv` 볼륨 제외 추가 (호스트/컨테이너 충돌 방지)
- Docker 내 pytest 393 passed, alembic check diff 없음

---

## Key Files (변경 완료)

| 파일 | 변경 내용 | 커밋 |
|------|----------|------|
| `app-backend/Dockerfile` L3 | `uv:0.9` → `uv:0.10` | 365227b |
| `app-backend/Dockerfile.prod` L3 | `uv:0.9` → `uv:0.10` | 365227b |
| `app-backend/pyproject.toml` | FastAPI/SA/SM 하한 업데이트 | 365227b |
| `app-backend/uv.lock` | `uv lock --upgrade` 재생성 | 365227b |
| `docker-compose.dev.yml` | backend/worker `.venv` 볼륨 제외 + worker 주석 수정 | uncommitted |

---

## Issues Discovered & Resolved

### 1. Docker worker `uv not found` 에러
- **원인**: 캐시된 이미지(uv 0.9)가 남아있어 `--build` 플래그 필요
- **해결**: `docker compose up -d --build`

### 2. Docker backend `.venv` 충돌 크래시
- **원인**: 호스트의 `.venv`가 볼륨 마운트로 컨테이너에 공유 → Python 인터프리터 경로 불일치
- **에러**: `failed to remove file /app/.venv/CACHEDIR.TAG: No such file or directory`
- **해결**: `docker-compose.dev.yml`에 `- /app/.venv` 익명 볼륨 추가 (frontend의 node_modules 패턴과 동일)

### 3. pytest flaky 2건 (기존 이슈, 런타임 업그레이드 무관)
- `test_real_oos_lawsuit`, `test_real_oos_health` — OpenAI 임베딩 응답 비결정적

---

## Decisions

| 결정 | 근거 |
|------|------|
| uv 0.10으로 통일 | 호스트(0.10.8)와 Docker 버전 불일치 해소 |
| FastAPI 하한 0.135.0 | 보안/기능 개선, 하위 호환 유지 |
| SQLAlchemy 하한 2.0.48 | 버그픽스 패치, 위험 없음 |
| SQLModel 하한 0.0.37 | Pydantic v2 호환 개선, 타입 안정성 |
| `.venv` 볼륨 제외 | 호스트/컨테이너 Python 경로 충돌 방지 |

---

## Next Steps

1. 변경사항 커밋 (docker-compose.dev.yml + 문서)
2. PR 생성 → develop 머지
