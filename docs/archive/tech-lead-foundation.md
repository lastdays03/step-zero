# Tech Lead Foundation (사전 작업 계획)

> **Last Verified: 2026-03-04 — 역사적 문서 (정확도 ~70%)**
>
> 이 문서는 Day 0~3 사전 작업 계획으로, 초기 의사결정 기록으로서 가치 유지.
> **실제 구현과 차이**:
> - 벡터 DB: ChromaDB 제안 → 실제 **PGVector** 사용
> - RAG 추상화: BaseRAGChain 제안 → 실제는 서비스 기반(RagService, SemanticRouter, ChatService)
> - Roadmap 렌더러: SVG/Canvas 제안 → 실제 **Recharts + React 컴포넌트**
> - Phase 4 AI 코치, Ops 관리 콘솔 등 후속 기능 미반영
> - Alembic 마이그레이션 전략 미문서화 (현재 013까지 진행)

## 1. 개요
**목표:** 4명의 주니어 개발자가 기술적 시행착오 없이 비즈니스 로직 개발에만 집중할 수 있도록, **Core Architecture**와 **Standard Pattern**을 미리 구축하는 것.
**기간:** Day 0 ~ Day 3 (개발 착수 전 선행 작업)
**담당:** Tech Lead (Senior)

---

## 2. 작업 상세 내용

### 2.1. Project Scaffolding (개발 환경 표준화)
주니어들이 각자 다른 스타일로 개발하는 것을 방지하기 위한 강제적 환경 설정.

- **Repository Strategy:** Monorepo (Turborepo) 또는 Polyrepo (Frontend/Backend 분리) 확정 및 초기화.
    - `apps/web`: Next.js (App Router)
    - `apps/api`: FastAPI (Python)
    - `packages/shared`: 공통 타입(TypeScript Interface), 상수, 유틸리티.
- **Lint & Format:**
    - **Frontend:** ESLint (Airbnb or Next.js Core), Prettier, Husky (pre-commit hook).
    - **Backend:** Black, Isort, Flake8, MyPy (Type Checking).
    - **Rule:** "Warning 없이 Error만 존재하도록" 설정 (Strict Mode).
- **Docker Compose:**
    - `docker-compose.dev.yml` 작성: DB(PostgreSQL), Redis, ChromaDB(Vector), API, Web을 명령어 하나로 실행 가능하게 함.
    - 데이터 시딩(Seeding) 스크립트 포함 (초기 더미 데이터).

### 2.2. Vertical Slice (기준 코드 구현)
"이 기능 어떻게 짜요?"라는 질문에 대한 **살아있는 예제 코드(Reference)** 제공.
가장 기본이 되는 **[회원가입 -> 로그인 -> 메인 대시보드 진입]** 흐름을 완벽하게 구현.

- **Authentication (Auth) with Hidden Multi-Tenancy:**
    - **Backend:** 
        - **Self-Hosted JWT Auth:** `FastAPI-Users` 또는 직접 구현 (`OAuth2PasswordBearer`, `Passlib`, `PyJWT`).
        - **User Model:** DB에 `password_hash` 저장 및 검증 로직 구현.
        - **Auto-Team Creation:** 회원가입 시 Service Layer에서 `1 User = 1 Default Team` 생성 트랜잭션 보장.
    - **Frontend:** 
        - `NextAuth.js (Auth.js)` 또는 커스텀 `AuthContext` 구현.
        - 로그인/회원가입 폼 직접 구현 (Shadcn UI).
- **API Communication:**
    - `fetch` 래퍼(Wrapper) 구현: 토큰 자동 주입, 에러 핸들링, 타임아웃 처리.
    - React Query (TanStack Query) 설정: `QueryClient` 전역 설정, 캐싱 전략.
- **Project Structure:**
    - **FE:** `components/ui`(Shadcn), `features/auth`, `app/(dashboard)/page.tsx` 등 폴더 구조 확립.
    - **BE:** `app/api/v1/auth.py`, `app/services/user_service.py`, `app/core/config.py` 등 계층 구조 확립.

### 2.3. Core Engine (난이도 최상위 모듈)
주니어 개발자가 구현하기 어렵거나 리스크가 큰 핵심 기능을 미리 개발하여 라이브러리처럼 제공.

- **Roadmap Renderer (FE):**
    - SVG/Canvas 기반의 인터랙티브 로드맵 컴포넌트 (`<RoadmapView />`).
    - 데이터(`nodes`, `edges`)만 넣으면 자동으로 그려주는 엔진 구현.
    - 줌 인/아웃, 드래그 앤 드롭, 노드 클릭 이벤트 캡슐화.
- **RAG Pipeline Base (BE):**
    - LangChain 기반의 `BaseRAGChain` 클래스 구현.
    - 벡터 DB 연결, 임베딩 모델(OpenAI) 호출, 프롬프트 템플릿 관리 기능을 추상화.
    - 주니어는 `class LegalAdviceChain(BaseRAGChain):` 형태로 상속받아 프롬프트만 수정하면 되도록 구성.

### 2.4. Type & API Contract (타입 정의)
프론트엔드와 백엔드 간의 오해를 없애기 위한 약속.

- **Shared Types:**
    - `User`, `Team`, `Roadmap`, `Step`, `ActionKit` 등 핵심 도메인 모델의 TypeScript Interface 정의.
    - Pydantic 모델(Python)과 Sync 맞추기 (가능하면 코드 제너레이터 사용 고려).
- **API Specification (Draft):**
    - 핵심 API(약 10개)에 대한 URL, Method, Request/Response Body 명세.
    - Swagger UI 자동 생성 설정 확인.

---

## 3. 주니어 개발자(Squad)에게 전달할 가이드
Tech Lead 작업 완료 후 배포될 문서.

1.  **Onboarding Guide:** `README.md`에 "설치부터 실행까지" 명령어 3줄로 끝내기.
2.  **Contribution Guide:** 브랜치 전략(Git Flow), 커밋 메시지 규칙, PR 템플릿.
3.  **Coding Convention:** 컴포넌트 네이밍, 변수명 규칙, 에러 처리 방식.
