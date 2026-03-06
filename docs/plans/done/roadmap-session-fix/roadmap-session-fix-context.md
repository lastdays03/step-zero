# 로드맵 세션 만료 버그 — Context

Last Updated: 2026-02-23 21:30

## 근본 원인

`GET /dashboard`가 `get_optional_current_user`를 사용 → 만료된 JWT를 401이 아닌 `None`(게스트)으로 처리 → 프론트엔드가 게스트 응답을 받아 로드맵 생성 화면을 표시.

**핵심**: 401 인터셉터가 발동되지 않으므로 프론트엔드에서 토큰 만료를 감지할 수 없음.

## 현재 구현 상태 (2026-02-23)

### 완료된 커밋 (develop 브랜치)

1. `d04015e` docs: 계획 문서 추가
2. `3e50c3a` feat: refresh token 전체 구현 (백엔드 Phase 1 + 프론트엔드 Phase 2)
3. `942083f` test: 7개 E2E 백엔드 API 테스트 추가 + timezone 비교 버그 수정
4. `e82adfa` fix: asyncpg 호환 — timezone-aware → utcnow() 전체 교체 (17개 파일)
5. `8babe2f` feat: Google 로그인 에러 로깅 추가

### 테스트 현황

- 총 **40개** 통과 (기존 33 + 신규 7)
- 신규 테스트 파일: `app-backend/tests/api/test_refresh_token.py`
- 테스트 커버리지: 로그인→refresh_token 발급, 토큰 로테이션, 재사용 감지, 무효 토큰, 게스트 모드, 만료 토큰 401, 로그아웃 폐기

## Key Files

### Backend — 수정 대상

| 파일 | 역할 | 변경 |
|------|------|------|
| `app-backend/app/api/deps.py` | 인증 의존성 | `get_current_user_or_guest` 추가 (만료 토큰 → 401) |
| `app-backend/app/api/v1/dashboard/stats.py` | 대시보드 API | `get_optional_current_user` → `get_current_user_or_guest` |
| `app-backend/app/api/v1/auth/router.py` | 인증 라우터 | `POST /refresh`, `POST /logout` 추가, 에러 로깅 추가 |
| `app-backend/app/api/v1/schemas.py` | API 스키마 | `TokenWithTeams`에 `refresh_token` 추가 |
| `app-backend/app/features/auth/application/auth_service.py` | 인증 서비스 | refresh token 생성·저장 로직 |
| `app-backend/app/core/security.py` | 보안 유틸리티 | `create_refresh_token()`, `hash_refresh_token()` |
| `app-backend/app/core/config.py` | 설정 | `REFRESH_TOKEN_EXPIRE_DAYS: int = 7` |

### Backend — 신규 파일

| 파일 | 역할 |
|------|------|
| `app-backend/app/models/refresh_token.py` | RefreshToken SQLModel |
| `app-backend/app/repositories/refresh_token_repository.py` | DB CRUD |
| `app-backend/tests/api/test_refresh_token.py` | E2E API 테스트 7개 |

### Frontend — 수정 대상

| 파일 | 역할 | 변경 |
|------|------|------|
| `app-frontend/src/lib/api-client.ts` | Axios 인터셉터 | Silent refresh + 요청 큐잉 |
| `app-frontend/src/lib/api-types.ts` | 타입 정의 | `refresh_token` 필드 추가 |
| `app-frontend/src/providers/AuthProvider.tsx` | 인증 컨텍스트 | login/logout에 refresh token 처리 |
| `app-frontend/src/features/auth/components/SocialAuthModal.tsx` | 소셜 로그인 | refresh_token 전달 |

### 참고 파일 (변경 없음)

| 파일 | 역할 |
|------|------|
| `app-frontend/src/app/(dashboard)/roadmap/page.tsx` | 로드맵 페이지 (변경 불필요 — 인터셉터에서 자동 처리) |
| `app-backend/app/features/dashboard/application/dashboard_service.py` | 대시보드 서비스 (변경 불필요) |
| `app-frontend/src/features/roadmap/components/RoadmapGenerationPanel.tsx` | 생성 패널 (기존 에러 핸들링 유지) |

## Key Decisions

1. **Refresh token 저장소**: localStorage (현재 access token과 동일 방식. HttpOnly 쿠키는 CORS 재구성 필요)
2. **Refresh token 형식**: 랜덤 문자열 (JWT 아님 — 자체 claim 불필요)
3. **토큰 로테이션**: 단일 사용. 매 refresh마다 이전 토큰 폐기 + 새 토큰 발급
4. **재사용 감지**: `replaced_by` 필드로 체인 추적. 이미 로테이션된 토큰 재사용 시 전체 폐기
5. **배포 순서**: 백엔드 먼저 (하위 호환) → 프론트엔드

## 이번 세션에서 해결한 트리키한 버그

### asyncpg timezone 호환 문제 (커밋 e82adfa)

**증상**: Google 로그인 시 503 에러. 로드맵 생성 실패.

**원인**: asyncpg는 PostgreSQL의 `TIMESTAMP WITHOUT TIME ZONE` 컬럼에 timezone-aware datetime 객체(`datetime.now(timezone.utc)`)를 거부함.

**해결**: 17개 파일에서 `datetime.now(timezone.utc)` → `datetime.utcnow()` 전체 교체.
- 이는 새로 추가한 `refresh_token.py`, `refresh_token_repository.py` 뿐 아니라 기존 파일들(`user.py`, `team.py`, `roadmap.py`, `growth_club.py` 등)도 모두 포함.

### 테스트에서 timezone 비교 버그 (커밋 942083f)

**증상**: `test_token_is_expired()` 실패. `is_expired()` 메서드가 SQLite 환경에서 timezone-naive datetime끼리 비교 실패.

**해결**: `refresh_token_repository.py`의 `is_expired()` 메서드에서 `.replace(tzinfo=None)` 적용해 timezone 정보 제거 후 비교.

## Dependencies

- `jose` (python-jose): `ExpiredSignatureError` 분리 catch 필요
- `secrets` (stdlib): refresh token 생성
- `hashlib` (stdlib): SHA-256 해싱
- Alembic: DB 마이그레이션

## Known Issues

- `app-frontend/src/features/growth-club/components/PostCard.tsx:152` — `<img>` warning (기존, 무관)
- `app-frontend/src/features/growth-club/components/CreatePostForm.tsx:227` — `<img>` warning (기존, 무관)
- `pnpm` not in PATH — `npx` 사용 필요

## 다음 세션 시작 시 할 일

1. 브라우저 E2E 테스트 진행 (tasks 3-3 ~ 3-6):
   - ACCESS_TOKEN_EXPIRE_MINUTES를 1분으로 임시 변경하여 만료 시뮬레이션
   - 로그인 → 만료 대기 → 로드맵 페이지 접근 → 자동 갱신 확인
   - 테스트 후 ACCESS_TOKEN_EXPIRE_MINUTES를 30으로 복원
2. develop → main PR 생성 및 병합 (자동 ECS 배포 트리거)
3. 프로덕션에서 Alembic 마이그레이션 적용 확인 (ECS 시작 시 자동 실행 여부 확인 필요)

## 명령어 참고

```bash
# 백엔드 테스트 실행
cd app-backend && python -m pytest tests/ -v

# 특정 테스트만 실행
cd app-backend && python -m pytest tests/api/test_refresh_token.py -v

# 프론트엔드 lint
cd app-frontend && npx next lint

# 개발 서버 실행
cd app-backend && uvicorn app.main:app --reload --port 8000
cd app-frontend && npx next dev
```
