
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
| **Frontend** | **Next.js 16.1.6** (App Router)  | React 기반 웹 프레임워크. UI/UX 담당.       |
| **Database** | **PostgreSQL 16** + **pgvector** | 관계형 데이터 및 벡터 임베딩 저장소.        |
| **Cache**    | **Redis**                        | 세션 관리, 작업 큐, 캐싱 용도.              |
| **Deploy**   | **Docker Compose**               | 로컬 개발 환경 통일 및 배포 관리.           |

---

## 🏃 2. 시작하기 (Quick Start)

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

### 5) (심화) DB/Cache만 띄우고 앱은 로컬에서 실행하기
개발 시 빠른 디버깅을 위해 프론트/백엔드는 로컬 터미널에서 직접 실행하고, DB와 Redis만 Docker로 띄울 수 있습니다.

**1. DB & Redis만 실행**
```bash
# -d 옵션으로 백그라운드 실행
docker compose -f docker-compose.dev.yml up -d app-db app-redis
```

**2. Backend 로컬 실행 (Python)**
```bash
cd app-backend

# 1) 개발환경 자동 초기화 (Python 3.11 + dev 의존성 + .env 생성)
# (최초 1회) 템플릿 복사
cp .env.example .env

# 개발환경 자동 초기화
./scripts/setup_dev.sh

# 2) 서버 실행
make run

# 3) 테스트 실행
make test

# 4) 마이그레이션 적용/검증
make migrate-up
make migrate-check
```

**3. ActionKit DB 데이터 동기화 (팀 공통)**
ActionKit 동기화는 로컬 Python 환경 대신 Docker 컨테이너 내부 실행을 권장합니다.

```bash
# (A) 컨테이너 준비 (처음 세팅/재기동 시)
docker compose -f docker-compose.dev.yml build app-backend
docker compose -f docker-compose.dev.yml up -d app-db app-redis app-backend

# (B) 마이그레이션 적용 (필요 시)
docker exec -it stepzero-backend bash -lc "cd /app && ./scripts/run_alembic.sh upgrade head"

# (C) ActionKit 시드 적용 (초기 1회 또는 데이터 리셋 후)
docker exec -it stepzero-backend bash -lc "cd /app && python scripts/seed_actionkit.py"
```

**4. 전체 DB 마이그레이션 순차 실행 (팀 공통)**
`alembic upgrade head` 대신 리비전 단위(`+1`)로 순차 적용/로그 확인이 필요한 경우 사용합니다.

```bash
# 컨테이너 이름 기준
docker exec -it stepzero-backend bash -lc "cd /app && ./scripts/migrate_all_sequential.sh"

# docker compose 서비스명 기준
docker compose -f docker-compose.dev.yml exec -T app-backend bash -lc "cd /app && ./scripts/migrate_all_sequential.sh"
```

**5. RAG 벡터 마이그레이션 + 시드 (팀 공통)**
RAG는 DB 마이그레이션(스키마 + pgvector extension 보장)과 벡터 적재를 함께 수행해야 합니다.

```bash
# (A) 기본 실행: /app/.temp/rag 경로의 pdf/md를 ETL 후 벡터 적재
docker exec -it stepzero-backend bash -lc "cd /app && ./scripts/bootstrap_rag.sh"
docker compose -f docker-compose.dev.yml exec -T app-backend bash -lc "cd /app && ./scripts/bootstrap_rag.sh"

# (B) 문서 경로 지정
docker exec -it stepzero-backend bash -lc "cd /app && RAG_BOOTSTRAP_SOURCE_DIR=/app/.temp/rag ./scripts/bootstrap_rag.sh"
docker compose -f docker-compose.dev.yml exec -T app-backend bash -lc "cd /app && RAG_BOOTSTRAP_SOURCE_DIR=/app/.temp/rag ./scripts/bootstrap_rag.sh"

# (C) 테스트용 일부만 적재(예: 20개)
docker exec -it stepzero-backend bash -lc "cd /app && RAG_BOOTSTRAP_LIMIT=20 ./scripts/bootstrap_rag.sh"
docker compose -f docker-compose.dev.yml exec -T app-backend bash -lc "cd /app && RAG_BOOTSTRAP_LIMIT=20 ./scripts/bootstrap_rag.sh"
```

옵션:
```bash
# 마이그레이션 + 시드를 한 번에 실행
cd app-backend
ACTIONKIT_BOOTSTRAP_MODE=docker ./scripts/bootstrap_actionkit.sh

# RAG 마이그레이션 + 벡터 시드 한 번에 실행
RAG_BOOTSTRAP_MODE=docker ./scripts/bootstrap_rag.sh

# 서비스명 기준으로 실행(컨테이너 이름 비의존)
docker compose -f docker-compose.dev.yml exec -T app-backend bash -lc "cd /app && ./scripts/run_alembic.sh upgrade head"
docker compose -f docker-compose.dev.yml exec -T app-backend bash -lc "cd /app && python scripts/seed_actionkit.py"
docker compose -f docker-compose.dev.yml exec -T app-backend bash -lc "cd /app && ./scripts/migrate_all_sequential.sh"
docker compose -f docker-compose.dev.yml exec -T app-backend bash -lc "cd /app && ./scripts/bootstrap_rag.sh"
```

> 참고:
> - 백엔드는 `app-backend/.python-version`으로 Python 3.11을 고정합니다.
> - `uv` 버전은 `app-backend/.uv-version`으로 고정합니다.
> - macOS(26 계열)에서는 `uv` 패닉 이슈를 우회하기 위해 `setup_dev.sh`가 기본적으로 `python/pip` 경로를 사용합니다.
> - `uv`를 강제로 쓰려면 `FORCE_UV=1 ./scripts/setup_dev.sh`를 사용하세요.
> - 팀 공통 기준은 Docker 컨테이너 내부 실행을 권장합니다.
> - 시드(`seed_actionkit.py`)는 데이터가 이미 존재하면 skip 하므로 초기 적재/리셋 후에 주로 실행하면 됩니다.
> - `bootstrap_actionkit.sh` 모드 강제: `ACTIONKIT_BOOTSTRAP_MODE=docker|local|auto`
> - `bootstrap_rag.sh` 모드 강제: `RAG_BOOTSTRAP_MODE=docker|local|auto`
> - `seed_rag_vectors.py` 기본 경로는 `app-backend/.temp/rag`이며, PDF/Markdown 파일을 재귀 탐색합니다.
> - 본 저장소는 `app-backend` 컨테이너 이름을 `stepzero-backend`로 고정하므로 `docker exec` 기준 명령을 사용합니다.
> - 컨테이너 이름 변경 가능성을 고려하면 `docker compose exec app-backend` 방식이 더 이식성이 좋습니다.

**4. Frontend 로컬 실행 (Node.js)**
```bash
# Node.js 20.9.0 이상 권장 (Next.js 16 요구사항)
cd app-frontend
npm install
npm run dev

# 백엔드 OpenAPI 기반 타입 동기화
npm run types:sync
```
> Windows/macOS/Linux 공통으로 `types:sync`는 실행 중인 `stepzero-backend` 컨테이너에서 OpenAPI를 추출합니다.

### 6) 환경변수 파일 분리 규칙 (권장)
로컬 직접 실행과 Docker Compose 실행을 파일로 분리합니다.

- 로컬 실행(백엔드/프론트를 로컬 프로세스로 실행):
`app-backend/.env` < `app-backend/.env.local`
`app-frontend/.env` < `app-frontend/.env.local`
- Docker Compose 실행:
`app-backend/.env` < `app-backend/.env.local` < `app-backend/.env.docker.local`
`app-frontend/.env` < `app-frontend/.env.local` < `app-frontend/.env.docker.local`

같은 키가 여러 파일에 있으면 **나중에 로드된 파일 값이 최종값**입니다.

1. `app-backend/.env`:
- 공유 가능한 기본값만 유지 (민감키 금지)
2. `app-backend/.env.local`:
- 로컬 전용 비밀값 저장 (Git 추적 제외)
3. `app-backend/.env.docker.local`:
- Docker Compose 전용 override (예: `DATABASE_URL` host=`app-db`, `REDIS_URL` host=`app-redis`)
4. `app-frontend/.env` / `app-frontend/.env.local`:
- `NEXT_PUBLIC_*` 값만 관리 (백엔드/시크릿 값 금지)
5. `app-frontend/.env.docker.local`:
- 프론트 Docker Compose 전용 override가 필요할 때만 사용
6. 최소 예시:
```bash
cp app-backend/.env.example app-backend/.env
cp app-frontend/.env.example app-frontend/.env

# 로컬 실행 전용(선택)
cp app-backend/.env.example app-backend/.env.local
cp app-frontend/.env.example app-frontend/.env.local

# Docker Compose 전용(선택)
cp app-backend/.env.docker.local.example app-backend/.env.docker.local
cp app-frontend/.env.docker.local.example app-frontend/.env.docker.local
```

---

## 📂 3. 프로젝트 구조 (Folder Structure)

이 프로젝트는 **Monorepo** 구조를 따릅니다. 하나의 저장소 안에 백엔드와 프론트엔드가 함께 있습니다.

```
step-zero/
├── app-backend/            # 🐍 FastAPI 백엔드 코드
│   ├── app/                # 실제 애플리케이션 로직
│   │   ├── api/            # API 라우터 (v1)
│   │   ├── features/       # feature 단위 도메인/애플리케이션 로직
│   │   ├── repositories/   # 데이터 접근 계층
│   │   ├── models/         # SQLModel/ORM 모델
│   │   ├── workers/        # ARQ 비동기 워커
│   │   └── core/           # 설정(Config), DB 연결 등 핵심 로직
│   ├── tests/              # 테스트 코드 (Pytest)
│   └── Dockerfile          # 백엔드 이미지 빌드 설정
│
├── app-frontend/           # ⚛️ Next.js 프론트엔드 코드
│   ├── src/
│   │   ├── app/            # 페이지 및 라우팅 (App Router)
│   │   ├── components/     # 재사용 가능한 UI 컴포넌트
│   │   └── lib/            # 유틸리티 함수
│   └── Dockerfile          # 프론트엔드 이미지 빌드 설정
│
├── data/                   # (Git 제외) 로컬 DB 데이터 저장소 (자동 생성됨)
├── docs/                   # 📄 기획 및 설계 문서 (필독!)
├── scripts/                # 유틸리티 스크립트 (DB 초기화 등)
└── docker-compose.dev.yml  # 🐳 로컬 개발 환경 구성 파일
```

---

## 🐛 4. 트러블슈팅 (자주 겪는 오류)

개발 중 자주 발생하는 문제와 해결 방법입니다.

### Q1. "docker-credential-desktop ... executable file not found" 오류가 나요.
Docker 설정 파일 문제일 수 있습니다. `~/.docker/config.json` 파일을 열어 `"credsStore": "desktop"` 부분을 삭제하세요.

### Q2. DB 연결 오류 또는 "database files are incompatible" 오류가 나요.
PostgreSQL 버전이 안 맞거나 데이터가 꼬인 경우입니다. 아래 명령어로 **볼륨을 싹 지우고 다시 시작**하세요.
```bash
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up -d --build
```

### Q3. "permission denied" (scripts/init_db.sh) 오류가 나요.
실행 스크립트 권한 문제일 수 있습니다.

**Mac/Linux:**
```bash
chmod +x scripts/init_db.sh
```

**Windows (Git Bash 또는 CMD):**
```bash
git update-index --add --chmod=+x scripts/init_db.sh
# 이후 commit & push를 하면 레포지토리에 권한이 반영됩니다.
```

### Q4. "For Next.js, Node.js version >=20.9.0 is required" 오류가 나요.
프론트 실행 Node 버전이 낮은 경우입니다.

```bash
# 로컬 실행 시 Node 20.9.0 이상 사용
node -v
```

- Docker 실행 시에는 `app-frontend/Dockerfile`의 베이스 이미지를 `node:20-alpine`으로 유지하세요.

---

## 📝 5. 개발 가이드 (Convention)

* **커밋 메시지:** `feat:`, `fix:`, `docs:` 등의 [Conventional Commits](https://www.conventionalcommits.org/) 규칙을 따릅니다.
* **코드 스타일:**
  * Backend: `black`, `isort` 포맷터를 사용합니다.
  * Frontend: `Please use Prettier` (설정된 경우).
* **문서:** 작업 전 `docs/` 폴더의 설계 문서를 먼저 읽어보세요.

### 협업 규칙 (Git-Flow + Commit Convention)
1. 브랜치 전략
- `main`: 배포 가능한 안정 브랜치 (직접 push 금지, PR만 허용, `develop`에서만 머지)
- `develop`: 기본 브랜치이자 개발 통합 브랜치
- `feature/*`: 기능 브랜치 (작업 후 `develop`으로 PR)
- 브랜치명: `feature/<issue-number>-<short-slug>` (예: `feature/1-login-page`)

2. 커밋 메시지 규칙
- 형식: `type: subject`
- 허용 타입: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`, `revert`

3. 로컬 훅 활성화
```bash
# 저장소 루트에서 1회 실행
npm install
```
- `commit-msg`: Conventional Commits 검사
- `pre-push`: backend 테스트 + frontend lint 검사

4. CI 검사
- PR 시 브랜치명 규칙 검사
- PR 커밋 메시지(commitlint) 검사
- backend `pytest`, frontend `lint` 검사

---

Made with ❤️ by StepZero Team
