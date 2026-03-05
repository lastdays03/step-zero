
# 🚀 StepZero (Core Engine)

StepZero 프로젝트의 **Core Engine(백엔드 + 기본 프론트엔드)** 레포지토리입니다.
이 문서는 프로젝트에 처음 합류한 주니어 개발자 분들을 위해 작성되었습니다.

---

## 📚 1. 프로젝트 개요

이 프로젝트는 **초기 스타트업 창업자를 위한 AI 액셀러레이팅 플랫폼**의 핵심 엔진을 담당합니다.
사용자의 입력을 받아 로드맵을 생성하고, RAG(Retrieval-Augmented Generation)를 통해 맞춤형 정보를 제공하는 것이 목표입니다.

### 🛠️ 기술 스택 (Tech Stack)

| 구분         | 기술                             | 설명                                        |
| :----------- | :------------------------------- | :------------------------------------------ |
| **Backend**  | **FastAPI** (Python 3.11)        | 고성능 비동기 웹 프레임워크. API 서버 담당. |
| **Frontend** | **Next.js 16** (App Router)      | React 기반 웹 프레임워크. UI/UX 담당.       |
| **Database** | **PostgreSQL 16** + **pgvector** | 관계형 데이터 및 벡터 임베딩 저장소.        |
| **Cache**    | **Redis**                        | 세션 관리, 작업 큐, 캐싱 용도.              |
| **Deploy**   | **Docker Compose**               | 로컬 개발 환경 통일 및 배포 관리.           |

---

## 📂 2. 프로젝트 구조 (Folder Structure)

이 프로젝트는 **Monorepo** 구조를 따릅니다. 하나의 저장소 안에 백엔드와 프론트엔드가 함께 있습니다.

```
step-zero/
├── app-backend/            # 🐍 FastAPI 백엔드 코드
│   ├── app/                # 실제 애플리케이션 로직
│   │   ├── api/            # API 라우터 (v1)
│   │   ├── features/       # feature 단위 도메인/애플리케이션 로직
│   │   ├── models/         # SQLModel/ORM 모델
│   │   ├── repositories/   # 데이터 접근 계층
│   │   ├── services/       # 공통 서비스 (RAG, Chat 등)
│   │   ├── workers/        # ARQ 비동기 워커
│   │   └── core/           # 설정(Config), DB 연결 등 핵심 로직
│   ├── alembic/            # DB 마이그레이션 (6개 통합 파일)
│   ├── scripts/            # 개발/운영 스크립트
│   ├── tests/              # 테스트 코드 (Pytest)
│   └── Dockerfile
│
├── app-frontend/           # ⚛️ Next.js 프론트엔드 코드
│   ├── src/
│   │   ├── app/            # 페이지 및 라우팅 (App Router)
│   │   ├── components/     # 재사용 가능한 UI 컴포넌트
│   │   ├── features/       # feature 단위 모듈
│   │   ├── lib/            # 유틸리티 함수
│   │   └── providers/      # React Context Providers
│   └── Dockerfile
│
├── docs/                   # 📄 기획 및 설계 문서 (필독!)
├── scripts/                # 루트 유틸리티 스크립트 (DB 초기화 등)
└── docker-compose.dev.yml  # 🐳 로컬 개발 환경 구성 파일
```

### Backend 스크립트 (`app-backend/scripts/`)

| 스크립트 | 용도 |
| :--- | :--- |
| `setup_dev.sh` | 로컬 개발환경 초기화 (uv sync + .env) |
| `run_alembic.sh` | Alembic 래퍼 (예: `./scripts/run_alembic.sh upgrade head`) |
| `reset_migrations.sh` | 마이그레이션 통합 관리 (`fresh` / `stamp` / `verify` / `status` / `history`) |
| `bootstrap_actionkit.sh` | ActionKit 마이그레이션 + 시드 통합 실행 |
| `bootstrap_rag.sh` | RAG 마이그레이션 + 벡터 시드 통합 실행 |
| `seed_actionkit.py` | ActionKit 시드 데이터 적재 |
| `seed_rag_vectors.py` | RAG 벡터 임베딩 적재 |
| `export_openapi.py` | OpenAPI 스펙 추출 |

---

## 🏃 3. 시작하기 (Quick Start)

가장 쉽고 빠르게 개발 환경을 세팅하는 방법입니다.
Docker가 설치되어 있어야 합니다.

### 1) 필수 프로그램 설치
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (실행 중이어야 함)
* [Git](https://git-scm.com/)

### 2) 프로젝트 실행 (한 방에 실행하기)
터미널에서 프로젝트 루트 경로로 이동한 뒤 아래 명령어를 입력하세요.

```bash
# 컨테이너 빌드 및 백그라운드 실행
docker compose -f docker-compose.dev.yml up -d --build
```
> **💡 Tip:** 로그 확인이 필요하면 서비스별로 조회하세요.
> `docker compose -f docker-compose.dev.yml logs -f app-backend app-worker app-frontend`

### 3) 접속 확인
실행이 완료되면 브라우저에서 아래 주소로 접속해보세요.

* **Frontend (메인 앱):** [http://localhost:3000](http://localhost:3000)
* **Backend (API 문서):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **DB 관리 (필요 시):** 별도 DB 툴(DBeaver 등) 사용 (Port: `5432`)
* **상태 확인:** `docker compose -f docker-compose.dev.yml ps`

> 참고: 로드맵 비동기 생성은 `app-worker`가 실행 중이어야 진행됩니다.

### 4) 프로덕션 Compose 실행
프로덕션은 `docker-compose.prod.yml`을 사용합니다.

```bash
# 1) 서비스별 환경 변수 파일 준비
cp app-backend/.env.example app-backend/.env
cp app-frontend/.env.example app-frontend/.env
# Docker Compose 전용 override (필요 시)
cp app-backend/.env.docker.local.example app-backend/.env.docker.local
cp app-frontend/.env.docker.local.example app-frontend/.env.docker.local

# 2) 프로덕션 이미지 빌드/기동
docker compose -f docker-compose.prod.yml up -d --build

# 3) 마이그레이션 (필요 시)
docker compose -f docker-compose.prod.yml exec -T app-backend \
  bash -lc "cd /app && ./scripts/run_alembic.sh upgrade head"
```

> 참고:
> - `docker-compose.prod.yml`은 소스 볼륨 마운트와 `--reload`를 사용하지 않습니다.
> - 배포 환경에서는 `docker exec stepzero-backend` 대신 `docker compose ... exec app-backend` 사용을 권장합니다.

---

## 🔧 4. 로컬 개발 환경 (심화)

DB와 Redis만 Docker로 띄우고, 프론트/백엔드는 로컬에서 직접 실행하는 방식입니다.

### 1) DB & Redis만 실행
```bash
docker compose -f docker-compose.dev.yml up -d app-db app-redis
```

### 2) Backend 로컬 실행
```bash
cd app-backend

# (최초 1회) 환경변수 파일 복사
cp .env.example .env

# 개발환경 자동 초기화 (Python 3.11 + dev 의존성)
./scripts/setup_dev.sh

# 서버 실행 / 테스트 / 마이그레이션
make run              # uvicorn 개발 서버 실행
make test             # pytest 실행
make migrate-up       # alembic upgrade head
make migrate-verify   # 모델 ↔ DB 스키마 diff 검증
```

### 3) Frontend 로컬 실행
```bash
cd app-frontend
pnpm install
pnpm dev

# 백엔드 OpenAPI 기반 타입 동기화
pnpm types:sync
```
> `types:sync`는 실행 중인 `stepzero-backend` 컨테이너에서 OpenAPI를 추출합니다.

### 4) 환경변수 파일 분리 규칙

로컬 직접 실행과 Docker Compose 실행을 파일로 분리합니다.
같은 키가 여러 파일에 있으면 **나중에 로드된 파일 값이 최종값**입니다.

| 파일 | 용도 |
| :--- | :--- |
| `app-backend/.env` | 공유 가능한 기본값 (민감키 금지) |
| `app-backend/.env.local` | 로컬 전용 비밀값 (Git 추적 제외) |
| `app-backend/.env.docker.local` | Docker Compose 전용 override (host=`app-db` 등) |
| `app-frontend/.env` | `NEXT_PUBLIC_*` 기본값 |
| `app-frontend/.env.local` | 프론트 로컬 전용 비밀값 |
| `app-frontend/.env.docker.local` | 프론트 Docker Compose 전용 override |

```bash
# 최소 셋업
cp app-backend/.env.example app-backend/.env
cp app-frontend/.env.example app-frontend/.env

# Docker Compose 전용 (선택)
cp app-backend/.env.docker.local.example app-backend/.env.docker.local
cp app-frontend/.env.docker.local.example app-frontend/.env.docker.local
```

> 참고:
> - 백엔드는 `uv`를 패키지 매니저로 사용합니다. `uv`가 설치되어 있어야 합니다.
> - 설치: `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## 🗄️ 5. 데이터 관리 (마이그레이션 / 시드)

Docker 컨테이너 내부에서 실행하는 것을 권장합니다.
아래 예시는 `docker compose exec` 기준이며, `docker exec -it stepzero-backend bash -lc "cd /app && ..."` 형태로도 실행할 수 있습니다.

### DB 마이그레이션

```bash
# 새 DB에 마이그레이션 전체 적용
docker compose -f docker-compose.dev.yml exec -T app-backend \
  bash -lc "cd /app && ./scripts/reset_migrations.sh fresh"

# 기존 DB에 alembic_version만 최신으로 stamp (스키마 변경 없음)
docker compose -f docker-compose.dev.yml exec -T app-backend \
  bash -lc "cd /app && ./scripts/reset_migrations.sh stamp"

# 모델 ↔ DB 스키마 diff 검증
docker compose -f docker-compose.dev.yml exec -T app-backend \
  bash -lc "cd /app && ./scripts/reset_migrations.sh verify"
```

### ActionKit 데이터 시드

```bash
# 마이그레이션 + 시드 통합 실행
cd app-backend
ACTIONKIT_BOOTSTRAP_MODE=docker ./scripts/bootstrap_actionkit.sh

# 또는 개별 실행
docker compose -f docker-compose.dev.yml exec -T app-backend \
  bash -lc "cd /app && ./scripts/run_alembic.sh upgrade head"
docker compose -f docker-compose.dev.yml exec -T app-backend \
  bash -lc "cd /app && python scripts/seed_actionkit.py"
```

> `seed_actionkit.py`는 데이터가 이미 존재하면 skip 하므로 초기 적재/리셋 후에 주로 실행합니다.

### RAG 벡터 시드

RAG는 DB 마이그레이션(pgvector extension 보장)과 벡터 적재를 함께 수행합니다.

```bash
# 마이그레이션 + 벡터 시드 통합 실행
cd app-backend
RAG_BOOTSTRAP_MODE=docker ./scripts/bootstrap_rag.sh

# 테스트용 일부만 적재 (예: 20개)
RAG_BOOTSTRAP_LIMIT=20 RAG_BOOTSTRAP_MODE=docker ./scripts/bootstrap_rag.sh
```

> - `bootstrap_rag.sh` 모드: `RAG_BOOTSTRAP_MODE=docker|local|auto` (기본: auto)
> - 기본 소스 경로: `app-backend/.temp/rag` (PDF/Markdown 재귀 탐색)

---

## 🐛 6. 트러블슈팅 (자주 겪는 오류)

### Q1. "docker-credential-desktop ... executable file not found" 오류
`~/.docker/config.json` 파일을 열어 `"credsStore": "desktop"` 부분을 삭제하세요.

### Q2. DB 연결 오류 또는 "database files are incompatible" 오류
PostgreSQL 버전이 안 맞거나 데이터가 꼬인 경우입니다. 볼륨을 지우고 다시 시작하세요.
```bash
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d --build
```

### Q3. "permission denied" (스크립트 실행 오류)
```bash
# Mac/Linux
chmod +x scripts/init_db.sh

# Windows (Git Bash)
git update-index --add --chmod=+x scripts/init_db.sh
```

### Q4. "Node.js version >=20.9.0 is required" 오류
로컬 실행 시 Node.js 20.9.0 이상이 필요합니다. Docker 실행 시에는 Dockerfile의 `node:20-alpine` 이미지를 유지하세요.

---

## 📝 7. 개발 가이드 (Convention)

* **커밋 메시지:** `feat:`, `fix:`, `docs:` 등의 [Conventional Commits](https://www.conventionalcommits.org/) 규칙을 따릅니다.
* **코드 스타일:**
  * Backend: `black`, `isort` 포맷터 사용
  * Frontend: Prettier 포맷터 사용 (설정된 경우)
* **문서:** 작업 전 `docs/` 폴더의 설계 문서를 먼저 읽어보세요.

### 협업 규칙 (Git-Flow + Commit Convention)

1. **브랜치 전략**
   - `main`: 배포 가능한 안정 브랜치 (직접 push 금지, PR만 허용, `develop`에서만 머지)
   - `develop`: 기본 브랜치이자 개발 통합 브랜치
   - `feature/*`: 기능 브랜치 (작업 후 `develop`으로 PR)
   - 브랜치명: `feature/<issue-number>-<short-slug>` (예: `feature/1-login-page`)

2. **커밋 메시지 규칙**
   - 형식: `type: subject`
   - 허용 타입: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`

3. **로컬 훅 활성화**
   ```bash
   # 저장소 루트에서 1회 실행
   pnpm install
   ```
   - `commit-msg`: Conventional Commits 검사
   - `pre-push`: backend 테스트 + frontend lint 검사

4. **CI 검사**
   - PR 시 브랜치명 규칙 검사
   - PR 커밋 메시지(commitlint) 검사
   - backend `pytest`, frontend `lint` 검사

---

Made with ❤️ by StepZero Team
