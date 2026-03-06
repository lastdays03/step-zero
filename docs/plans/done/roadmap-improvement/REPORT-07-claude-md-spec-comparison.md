# CLAUDE.md 스펙 변경 전/후 비교 분석

> 분석일: 2026-03-01
> 목적: 기존 CLAUDE.md(구버전)와 실제 코드베이스(현재) 간 스펙 차이 비교 및 장단점 분석

---

## 1. 디렉토리 구조

| | 변경 전 | 변경 후 |
|---|---|---|
| **경로** | `backend/`, `frontend/` | `app-backend/`, `app-frontend/` |

**변경 전 장점:** 간결하고 직관적. 타이핑 짧음.
**변경 전 단점:** 모노레포에서 루트의 다른 폴더(scripts/, docs/)와 역할 구분이 모호.

**변경 후 장점:** `app-` 접두사로 실행 가능한 서비스와 보조 폴더(docs/, scripts/)를 명확히 구분. Docker Compose 서비스명과 일치 (`app-backend`, `app-frontend`, `app-worker`).
**변경 후 단점:** 경로가 길어짐. `cd app-backend` 반복 입력.

---

## 2. Python 버전

| | 변경 전 | 변경 후 |
|---|---|---|
| **버전** | Python 3.12.3 (exact) | Python >= 3.11 (target: 3.11) |

**변경 전 장점:** 최신 버전으로 성능 우위 (CPython 3.12는 ~5% 빠름). f-string 개선, 에러 메시지 향상.
**변경 전 단점:** exact 버전 고정은 환경 구성 까다로움. Docker 이미지/CI에서 정확히 3.12.3 맞춰야 함.

**변경 후 장점:** 3.11은 안정적이고 검증된 버전. `>=3.11` 범위 지정으로 환경 유연성 확보. asyncpg, SQLAlchemy 등 의존성 호환성 높음.
**변경 후 단점:** 3.12의 성능 개선, `type` 문법 개선 등 활용 불가.

---

## 3. 모듈 경로 / 실행 포트

| | 변경 전 | 변경 후 |
|---|---|---|
| **uvicorn** | `backend.main:app --port 28080` | `app.main:app --port 8000` |

**변경 전 장점:** 28080은 다른 서비스와 포트 충돌 가능성 낮음.
**변경 전 단점:** 비표준 포트라 기억하기 어려움. 팀 내 혼란.

**변경 후 장점:** 8000은 FastAPI/uvicorn 관례 포트. 새 팀원이 즉시 이해. Docker Compose, 프론트엔드 프록시 설정과 일관성.
**변경 후 단점:** 다른 로컬 서비스와 충돌 가능성 (Django 등도 8000 사용).

---

## 4. 아키텍처 패턴

| | 변경 전 | 변경 후 |
|---|---|---|
| **구조** | Domain-Driven Design (`domain/{entity}/`) | Feature-Based Architecture (`features/{feature}/`) |
| **레이어** | `model.py` + `service.py` + `repository.py` per domain | `domain/` + `application/` per feature + 공유 `repositories/` |

**변경 전 (DDD) 장점:**
- 도메인 모델 중심 설계로 비즈니스 로직 캡슐화 강함
- 각 도메인이 자체 repository를 가져 독립성 높음
- 대규모 팀에서 도메인별 ownership 명확

**변경 전 단점:**
- 오버엔지니어링 경향 (초기 스타트업에 과함)
- 도메인 간 의존성 관리 복잡
- 파일 3개(model/service/repo)가 항상 세트로 필요

**변경 후 (Feature-Based) 장점:**
- Feature 단위로 관련 코드가 한 곳에 모임 (높은 응집도)
- 공유 repository로 중복 제거 (`user_repository`를 auth, profile, ops가 공유)
- 새 기능 추가 시 `features/` 아래 폴더 하나만 생성
- domain/application 분리로 비즈니스 규칙과 유스케이스 구분 유지

**변경 후 단점:**
- 공유 `repositories/`가 비대해질 수 있음
- Feature 간 경계가 DDD보다 느슨

---

## 5. DB 세션 관리

| | 변경 전 | 변경 후 |
|---|---|---|
| **방식** | Read/Write 분리 (`get_read_session` / `get_write_session`) | 단일 세션 (`get_session()`) |

**변경 전 (R/W 분리) 장점:**
- 읽기 전용 레플리카로 부하 분산 가능
- 읽기 엔드포인트에서 실수로 write 방지 (안전장치)
- 대규모 트래픽 시 수평 확장 용이

**변경 전 단점:**
- 세션 2종류 관리로 코드 복잡도 증가
- 모든 엔드포인트에서 read/write 판단 필요
- 초기 단계에 불필요한 복잡성

**변경 후 (단일 세션) 장점:**
- 단순함. 모든 곳에서 `get_session()` 하나만 사용
- 트랜잭션 관리 간편
- 초기 스타트업에 적합한 복잡도

**변경 후 단점:**
- 트래픽 증가 시 DB 병목 → 나중에 분리 작업 필요
- 읽기 전용 엔드포인트도 write 세션 사용 (자원 낭비)

---

## 6. UI 컴포넌트 라이브러리

| | 변경 전 | 변경 후 |
|---|---|---|
| **UI** | MUI Material + Emotion (CSS-in-JS) | Radix UI + shadcn/ui + Tailwind CSS 3.3 |

**변경 전 (MUI) 장점:**
- 즉시 사용 가능한 완성도 높은 컴포넌트 (DatePicker, DataGrid 등)
- Material Design 가이드라인 자동 준수
- 테마 시스템 강력 (ThemeProvider로 전역 커스텀)
- 비개발자도 일관된 UI 구현 가능

**변경 전 단점:**
- 번들 사이즈 큼 (~300KB+ gzipped)
- CSS-in-JS(Emotion) 런타임 오버헤드 → SSR/RSC와 충돌
- Material Design 탈피 어려움 (커스텀 디자인 비용 높음)
- Next.js App Router + React Server Components와 궁합 나쁨

**변경 후 (Radix + shadcn) 장점:**
- **Headless UI** → 디자인 100% 자유 (Tailwind로 완전 커스텀)
- 번들 사이즈 최소 (필요한 컴포넌트만 import)
- SSR/RSC 완벽 호환 (CSS-in-JS 런타임 없음)
- shadcn/ui: 코드 복사 방식이라 소유권 100% (node_modules 의존 없음)
- 접근성(a11y) Radix가 업계 최고 수준

**변경 후 단점:**
- 복잡한 컴포넌트(DataGrid, DatePicker) 직접 구현 필요
- 디자인 시스템을 직접 만들어야 함 (초기 시간 투자)
- shadcn/ui 업데이트 시 수동 반영 필요

---

## 7. 인증 방식

| | 변경 전 | 변경 후 |
|---|---|---|
| **저장** | 서버 사이드 JWT 검증 (`serverAuth.ts`) | localStorage JWT + Axios 인터셉터 |
| **OAuth** | Firebase + Kakao OAuth | Google OAuth (@react-oauth/google) |

**변경 전 (서버사이드 + Firebase) 장점:**
- JWT가 httpOnly 쿠키에 저장 → XSS로 토큰 탈취 불가
- Firebase Auth: 소셜 로그인 통합 관리 (Google, Kakao, Apple 등 한번에)
- 서버 사이드 검증으로 보안 강화

**변경 전 단점:**
- Firebase 종속성 (벤더 락인)
- Firebase 무료 한도 초과 시 비용 발생
- CORS/쿠키 설정 복잡 (크로스도메인)

**변경 후 (localStorage + Google) 장점:**
- 외부 서비스 의존 없음 (자체 JWT 발급/검증)
- 구현 단순 (Axios 인터셉터로 자동 refresh)
- `useSyncExternalStore`로 탭 간 인증 상태 동기화
- Google OAuth만으로 시작 → 필요 시 추가

**변경 후 단점:**
- **localStorage는 XSS 취약** (httpOnly 쿠키보다 보안 약함)
- Silent refresh 실패 시 사용자 경험 저하
- 소셜 로그인 추가 시 각각 직접 구현 필요

---

## 8. 파일 업로드

| | 변경 전 | 변경 후 |
|---|---|---|
| **방식** | AWS S3 Presigned POST + 클라이언트 압축 | 로컬 파일시스템 (`STORAGE_LOCAL_ROOT`) |

**변경 전 (S3) 장점:**
- 무제한 스토리지, 고가용성 (99.999999999% 내구성)
- CDN(CloudFront) 연동으로 글로벌 배포 용이
- 서버 부하 없음 (클라이언트 → S3 직접 업로드)
- 자동 백업/버전 관리

**변경 전 단점:**
- AWS 종속, 비용 발생
- Presigned URL 구현 복잡
- 로컬 개발 시 S3 접근 필요 (또는 LocalStack 필요)

**변경 후 (로컬 파일시스템) 장점:**
- 구현 단순, 외부 의존 없음
- 로컬 개발환경에서 즉시 동작
- 비용 제로
- 디버깅 쉬움 (파일 직접 확인)

**변경 후 단점:**
- **서버 디스크 용량 한계**
- 서버 장애 시 파일 유실 위험
- 수평 확장 시 파일 공유 문제 (NFS/EFS 필요)
- CDN 불가 → 이미지 로딩 느림

---

## 9. 국제화 (i18n)

| | 변경 전 | 변경 후 |
|---|---|---|
| **방식** | next-intl (다국어 지원) | 없음 (한국어 단일) |

**변경 전 장점:** 글로벌 확장 준비 완료. 언어별 라우팅 (`/ko`, `/en`).
**변경 전 단점:** 번역 관리 비용, 초기 개발 속도 저하, 한국 타겟 제품에 불필요한 복잡성.

**변경 후 장점:** 개발 속도 빠름. 코드 단순. 한국 시장 집중.
**변경 후 단점:** 글로벌 진출 시 i18n 후속 작업 필요.

---

## 10. CSS 프레임워크 버전

| | 변경 전 | 변경 후 |
|---|---|---|
| **Tailwind** | v4 | v3.3 |

**변경 전 (v4) 장점:** CSS-first 설정 (`@theme`), 성능 개선 (Oxide 엔진), CSS nesting 네이티브.
**변경 전 단점:** 2025년 초 출시로 생태계 미성숙, 플러그인 호환성 이슈, 마이그레이션 가이드 불완전.

**변경 후 (v3.3) 장점:** 안정적, 생태계 완성 (shadcn/ui, tailwind-merge 등 완벽 호환), 레퍼런스 풍부.
**변경 후 단점:** v4 대비 빌드 속도 느림, CSS 네이티브 기능 활용 제한.

---

## 11. 패키지 매니저

| | 변경 전 | 변경 후 |
|---|---|---|
| **프론트엔드** | pnpm | npm |

**변경 전 (pnpm) 장점:** 디스크 절약 (하드링크), 엄격한 의존성 (phantom deps 방지), 속도 빠름.
**변경 전 단점:** 팀원 추가 설치 필요, 일부 패키지 호환성 이슈, 학습 곡선.

**변경 후 (npm) 장점:** Node.js 내장 (추가 설치 없음), 가장 넓은 호환성, 문서/예제 풍부.
**변경 후 단점:** `node_modules` 크기 큼, phantom deps 가능, pnpm보다 느림.

---

## 12. 번들러 (Dev 서버)

| | 변경 전 | 변경 후 |
|---|---|---|
| **방식** | Turbopack | Webpack |

**변경 전 (Turbopack) 장점:** HMR 10배 이상 빠름, Rust 기반 병렬 처리, Next.js 공식 미래 방향.
**변경 전 단점:** 2025년 기준 아직 beta 기능 일부 미지원, 커스텀 webpack 플러그인 비호환.

**변경 후 (Webpack) 장점:** 완전히 안정적, 모든 플러그인/로더 호환, 디버깅 도구 풍부.
**변경 후 단점:** 프로젝트 커지면 HMR 느려짐, Turbopack 대비 빌드 속도 열위.

---

## 종합 평가

| 관점 | 변경 전 (구 CLAUDE.md) | 변경 후 (현재 코드베이스) |
|------|----------------------|------------------------|
| **설계 철학** | 엔터프라이즈 지향 (확장성 우선) | 스타트업 지향 (속도 + 단순성 우선) |
| **외부 의존** | AWS S3, Firebase, MUI, pnpm | 최소화 (로컬 스토리지, 자체 인증) |
| **보안** | httpOnly 쿠키, 서버사이드 검증 | localStorage JWT (보안 약화 트레이드오프) |
| **개발 속도** | 느림 (DDD, R/W 분리, i18n 등 오버헤드) | 빠름 (Feature-Based, 단일 세션) |
| **확장성** | 높음 (S3, DB 분리, 다국어) | 제한적 (나중에 마이그레이션 필요) |
| **팀 온보딩** | 어려움 (많은 외부 서비스, 복잡한 패턴) | 쉬움 (Docker Compose 한 줄로 시작) |

현재 코드베이스는 **"먼저 빠르게 검증하고, 트래픽 오면 스케일"** 전략을 반영하고 있습니다. localStorage JWT 보안과 파일시스템 스토리지는 프로덕션 확장 시 우선 개선 대상입니다.

---

*분석 작성: Claude Code*
*분석일: 2026-03-01*
