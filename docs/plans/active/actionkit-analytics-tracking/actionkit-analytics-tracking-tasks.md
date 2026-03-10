# TASKS: ActionKit 통계 추적 기능

**Last Updated:** 2026-03-10

---

## Phase 1: 이벤트 수집 인프라 (BE)

- [ ] **1.1** ActionKitEvent 모델 생성 `[S]`
  - 파일: `app/models/actionkit_event.py`
  - 필드: id, event_type, item_id(FK nullable), user_id(FK nullable), search_query, created_at
  - 이벤트 타입: view, download, bulk_download, search, bookmark, detail_view
  - 복합 인덱스: (event_type, created_at), (item_id, created_at)
  - FK ondelete="SET NULL"
  - 수락 기준: 모델 파일 존재, SQLModel 패턴 준수

- [ ] **1.2** 모델 등록 `[S]`
  - `app/models/__init__.py`에 import + `__all__` 추가
  - `alembic/env.py`에 `import app.models.actionkit_event` 추가
  - 수락 기준: 두 파일 모두 import 포함

- [ ] **1.3** Alembic 마이그레이션 생성 + 적용 `[S]`
  - `uv run alembic revision --autogenerate -m "add actionkit_events"`
  - `uv run alembic upgrade head`
  - `uv run alembic check` → diff 없음 확인
  - 수락 기준: 마이그레이션 파일 존재, alembic check clean
  - 의존: 1.1, 1.2

- [ ] **1.4** 트래킹 API 엔드포인트 `[M]`
  - 파일: `app/api/v1/actionkit/tracking.py`
  - `POST /actionkits/track` (status 204)
  - Request: `{event_type, item_id?, search_query?}`
  - `get_optional_current_user`로 optional 인증
  - fire-and-forget 패턴 (빠른 응답 우선)
  - 수락 기준: 엔드포인트 응답 204, 이벤트 DB 기록 확인
  - 의존: 1.3

- [ ] **1.5** 라우터 등록 `[S]`
  - `app/api/v1/actionkit/router.py`에 tracking 모듈 include
  - 수락 기준: `/actionkits/track` 라우트 등록 확인
  - 의존: 1.4

- [ ] **1.6** files.py download/view 추적 삽입 `[M]`
  - `download_item_current_file()`에 download 이벤트 기록
  - `view_item_current_file()`에 view 이벤트 기록
  - `get_optional_current_user` 의존성 추가
  - `source=bulk` 파라미터 시 download 이벤트 스킵
  - try/except로 감싸기 (추적 실패해도 파일 정상 제공)
  - 수락 기준: download/view 시 이벤트 기록, 추적 에러 시 파일 정상 반환
  - 의존: 1.3

- [ ] **1.7** 마이그레이션 양쪽 DB 적용 확인 `[S]`
  - dind DB: `uv run alembic upgrade head`
  - Docker DB: `docker compose exec app-backend uv run alembic upgrade head`
  - 수락 기준: 양쪽 DB에 actionkit_events 테이블 존재
  - 의존: 1.3

---

## Phase 2: 통계 집계 서비스 (BE)

- [ ] **2.1** ActionKitStatsService 구현 `[L]`
  - 파일: `app/features/ops/application/actionkit/stats_service.py`
  - `get_stats(range_days)` → KPI + 인기순위 + 검색어 + 인사이트
  - `_get_kpi()` → 다운로드수/활성유저/전환율 + 델타
  - `_get_popular_items()` → TOP 5 + trend 계산
  - `_get_search_keywords()` → TOP 10 검색어
  - `_generate_insight()` → 규칙 기반 자동 텍스트
  - `_delta()` → OpsReportsService 패턴 재사용
  - 수락 기준: 각 메서드 동작, 빈 데이터 시 안전 반환
  - 의존: Phase 1 완료

- [ ] **2.2** 응답 스키마 정의 `[M]`
  - 파일: `app/api/v1/ops/schemas.py`
  - ActionKitStatsResponse, ActionKitKPI, PopularItem, SearchKeyword
  - 수락 기준: Pydantic v2 BaseModel, ConfigDict 준수
  - 의존: 2.1과 병렬 가능

- [ ] **2.3** Stats API 엔드포인트 `[S]`
  - `GET /ops/actionkit/stats?range_days=30`
  - `require_platform_admin` 의존성
  - range_days: Query(default=30, ge=7, le=365)
  - 수락 기준: 관리자 인증 후 JSON 응답, 비관리자 403
  - 의존: 2.1, 2.2

- [ ] **2.4** 인사이트 자동 생성 `[M]`
  - stats_service.py 내 `_generate_insight()` 메서드
  - 급성장 아이템 (trend > 10%) + 인기 검색어 자동 텍스트
  - 데이터 없으면 None 반환
  - 수락 기준: 데이터 존재 시 한국어 인사이트 문자열 생성

- [ ] **2.5** 이벤트 정리 cron job `[S]`
  - `app/workers/roadmap_worker.py`의 `cron_jobs` 리스트에 추가
  - 매일 04:00 UTC에 90일 이전 이벤트 삭제
  - 수락 기준: cron 함수 존재, 삭제 쿼리 정확

---

## Phase 3: 프론트엔드 연동

- [ ] **3.1** API 함수 추가 `[S]`
  - 파일: `src/features/ops/actionkit/api.ts`
  - `fetchStats(rangeDays)` → GET /ops/actionkit/stats
  - `trackEvent(payload)` → POST /actionkits/track (fire-and-forget)
  - ActionKitStatsResponse 타입 정의
  - 수락 기준: 타입 안전 API 함수, catch로 에러 무시

- [ ] **3.2** 사용자 뷰 트래킹 삽입 `[M]`
  - 파일: `src/features/actionkit/components/ActionKitLibraryView.tsx`
  - 검색어: debounce 1초, 2글자 이상 → search 이벤트
  - ZIP 다운로드: handleBulkDownload에 bulk_download 이벤트
  - 북마크: toggleBookmark에 bookmark 이벤트 (추가만)
  - 상세 모달: openDetail에 detail_view 이벤트
  - ZIP 개별 다운로드: `?source=bulk` 파라미터 추가
  - 수락 기준: 각 행동 시 POST /track 호출, 실패해도 UX 영향 없음
  - 의존: 3.1

- [ ] **3.3** 법령 뷰 트래킹 삽입 `[S]`
  - 파일: `src/features/actionkit/components/LawGuideView.tsx`
  - 검색어 + 다운로드 클릭 트래킹
  - 수락 기준: 법령 뷰에서도 이벤트 전송
  - 의존: 3.1

- [ ] **3.4** stats-dashboard.tsx 전면 교체 `[L]`
  - 하드코딩 상수 (POPULAR_DOCS, SEARCH_KEYWORDS) 제거
  - props에서 stats API 데이터 수신
  - KPI 카드: stats.kpi 데이터 바인딩
  - 인기 서류: stats.popular_items 렌더링
  - 검색어: stats.search_keywords 렌더링
  - 인사이트: stats.insight 렌더링 (null이면 숨김)
  - 기간 필터: timeRange 변경 → fetchStats(rangeDays) 호출
  - 노후 항목: allItems 기반으로 변경
  - 수락 기준: 하드코딩 0개, 기간 필터 실제 동작, 빈 데이터 UI 존재
  - 의존: 3.1

- [ ] **3.5** view.tsx allItems 연동 `[M]`
  - 전체 카테고리 아이템 로드 (stats 탭용)
  - stats 탭에 allItems prop 전달
  - 수락 기준: 노후 항목 감지가 전체 아이템 기반으로 동작
  - 의존: 3.4

- [ ] **3.6** 빈 데이터 + delta=null 처리 `[S]`
  - 이벤트 데이터 0건: "아직 충분한 데이터가 수집되지 않았습니다" UI
  - delta가 null: 변화율 대신 "신규" 뱃지
  - 로딩 상태: Loader2 스피너
  - 수락 기준: 빈 데이터/로딩/에러 각 상태 정상 렌더링

---

## Phase 4: 테스트 + 검증

- [ ] **4.1** 트래킹 API 테스트 `[M]`
  - 파일: `tests/api/test_actionkit_tracking.py`
  - 테스트 케이스:
    - POST /track 정상 기록 (각 event_type)
    - 비인증 사용자 → user_id=None 기록
    - 잘못된 event_type → 422
    - item_id 없는 search 이벤트 정상
  - `git add -f` 필요 (.gitignore test_*.py 패턴)
  - 수락 기준: 4개 이상 테스트 통과
  - 의존: Phase 1 완료

- [ ] **4.2** 집계 서비스 테스트 `[L]`
  - 파일: `tests/services/test_actionkit_stats.py`
  - 테스트 케이스:
    - 빈 테이블 → 안전 반환 (0/None)
    - 이벤트 삽입 후 KPI 집계 정확성
    - 기간별 필터링 (7/30/365일)
    - 델타 계산 (이전 기간 0 → None)
    - 인기 순위 정렬
    - 검색어 집계
    - 인사이트 생성 (데이터 있을 때/없을 때)
  - `git add -f` 필요
  - 수락 기준: 7개 이상 테스트 통과
  - 의존: Phase 2 완료

- [ ] **4.3** Quality Gate 통과 `[S]`
  - `cd app-backend && uv run pytest -q` → 전체 pass
  - `cd app-frontend && pnpm lint` → 0 errors
  - 수락 기준: 기존 테스트 회귀 없음
  - 의존: Phase 3 완료

- [ ] **4.4** 마이그레이션 최종 검증 `[S]`
  - `uv run alembic check` → diff 없음
  - actionkit_events 테이블 DDL 확인
  - 수락 기준: alembic check clean

- [ ] **4.5** 브라우저 통합 테스트 `[M]`
  - chrome-devtools MCP로 localhost:3000 접속
  - Ops > 액션 키트 > 통계 대시보드 탭 확인
  - 기간 필터 변경 → API 호출 + 데이터 변경 확인
  - 콘솔 에러 없음 확인
  - 수락 기준: 하드코딩 데이터 없음, 동적 데이터 렌더링 확인

---

## Summary

| Phase | 태스크 수 | 상태 |
|-------|----------|------|
| Phase 1: 이벤트 수집 | 7 | 미시작 |
| Phase 2: 집계 서비스 | 5 | 미시작 |
| Phase 3: FE 연동 | 6 | 미시작 |
| Phase 4: 테스트/검증 | 5 | 미시작 |
| **합계** | **23** | |
