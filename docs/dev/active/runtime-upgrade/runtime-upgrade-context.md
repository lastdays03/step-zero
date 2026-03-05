# Runtime Upgrade Context

> Last Updated: 2026-03-05

---

## Related Planning Doc

- `docs/planning/REPORT-runtime-upgrade-assessment.md` — 전체 버전 분석 보고서

---

## Key Files (변경 대상)

| 파일 | 역할 | 변경 내용 |
|------|------|----------|
| `app-backend/Dockerfile` | 개발 Docker 이미지 | uv 0.9 → 0.10 |
| `app-backend/Dockerfile.prod` | 프로덕션 Docker 이미지 | uv 0.9 → 0.10 |
| `app-backend/pyproject.toml` | Python 의존성 선언 | FastAPI/SA/SM 하한 업데이트 |
| `app-backend/uv.lock` | 의존성 lock 파일 | `uv lock --upgrade` 재생성 |

## Key Files (참조만)

| 파일 | 역할 | 비고 |
|------|------|------|
| `docker-compose.dev.yml` | 개발 Docker Compose | 변경 없음 — 이미지 빌드 시 자동 반영 |
| `docker-compose.prod.yml` | 프로덕션 Docker Compose | 변경 없음 |
| `.github/workflows/ci.yml` | CI 파이프라인 | Python/uv 관련은 변경 없음 (setup-uv@v5가 최신 자동 사용) |

---

## Decisions

| 결정 | 근거 |
|------|------|
| uv 0.10으로 통일 | 호스트(0.10.8)와 Docker 버전 불일치 해소 필수 |
| FastAPI 하한 0.135.0 | 보안/기능 개선, 하위 호환 유지 |
| SQLAlchemy 하한 2.0.48 | 버그픽스 패치, 위험 없음 |
| SQLModel 하한 0.0.37 | Pydantic v2 호환 개선, 타입 안정성 |
| Node/pnpm은 범위 밖 | 호스트 쪽에서 사용자가 직접 진행 |
| React 19/Tailwind 4 보류 | 마이그레이션 공수 크고 별도 기획 필요 |

---

## Dependencies

- Docker + Docker Compose 실행 환경
- `uv` 0.10.8 (호스트에 이미 설치됨)
- PostgreSQL + Redis (Docker Compose 서비스)
