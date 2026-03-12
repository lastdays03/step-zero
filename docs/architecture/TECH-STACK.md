# StepZero 기술 스택 문서

> AI 기반 스타트업 창업자 액셀러레이팅 플랫폼
> 최종 갱신: 2026-03-12

---

## 1. 프로젝트 개요

StepZero는 사용자 입력으로 개인화 로드맵을 생성하고, RAG 기반 법률/창업 상담을 제공하는 모노레포(Monorepo) 프로젝트이다.

| 구성 요소 | 기술 스택 | 포트 |
|-----------|----------|------|
| Backend | FastAPI + Python 3.13 | 8000 |
| Frontend | Next.js 16 + React 18 + TypeScript 5 | 3000 |
| Database | PostgreSQL 16 + pgvector | 5432 |
| Cache/Queue | Redis (alpine) + ARQ | 6379 |
| Worker | ARQ 비동기 워커 (로드맵 생성 전용) | - |

---

## 2. 루트 디렉토리 구조

```
step-zero/
├── app-backend/                 # FastAPI 백엔드 (Python 3.13)
├── app-frontend/                # Next.js 프론트엔드 (React 18)
├── docs/                        # 기획/설계/컨텍스트 문서
│   ├── context/                 #   세션 운영 (dev-status, decisions, handoff, ops-rules)
│   ├── plans/                   #   기획 + 구현
│   │   ├── active/              #     진행 중인 작업
│   │   ├── reports/             #     독립 리서치 보고서
│   │   └── done/                #     완료 아카이브 (37개 프로젝트)
│   ├── architecture/            #   시스템 아키텍처 설계
│   ├── operations/              #   팀 협업 프로세스 규칙
│   ├── dev-guide/               #   개발자 가이드/체크리스트
│   └── archive/                 #   역할 완료 문서 보관
│       ├── brainstorm/
│       └── feedback/
├── scripts/                     # 루트 유틸리티 스크립트
│   ├── init_db.sh               #   pgvector 확장 초기화 (Docker entrypoint)
│   └── playwright/              #   브라우저 테스트 스니펫
│       ├── smoke-test.js        #     전체 스택 smoke 테스트
│       ├── api-health.js        #     API 상태 점검
│       └── web-vitals.js        #     Core Web Vitals 측정
├── package.json                 # 루트 npm 패키지 (Husky + commitlint)
├── pnpm-lock.yaml               # pnpm 잠금 파일
├── commitlint.config.cjs        # Conventional Commits 규칙
├── docker-compose.dev.yml       # 개발 환경 (5 서비스)
├── docker-compose.prod.yml      # 프로덕션 환경
├── CLAUDE.md                    # AI 에이전트 개발 가이드
└── AGENTS.md                    # AI 에이전트 프로젝트 규칙
```

### 루트 설정 파일

#### package.json

루트 `package.json`은 코드 품질 도구만 관리한다. 애플리케이션 의존성은 각 서브 프로젝트에서 관리.

```json
{
  "name": "stepzero-repo-tools",
  "private": true,
  "packageManager": "pnpm@10.30.3",
  "scripts": {
    "prepare": "husky",
    "lint:commits": "commitlint --from HEAD~1 --to HEAD"
  },
  "devDependencies": {
    "@commitlint/cli": "^19.8.1",
    "@commitlint/config-conventional": "^19.8.1",
    "husky": "^9.1.7"
  }
}
```

| 도구 | 버전 | 역할 |
|------|------|------|
| pnpm | 10.30.3 | 패키지 매니저 (Corepack 관리) |
| Husky | 9.1.7 | Git 훅 관리 (pre-push, commit-msg) |
| commitlint | 19.8.1 | Conventional Commits 검증 |

#### commitlint.config.cjs

Conventional Commits 스타일 강제: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `perf:`, `ci:`, `build:`, `revert:`

---

## 3. Backend (app-backend/)

### 3.1 디렉토리 구조

```
app-backend/
├── app/                              # 애플리케이션 소스 코드
│   ├── main.py                       #   FastAPI 앱 진입점 (미들웨어, 라우터 등록)
│   │
│   ├── core/                         #   핵심 인프라 레이어
│   │   ├── config.py                 #     Pydantic Settings (환경변수 관리)
│   │   ├── db.py                     #     DB 세션 팩토리 (get_session)
│   │   ├── security.py               #     JWT 생성/검증 유틸리티
│   │   ├── exceptions.py             #     DDD Exception 계층 (AppException → 구체 클래스)
│   │   ├── logging.py                #     structlog 기반 구조화 로깅
│   │   ├── sentry.py                 #     GlitchTip(Sentry) 초기화
│   │   └── rate_limit.py             #     slowapi Rate Limiting 설정
│   │
│   ├── middleware/                    #   HTTP 미들웨어
│   │   └── logging.py                #     요청 컨텍스트 로깅 미들웨어
│   │
│   ├── api/                          #   HTTP API 레이어
│   │   ├── deps.py                   #     공통 의존성 (get_current_user, require_platform_admin 등)
│   │   ├── problem.py                #     RFC 9457 에러 응답 (application/problem+json)
│   │   └── v1/                       #     API v1 라우터 (/api/v1 prefix)
│   │       ├── api.py                #       라우터 통합 (모든 feature 라우터 등록)
│   │       ├── schemas.py            #       공통 응답 스키마
│   │       ├── announcements.py      #       공지사항 API
│   │       ├── notifications.py      #       알림 API (SSE 포함)
│   │       ├── storage.py            #       파일 업로드/다운로드 API
│   │       ├── auth/                 #       인증 라우터
│   │       │   └── router.py         #         이메일/Google OAuth 로그인, 토큰 갱신
│   │       ├── dashboard/            #       대시보드 라우터
│   │       │   ├── router.py         #         통합 라우터
│   │       │   └── stats.py          #         통계 엔드포인트
│   │       ├── roadmaps/             #       로드맵 라우터
│   │       │   ├── router.py         #         통합 라우터
│   │       │   ├── create.py         #         로드맵 생성 (POST)
│   │       │   ├── get.py            #         로드맵 조회 (GET)
│   │       │   └── jobs.py           #         비동기 Job 관리 (생성/폴링)
│   │       ├── profile/              #       프로필 라우터
│   │       │   ├── router.py         #         통합 라우터
│   │       │   └── me.py             #         내 프로필 CRUD
│   │       ├── actionkit/            #       액션킷 라우터
│   │       │   ├── router.py         #         통합 라우터
│   │       │   ├── listing.py        #         카테고리/아이템 목록
│   │       │   ├── detail.py         #         아이템 상세
│   │       │   ├── files.py          #         파일 서빙 (Static mount)
│   │       │   ├── tracking.py       #         열람/다운로드 추적
│   │       │   └── schemas.py        #         요청/응답 스키마
│   │       ├── chat/                 #       AI 채팅 라우터
│   │       │   └── router.py         #         세션 관리 + SSE 스트리밍
│   │       ├── rag/                  #       RAG 라우터
│   │       │   └── router.py         #         벡터 검색 + 법률 채팅
│   │       ├── growth_club/          #       그로스클럽(커뮤니티) 라우터
│   │       │   ├── router.py         #         통합 라우터
│   │       │   ├── posts.py          #         게시글 CRUD
│   │       │   └── comments.py       #         댓글 CRUD
│   │       └── ops/                  #       관리자(Ops) 라우터
│   │           ├── router.py         #         통합 라우터 (superuser 전용)
│   │           ├── home.py           #         관리자 대시보드 통계
│   │           ├── users.py          #         사용자 관리 (정지/해제)
│   │           ├── announcements.py  #         공지사항 관리
│   │           ├── audit_logs.py     #         감사 로그 조회
│   │           ├── actionkit.py      #         액션킷 관리
│   │           ├── files.py          #         파일 관리
│   │           ├── growth_club.py    #         게시글 관리
│   │           ├── reports.py        #         운영 리포트
│   │           ├── roadmap_templates.py  #     로드맵 템플릿 CRUD
│   │           ├── roadmap_template_schemas.py
│   │           └── schemas.py        #         관리자 전용 스키마
│   │
│   ├── features/                     #   비즈니스 로직 (Feature-Based 구조)
│   │   ├── auth/                     #     인증 feature
│   │   │   ├── application/
│   │   │   │   └── auth_service.py   #       이메일/OAuth 로그인, JWT 발급, 팀 자동 생성
│   │   │   └── domain/               #       인증 도메인 모델
│   │   │
│   │   ├── profile/                  #     사용자 프로필 feature
│   │   │   ├── application/
│   │   │   │   └── service.py        #       프로필 CRUD 서비스
│   │   │   └── domain/
│   │   │
│   │   ├── dashboard/                #     대시보드 feature
│   │   │   ├── application/
│   │   │   │   └── dashboard_service.py  #   통계 집계 (로드맵 진행률, 활동 요약)
│   │   │   └── domain/
│   │   │
│   │   ├── roadmaps/                 #     로드맵 feature (핵심 비즈니스 로직)
│   │   │   ├── application/
│   │   │   │   ├── roadmap_service.py            #  로드맵 CRUD
│   │   │   │   ├── roadmap_generation_service.py #  AI 로드맵 생성 파이프라인
│   │   │   │   ├── roadmap_progress_service.py   #  진행률 추적
│   │   │   │   ├── actionkit_matcher.py          #  ActionKit 매칭 (업종별 법률)
│   │   │   │   ├── llm_personalizer.py           #  LLM 기반 개인화
│   │   │   │   ├── template_resolver.py          #  템플릿 해석
│   │   │   │   ├── context_builder.py            #  LLM 컨텍스트 구성
│   │   │   │   ├── worker_queue.py               #  ARQ 작업 큐 연동
│   │   │   │   └── deps.py                       #  DI 설정 (@lru_cache singleton)
│   │   │   └── domain/
│   │   │
│   │   ├── rag/                      #     RAG feature
│   │   │   ├── application/
│   │   │   │   ├── rag_service.py    #       PGVector 벡터 검색 + OpenAI 임베딩
│   │   │   │   ├── semantic_router.py #      의미 기반 라우팅 (법률 vs 일반 쿼리 분류)
│   │   │   │   └── deps.py           #       DI 설정
│   │   │   └── domain/
│   │   │
│   │   ├── chat/                     #     AI 채팅 feature
│   │   │   └── application/
│   │   │       ├── chat_service.py   #       법률 → RAG, 일반 → LLM 직접 호출
│   │   │       ├── session_service.py #      채팅 세션 관리
│   │   │       ├── intent_classifier.py #    의도 분류기
│   │   │       ├── schemas.py        #       채팅 스키마
│   │   │       └── deps.py
│   │   │
│   │   ├── actionkit/                #     법률 행정 키트 feature
│   │   │   ├── application/
│   │   │   │   ├── service.py        #       카테고리/아이템/파일 관리
│   │   │   │   └── file_pipeline.py  #       파일 생성 파이프라인
│   │   │   └── domain/
│   │   │       └── data.py           #       도메인 상수/데이터
│   │   │
│   │   ├── growth_club/              #     그로스클럽(커뮤니티) feature
│   │   │   └── application/
│   │   │       └── post_service.py   #       게시글/댓글 CRUD
│   │   │
│   │   ├── ops/                      #     관리자 콘솔 feature (superuser only)
│   │   │   ├── application/
│   │   │   │   ├── home/
│   │   │   │   │   └── service.py    #       관리자 대시보드 통계
│   │   │   │   ├── users/
│   │   │   │   │   ├── service.py    #       사용자 관리 (정지/해제)
│   │   │   │   │   └── schemas.py
│   │   │   │   ├── announcements/
│   │   │   │   │   └── service.py    #       공지사항 CRUD
│   │   │   │   ├── audit_logs/
│   │   │   │   │   ├── service.py    #       감사 로그 조회/필터
│   │   │   │   │   └── constants.py  #       로그 타입 상수
│   │   │   │   ├── actionkit/
│   │   │   │   │   ├── service.py    #       액션킷 관리
│   │   │   │   │   └── stats_service.py  #   액션킷 통계
│   │   │   │   ├── growth_club/
│   │   │   │   │   └── service.py    #       게시글 관리
│   │   │   │   ├── roadmap_templates/
│   │   │   │   │   └── service.py    #       로드맵 템플릿 CRUD
│   │   │   │   ├── files/
│   │   │   │   │   └── service.py    #       파일 관리
│   │   │   │   └── reports/
│   │   │   │       └── service.py    #       운영 리포트 생성
│   │   │   └── domain/
│   │   │
│   │   └── AGENTS.md
│   │
│   ├── models/                       #   SQLModel ORM 모델 (16개 모델)
│   │   ├── user.py                   #     User 모델
│   │   ├── team.py                   #     Team, TeamMember 모델
│   │   ├── profile.py                #     UserProfile 모델
│   │   ├── roadmap.py                #     Roadmap, RoadmapStep, RoadmapJob 모델
│   │   ├── roadmap_template.py       #     RoadmapTemplate 모델
│   │   ├── roadmap_chat.py           #     RoadmapChatSession, RoadmapChatMessage 모델
│   │   ├── actionkit.py              #     ActionKitCategory, ActionKitItem, ActionKitFile 모델
│   │   ├── actionkit_event.py        #     ActionKitEvent 모델 (열람/다운로드 추적)
│   │   ├── growth_club.py            #     Post, Comment 모델
│   │   ├── file.py                   #     File 모델 (범용 파일 관리)
│   │   ├── announcement.py           #     Announcement 모델
│   │   ├── notification.py           #     Notification 모델
│   │   ├── audit_log.py              #     AuditLog 모델
│   │   ├── admin_audit_log.py        #     AdminAuditLog 모델
│   │   ├── refresh_token.py          #     RefreshToken 모델
│   │   └── user_discipline_history.py #    UserDisciplineHistory 모델
│   │
│   ├── repositories/                 #   데이터 접근 계층 (Repository 패턴)
│   │   ├── user_repository.py        #     사용자 CRUD
│   │   ├── team_repository.py        #     팀/멤버 CRUD
│   │   ├── roadmap_repository.py     #     로드맵 CRUD
│   │   ├── roadmap_job_repository.py #     비동기 Job 관리
│   │   ├── roadmap_chat_repository.py #    채팅 세션/메시지 CRUD
│   │   ├── actionkit_repository.py   #     액션킷 CRUD
│   │   ├── file_repository.py        #     파일 CRUD
│   │   └── refresh_token_repository.py #   Refresh Token 관리
│   │
│   ├── services/                     #   공유 인프라 서비스
│   │   ├── vector_store.py           #     VectorStoreService (PGVector + OpenAI 임베딩)
│   │   ├── law_api_client.py         #     국가법령정보센터 API 클라이언트
│   │   ├── law_fetcher.py            #     법령 데이터 수집기
│   │   ├── law_etl.py                #     법령 ETL 파이프라인
│   │   ├── actionkit_etl.py          #     ActionKit ETL 파이프라인
│   │   ├── actionkit_data_source.py  #     ActionKit 시드 데이터 소스
│   │   ├── notification_pubsub.py    #     Redis Pub/Sub 알림 서비스
│   │   └── storage/                  #     파일 스토리지 추상화
│   │       ├── base.py               #       스토리지 인터페이스
│   │       ├── factory.py            #       팩토리 (local/r2 선택)
│   │       ├── local.py              #       로컬 파일시스템 구현
│   │       └── r2.py                 #       Cloudflare R2 구현
│   │
│   └── workers/                      #   비동기 워커
│       └── roadmap_worker.py         #     ARQ 워커 (로드맵 생성 작업 처리)
│
├── tests/                            # 테스트 코드
│   ├── conftest.py                   #   pytest 설정 (테스트 유저/팀 시드, DB fixture)
│   ├── test_config.py                #   설정 테스트
│   ├── test_sentry_integration.py    #   Sentry 통합 테스트
│   ├── api/                          #   API 엔드포인트 테스트 (20개)
│   │   ├── test_auth.py              #     인증 API 테스트
│   │   ├── test_v2_auth.py           #     v2 인증 테스트
│   │   ├── test_profile.py           #     프로필 API 테스트
│   │   ├── test_dashboard.py         #     대시보드 API 테스트
│   │   ├── test_roadmap_multi.py     #     멀티 로드맵 테스트
│   │   ├── test_roadmap_jobs_validate.py  # Job 유효성 검증
│   │   ├── test_roadmap_task_status.py    # 태스크 상태 테스트
│   │   ├── test_chat_sessions.py     #     채팅 세션 테스트
│   │   ├── test_chat_stream.py       #     채팅 스트리밍 테스트
│   │   ├── test_actionkit_tracking.py #    액션킷 추적 테스트
│   │   ├── test_ops_audit_logs.py    #     감사 로그 테스트
│   │   ├── test_ops_audit_log_actions.py
│   │   ├── test_ops_files.py         #     파일 관리 테스트
│   │   ├── test_ops_roadmap_templates.py  # 템플릿 관리 테스트
│   │   ├── test_refresh_token.py     #     토큰 갱신 테스트
│   │   ├── test_announcement_notifications.py
│   │   ├── test_notification_optimization.py
│   │   └── test_v1_deprecation_headers.py
│   ├── services/                     #   서비스 단위 테스트 (10개)
│   │   ├── test_roadmap_generation_service.py
│   │   ├── test_llm_personalizer.py
│   │   ├── test_context_builder.py
│   │   ├── test_template_resolver.py
│   │   ├── test_semantic_router.py
│   │   ├── test_intent_classifier.py
│   │   ├── test_law_api_client.py
│   │   ├── test_actionkit_stats.py
│   │   ├── test_storage_backend.py
│   │   └── test_safety_qa.py
│   ├── repositories/                 #   Repository 테스트
│   │   ├── test_file_repository.py
│   │   └── test_roadmap_chat_repository.py
│   ├── integration/                  #   통합 테스트
│   │   └── test_roadmap_generation.py
│   └── eval/                         #   RAG 평가 테스트 (비용 발생, 기본 제외)
│       ├── conftest.py
│       ├── test_tier2_metrics.py     #     Tier 2 (~5분, ~$2-5)
│       └── test_tier3_full.py        #     Tier 3 (~15분, ~$15-25)
│
├── alembic/                          # DB 마이그레이션
│   ├── env.py                        #   Alembic 환경 설정
│   ├── script.py.mako                #   마이그레이션 템플릿
│   └── versions/                     #   마이그레이션 파일 (18개, 001~018)
│
├── scripts/                          # 유틸리티 스크립트
│   ├── setup_dev.sh                  #   개발 환경 초기화 (uv sync + DB)
│   ├── export_openapi.py             #   OpenAPI 스키마 JSON 생성
│   ├── fetch_laws.py                 #   국가법령정보센터 법령 수집
│   ├── fetch_laws_config.py          #   법령 수집 설정 (WAVE_CONFIG)
│   ├── seed_rag_vectors.py           #   RAG 벡터 생성/적재
│   ├── seed_actionkit.py             #   ActionKit 시드 데이터 생성
│   ├── bootstrap_rag.sh              #   RAG 시드 실행 래퍼
│   ├── bootstrap_actionkit.sh        #   ActionKit 시드 실행 래퍼
│   ├── backup_law_vectors.py         #   법률 벡터 백업
│   ├── migrate_to_r2.py              #   로컬 → R2 스토리지 마이그레이션
│   ├── run_alembic.sh                #   Alembic 실행 래퍼
│   ├── reset_migrations.sh           #   마이그레이션 초기화
│   ├── seeds/                        #   시드 데이터
│   │   └── actionkit_seed_source.py  #     ActionKit 시드 소스
│   └── eval/                         #   평가 스크립트
│       ├── generate_golden_dataset.py #    Golden Dataset 생성
│       ├── roadmap_evaluator.py      #     로드맵 품질 평가기
│       └── run_evaluation.py         #     평가 실행
│
├── pyproject.toml                    # 패키지 메타데이터 + 도구 설정
├── Makefile                          # 개발 명령 자동화
├── alembic.ini                       # Alembic 설정
├── openapi.json                      # 생성된 OpenAPI 스키마
├── Dockerfile                        # 개발용 Docker 이미지
├── Dockerfile.prod                   # 프로덕션 Docker 이미지
├── .python-version                   # Python 3.13
├── uv.lock                           # uv 잠금 파일
├── .env                              # 공유 기본값
├── .env.local                        # 로컬 비밀값 (Git 제외)
└── .env.docker.local                 # Docker Compose override
```

### 3.2 레이어 구조 설명

Backend는 **Feature-Based + Layered Architecture**를 따른다.

```
요청 흐름:
  HTTP Request
    → api/v1/{feature}/router.py     (HTTP 라우터: 요청 파싱, 응답 포맷)
    → api/deps.py                    (인증/인가 의존성 주입)
    → features/{feature}/application/ (비즈니스 로직: 서비스 계층)
    → repositories/                  (데이터 접근: Repository 패턴)
    → models/                        (ORM 모델: SQLModel)
    → core/db.py                     (DB 세션: asyncpg)
```

| 레이어 | 디렉토리 | 역할 |
|--------|---------|------|
| API | `api/v1/{feature}/` | HTTP 엔드포인트 정의, 요청/응답 스키마 |
| Application | `features/{feature}/application/` | 비즈니스 로직, 유스케이스 |
| Domain | `features/{feature}/domain/` | 도메인 모델, 비즈니스 규칙 |
| Repository | `repositories/` | 데이터 접근 추상화 |
| Model | `models/` | SQLModel ORM 모델 정의 |
| Core | `core/` | 횡단 관심사 (설정, 보안, 로깅, 예외) |
| Service | `services/` | 공유 인프라 서비스 (벡터 스토어, 스토리지) |

### 3.3 Feature 모듈 상세

| Feature | 역할 | 주요 서비스 |
|---------|------|------------|
| `auth` | 이메일/Google OAuth 로그인, JWT 토큰 발급, 팀 자동 생성 | `AuthService` |
| `profile` | 사용자 프로필 CRUD (이름, 업종, 사업 단계) | `ProfileService` |
| `dashboard` | 대시보드 통계 (로드맵 진행률, 활동 요약) | `DashboardService` |
| `roadmaps` | AI 로드맵 생성/관리 (비동기 파이프라인) | `RoadmapService`, `RoadmapGenerationService`, `ActionKitMatcher`, `LLMPersonalizer` |
| `rag` | RAG 벡터 검색 + 의미 기반 라우팅 | `RagService`, `SemanticRouter` |
| `chat` | 로드맵 기반 AI 채팅 (SSE 스트리밍) | `ChatService`, `SessionService`, `IntentClassifier` |
| `actionkit` | 법률 행정 키트 (카테고리/아이템/파일) | `ActionKitService`, `FilePipeline` |
| `growth_club` | 커뮤니티 게시판 (게시글/댓글) | `PostService` |
| `ops` | 관리자 콘솔 (사용자/콘텐츠/통계 관리, superuser 전용) | 8개 서브 서비스 |

### 3.4 주요 의존성

#### 프로덕션 의존성

| 카테고리 | 라이브러리 | 버전 | 용도 |
|---------|-----------|------|------|
| **웹 프레임워크** | FastAPI | >=0.135.0 | ASGI 웹 프레임워크 |
| | Uvicorn | >=0.27.0 | ASGI 서버 (표준 extras 포함) |
| **ORM/DB** | SQLAlchemy | >=2.0.48 | ORM (비동기 지원) |
| | SQLModel | >=0.0.37 | Pydantic + SQLAlchemy 하이브리드 |
| | asyncpg | >=0.29.0 | PostgreSQL 비동기 드라이버 |
| | Alembic | >=1.13.2 | DB 마이그레이션 |
| | pgvector | >=0.2.0 | PostgreSQL 벡터 확장 |
| | psycopg2-binary | >=2.9.9 | PostgreSQL 동기 드라이버 (시드용) |
| **AI/LLM** | LangChain | >=0.1.0 | LLM 오케스트레이션 |
| | langchain-openai | >=0.0.5 | OpenAI 통합 |
| | langchain-core | >=0.1.20 | LangChain 코어 |
| | langchain-community | >=0.0.20 | 커뮤니티 통합 |
| | langchain-postgres | >=0.0.3 | PostgreSQL Vector Store |
| | OpenAI | >=1.0.0 | OpenAI API 클라이언트 |
| | tiktoken | >=0.5.0 | 토큰 카운팅 |
| **캐시/큐** | Redis | >=5.0.0 | 캐시 + Pub/Sub |
| | ARQ | >=0.25.0 | 비동기 작업 큐 (Redis 기반) |
| **보안** | bcrypt | >=4.0.0 | 비밀번호 해싱 |
| | PyJWT | >=2.8.0 | JWT 토큰 생성/검증 |
| | google-auth | >=2.26.0 | Google OAuth 토큰 검증 |
| **스토리지** | boto3 | >=1.42.61 | AWS S3/Cloudflare R2 |
| **관찰성** | sentry-sdk[fastapi] | >=2.19.0 | 에러 추적 (GlitchTip 호환) |
| | structlog | >=24.4.0 | 구조화 JSON 로깅 |
| **기타** | Pydantic Settings | >=2.1.0 | 환경변수 관리 |
| | slowapi | >=0.1.9 | Rate Limiting |
| | pdfplumber | >=0.10.3 | PDF 파싱 (법령 문서) |
| | requests | >=2.31.0 | HTTP 클라이언트 |
| | python-multipart | - | 폼 데이터 파싱 |
| | numpy | >=1.26.0 | 수치 계산 (벡터 연산) |
| | greenlet | >=3.0.0 | 경량 스레딩 (SQLAlchemy 비동기) |

#### 개발 의존성

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| pytest | >=8.0.0 | 테스트 프레임워크 |
| pytest-asyncio | >=0.23.0 | 비동기 테스트 (asyncio_mode="auto") |
| httpx | >=0.26.0 | 비동기 HTTP 테스트 클라이언트 |
| aiosqlite | >=0.20.0 | SQLite 비동기 드라이버 (테스트 DB) |
| black | >=24.0.0 | 코드 포맷팅 (line-length=88) |
| isort | >=5.13.0 | import 정렬 (profile=black) |
| flake8 | >=7.0.0 | 린팅 |
| mypy | >=1.8.0 | 타입 체크 (strict mode) |
| polyfactory | >=2.14.0 | 테스트 팩토리 |

### 3.5 Docker 이미지

| 환경 | Dockerfile | 베이스 이미지 | 특징 |
|------|-----------|-------------|------|
| 개발 | `Dockerfile` | python:3.13-slim | `uv sync --extra dev`, --reload |
| 프로덕션 | `Dockerfile.prod` | python:3.13-slim | `uv sync --no-dev`, 최적화 |

빌드 도구: **uv 0.10** (`ghcr.io/astral-sh/uv:0.10`에서 복사)

---

## 4. Frontend (app-frontend/)

### 4.1 디렉토리 구조

```
app-frontend/
├── src/
│   ├── app/                           # Next.js App Router 페이지
│   │   ├── layout.tsx                 #   루트 레이아웃 (AuthProvider, 폰트, 메타데이터)
│   │   ├── page.tsx                   #   루트 페이지 (/ → /dashboard 리다이렉트)
│   │   ├── error.tsx                  #   전역 에러 바운더리
│   │   ├── login/
│   │   │   └── page.tsx               #   로그인 페이지 (Public)
│   │   └── (dashboard)/               #   인증 필요 Route Group
│   │       ├── layout.tsx             #     대시보드 레이아웃 (Sidebar + Header)
│   │       ├── dashboard/
│   │       │   └── page.tsx           #     대시보드 메인 (통계/로드맵 요약)
│   │       ├── roadmap/
│   │       │   └── page.tsx           #     로드맵 관리 (생성/실행/진행률)
│   │       ├── actionkit/
│   │       │   └── page.tsx           #     액션킷 (법령 가이드 + 키트 라이브러리)
│   │       ├── growth-club/
│   │       │   └── page.tsx           #     그로스클럽 (커뮤니티 게시판)
│   │       ├── profile/
│   │       │   └── page.tsx           #     내 프로필 편집
│   │       ├── announcements/
│   │       │   └── [id]/
│   │       │       └── page.tsx       #     공지사항 상세 (동적 라우트)
│   │       ├── settings/
│   │       │   └── page.tsx           #     설정
│   │       ├── billing/
│   │       │   └── page.tsx           #     결제 (준비 중)
│   │       └── ops/                   #     관리자 콘솔 (superuser only)
│   │           ├── page.tsx           #       관리자 대시보드
│   │           ├── users/
│   │           │   └── page.tsx       #       사용자 관리
│   │           ├── audit-logs/
│   │           │   └── page.tsx       #       감사 로그
│   │           ├── announcements/
│   │           │   └── page.tsx       #       공지사항 관리
│   │           ├── actionkit/
│   │           │   └── page.tsx       #       액션킷 관리
│   │           ├── growth-club/
│   │           │   └── page.tsx       #       게시글 관리
│   │           ├── files/
│   │           │   └── page.tsx       #       파일 관리
│   │           ├── reports/
│   │           │   └── page.tsx       #       운영 리포트
│   │           └── roadmap-templates/
│   │               ├── page.tsx       #       템플릿 목록
│   │               └── [templateId]/
│   │                   └── page.tsx   #       템플릿 상세 (동적 라우트)
│   │
│   ├── features/                      # Feature 모듈 (11개)
│   │   │
│   │   ├── auth/                      #   인증 feature
│   │   │   ├── index.ts               #     Public API (barrel export)
│   │   │   ├── components/
│   │   │   │   ├── LoginForm.tsx      #       이메일 + Google OAuth 로그인 폼
│   │   │   │   ├── SocialAuthModal.tsx #      소셜 로그인 연동 모달
│   │   │   │   └── SuspensionModal.tsx #     계정 정지 안내 모달
│   │   │   ├── hooks/
│   │   │   │   └── useAuth.ts         #       인증 상태 관리 (로그인/로그아웃/토큰)
│   │   │   └── __tests__/
│   │   │       ├── LoginForm.test.tsx
│   │   │       └── SocialAuthModal.test.tsx
│   │   │
│   │   ├── dashboard/                 #   대시보드 feature
│   │   │   ├── index.ts
│   │   │   ├── components/
│   │   │   │   ├── DashboardView.tsx  #       대시보드 메인 뷰 (통계 카드)
│   │   │   │   ├── Header.tsx         #       상단 헤더 (z-30)
│   │   │   │   ├── Sidebar.tsx        #       사이드바 내비게이션
│   │   │   │   ├── MobileNav.tsx      #       모바일 내비게이션 (z-40)
│   │   │   │   ├── AuthGuard.tsx      #       인증 가드 (미로그인 → 로그인 페이지)
│   │   │   │   ├── AccountMenu.tsx    #       계정 드롭다운 메뉴
│   │   │   │   ├── ProgressCard.tsx   #       로드맵 진행률 카드
│   │   │   │   ├── RoadmapStepper.tsx #       로드맵 단계 표시
│   │   │   │   ├── GrowthClubCard.tsx #       그로스클럽 요약 카드
│   │   │   │   ├── ColdStartHero.tsx  #       첫 방문 안내 히어로
│   │   │   │   └── index.ts
│   │   │   ├── config/
│   │   │   │   └── nav-config.ts      #       내비게이션 메뉴 구성
│   │   │   ├── hooks/
│   │   │   │   ├── useDashboard.ts    #       대시보드 데이터 fetching
│   │   │   │   └── index.ts
│   │   │   ├── providers/
│   │   │   │   └── AuthModalProvider.tsx  #   인증 모달 컨텍스트
│   │   │   └── __tests__/
│   │   │       └── Dashboard.test.tsx
│   │   │
│   │   ├── roadmap/                   #   로드맵 feature (핵심 UI)
│   │   │   ├── index.ts
│   │   │   ├── components/
│   │   │   │   ├── RoadmapExecutionView.tsx  #  로드맵 실행 뷰 (메인)
│   │   │   │   ├── RoadmapGenerationPanel.tsx # 로드맵 생성 패널
│   │   │   │   ├── RoadmapGeneratingState.tsx # 생성 중 상태 표시
│   │   │   │   ├── RoadmapChatIntake.tsx     #  채팅 기반 입력 수집
│   │   │   │   ├── RoadmapEmptyHero.tsx      #  로드맵 없음 히어로
│   │   │   │   ├── RoadmapHeader.tsx         #  로드맵 헤더
│   │   │   │   ├── RoadmapSidebar.tsx        #  로드맵 사이드바
│   │   │   │   ├── RoadmapSwitcher.tsx       #  로드맵 전환기
│   │   │   │   ├── RoadmapRenameDialog.tsx   #  이름 변경 다이얼로그
│   │   │   │   ├── RoadmapDeleteDialog.tsx   #  삭제 확인 다이얼로그
│   │   │   │   ├── TimelinePhaseCard.tsx     #  타임라인 단계 카드
│   │   │   │   ├── TimelineStepItem.tsx      #  타임라인 스텝 항목
│   │   │   │   ├── ReadinessTracker.tsx      #  준비도 추적기
│   │   │   │   ├── MilestoneCelebration.tsx  #  마일스톤 축하 (confetti)
│   │   │   │   ├── roadmap-utils.ts          #  유틸리티 함수
│   │   │   │   ├── roadmap-constants.ts      #  상수 정의
│   │   │   │   └── index.ts
│   │   │   ├── types/
│   │   │   │   ├── index.ts
│   │   │   │   └── roadmap.ts         #       로드맵 타입 정의
│   │   │   ├── hooks/
│   │   │   │   ├── useRoadmapList.ts  #       로드맵 목록 관리
│   │   │   │   ├── useActiveRoadmap.ts #      활성 로드맵 상태
│   │   │   │   ├── useRoadmapJob.ts   #       비동기 Job 폴링
│   │   │   │   └── index.ts
│   │   │   ├── api/
│   │   │   │   └── index.ts           #       로드맵 API 호출
│   │   │   └── __tests__/
│   │   │       ├── roadmap-utils.test.ts
│   │   │       ├── ReadinessTracker.test.tsx
│   │   │       ├── RoadmapSwitcher.test.tsx
│   │   │       ├── useActiveRoadmap.test.ts
│   │   │       ├── useRoadmapList.test.ts
│   │   │       └── useRoadmapJob.test.ts
│   │   │
│   │   ├── chat/                      #   AI 채팅 feature (플로팅 위젯)
│   │   │   ├── index.ts
│   │   │   ├── components/
│   │   │   │   ├── ChatFAB.tsx        #       플로팅 액션 버튼 (z-50)
│   │   │   │   ├── ChatPanel.tsx      #       채팅 패널 (z-50)
│   │   │   │   ├── ChatWidget.tsx     #       채팅 위젯 컨테이너
│   │   │   │   ├── ChatInput.tsx      #       메시지 입력
│   │   │   │   ├── ChatMessages.tsx   #       메시지 목록
│   │   │   │   ├── ChatMessage.tsx    #       개별 메시지 (마크다운 렌더링)
│   │   │   │   ├── ChatHistory.tsx    #       채팅 히스토리
│   │   │   │   ├── ChatEmptyState.tsx #       빈 상태 안내
│   │   │   │   ├── ChatWarningBadge.tsx #     경고 배지
│   │   │   │   └── SourcesCard.tsx    #       RAG 출처 카드
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   ├── providers/
│   │   │   │   └── ChatProvider.tsx   #       채팅 상태 컨텍스트
│   │   │   ├── utils/
│   │   │   │   ├── api.ts             #       채팅 API 호출
│   │   │   │   ├── sse.ts             #       SSE 스트리밍 유틸
│   │   │   │   └── citations.tsx      #       인용 처리
│   │   │   ├── hooks/
│   │   │   │   ├── useChat.ts         #       채팅 상태/메시지 관리
│   │   │   │   └── useSessions.ts     #       세션 관리
│   │   │   └── __tests__/
│   │   │       ├── ChatInput.test.tsx
│   │   │       ├── useChat.test.ts
│   │   │       ├── useSessions.test.ts
│   │   │       ├── sse.test.ts
│   │   │       └── chat-api.test.ts
│   │   │
│   │   ├── actionkit/                 #   액션킷 feature
│   │   │   ├── index.ts
│   │   │   ├── components/
│   │   │   │   ├── ActionKitContainer.tsx    #  탭 컨테이너 (법령 가이드 / 키트)
│   │   │   │   ├── LawGuideView.tsx          #  창업 법령 가이드 뷰
│   │   │   │   ├── LawDetailPopup.tsx        #  법령 상세 팝업
│   │   │   │   ├── ActionKitLibraryView.tsx  #  액션 키트 라이브러리 뷰
│   │   │   │   ├── ActionKitDetailModal.tsx  #  아이템 상세 모달
│   │   │   │   └── index.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   ├── hooks/
│   │   │   │   ├── useActionKit.ts    #       액션킷 데이터 관리
│   │   │   │   ├── useLawGuide.ts     #       법령 가이드 데이터
│   │   │   │   └── index.ts
│   │   │   ├── api/
│   │   │   │   └── index.ts
│   │   │   └── __tests__/
│   │   │       └── useActionKit.test.ts
│   │   │
│   │   ├── growth-club/               #   그로스클럽(커뮤니티) feature
│   │   │   ├── index.ts
│   │   │   ├── components/
│   │   │   │   ├── PostCard.tsx       #       게시글 카드
│   │   │   │   ├── CreatePostForm.tsx #       게시글 작성 폼
│   │   │   │   ├── CommentSection.tsx #       댓글 섹션
│   │   │   │   └── index.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   ├── utils/
│   │   │   │   └── upload-url.ts      #       이미지 업로드 URL 생성
│   │   │   ├── hooks/
│   │   │   │   ├── usePosts.ts        #       게시글 목록/CRUD
│   │   │   │   ├── useTimeAgo.ts      #       상대 시간 표시
│   │   │   │   └── index.ts
│   │   │   ├── api/
│   │   │   │   ├── growth-club.ts     #       API 호출
│   │   │   │   └── index.ts
│   │   │   └── __tests__/
│   │   │       ├── PostCard.test.tsx
│   │   │       ├── CreatePostForm.test.tsx
│   │   │       ├── usePosts.test.ts
│   │   │       └── growth-club-api.test.ts
│   │   │
│   │   ├── notifications/            #   알림 feature
│   │   │   ├── index.ts
│   │   │   ├── components/
│   │   │   │   └── NotificationBell.tsx  #    알림 벨 아이콘 + 드롭다운
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   ├── hooks/
│   │   │   │   ├── useNotifications.ts    #   알림 목록/읽음 처리
│   │   │   │   └── useNotificationSSE.ts  #   실시간 알림 (SSE)
│   │   │   ├── api/
│   │   │   │   └── index.ts
│   │   │   └── __tests__/
│   │   │       ├── NotificationBell.test.tsx
│   │   │       ├── useNotifications.test.ts
│   │   │       └── notifications-api.test.ts
│   │   │
│   │   ├── announcements/            #   공지사항 feature
│   │   │   ├── index.ts
│   │   │   ├── api.ts                 #     공지사항 API 호출
│   │   │   └── components/
│   │   │       └── AnnouncementDetailView.tsx  # 공지 상세 뷰
│   │   │
│   │   ├── profile/                   #   프로필 feature
│   │   │   ├── index.ts
│   │   │   ├── components/
│   │   │   │   └── index.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts
│   │   │   ├── hooks/
│   │   │   │   └── index.ts
│   │   │   └── api/
│   │   │       └── index.ts
│   │   │
│   │   ├── ops/                       #   관리자 콘솔 feature (9개 서브 모듈)
│   │   │   ├── index.ts
│   │   │   ├── types/
│   │   │   │   └── index.ts           #     공통 관리자 타입
│   │   │   ├── components/
│   │   │   │   └── index.ts
│   │   │   ├── hooks/
│   │   │   │   └── index.ts
│   │   │   ├── api/
│   │   │   │   └── index.ts           #     공통 관리자 API
│   │   │   ├── shared/                #     공유 컴포넌트
│   │   │   │   ├── confirm-dialog.tsx        #  확인 다이얼로그
│   │   │   │   ├── ops-access-placeholder.tsx # 접근 권한 없음 플레이스홀더
│   │   │   │   └── use-ops-access-guard.ts   # 관리자 접근 가드 훅
│   │   │   ├── home/                  #     관리자 대시보드
│   │   │   │   ├── view.tsx
│   │   │   │   └── index.ts
│   │   │   ├── users/                 #     사용자 관리
│   │   │   │   ├── view.tsx           #       사용자 목록/관리 뷰
│   │   │   │   ├── api.ts
│   │   │   │   ├── types.ts
│   │   │   │   ├── index.ts
│   │   │   │   └── _components/
│   │   │   │       ├── DisciplineModal.tsx       # 징계 모달
│   │   │   │       └── DisciplinaryHistoryList.tsx # 징계 이력
│   │   │   ├── audit-logs/            #     감사 로그
│   │   │   │   ├── view.tsx
│   │   │   │   ├── api.ts
│   │   │   │   ├── types.ts
│   │   │   │   └── index.ts
│   │   │   ├── announcements/         #     공지사항 관리
│   │   │   │   ├── view.tsx
│   │   │   │   ├── api.ts
│   │   │   │   ├── types.ts
│   │   │   │   ├── index.ts
│   │   │   │   └── _components/
│   │   │   │       └── AnnouncementModal.tsx
│   │   │   ├── actionkit/             #     액션킷 관리
│   │   │   │   ├── view.tsx
│   │   │   │   ├── api.ts
│   │   │   │   ├── index.ts
│   │   │   │   └── components/
│   │   │   │       ├── actionkit-edit-modal.tsx
│   │   │   │       ├── category-edit-modal.tsx
│   │   │   │       └── stats-dashboard.tsx
│   │   │   ├── growth-club/           #     게시글 관리
│   │   │   │   ├── view.tsx
│   │   │   │   ├── api.ts
│   │   │   │   └── index.ts
│   │   │   ├── files/                 #     파일 관리
│   │   │   │   ├── view.tsx
│   │   │   │   ├── api.ts
│   │   │   │   ├── types.ts
│   │   │   │   └── index.ts
│   │   │   ├── reports/               #     운영 리포트
│   │   │   │   ├── view.tsx
│   │   │   │   ├── api.ts
│   │   │   │   ├── types.ts
│   │   │   │   └── index.ts
│   │   │   └── roadmap-templates/     #     로드맵 템플릿 관리
│   │   │       ├── view.tsx           #       템플릿 목록 뷰
│   │   │       ├── template-detail-view.tsx  # 템플릿 상세 뷰
│   │   │       ├── api.ts
│   │   │       ├── types.ts
│   │   │       ├── index.ts
│   │   │       └── components/
│   │   │           ├── template-list-table.tsx
│   │   │           ├── template-step-editor.tsx
│   │   │           ├── template-action-editor.tsx
│   │   │           ├── template-status-badge.tsx
│   │   │           ├── status-change-dialog.tsx
│   │   │           └── create-from-roadmap-dialog.tsx
│   │   │
│   │   └── shared/                    #   공유 모듈
│   │       ├── contracts/
│   │       │   └── index.ts           #     크로스 feature 공유 타입/인터페이스
│   │       ├── file/                  #     파일 유틸리티
│   │       │   ├── index.ts
│   │       │   ├── utils/
│   │       │   │   ├── validation.ts  #       파일 유효성 검증
│   │       │   │   └── url.ts         #       파일 URL 생성
│   │       │   └── hooks/
│   │       │       ├── useFileUpload.ts  #    파일 업로드 훅
│   │       │       └── useFileDownload.ts #   파일 다운로드 훅
│   │       └── __tests__/
│   │           └── file-utils.test.ts
│   │
│   ├── providers/                     # 글로벌 Provider
│   │   └── AuthProvider.tsx           #   인증 상태 관리 (useSyncExternalStore, 탭 간 동기화)
│   │
│   ├── components/                    # 공유 UI 컴포넌트 (shadcn/ui)
│   │   └── ui/                        #   Radix UI 기반 커스텀 컴포넌트
│   │       ├── button.tsx             #     버튼 (CVA variants)
│   │       ├── dialog.tsx             #     다이얼로그 (Radix Dialog)
│   │       ├── dropdown-menu.tsx      #     드롭다운 메뉴 (Radix DropdownMenu)
│   │       ├── card.tsx               #     카드 레이아웃
│   │       ├── input.tsx              #     텍스트 입력
│   │       ├── textarea.tsx           #     텍스트에어리어
│   │       ├── label.tsx              #     라벨 (Radix Label)
│   │       ├── badge.tsx              #     배지
│   │       ├── table.tsx              #     테이블
│   │       ├── avatar.tsx             #     아바타 (Radix Avatar)
│   │       ├── checkbox.tsx           #     체크박스
│   │       ├── switch.tsx             #     스위치 토글 (Radix Switch)
│   │       ├── separator.tsx          #     구분선 (Radix Separator)
│   │       ├── popover.tsx            #     팝오버 (Radix Popover)
│   │       ├── progress.tsx           #     프로그레스 바 (Radix Progress)
│   │       ├── sonner.tsx             #     토스트 알림 (Sonner)
│   │       └── Disclaimer.tsx         #     면책 조항 컴포넌트
│   │
│   ├── lib/                           # 유틸리티 라이브러리
│   │   ├── api-client.ts              #   Axios 인스턴스 (인터셉터, 토큰 갱신)
│   │   ├── api-types.ts               #   자동 생성 타입 (OpenAPI → TS, 수동 편집 금지)
│   │   ├── env.ts                     #   환경변수 타입 안전 접근
│   │   ├── utils.ts                   #   cn() 등 범용 유틸
│   │   ├── format.ts                  #   날짜/숫자 포맷팅
│   │   └── sse-auth.ts               #   SSE 인증 헤더 유틸
│   │
│   └── app.css                        # Tailwind CSS + 글로벌 스타일
│
├── public/                            # 정적 파일
├── scripts/
│   └── generate_api_types.mjs         #   OpenAPI → TypeScript 타입 생성 스크립트
│
├── package.json                       # 의존성 + 스크립트
├── pnpm-lock.yaml                     # pnpm 잠금 파일
├── tsconfig.json                      # TypeScript 설정 (strict, 경로 별칭)
├── next.config.mjs                    # Next.js 설정 (standalone, turbopack)
├── tailwind.config.ts                 # Tailwind CSS 설정 (Pretendard, HSL 변수)
├── eslint.config.mjs                  # ESLint 설정 (Next.js Core Web Vitals)
├── postcss.config.js                  # PostCSS 설정 (Tailwind + Autoprefixer)
├── jest.config.js                     # Jest 설정 (jsdom, @/ 경로 매핑)
├── jest.setup.js                      # Jest 초기화 (testing-library/jest-dom)
├── components.json                    # shadcn/ui 설정
├── Dockerfile                         # 개발용 Docker 이미지
├── Dockerfile.prod                    # 프로덕션 Docker 이미지
├── .npmrc                             # npm 설정
├── .env                               # 기본 환경변수
├── .env.local                         # 로컬 오버라이드 (Git 제외)
└── .env.docker.local                  # Docker Compose 오버라이드
```

### 4.2 Feature 모듈 규칙

각 Feature 모듈은 아래 구조를 따르며, `index.ts`를 통해서만 외부에 export한다.

```
features/{name}/
├── index.ts              # Barrel export (Public API)
├── components/           # React 컴포넌트
│   └── index.ts
├── hooks/                # 커스텀 훅
│   └── index.ts
├── types/                # TypeScript 타입 정의
│   └── index.ts
├── api/                  # API 호출 함수
│   └── index.ts
├── utils/                # 유틸리티 (선택)
├── providers/            # Context Provider (선택)
└── __tests__/            # 테스트
```

**규칙:**
- 크로스 feature 내부 경로 import 금지 (예: `import from '@/features/auth/components/LoginForm'` 불가)
- `@feature/*` 별칭을 통한 feature 간 참조만 허용
- 공유 타입은 `features/shared/contracts/index.ts`에 정의

### 4.3 경로 별칭 (tsconfig.json)

```
@/*                 → ./src/*
@feature/profile    → ./src/features/profile
@feature/actionkit  → ./src/features/actionkit
@feature/community  → ./src/features/growth-club
@feature/ops        → ./src/features/ops
@feature/dashboard  → ./src/features/dashboard
@feature/roadmap    → ./src/features/roadmap
@feature/contracts  → ./src/features/shared/contracts
```

### 4.4 주요 의존성

#### 프로덕션 의존성

| 카테고리 | 라이브러리 | 버전 | 용도 |
|---------|-----------|------|------|
| **프레임워크** | Next.js | ^16.1.6 | React 프레임워크 (App Router) |
| | React | ^18 | UI 라이브러리 |
| **UI 기반** | @radix-ui/react-dialog | ^1.1.15 | 접근성 기반 다이얼로그 |
| | @radix-ui/react-dropdown-menu | ^2.1.16 | 드롭다운 메뉴 |
| | @radix-ui/react-avatar | ^1.1.11 | 아바타 |
| | @radix-ui/react-popover | ^1.1.15 | 팝오버 |
| | @radix-ui/react-progress | ^1.1.8 | 프로그레스 바 |
| | @radix-ui/react-label | ^2.1.8 | 라벨 |
| | @radix-ui/react-separator | ^1.1.8 | 구분선 |
| | @radix-ui/react-switch | ^1.2.6 | 스위치 토글 |
| | @radix-ui/react-slot | ^1.2.4 | Slot 패턴 |
| **스타일링** | class-variance-authority | ^0.7.1 | 컴포넌트 변형 관리 |
| | clsx | ^2.1.1 | 조건부 클래스명 결합 |
| | tailwind-merge | ^2.6.1 | Tailwind 클래스 충돌 해결 |
| | tailwindcss-animate | ^1.0.7 | 애니메이션 유틸리티 |
| **아이콘** | lucide-react | ^0.300.0 | 아이콘 라이브러리 |
| **HTTP** | axios | ^1.13.5 | HTTP 클라이언트 (인터셉터 기반) |
| **인증** | @react-oauth/google | ^0.13.4 | Google OAuth |
| **DnD** | @hello-pangea/dnd | ^18.0.1 | Drag & Drop (로드맵 단계 재정렬) |
| **파일** | react-dropzone | ^15.0.0 | 파일 업로드 드롭존 |
| | jszip | ^3.10.1 | ZIP 파일 생성 (다건 다운로드) |
| | file-saver | ^2.0.5 | 클라이언트 파일 다운로드 |
| **UX** | sonner | ^2.0.7 | 토스트 알림 |
| | canvas-confetti | ^1.9.4 | 축하 애니메이션 (마일스톤) |

#### 개발 의존성

| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| TypeScript | ^5 | 타입 안전성 (strict mode) |
| ESLint | ^9 | 린팅 (eslint-config-next) |
| Jest | ^30.2.0 | 단위 테스트 |
| @testing-library/react | ^16.3.2 | 컴포넌트 테스트 |
| @testing-library/jest-dom | ^6.9.1 | DOM 매처 확장 |
| Tailwind CSS | ^3.3.0 | 유틸리티 CSS |
| PostCSS | ^8 | CSS 처리 |
| Autoprefixer | ^10.0.1 | Vendor 프리픽스 |
| ts-node | ^10.9.2 | TypeScript 실행 |

### 4.5 Docker 이미지

| 환경 | Dockerfile | 베이스 이미지 | 특징 |
|------|-----------|-------------|------|
| 개발 | `Dockerfile` | node:24-alpine | Corepack + pnpm, hot reload |
| 프로덕션 | `Dockerfile.prod` | node:24-alpine | `pnpm build && pnpm start` |

Next.js `output: 'standalone'` 모드로 의존성 경량화.

### 4.6 z-index 계층 구조

```
z-30  Header (상단 헤더)
z-40  MobileNav (모바일 내비게이션)
z-50  ChatFAB + ChatPanel (플로팅 채팅)
```

---

## 5. Docker Compose 설정

### 5.1 개발 환경 (docker-compose.dev.yml)

5개 서비스로 구성된 로컬 개발 환경.

| 서비스 | 이미지 | 포트 | 역할 |
|--------|--------|------|------|
| `app-db` | pgvector/pgvector:pg16 | 5432 | PostgreSQL + pgvector 확장 |
| `app-redis` | redis:alpine | 6379 | 캐시 + 작업 큐 |
| `app-backend` | ./app-backend (Dockerfile) | 8000 | FastAPI API 서버 (--reload) |
| `app-worker` | ./app-backend (Dockerfile) | - | ARQ 비동기 워커 |
| `app-frontend` | ./app-frontend (Dockerfile) | 3000 | Next.js 개발 서버 |

**개발 환경 특징:**
- Backend/Frontend에 볼륨 마운트 (소스 코드 실시간 반영)
- `.venv`와 `node_modules`는 볼륨 마운트에서 제외
- `--reload` 플래그로 코드 변경 시 자동 재시작
- `init_db.sh` 스크립트로 pgvector 확장 자동 활성화
- `nginx-proxy` 외부 네트워크 사용

**환경 파일 우선순위:**
```
.env (기본값) → .env.local (로컬 오버라이드) → .env.docker.local (Docker 오버라이드)
```

**서비스 의존성:**
```
app-frontend → app-backend → app-db (healthy)
                           → app-redis (healthy)
app-worker                 → app-db (healthy)
                           → app-redis (healthy)
```

### 5.2 프로덕션 환경 (docker-compose.prod.yml)

| 차이점 | 개발 | 프로덕션 |
|--------|------|---------|
| Dockerfile | Dockerfile | Dockerfile.prod |
| 재시작 | - | `restart: unless-stopped` |
| 핫 리로드 | `--reload` | 없음 |
| 볼륨 마운트 | 소스 코드 마운트 | 없음 |
| Healthcheck | interval=5s, retries=5 | interval=10s, retries=10 |
| 포트 노출 | Backend 8000, Frontend 3000 | Backend만 (Frontend는 nginx 경유) |

---

## 6. 환경 변수 가이드

### Backend 필수 환경변수

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/dbname

# Security
SECRET_KEY=<64자 이상 랜덤 문자열>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://redis:6379/0
```

### Backend 선택 환경변수

```bash
# AI/LLM
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small

# OAuth
GOOGLE_CLIENT_ID=...

# 외부 API
LAW_API_OC=...                      # 국가법령정보센터 API

# 스토리지
STORAGE_BACKEND=local                # "local" 또는 "r2"
STORAGE_LOCAL_ROOT=/app/uploads

# 관찰성
SENTRY_DSN=...                       # GlitchTip 호환

# Feature Flags
ENABLE_SOCIAL_MOCK=true              # 테스트 환경 전용 (프로덕션 false)
```

### Frontend 환경변수

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_GOOGLE_CLIENT_ID=...
NEXT_PUBLIC_STORAGE_URL=...          # R2 Public URL
```

---

## 7. 테스트 전략

### Backend (Pytest)

| 카테고리 | 디렉토리 | 테스트 수 | 실행 방식 |
|---------|---------|----------|----------|
| API 엔드포인트 | `tests/api/` | 20개 | `make test` (기본) |
| 서비스 단위 | `tests/services/` | 10개 | `make test` (기본) |
| Repository | `tests/repositories/` | 2개 | `make test` (기본) |
| 통합 | `tests/integration/` | 1개 | `make test` (기본) |
| RAG 평가 | `tests/eval/` | 2개 | `make test-eval` (별도, 비용 발생) |

- 테스트 DB: SQLite (`sqlite+aiosqlite`)
- 비동기 모드: `asyncio_mode = "auto"`
- 마커: `requires_openai`, `eval`, `slow`, `full_eval`
- pre-push 훅: `tests/services`, `tests/repositories`, `tests/integration`만 실행

### Frontend (Jest)

| 카테고리 | 위치 | 실행 |
|---------|------|------|
| 컴포넌트 | `features/{name}/__tests__/` | `pnpm test` |
| 유틸리티 | `features/shared/__tests__/` | `pnpm test` |

- 테스트 환경: `jest-environment-jsdom`
- 라이브러리: `@testing-library/react`

---

## 8. 버전 요약

| 항목 | 버전 |
|------|------|
| Python | 3.13 |
| Node.js | 24-alpine |
| uv | 0.10 |
| pnpm | 10.30.3 |
| FastAPI | >=0.135.0 |
| Next.js | ^16.1.6 |
| React | ^18 |
| TypeScript | ^5 |
| PostgreSQL | 16 (pgvector) |
| Redis | alpine |
| SQLAlchemy | >=2.0.48 |
| SQLModel | >=0.0.37 |
| Alembic | >=1.13.2 |
| LangChain | >=0.1.0 |
| Tailwind CSS | ^3.3.0 |
| Radix UI | ^1.x |
| Jest | ^30.2.0 |
| Pytest | >=8.0.0 |
