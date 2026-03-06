# REPORT: 런타임 및 패키지 매니저 업그레이드 평가

> 작성일: 2026-03-05
> 브랜치: `feature/5-pkg-manager-migration`
> 목적: 프로젝트 전체 도구/런타임 최신 안정 버전 분석 및 안전한 마이그레이션 방안 수립

---

## 1. 현재 버전 현황

### 1.1 Backend (app-backend)

| 항목 | 설정 버전 | 실제 설치 | 설정 위치 |
|------|----------|----------|----------|
| Python | `>=3.13` | 호스트 3.12.3 / Docker 3.13 | `pyproject.toml` L37, `Dockerfile` L1 |
| uv | Docker `0.9` / 호스트 `0.10.8` | 0.10.8 (호스트) | `Dockerfile` L3, `Dockerfile.prod` L3 |
| FastAPI | `>=0.109.0` | lock 기준 | `pyproject.toml` L9 |
| SQLAlchemy | `>=2.0.44` | lock 기준 | `pyproject.toml` L12 |
| SQLModel | `>=0.0.14` | lock 기준 | `pyproject.toml` L13 |
| PostgreSQL | 16 (pgvector) | Docker 이미지 | `docker-compose.dev.yml` L6 |

### 1.2 Frontend (app-frontend)

| 항목 | 설정 버전 | 실제 설치 | 설정 위치 |
|------|----------|----------|----------|
| Node.js | 22 | v22.14.0 | `Dockerfile` L1, `ci.yml` L170 |
| pnpm | 9.15.4 | 9.15.4 | 루트 `package.json` L4 (`packageManager`) |
| Next.js | `^16.1.6` | 16.1.6 | `package.json` L35 |
| React | `^18` | 18.3.1 | `package.json` L36, `pnpm-lock.yaml` L13 |
| TypeScript | `^5` | 5.x | `package.json` L60 |
| Tailwind CSS | `^3.3.0` | 3.x | `package.json` L58 |
| ESLint | `^9` | 9.x | `package.json` L53 |

### 1.3 CI/CD (.github/workflows/ci.yml)

| 항목 | 버전 |
|------|------|
| Python | 3.13 (actions/setup-python) |
| Node.js | 22 (actions/setup-node) |
| pnpm | action-setup@v4 (packageManager 필드에서 자동 감지) |
| uv | astral-sh/setup-uv@v5 |

### 1.4 불일치 포인트

| 문제 | 설명 | 위험도 |
|------|------|--------|
| uv 버전 불일치 | Docker 이미지 `ghcr.io/astral-sh/uv:0.9` vs 호스트 `0.10.8` | **높음** — 동작 차이 발생 가능 |
| 호스트 Python 버전 | 호스트 3.12.3 vs Docker/CI 3.13 | 낮음 — Docker 내 실행이므로 |

---

## 2. 최신 안정 버전 비교 (2026-03-05 기준)

| 도구 | 현재 | 최신 안정 | 변경 규모 | 업그레이드 권장도 |
|------|------|----------|----------|-----------------|
| **Python** | 3.13 (Docker) | **3.13.12** | 패치 | 권장 |
| **uv** | Docker 0.9 / 호스트 0.10.8 | **0.10.8** | Docker 메이저 | **필수** |
| **Node.js** | 22 LTS | **24 LTS** "Krypton" | 메이저 | 검토 후 결정 |
| **pnpm** | 9.15.4 | **10.30.3** | 메이저 | 검토 후 결정 |
| **Next.js** | 16.1.6 | **16.1.6** | 없음 | 최신 상태 |
| **React** | 18.3.1 | **19.2.4** | 메이저 | 별도 기획 필요 |
| **TypeScript** | ^5 | **5.8.3** (6.0 beta) | 마이너 | 자동 반영 |
| **Tailwind CSS** | 3.3 | **4.2.0** | 메이저 | 별도 기획 필요 |
| **FastAPI** | >=0.109.0 | **0.135.1** | 마이너 | 권장 |
| **SQLAlchemy** | >=2.0.44 | **2.0.48** | 패치 | 권장 |
| **SQLModel** | >=0.0.14 | **0.0.37** | 마이너 | 권장 |
| **PostgreSQL** | 16 | **17.x** | 메이저 | 관망 |

---

## 3. 항목별 상세 분석

### 3.1 uv (0.9 → 0.10) — 필수 업그레이드

**현상:** Docker 이미지에서 `ghcr.io/astral-sh/uv:0.9`를 사용하지만 호스트는 `0.10.8`. 이 불일치로 lock 파일 해석이나 의존성 해결 동작이 다를 수 있음.

**주요 변경점 (0.9 → 0.10):**
- Docker 기본 이미지: Debian Bookworm → Trixie, Alpine 3.21 → 3.22
- `uv venv`가 기존 venv 삭제 시 `--clear` 플래그 필수
- `default = true` 중복 인덱스 설정 시 에러로 변경
- Python 3.8 및 PPC64 지원 제거
- `uv python upgrade` 명령 stable 승격

**영향 범위:** `Dockerfile`, `Dockerfile.prod` (2개 파일)

**수정 방안:**
```dockerfile
# Before
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/
# After
COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /uvx /bin/
```

**위험도:** 낮음 — 프로젝트에서 index 커스텀 설정이나 `uv venv` 직접 사용 없음. `uv sync` / `uv run` 패턴만 사용 중.

---

### 3.2 FastAPI (0.109 → 0.135) — 권장

**주요 변경점:**
- Starlette 1.0.0+ 지원
- SSE / Streaming JSON Lines 지원 추가
- `strict_content_type` 기본 활성화 — JSON Content-Type 검증 강화
- Python 3.8 지원 종료 (무관)
- `fastapi-slim` 지원 중단 (미사용)

**영향 범위:** `pyproject.toml` 하한 버전만 변경, `uv lock` 재실행

**위험도:** 낮음 — `strict_content_type` 기본 활성화가 유일한 잠재 이슈이나, 프론트엔드에서 Axios로 JSON 전송 시 Content-Type 헤더 자동 설정되므로 문제 없음.

---

### 3.3 SQLModel (0.0.14 → 0.0.37) — 권장

**주요 변경점:**
- Pydantic 2.7+ 지원 개선
- 타입 시스템 리팩토링
- SQLAlchemy 2.x 완전 호환

**위험도:** 낮음 — 프로젝트가 이미 Pydantic v2 + SQLAlchemy 2.x 사용 중.

---

### 3.4 SQLAlchemy (2.0.44 → 2.0.48) — 권장

버그 픽스 패치. 위험도 매우 낮음. 2.1.0 beta는 보류.

---

### 3.5 Node.js (22 → 24) — 검토 후 결정

**주요 변경점:**
- OpenSSL 3.5 탑재, 보안 레벨 2 (RSA/DSA 2048bit 미만 키 차단)
- `Buffer` 범위 초과 쓰기 시 throw 변경
- `URLPattern` 전역 객체 승격
- 32-bit Linux armv7 prebuild 제거

**영향 범위:** `Dockerfile`, `Dockerfile.prod`, `ci.yml`

**현재 권장:** Node 22 LTS는 2027년 EOL. 아직 충분한 지원 기간이 남아 있으므로 **급하지 않음**. 단, Next.js 16이 Node 22+를 요구하므로 22 유지도 문제 없음.

**결정 기준:** Node 24 전환은 모든 npm 패키지가 Node 24 호환 확인 후 진행. 특히 `@hello-pangea/dnd`, `canvas-confetti` 등 native addon 의존 패키지 확인 필요.

---

### 3.6 pnpm (9 → 10) — 검토 후 결정

**주요 변경점:**
- **lifecycle script 기본 비활성화** — `pnpm.onlyBuiltDependencies`에 명시 필요
- `pnpm link` 방식 변경 (overrides 기반)
- lockfile v6 → v9 변환 제거 (현재 v9 사용 중 — 영향 없음)
- `pnpm test` 파라미터 전달 방식 변경

**잠재적 문제:**
- `husky` prepare 스크립트가 lifecycle script에 의존 → `pnpm.onlyBuiltDependencies` 설정 필요
- `corepack enable` 후 `packageManager` 필드 업데이트 필요

**수정 방안 (진행 시):**
```jsonc
// 루트 package.json
{
  "packageManager": "pnpm@10.30.3",
  "pnpm": {
    "onlyBuiltDependencies": ["husky"]
  }
}
```

**위험도:** 중간 — lifecycle script 변경으로 CI 파이프라인 테스트 필수.

---

### 3.7 React (18 → 19) — 별도 기획 필요

**주요 변경점:**
- `forwardRef` 불필요 (ref를 prop으로 직접 전달)
- `use()` Hook 도입
- `useActionState()` 신규
- Server Components / Server Actions 정식 stable
- `react-dom/client` API 변경

**영향 범위 평가:**
- `@hello-pangea/dnd` — React 19 호환성 확인 필요 (DnD 라이브러리)
- `@react-oauth/google` — React 19 호환성 확인 필요
- Radix UI — 최신 버전은 React 19 지원
- `react-dropzone` — 호환성 확인 필요

**참고:** Next.js 16은 React 18과 19 모두 지원. 현재 React 18로 안정적 동작 중이므로 **급하지 않음**.

**위험도:** 높음 — 서드파티 라이브러리 호환성 전수 점검 + 전체 UI 리그레션 테스트 필요.

---

### 3.8 Tailwind CSS (3.3 → 4.x) — 별도 기획 필요

**주요 변경점:**
- `tailwind.config.js` → CSS `@theme` 지시어로 구성 전면 변경
- `@tailwind` → `@import "tailwindcss"` 변경
- `border` 기본색: `gray-200` → `currentColor`
- Lightning CSS 기반 새 엔진
- PostCSS 플러그인 → `@tailwindcss/postcss` 또는 `@tailwindcss/webpack`
- 브라우저 최소 요구: Safari 16.4+, Chrome 111+, Firefox 128+

**현재 프로젝트 영향:**
- `tailwind.config.ts` — 104줄 커스텀 설정 (shadcn/ui 테마) 전면 재작성 필요
- `postcss.config.js` — 플러그인 교체 필요
- `tailwindcss-animate` 플러그인 — v4 호환 버전 확인 필요
- 모든 컴포넌트의 Tailwind 클래스 호환성 점검

**위험도:** 매우 높음 — 전체 UI 스타일 리그레션 가능성. `npx @tailwindcss/upgrade` 자동 마이그레이션 도구 사용 가능하나 커스텀 설정은 수동 작업 필요.

---

## 4. 업그레이드 전략

### Phase A: 즉시 실행 (안전한 패치/마이너 업그레이드)

**범위:** 동작 변경 없는 안전한 업그레이드만 포함
**예상 작업량:** 1시간 이내
**롤백 용이성:** 높음

| 작업 | 파일 | 변경 내용 |
|------|------|----------|
| uv Docker 이미지 통일 | `Dockerfile`, `Dockerfile.prod` | `0.9` → `0.10` |
| Python 패치 반영 | Docker 이미지 기반 자동 | 3.13-slim (최신 패치 자동 포함) |
| Backend 의존성 업데이트 | `pyproject.toml`, `uv.lock` | FastAPI, SQLAlchemy, SQLModel 하한 조정 + `uv lock --upgrade` |

**검증 절차:**
```bash
# 1. Docker 빌드 테스트
docker compose -f docker-compose.dev.yml build app-backend app-worker

# 2. 백엔드 테스트 실행
docker compose -f docker-compose.dev.yml exec app-backend uv run pytest -q

# 3. 마이그레이션 정합성
docker compose -f docker-compose.dev.yml exec app-backend python -m alembic check
```

### Phase B: 검토 후 결정 (pnpm 10, Node 24)

**범위:** 메이저 업그레이드이나 코드 변경 없이 설정만 조정
**예상 작업량:** 반나절
**전제조건:** Phase A 완료 + CI 통과

#### B-1: pnpm 9 → 10

```bash
# 1. 루트 package.json 수정
#    "packageManager": "pnpm@10.30.3"
#    + "pnpm": { "onlyBuiltDependencies": ["husky"] }

# 2. app-frontend/pnpm-lock.yaml 재생성
cd app-frontend && rm -f pnpm-lock.yaml && pnpm install

# 3. CI 테스트
pnpm lint && pnpm build
```

#### B-2: Node 22 → 24 (선택)

```bash
# Dockerfile, Dockerfile.prod: node:22-alpine → node:24-alpine
# ci.yml: node-version: "22" → "24"

# 검증: Docker 빌드 + 프론트엔드 빌드 + lint
```

### Phase C: 별도 기획 필요 (React 19, Tailwind 4)

이 항목들은 코드 변경량이 크고 전체 UI 리그레션 테스트가 필수. 별도 feature 브랜치에서 진행 권장.

#### C-1: React 18 → 19

- 서드파티 라이브러리 호환성 전수 점검 선행
- `forwardRef` 사용처 리팩토링
- `react-dom/client` API 변경 대응
- **별도 브랜치 + 전체 수동 QA 필요**

#### C-2: Tailwind CSS 3 → 4

- `npx @tailwindcss/upgrade` 자동 마이그레이션 먼저 실행
- `tailwind.config.ts` → CSS `@theme` 수동 변환
- `postcss.config.js` → `@tailwindcss/postcss` 교체
- shadcn/ui 테마 변수 전면 재매핑
- **별도 브랜치 + 전체 UI 시각 점검 필요**

---

## 5. 권장 실행 순서

```
Phase A (즉시)
  └── uv 0.10 통일 + Backend 의존성 업데이트
       ├── Docker 빌드 테스트
       ├── pytest 통과
       └── alembic check 통과

Phase B (Phase A 안정화 후)
  ├── B-1: pnpm 10 업그레이드
  │    ├── lockfile 재생성
  │    ├── lint + build 통과
  │    └── CI 파이프라인 통과
  └── B-2: Node 24 (선택, B-1 안정 후)
       ├── Docker 빌드 테스트
       └── 프론트엔드 빌드 + lint 통과

Phase C (별도 Sprint 기획)
  ├── C-1: React 19 마이그레이션
  └── C-2: Tailwind CSS 4 마이그레이션
```

---

## 6. 현재 브랜치(feature/5-pkg-manager-migration)에서 할 것

이 브랜치의 원래 목적은 패키지 매니저 마이그레이션이므로, **Phase A + Phase B-1**을 이 브랜치에서 완료하는 것이 적절:

1. uv Docker 이미지 `0.9` → `0.10` 통일
2. Backend 의존성 하한 버전 업데이트 + lock 재생성
3. (선택) pnpm 10 업그레이드 + lockfile 재생성
4. CI 파이프라인 검증
5. PR → develop

Phase B-2(Node 24)와 Phase C는 별도 이슈/브랜치로 분리.

---

## 7. 위험 요약 매트릭스

| 작업 | 코드 변경량 | 빌드 영향 | UI 영향 | 롤백 용이성 | 종합 위험도 |
|------|-----------|----------|---------|-----------|-----------|
| uv 0.10 | 2줄 | 재빌드 필요 | 없음 | git revert | **낮음** |
| FastAPI/SA/SM 업데이트 | 3줄 + lock | 없음 | 없음 | lock revert | **낮음** |
| pnpm 10 | 설정 + lock | lockfile 재생성 | 없음 | lock revert | **중간** |
| Node 24 | 3줄 | Docker 재빌드 | 없음 | 이미지 태그 변경 | **중간** |
| React 19 | 다수 컴포넌트 | 빌드 오류 가능 | 리그레션 가능 | 복잡 | **높음** |
| Tailwind 4 | 전체 스타일 | 빌드 오류 가능 | 전면 리그레션 | 복잡 | **매우 높음** |
