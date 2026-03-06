
# Implementation Plan: Tech Lead Foundation

**Objective:**
StepZero MVP 개발을 위해 시니어 엔지니어(Tech Lead)가 4명의 주니어 개발자(Squad)에게 제공해야 할 **"Core Architecture"**와 **"Golden Path"**를 선행 구축합니다.
주니어 개발자들이 온전히 비즈니스 로직(CRUD)에 집중할 수 있도록 기술적 난이도가 높은 부분(RAG, Roadmap Engine)을 해결하고, 개발 환경(Monorepo, Lint)을 표준화합니다.

**Owner:** Tech Lead
**Timeline:** Day 0 ~ Day 3 (Pre-Kickoff)

---

## Technical Context
- **Stack:** Next.js 16 (FE), FastAPI 0.109+ (BE), PostgreSQL 16 + pgvector (DB)
- **Repo:** Monorepo (Simplified Folders: `app-frontend`, `app-backend`)
- **Deployment:** Docker Compose (All-in-One Monolith)
- **Architecture:** Clean Architecture (Layered: Router -> Service -> Repository -> Model)
- **Methodology:** TDD (Test-Driven Development) Mandatory for Business Logic

---

## User Review Required
> [!IMPORTANT]
> **Monorepo Structure Decision:** 
> `apps/web` + `apps/api` 구조 대신 **단순 폴더 분리(`app-frontend/`, `app-backend/`)**를 사용하여 Turborepo 설정 복잡도를 줄일 예정입니다.
> - **Shared Types:** `app-shared/types.ts` 생성 후, 각 앱의 `src/types`에 복사-동기화하는 방식을 권장합니다.
> - **Docker Context:** 루트 `docker-compose.yml`에서 각 폴더를 빌드 컨텍스트로 잡습니다.

---

## 📅 Phase 1: Project Scaffolding (Day 0-1)
> **Goal:** " Clone 받고 `docker compose -f docker-compose.dev.yml up -d --build` 하면 끝"인 상태 만들기.

### [Core Setup]
#### [NEW] `docker-compose.dev.yml`
- [ ] PostgreSQL + pgvector 이미지 설정 (Port: 5432)
- [ ] Redis (Port: 6379, Caching & Queue)
- [ ] Backend (FastAPI, Port: 8000, Volume Mount for Hot Reload)
- [ ] Frontend (Next.js, Port: 3000, Volume Mount)
- [ ] `scripts/init_db.sh` 작성 (초기 테이블 및 관리자 계정 생성)

#### [NEW] Backend Boilerplate (`app-backend/`)
- [ ] FastAPI 기본 설정 (`main.py`, `lifespan` handler)
- [ ] DB 연결 (`sqlmodel` or `sqlalchemy`, `app/core/db.py`)
- [ ] Config 관리 (`pydantic-settings`, `.env` 로딩)
- [ ] Lint/Format 설정 (`pyproject.toml`: Black, Isort, Flake8, MyPy)
- [ ] **Clean Architecture Setup:**
    - `app/api/v1` (Controller): 요청/응답 처리.
    - `app/services` (UseCase): 비즈니스 로직.
    - `app/repositories` (Data Access): DB 쿼리 분리.
- [ ] **TDD Environment:**
    - `tests/conftest.py`: DB Session fixture, AsyncClient fixture 설정.
    - `tests/factories.py`: Polyfactory 기반 테스트 데이터 생성기.
- [ ] **DB Audit Base:**
    - `TimestampMixin` (`created_at`, `updated_at`) 구현.
    - `SoftDeleteMixin` (`deleted_at` 처리 로직) 구현.
    - `AuditLog` 모델 및 트랜잭션 훅 검토.

#### [NEW] Frontend Boilerplate (`app-frontend/`)
- [ ] **Feature-Based Architecture:**
    - `features/auth`, `features/roadmap`, `features/dashboard` 폴더 구조 확립.
    - 각 Feature 내 `components`, `hooks`, `api`, `types` 분리.
- [ ] **TDD Environment:**
    - Jest + React Testing Library 설정.
    - `msw` (Mock Service Worker) API 모킹 설정.
- [ ] Next.js 16 App Router 초기화 (`npx create-next-app`)
- [ ] TailwindCSS v3 + Shadcn UI 초기 설정
- [ ] ESLint, Prettier, Husky (pre-commit) 설정
- [ ] API Fetch Wrapper (`lib/api-client.ts` - 토큰 자동 주입, 에러 처리)

---

## 🚀 Phase 2: Core Engine Development (Day 1-2)
> **Goal:** 주니어가 구현하기 힘든 "핵심 기능 엔진"을 라이브러리(Blackbox) 형태로 제공.

### 2.1. Roadmap Renderer Engine (FE)
주니어 개발자들은 "노드 데이터"만 넣으면 로드맵이 그려지도록 만듭니다.
- [ ] **RoadmapView Component:** SVG/Canvas 기반 (React Flow 고려) 로드맵 뷰어 구현.
- [ ] **Interaction Handler:** 줌/팬(Zoom/Pan), 노드 클릭 이벤트 콜백 정의.
- [ ] **Responsive Logic:** 모바일(Bottom Sheet) / 데스크톱(Side Panel) 반응형 처리 로직.

### 2.2. RAG Pipeline Base (BE)
복잡한 LangChain 로직을 추상화하여, 주니어는 "프롬프트"만 신경 쓰도록 합니다.
- [ ] **BaseRAGChain Class:** `retriever`, `llm`, `prompt`를 조립하는 부모 클래스.
- [ ] **Vector Store Manager:** ChromaDB 연결 및 문서 임베딩(Upsert) 유틸리티.
- [ ] **Hybrid Search Util:** Keyword(BM25) + Vector(Cosine) 하이브리드 검색 구현.

---

## 🛡️ Phase 3: Vertical Slice (Day 2-3)
> **Goal:** "로그인부터 대시보드 진입까지"의 기준 코드(Guideline Code) 작성.

### 3.1. Authentication System
- [ ] **Self-Hosted Auth System:**
    - BE: `FastAPI-Users` 또는 `OAuth2PasswordBearer` 기반 JWT 발급/검증 로직 구현.
    - BE: `users` 테이블 마이그레이션 (`email`, `hashed_password`, `is_active`).
    - FE: `NextAuth` (Auth.js) Credentials Provider 연동 또는 커스텀 로그인 폼.
- [ ] **User & Team Model:** 
    - `users`: Identity Provider로 사용.
    - `teams`: 데이터 소유의 주체 (Multi-Tenancy Root).
    - `team_members`: 유저-팀 권한 매핑.
    - `audit_logs`: 중요 데이터 변경 이력 저장.
    - Alembic으로 마이그레이션 스크립트 작성.

### 3.2. Dashboard "Hello World"
- [ ] **Frontend:** 
    - `app/(dashboard)/layout.tsx` (사이드바/GNB 레이아웃 적용).
    - `DashboardCard` 컴포넌트 예제 및 `useQuery` 예제 작성.
- [ ] **Backend:** 
    - `GET /api/v1/dashboard/stats` (Dummy Data 반환) API 구현.
    - Pydantic Schema (`DashboardStatsResponse`) 정의.

---

## 📝 Phase 4: API Contract & Handover (Day 3)
> **Goal:** Frontend와 Backend가 병렬로 달릴 수 있는 약속 정의.

### 4.1. Shared Types & API Spec
- [ ] **OpenAPI (Swagger):** 핵심 API (Auth, Roadmap, ActionKit) URL 및 스키마 정의.
- [ ] **TypeScript Interfaces:** 
    - `User`, `Roadmap`, `Step`, `ActionKit` 타입 정의 (`types/schema.d.ts`).
    - Backend Pydantic 모델과 필드명 동기화.

### 4.2. Developer Guide (README.md)
- [ ] **Onboarding:** "git clone -> docker compose -f docker-compose.dev.yml up -d --build" 3단계 실행 가이드.
- [ ] **Convention:** 폴더 구조 설명, 커밋 메시지 규칙(Conventional Commits), 에러 핸들링 패턴.
- [ ] **Troubleshooting:** 자주 발생하는 예상 에러(DB 연결 실패, 포트 충돌) 및 해결법.

---

## Verification Plan (Success Criteria)

### Automated Checks
- [ ] `docker compose -f docker-compose.dev.yml up -d --build` 실행 시 모든 컨테이너(FE, BE, Worker, DB, Redis)가 `Healthy` 상태여야 함.
- [ ] Backend: `pytest` 실행 시 Auth 관련 테스트 통과 (`tests/api/test_auth.py`).
- [ ] Frontend: `npm run lint` 실행 시 에러 0개.

### Manual Checks
- [ ] `localhost:3000` 접속 시 로그인 페이지 -> 대시보드 진입이 정상 동작해야 함.
- [ ] Swagger UI (`localhost:8000/docs`)에서 API 호출 테스트 성공.
- [ ] 로드맵 뷰어 컴포넌트 (`/roadmap-demo`)가 모바일/PC에서 깨짐 없이 렌더링 되어야 함.
