# PLAN: ActionKit 통계 추적 기능 구현

**Last Updated:** 2026-03-10
**참조 보고서:** `docs/plans/reports/REPORT-actionkit-analytics-tracking.md`

---

## 1. Executive Summary

ActionKit 통계 대시보드의 하드코딩 데이터(KPI 3개, 인기서류 TOP5, 검색어 6개, 인사이트)를 실제 사용자 행동 데이터 기반으로 전환한다. PostgreSQL 이벤트 테이블 + 서버/클라이언트 양쪽 추적 + 집계 서비스 + 프론트엔드 연동으로 구성.

**핵심 목표:**
- 사용자 행동(다운로드/조회/검색/북마크) 서버 수집
- 기간별(7/30/365일) KPI 집계 + 델타 계산
- 인기 서류 순위 + 인기 검색어 실시간 반영
- 규칙 기반 자동 인사이트 생성

---

## 2. Current State

### 하드코딩 현황

| 항목 | 하드코딩 값 | 소스 파일 |
|------|-----------|----------|
| KPI 카드 3개 | 4,520건/1,284명/42% | `stats-dashboard.tsx` JSX 인라인 |
| 인기 서류 TOP 5 | `POPULAR_DOCS` 상수 | `stats-dashboard.tsx:8-13` |
| 검색어 6개 | `SEARCH_KEYWORDS` 상수 | `stats-dashboard.tsx:15` |
| 인사이트 | 고정 문구 | `stats-dashboard.tsx:196` |
| 기간 필터 | UI만 존재, 미연동 | `stats-dashboard.tsx:29` |

### 인프라 준비 상태

| 컴포넌트 | 상태 | 비고 |
|---------|------|------|
| `get_optional_current_user()` | **준비됨** | `app/api/deps.py:120-159` |
| `require_platform_admin()` | **준비됨** | `app/api/deps.py:211-219` |
| OpsReportsService 델타 패턴 | **준비됨** | `reports/service.py` |
| AdminAuditLog 프레임워크 | **준비됨** | 이미 ActionKit 상태 변경 추적 중 |
| ARQ cron 패턴 | **준비됨** | `roadmap_worker.py` — 토큰 정리 cron 존재 |
| Alembic 마이그레이션 | **준비됨** | 017번까지 완료, 018번 사용 가능 |
| Ops 라우터 구조 | **준비됨** | `ops/actionkit.py`에 엔드포인트 추가만 하면 됨 |

---

## 3. Proposed Architecture

```
사용자 행동          프론트엔드              백엔드                  저장소
──────────          ──────────             ────────                ──────

다운로드 클릭  ──→  GET /download  ────→  files.py + 추적 ──────→  PostgreSQL
파일 뷰어 열기 ──→  GET /view     ────→  files.py + 추적 ──────→  (actionkit_events)
ZIP 다운로드   ──→  POST /track   ────→  tracking.py     ──────→
검색어 입력    ──→  POST /track   ────→  (debounce 1초)  ──────→
북마크 추가    ──→  POST /track   ────→                  ──────→
                                                ↓
통계 대시보드  ←──  GET /stats    ←────  StatsService    ←──────  집계 쿼리
                                         ├─ 기간별 집계
                                         ├─ 델타 계산
                                         ├─ 인기 순위
                                         └─ 인사이트 생성
```

**양쪽 추적 전략 (Belt-and-Suspenders):**
- 서버 사이드: download/view 엔드포인트 자동 기록 (누락 불가)
- 클라이언트 사이드: search/bulk_download/bookmark 등 서버 감지 불가 이벤트

---

## 4. Implementation Phases

### Phase 1: 이벤트 수집 인프라 (BE)

DB 모델 + 마이그레이션 + 트래킹 API + 기존 엔드포인트 수정

| # | 작업 | 파일 | 규모 |
|---|------|------|------|
| 1.1 | ActionKitEvent 모델 생성 | `app/models/actionkit_event.py` | S |
| 1.2 | `__init__.py`에 import + `__all__` 추가 | `app/models/__init__.py` | S |
| 1.3 | `alembic/env.py`에 import 추가 | `alembic/env.py` | S |
| 1.4 | Alembic 마이그레이션 생성 + 적용 | `alembic/versions/018_*.py` | S |
| 1.5 | 트래킹 API 엔드포인트 생성 | `app/api/v1/actionkit/tracking.py` | M |
| 1.6 | 라우터에 tracking 등록 | `app/api/v1/actionkit/router.py` | S |
| 1.7 | files.py download/view에 추적 삽입 | `app/api/v1/actionkit/files.py` | M |
| 1.8 | `alembic check` 검증 + dind/Docker 양쪽 적용 | - | S |

**의존성:** 1.1 → 1.2+1.3 → 1.4 → 1.5+1.6+1.7 → 1.8

### Phase 2: 통계 집계 서비스 (BE)

StatsService + 응답 스키마 + API 엔드포인트 + 인사이트 생성

| # | 작업 | 파일 | 규모 |
|---|------|------|------|
| 2.1 | ActionKitStatsService 구현 | `app/features/ops/application/actionkit/stats_service.py` | L |
| 2.2 | 응답 스키마 정의 | `app/api/v1/ops/schemas.py` | M |
| 2.3 | Stats API 엔드포인트 추가 | `app/api/v1/ops/actionkit.py` | S |
| 2.4 | 인사이트 자동 생성 로직 | stats_service.py 내 | M |
| 2.5 | 이벤트 정리 ARQ cron job | `app/workers/roadmap_worker.py` | S |

**의존성:** Phase 1 완료 → 2.1+2.2 → 2.3 → 2.4, 2.5는 독립

### Phase 3: 프론트엔드 연동

API 클라이언트 + 트래킹 삽입 + 대시보드 교체

| # | 작업 | 파일 | 규모 |
|---|------|------|------|
| 3.1 | fetchStats + trackEvent API 함수 | `ops/actionkit/api.ts` | S |
| 3.2 | 사용자 뷰 트래킹 삽입 (search/zip/bookmark/detail) | `ActionKitLibraryView.tsx` | M |
| 3.3 | 법령 뷰 트래킹 삽입 (view/search) | `LawGuideView.tsx` | S |
| 3.4 | stats-dashboard.tsx 전면 교체 | `stats-dashboard.tsx` | L |
| 3.5 | view.tsx allItems 로드 + stats 연동 | `view.tsx` | M |
| 3.6 | 빈 데이터 상태 UI + delta=null 처리 | stats-dashboard.tsx 내 | S |

**의존성:** Phase 2 완료 → 3.1 → 3.2+3.3 (병렬), 3.4+3.5 → 3.6

### Phase 4: 테스트 + 검증

| # | 작업 | 파일 | 규모 |
|---|------|------|------|
| 4.1 | 이벤트 기록 API 테스트 | `tests/api/test_actionkit_tracking.py` | M |
| 4.2 | 통계 집계 서비스 테스트 | `tests/services/test_actionkit_stats.py` | L |
| 4.3 | FE lint 통과 확인 | - | S |
| 4.4 | 마이그레이션 검증 (`alembic check`) | - | S |
| 4.5 | 브라우저 통합 테스트 (chrome-devtools MCP) | - | M |

**의존성:** 4.1은 Phase 1 후, 4.2는 Phase 2 후, 4.3+4.5는 Phase 3 후

---

## 5. 핵심 설계 결정

### 5.1 이벤트 타입 6종

```python
VIEW = "view"                   # 파일 뷰어 열기 (서버 자동)
DOWNLOAD = "download"           # 단일 파일 다운로드 (서버 자동)
BULK_DOWNLOAD = "bulk_download" # Zip 일괄 다운로드 (클라이언트)
SEARCH = "search"               # 검색어 입력 (클라이언트, debounce)
BOOKMARK = "bookmark"           # 서랍장 찜 추가 (클라이언트)
DETAIL_VIEW = "detail_view"     # 상세 모달 열기 (클라이언트)
```

### 5.2 ZIP 중복 카운트 방지

`handleBulkDownload()`는 각 아이템에 대해 `GET /download` 호출 → 서버에서 개별 download 이벤트 발생.

**해결:** 클라이언트에서 `?source=bulk` 쿼리 파라미터 추가 → 서버에서 source=bulk이면 download 이벤트 스킵 (클라이언트가 bulk_download를 별도 POST)

### 5.3 stats 탭 아이템 전달 버그 수정

현재 view.tsx에서 stats 탭에 **현재 카테고리 아이템만** 전달됨 → 전체 아이템으로 수정 필요

### 5.4 데이터 보존 90일

ARQ cron job으로 90일 이전 이벤트 삭제. 기존 `cleanup_expired_refresh_tokens` 패턴 참조.

---

## 6. Risk Assessment

| 위험 | 확률 | 영향 | 완화 |
|------|------|------|------|
| 이벤트 테이블 무한 증가 | 높음 | 중간 | 90일 cron + 인덱스 최적화 |
| 비인증 사용자 추적 | 중간 | 낮음 | user_id nullable, COUNT 기반 집계 |
| files.py 수정 시 기존 기능 영향 | 낮음 | 높음 | try/except 감싸기, 추적 실패해도 파일 정상 제공 |
| ZIP 중복 카운트 | 중간 | 중간 | source=bulk 파라미터로 구분 |
| 봇/크롤러 트래픽 왜곡 | 낮음 | 중간 | slowapi rate limit (이미 의존) |
| 배포 직후 빈 데이터 | 확실 | 낮음 | 빈 상태 UI + 1~2주 수집 후 FE 배포 |
| stats 탭 allItems 로드 성능 | 낮음 | 낮음 | 카테고리 수 적음 (~10개), 한 번만 로드 |

---

## 7. Success Metrics

| 지표 | 기준 |
|------|------|
| 이벤트 수집 | 배포 24시간 내 이벤트 1건 이상 기록 |
| 통계 API 응답 | 200ms 이내 (range_days=30 기준) |
| 기존 테스트 통과 | `make test` 423건+ 전체 pass |
| FE lint 통과 | `pnpm lint` 0 errors |
| KPI 카드 동적 데이터 | 기간 필터 변경 시 실제 데이터 반영 |
| 인기 서류 순위 | 실제 다운로드 수 기반 정렬 |
| 검색어 순위 | 실제 검색 이벤트 기반 |
| 인사이트 자동 생성 | 데이터 존재 시 규칙 기반 텍스트 생성 |
| 노후 항목 경고 | 전체 아이템 기반 (버그 수정) |

---

## 8. 작업량 요약

| Phase | 신규 파일 | 수정 파일 | 코드량 | 규모 |
|-------|----------|----------|--------|------|
| 1. 이벤트 수집 | 3개 | 4개 | ~130줄 | M |
| 2. 집계 서비스 | 1개 | 3개 | ~300줄 | L |
| 3. FE 연동 | 0개 | 5개 | ~335줄 | L |
| 4. 테스트 | 2개 | 0개 | ~250줄 | M |
| **합계** | **6개** | **12개** | **~1,015줄** | **XL** |
