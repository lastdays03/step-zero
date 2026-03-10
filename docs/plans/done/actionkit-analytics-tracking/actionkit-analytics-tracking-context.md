# CONTEXT: ActionKit 통계 추적 기능

**Last Updated:** 2026-03-10

---

## Key Files

### 신규 생성 파일

| 파일 | 용도 |
|------|------|
| `app/models/actionkit_event.py` | ActionKitEvent 모델 |
| `alembic/versions/018_actionkit_events.py` | DB 마이그레이션 |
| `app/api/v1/actionkit/tracking.py` | POST /track 엔드포인트 |
| `app/features/ops/application/actionkit/stats_service.py` | 통계 집계 서비스 |
| `tests/api/test_actionkit_tracking.py` | 트래킹 API 테스트 |
| `tests/services/test_actionkit_stats.py` | 집계 서비스 테스트 |

### 수정 대상 파일

| 파일 | 수정 내용 |
|------|----------|
| `app/models/__init__.py` | ActionKitEvent import + `__all__` |
| `alembic/env.py` | `import app.models.actionkit_event` 추가 |
| `app/api/v1/actionkit/router.py` | tracking 라우터 include |
| `app/api/v1/actionkit/files.py` | download/view에 추적 삽입 + optional auth |
| `app/api/v1/ops/actionkit.py` | GET /stats 엔드포인트 추가 |
| `app/api/v1/ops/schemas.py` | Stats 응답 스키마 추가 |
| `app/workers/roadmap_worker.py` | 이벤트 정리 cron job 추가 |
| `src/features/ops/actionkit/api.ts` | fetchStats + trackEvent 함수 |
| `src/features/actionkit/components/ActionKitLibraryView.tsx` | 트래킹 호출 삽입 |
| `src/features/actionkit/components/LawGuideView.tsx` | 트래킹 호출 삽입 |
| `src/features/ops/actionkit/components/stats-dashboard.tsx` | 전면 교체 |
| `src/features/ops/actionkit/view.tsx` | allItems + stats 연동 |

### 참조 파일 (수정 없음, 패턴 참고용)

| 파일 | 참조 내용 |
|------|----------|
| `app/api/deps.py` | `get_optional_current_user()` (L120-159) — optional 인증 |
| `app/features/ops/application/reports/service.py` | OpsReportsService 델타 계산 패턴 |
| `app/features/ops/application/actionkit/service.py` | 기존 get_summary() + CRUD 패턴 |
| `app/workers/roadmap_worker.py` | ARQ cron job 패턴 (cleanup_expired_refresh_tokens) |
| `app/models/admin_audit_log.py` | 모델 생성 패턴 (Optional[int], FK, Index) |
| `app/features/ops/application/audit_logs/constants.py` | ACTIONKIT_ITEM_STATUS_UPDATED 등 |

---

## Key Decisions

### D1: PostgreSQL 단독 (Redis 하이브리드 미채택)
- **이유:** 현재 사용자 규모 수백~수천명, 이벤트 빈도 낮음
- **조건:** 사용자 수만명 이상 시 Redis ZSET 검토

### D2: 이벤트 타입 6종
- view, download, bulk_download, search, bookmark, detail_view
- 기존 보고서(4종) 대비 bookmark, detail_view 추가

### D3: 서버+클라이언트 양쪽 추적
- download/view: 서버 files.py에서 자동 기록 (누락 방지)
- search/bulk_download/bookmark/detail_view: 클라이언트 POST /track

### D4: ZIP 중복 방지 — `?source=bulk` 파라미터
- handleBulkDownload()가 개별 GET /download 호출 → 서버 download 이벤트 발생
- source=bulk이면 서버 download 이벤트 스킵

### D5: 데이터 보존 90일
- ARQ cron job으로 90일 이전 삭제
- 기존 cleanup_expired_refresh_tokens 패턴 참조

### D6: 인사이트 — 규칙 기반 자동 생성
- LLM 기반은 과도한 복잡도, 현재 규칙 기반 충분
- 급성장 아이템 + 인기 검색어 자동 텍스트

### D7: stats 탭 allItems 버그 수정
- 현재: 현재 카테고리 아이템만 전달 → 노후 감지 불완전
- 수정: 전체 카테고리 아이템 로드

### D8: KPI "이용 건수"에 view 포함
- 프론트엔드 모든 다운로드/보기 버튼이 `/view` 엔드포인트 사용
- view 이벤트 제외 시 KPI 0건 → `["view", "download", "bulk_download"]` 전부 포함

### D9: session.commit() 필수 (flush 아님)
- `get_session()` 컨텍스트가 auto-commit하지 않음
- `session.flush()`만 하면 컨텍스트 종료 시 rollback → 이벤트 미저장

### D10: KPI 3번째 지표 = per_user (인당 이용 건수)
- conversion_rate → daily_average → per_user 순으로 반복 개선
- daily_average는 첫 번째 KPI의 단순 나눗셈이라 무의미
- per_user = downloads / active_users (활성 유저당 평균 이용 횟수)

---

## Dependencies

### 외부 의존성
- 없음 (새 패키지 추가 불필요)

### 내부 의존성
- `get_optional_current_user()` — 이미 존재 (`app/api/deps.py:120`)
- `require_platform_admin()` — 이미 존재 (`app/api/deps.py:211`)
- Alembic 017번까지 완료 → 018번 사용 가능
- ARQ worker cron 패턴 — 이미 존재 (`roadmap_worker.py`)
- slowapi rate limit — 이미 의존 중 (pyproject.toml)

### Phase 간 의존성
```
Phase 1 (이벤트 수집)
  ↓
Phase 2 (집계 서비스)  ←── Phase 4.1 (트래킹 테스트, Phase 1 후 가능)
  ↓
Phase 3 (FE 연동)     ←── Phase 4.2 (집계 테스트, Phase 2 후 가능)
  ↓
Phase 4.3~4.5 (FE 테스트/검증)
```

---

## Critical Patterns to Follow

### 모델 생성 패턴 (actionkit.py 참조)
```python
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime, timezone

class NewModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
```

### FK 규칙
- `ondelete=` 반드시 명시
- ActionKitEvent: `ondelete="SET NULL"` (아이템/사용자 삭제 시 이벤트 보존)

### 모델 등록 체크리스트
1. `app/models/actionkit_event.py` 생성
2. `app/models/__init__.py`에 import + `__all__`
3. `alembic/env.py`에 `import app.models.actionkit_event`
4. `uv run alembic revision --autogenerate -m "add actionkit_events"`
5. `uv run alembic upgrade head` (dind DB)
6. `uv run alembic check` (diff 없음 확인)
7. Docker DB: `docker compose exec app-backend uv run alembic upgrade head`

### 테스트 DB: SQLite
- FK 제약이 다를 수 있음 — 테스트에서 FK 관련 에러 시 `PRAGMA foreign_keys=ON` 확인
- `tests/conftest.py`의 기존 유저/팀 시드 활용

### .gitignore 주의
- 루트 `.gitignore`에 `test_*.py` 패턴 존재
- 새 테스트 파일: `git add -f tests/api/test_actionkit_tracking.py` 필요
