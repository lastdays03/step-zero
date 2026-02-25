# StepZero Backend

FastAPI + PostgreSQL 백엔드 서비스

## 빠른 시작

```bash
# 1. 개발환경 셋업 (venv + 의존성)
./scripts/setup_dev.sh

# 2. DB 마이그레이션
source .venv/bin/activate
alembic upgrade head

# 3. 서버 실행
uvicorn app.main:app --reload --port 8000
```

## Scripts

### 마이그레이션

| 명령 | 설명 |
|------|------|
| `./scripts/reset_migrations.sh fresh` | 새 DB에 마이그레이션 전체 적용 |
| `./scripts/reset_migrations.sh stamp` | 기존 DB에 alembic_version만 최신으로 갱신 (스키마 변경 없음) |
| `./scripts/reset_migrations.sh verify` | autogenerate로 모델과 DB 스키마 차이 검증 |
| `./scripts/reset_migrations.sh status` | 현재 마이그레이션 상태 확인 |
| `./scripts/reset_migrations.sh history` | 마이그레이션 체인 출력 |
| `./scripts/run_alembic.sh <args>` | alembic 명령 래퍼 (venv 자동 탐색) |

### 데이터 초기화

| 명령 | 설명 |
|------|------|
| `./scripts/bootstrap_actionkit.sh` | 마이그레이션 + ActionKit 시드 데이터 투입 |
| `./scripts/bootstrap_rag.sh` | 마이그레이션 + RAG 벡터 시드 투입 |
| `python scripts/seed_actionkit.py` | ActionKit 시드 데이터만 투입 |
| `python scripts/seed_rag_vectors.py` | RAG 벡터 데이터만 투입 |

### 유틸리티

| 명령 | 설명 |
|------|------|
| `./scripts/setup_dev.sh` | Python venv 생성 + 의존성 설치 + .env 복사 |
| `python scripts/export_openapi.py` | OpenAPI 스키마 JSON 추출 |
| `python -m scripts.backup_law_vectors` | law_vectors 컬렉션 백업 |
| `python -m scripts.verify_chunking` | 청킹 품질 검증 |

### 평가

| 명령 | 설명 |
|------|------|
| `python -m scripts.eval.run_evaluation --tier 1` | RAG Tier 1 라우팅 테스트 |
| `python -m scripts.eval.run_evaluation --tier 2` | RAG Tier 2 베이스라인 평가 |
| `python -m scripts.eval.run_evaluation --update-baseline` | 평가 베이스라인 갱신 |

## 마이그레이션 구조

6개의 통합 마이그레이션 파일로 구성:

```
001_core.py         → user, team, profile, refresh_token, discipline_history
002_roadmap.py      → roadmap, roadmapstep, jobs, details, actions
003_actionkit.py    → categories, items, highlights, laws, files
004_growth_club.py  → posts, comments, likes, attachments, reports, tags
005_admin.py        → admin_audit_logs, announcements
006_notification.py → notification
```

### 새 PC에서 처음 셋업

```bash
./scripts/setup_dev.sh
./scripts/reset_migrations.sh fresh
```

### 기존 DB가 있는 환경에서 마이그레이션 리셋

```bash
./scripts/reset_migrations.sh stamp
```

## 테스트

```bash
source .venv/bin/activate
pytest tests/ -q                    # 전체 테스트
pytest tests/ -q --ignore=tests/eval  # eval 제외
```
