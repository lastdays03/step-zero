# StepZero 서비스 운영 모니터링 및 리포트 전략 보고서

> 작성일: 2026-03-04 | Status: 검토 대기

---

## 1. 현재 상태 분석

### 1.1 기존 `/ops/reports` 구현 현황

| 구성 요소 | 상태 | 상세 |
|-----------|------|------|
| **BE 서비스** | 🔴 Placeholder | `get_summary()` → 하드코딩 0 반환 |
| **BE API** | 🟡 라우트만 존재 | `GET /api/v1/ops/reports/summary` |
| **FE UI** | 🟢 완성됨 | 3개 KPI 카드 + 그리드 레이아웃 + 에러/로딩 처리 |
| **FE 타입** | 🟢 완성됨 | `OpsSummary` 타입 정의됨 |

**현재 반환 구조:**
```python
OpsSummary = {
    "active_users_7d": 0,       # placeholder
    "new_signups_7d": 0,        # placeholder
    "roadmaps_generated_7d": 0, # placeholder
    "generated_at": "2026-03-04T..."  # 실제 타임스탬프
}
```

### 1.2 사용 가능한 데이터 소스

| 지표 | DB 모델 | 핵심 필드 | 쿼리 난이도 |
|------|---------|-----------|------------|
| 활성 사용자 | `User` | `last_login_at` (indexed) | 간단 COUNT |
| 신규 가입 | `User` | `created_at` (indexed) | 간단 COUNT |
| 로드맵 생성 | `Roadmap` | `created_at` + `deleted_at` | 간단 COUNT |
| 채팅 세션 | `RoadmapChatThread` | `created_at` | 간단 COUNT |
| 액션킷 이용 | `ActionKitFile` | 접근 로그 없음 | ❌ 추가 모델 필요 |
| 커뮤니티 활동 | `GrowthClubPost` | `created_at` | 간단 COUNT |
| 에러/장애 | 없음 | - | ❌ 외부 서비스 필요 |

### 1.3 기존 인프라

- **Docker 서비스 5개:** app-db, app-redis, app-backend, app-worker, app-frontend
- **ARQ Worker:** 이미 비동기 작업 처리 중 (로드맵 생성) → cron job 확장 가능
- **UI 스택:** shadcn/ui + Tailwind → 차트 컴포넌트 추가 용이
- **감사 로그:** `AdminAuditLog` 모델 이미 존재

---

## 2. 2025-2026 운영 모니터링 모범 사례

### 2.1 Observability 3대 축

```
Logs (로그)    → structlog + JSON → Grafana Loki
Metrics (지표)  → Prometheus → Grafana Dashboard
Traces (추적)   → OpenTelemetry → Grafana Tempo / Sentry
```

### 2.2 외부 서비스 비교 (스타트업 관점)

#### 에러 트래킹

| 서비스 | Free Tier | 유료 시작가 | 특징 |
|--------|-----------|------------|------|
| **Sentry** | 5K 에러/월, 1 사용자 | $29/월 | FastAPI 네이티브 통합, 업계 표준 |
| **Better Stack** | 제한적 | Sentry의 ~1/6 가격 | Sentry SDK 호환, 로그+업타임 통합 |
| **New Relic** | 100GB/월 | $0.30/GB 초과분 | 관대한 무료 티어 |
| **Datadog** | 제한적 | $15/호스트/월 + APM $31 | 스타트업에겐 비용 부담 |

**권장: Sentry** — 10분 설정, $0 비용, FastAPI 네이티브

#### 제품 분석 (Product Analytics)

| 서비스 | Free Tier | 핵심 차이점 |
|--------|-----------|------------|
| **PostHog** | 100만 이벤트/월, 5K 세션 리플레이 | 올인원 (A/B 테스트, 기능 플래그, 세션 리플레이, SQL 에디터) |
| **Mixpanel** | 2000만 이벤트/월 | 이벤트 분석 특화, 세션 리플레이 없음 |
| **Amplitude** | 100K MTU | 대기업 향, 복잡한 설정 |

**권장: PostHog** — DAU/MAU, 퍼널, 리텐션 코호트, 기능 플래그 모두 무료

#### 메트릭 시각화

| 서비스 | Free Tier | 특징 |
|--------|-----------|------|
| **Grafana Cloud** | 10K 시리즈, 50GB 로그/트레이스 | 가장 관대한 무료 티어, Prometheus 네이티브 |
| **Self-hosted Grafana** | 무제한 | Docker Compose에 2개 서비스 추가 |

**권장: Grafana Cloud Free Tier** (초기) → Self-hosted (성장 시)

#### 업타임 모니터링

| 서비스 | Free Tier | 특징 |
|--------|-----------|------|
| **UptimeRobot** | 50 모니터 | HTTP/HTTPS, SSL, 이메일 알림 |
| **Better Uptime** | 10 모니터 | 인시던트 관리 통합 |

**권장: UptimeRobot** — 간단, 무료, 즉시 설정

### 2.3 Python/FastAPI 라이브러리 스택

| 라이브러리 | 용도 | 비용 |
|-----------|------|------|
| `sentry-sdk[fastapi]` | 에러 추적 + 성능 프로파일링 | 무료 |
| `structlog` | 구조화 JSON 로깅 | 무료 |
| `prometheus-fastapi-instrumentator` | `/metrics` 엔드포인트 자동 노출 | 무료 |
| `opentelemetry-instrumentation-fastapi` | 분산 추적 | 무료 |
| `opentelemetry-instrumentation-sqlalchemy` | SQL 쿼리 추적 | 무료 |
| `opentelemetry-instrumentation-redis` | Redis 추적 | 무료 |

### 2.4 프론트엔드 차트 라이브러리

| 라이브러리 | 특징 | StepZero 호환성 |
|-----------|------|----------------|
| **shadcn/ui Charts** (Recharts 기반) | 기존 스택과 100% 호환, copy-paste 패턴 | ✅ 최적 |
| **Tremor** | 분석 대시보드 특화 30+ 컴포넌트 | ⚠️ 추가 의존성 |
| **Recharts** (직접 사용) | 가장 유연하지만 스타일링 수동 | ⚠️ 작업량 많음 |

**권장: shadcn/ui Charts** — `npx shadcn@latest add chart` 한 줄로 설치

---

## 3. 추천 모니터링 스택 (단계별)

### Tier 0: 즉시 구현 (비용 $0, 1-2일)

| 영역 | 도구 | 설정 시간 |
|------|------|----------|
| 내부 KPI 대시보드 | 기존 `/ops/reports` → 실 DB 쿼리 연결 | 4시간 |
| 구조화 로깅 | `structlog` + RequestID 미들웨어 | 2시간 |
| Health Check | `GET /health` (DB + Redis 상태) | 1시간 |
| Docker Healthcheck | `docker-compose.yml` HEALTHCHECK 디렉티브 | 30분 |

### Tier 1: 첫 주 (비용 $0, 3-5일)

| 영역 | 도구 | 설정 시간 |
|------|------|----------|
| 에러 추적 | Sentry (free tier) | 2시간 |
| 제품 분석 | PostHog (free tier) | 3시간 |
| 업타임 모니터링 | UptimeRobot | 30분 |
| 메트릭 수집 | `prometheus-fastapi-instrumentator` | 1시간 |
| Slack 알림 | Incoming Webhook + AlertService | 2시간 |

### Tier 2: 첫 달 (비용 $0)

| 영역 | 도구 | 설정 시간 |
|------|------|----------|
| 메트릭 시각화 | Grafana Cloud Free Tier | 3시간 |
| 로그 집계 | Grafana Loki (via Cloud) | 2시간 |
| DB 모니터링 | `pg_stat_statements` + 슬로우 쿼리 대시보드 | 3시간 |
| 주간 리포트 자동화 | ARQ cron job → Slack 발송 | 4시간 |
| 시계열 차트 | shadcn/ui Charts | 4시간 |

### Tier 3: PMF 이후 (유료 전환 시점)

| 영역 | 도구 | 예상 비용 |
|------|------|----------|
| Sentry Team | 더 많은 에러 + 알림 규칙 | $29/월 |
| Grafana Cloud Pro | 더 많은 시리즈 | $49/월 |
| PostHog 유료 | 100만+ 이벤트 | 종량제 |
| OpenTelemetry 분산 추적 | Grafana Tempo | Tier 2 내 무료 |

---

## 4. `/ops/reports` 구체적 구현 전략

### 4.1 확장된 KPI 정의

#### Phase 1 (즉시 - 기존 DB로 가능)

```python
class OpsSummary:
    # === 성장 지표 ===
    active_users_7d: int          # last_login_at >= 7일 전
    active_users_30d: int         # last_login_at >= 30일 전
    new_signups_7d: int           # created_at >= 7일 전
    new_signups_30d: int          # created_at >= 30일 전

    # === 핵심 기능 사용 ===
    roadmaps_generated_7d: int    # Roadmap.created_at >= 7일 전
    roadmaps_generated_30d: int
    chat_sessions_7d: int         # RoadmapChatThread.created_at >= 7일 전
    community_posts_7d: int       # GrowthClubPost.created_at >= 7일 전

    # === 비율 지표 ===
    dau_mau_ratio: float          # active_7d / active_30d (stickiness)
    signup_to_roadmap_rate: float # 가입 후 로드맵 생성 비율

    # === 총계 ===
    total_users: int
    total_teams: int
    total_roadmaps: int

    # === 메타 ===
    generated_at: str
    range: str  # "7d" | "30d"
```

#### Phase 2 (시계열 데이터)

```python
class OpsTimeSeries:
    period: str                        # "daily" | "weekly"
    data_points: list[TimeSeriesPoint] # [{date, active_users, signups, roadmaps}]
```

#### Phase 3 (외부 서비스 연동)

```python
class OpsSystemHealth:
    api_error_rate_1h: float      # Sentry에서 가져옴
    api_p99_latency_ms: float     # Prometheus에서 가져옴
    db_connection_usage_pct: float # pg_stat_activity
    redis_memory_usage_mb: float  # Redis INFO
    uptime_30d_pct: float         # UptimeRobot에서 가져옴
```

### 4.2 백엔드 API 설계

```
GET /api/v1/ops/reports/summary?range=7d|30d
GET /api/v1/ops/reports/timeseries?range=7d|30d&granularity=daily
GET /api/v1/ops/reports/system-health        (Phase 3)
GET /api/v1/ops/reports/export?format=csv    (Phase 3)
```

### 4.3 프론트엔드 UI 구성

```
┌─────────────────────────────────────────────────────────┐
│  [7일 ▼] [30일]  [새로고침 🔄]        생성: 2026-03-04 09:00 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ 활성 사용자 │  │ 신규 가입  │  │ 로드맵 생성 │  │ 채팅 세션  ││
│  │   127    │  │    23    │  │    45    │  │    89    ││
│  │ +12% ▲   │  │ -5% ▼   │  │ +30% ▲   │  │ +8% ▲   ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │ DAU/MAU  │  │ 가입→로드맵│  │ 총 사용자  │  │ 커뮤니티   ││
│  │  42.3%   │  │  68.2%   │  │  1,234   │  │  15 게시물 ││
│  │ 양호 🟢   │  │ 우수 🟢   │  │          │  │          ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
│                                                         │
│  ─── 시계열 차트 (Phase 2) ───                            │
│  📈 [일별 활성 사용자] [일별 가입] [일별 로드맵]               │
│  ┌─────────────────────────────────────────────────────┐│
│  │                    ╱╲                               ││
│  │              ╱╲  ╱  ╲  ╱╲                          ││
│  │         ╱╲ ╱  ╲╱    ╲╱  ╲                         ││
│  │    ╱╲ ╱  ╲                 ╲                       ││
│  │ ──╱  ╲                      ╲──                    ││
│  │ 2/25  2/26  2/27  2/28  3/1   3/2  3/3  3/4      ││
│  └─────────────────────────────────────────────────────┘│
│                                                         │
│  ─── 시스템 상태 (Phase 3) ───                            │
│  [API 에러율: 0.3%] [P99 지연: 234ms] [DB 연결: 12/100]   │
└─────────────────────────────────────────────────────────┘
```

### 4.4 알림/리포트 자동화

```
ARQ Worker (cron)
├── 매일 09:00 KST → Slack 일일 요약
├── 매주 월요일 09:00 KST → Slack 주간 리포트
└── 실시간 → 임계값 알림
    ├── 에러율 > 5% (1분 간) → ⚠️ Slack
    ├── 신규가입 = 0 (24시간) → ⚠️ Slack
    └── DB 연결 > 80% → 🚨 Slack
```

---

## 5. PostgreSQL 모니터링 쿼리

### 핵심 운영 쿼리 (Phase 3에서 API 노출)

```sql
-- 1. 느린 쿼리 Top 10 (pg_stat_statements 필요)
SELECT query, calls, total_exec_time/calls AS avg_ms
FROM pg_stat_statements ORDER BY avg_ms DESC LIMIT 10;

-- 2. 현재 활성 연결
SELECT count(*) AS total,
       count(*) FILTER (WHERE state = 'active') AS active,
       count(*) FILTER (WHERE state = 'idle') AS idle
FROM pg_stat_activity;

-- 3. 테이블 크기
SELECT tablename, pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size
FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size('public.'||tablename) DESC;

-- 4. 캐시 적중률 (목표: >99%)
SELECT sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) AS ratio
FROM pg_statio_user_tables;
```

---

## 6. Docker Health Check 전략

```yaml
# docker-compose.dev.yml 업그레이드
services:
  app-backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  app-db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  app-redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
```

`GET /health` 엔드포인트: DB ping + Redis ping + 워커 상태 확인

---

## 7. 비용 요약

| 단계 | 월 비용 | 포함 서비스 |
|------|--------|-----------|
| **Tier 0-2** (첫 1-3개월) | **$0** | 내부 대시보드, Sentry, PostHog, Grafana Cloud, UptimeRobot, structlog |
| **Tier 3** (PMF 이후) | **~$80-120** | Sentry Team + Grafana Pro + PostHog 종량제 |

---

## 8. 구현 우선순위 권장

```
Week 1 (즉시):
 ① BE reports 실 쿼리 연결 (active_users, signups, roadmaps)
 ② 기간 필터 지원 (7d/30d)
 ③ 전주 대비 변화율 계산
 ④ FE KPI 카드 확장 (4→8개)

Week 2:
 ⑤ structlog + RequestID 미들웨어
 ⑥ GET /health 엔드포인트
 ⑦ Sentry 통합
 ⑧ Docker healthcheck

Week 3:
 ⑨ PostHog 프론트엔드 통합
 ⑩ 시계열 API + shadcn/ui 차트
 ⑪ Slack 알림 서비스

Week 4:
 ⑫ ARQ cron 주간 리포트
 ⑬ Prometheus metrics 노출
 ⑭ Grafana Cloud 연결
```

---

## 부록: 참고 자료

- [Sentry FastAPI Integration](https://docs.sentry.io/platforms/python/integrations/fastapi/)
- [PostHog B2B SaaS Metrics](https://posthog.com/product-engineers/b2b-saas-product-metrics)
- [Grafana Cloud Free Tier](https://grafana.com/pricing/)
- [FastAPI Observability Stack](https://github.com/blueswen/fastapi-observability)
- [shadcn/ui Charts](https://ui.shadcn.com/charts/area)
- [pg_stat_statements Guide](https://stormatics.tech/blogs/enhancing-postgresql-performance-monitoring-a-comprehensive-guide-to-pg_stat_statements)
- [FastAPI Observability Practical Guide (2025)](https://blog.greeden.me/en/2025/12/16/fastapi-observability-practical-guide/)
