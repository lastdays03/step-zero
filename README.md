
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
| **Frontend** | **Next.js 14** (App Router)      | React 기반 웹 프레임워크. UI/UX 담당.       |
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
# 컨테이너 빌드 및 실행 (로그 확인 가능)
docker compose -f docker-compose.dev.yml up --build
```
> **💡 Tip:** 백그라운드에서 실행하려면 뒤에 `-d` 옵션을 붙이세요. (`up --build -d`)

### 3) 접속 확인
실행이 완료되면 브라우저에서 아래 주소로 접속해보세요.

* **Frontend (메인 앱):** [http://localhost:3000](http://localhost:3000)
* **Backend (API 문서):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **DB 관리 (필요 시):** 별도 DB 툴(DBeaver 등) 사용 (Port: `5432`)


### 4) (심화) DB/Cache만 띄우고 앱은 로컬에서 실행하기
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
./scripts/setup_dev.sh

# 2) 서버 실행
make run

# 3) 테스트 실행
make test

# 4) 마이그레이션 적용/검증
make migrate-up
make migrate-check
```

> 참고:
> - 백엔드는 `app-backend/.python-version`으로 Python 3.11을 고정합니다.
> - `uv` 버전은 `app-backend/.uv-version`으로 고정합니다.
> - macOS(26 계열)에서는 `uv` 패닉 이슈를 우회하기 위해 `setup_dev.sh`가 기본적으로 `python/pip` 경로를 사용합니다.
> - `uv`를 강제로 쓰려면 `FORCE_UV=1 ./scripts/setup_dev.sh`를 사용하세요.

**3. Frontend 로컬 실행 (Node.js)**
```bash
cd app-frontend
npm install
npm run dev

# 백엔드 OpenAPI 기반 타입 동기화
npm run types:sync
```

### 5) 로컬 시크릿 관리 (권장)
백엔드는 `app-backend/.env.local`을 `app-backend/.env`보다 우선해서 읽습니다.

1. `app-backend/.env`:
- 공유 가능한 기본값만 유지 (민감키 금지)
2. `app-backend/.env.local`:
- 로컬 전용 비밀값 저장 (Git 추적 제외)
3. 최소 예시:
```bash
cd app-backend
cp .env.example .env.local
# .env.local에 OPENAI_API_KEY, GOOGLE_CLIENT_ID 등 실제 값 입력
```

---

## 📂 3. 프로젝트 구조 (Folder Structure)

이 프로젝트는 **Monorepo** 구조를 따릅니다. 하나의 저장소 안에 백엔드와 프론트엔드가 함께 있습니다.

```
step-zero/
├── app-backend/            # 🐍 FastAPI 백엔드 코드
│   ├── app/                # 실제 애플리케이션 로직
│   │   ├── api/            # API 라우터 (Endpoints)
│   │   ├── core/           # 설정(Config), DB 연결 등 핵심 로직
│   │   └── services/       # 비즈니스 로직 (RAG, AI 처리 등)
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
docker compose -f docker-compose.dev.yml up --build
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

---

## 📝 5. 개발 가이드 (Convention)

* **커밋 메시지:** `feat:`, `fix:`, `docs:` 등의 [Conventional Commits](https://www.conventionalcommits.org/) 규칙을 따릅니다.
* **코드 스타일:**
  * Backend: `black`, `isort` 포맷터를 사용합니다.
  * Frontend: `Please use Prettier` (설정된 경우).
* **문서:** 작업 전 `docs/` 폴더의 설계 문서를 먼저 읽어보세요.

### 협업 규칙 (Git-Flow + Commit Convention)
1. 브랜치 전략
- `main`: 배포 가능한 안정 브랜치 (직접 push 금지, PR만 허용)
- `develop`: 개발 통합 브랜치
- `feature/*`: 기능 브랜치
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
