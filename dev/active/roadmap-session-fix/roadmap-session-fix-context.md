# 로드맵 세션 만료 버그 — Context

Last Updated: 2026-02-23

## 근본 원인

`GET /dashboard`가 `get_optional_current_user`를 사용 → 만료된 JWT를 401이 아닌 `None`(게스트)으로 처리 → 프론트엔드가 게스트 응답을 받아 로드맵 생성 화면을 표시.

**핵심**: 401 인터셉터가 발동되지 않으므로 프론트엔드에서 토큰 만료를 감지할 수 없음.

## Key Files

### Backend — 수정 대상

| 파일 | 역할 | 변경 |
|------|------|------|
| `app-backend/app/api/deps.py` | 인증 의존성 | `get_current_user_or_guest` 추가 (만료 토큰 → 401) |
| `app-backend/app/api/v1/dashboard/stats.py` | 대시보드 API | `get_optional_current_user` → `get_current_user_or_guest` |
| `app-backend/app/api/v1/auth/router.py` | 인증 라우터 | `POST /refresh`, `POST /logout` 추가 |
| `app-backend/app/api/v1/schemas.py` | API 스키마 | `TokenWithTeams`에 `refresh_token` 추가 |
| `app-backend/app/features/auth/application/auth_service.py` | 인증 서비스 | refresh token 생성·저장 로직 |
| `app-backend/app/core/security.py` | 보안 유틸리티 | `create_refresh_token()`, `hash_refresh_token()` |
| `app-backend/app/core/config.py` | 설정 | `REFRESH_TOKEN_EXPIRE_DAYS: int = 7` |

### Backend — 신규 파일

| 파일 | 역할 |
|------|------|
| `app-backend/app/models/refresh_token.py` | RefreshToken SQLModel |
| `app-backend/app/repositories/refresh_token_repository.py` | DB CRUD |

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

## Dependencies

- `jose` (python-jose): `ExpiredSignatureError` 분리 catch 필요
- `secrets` (stdlib): refresh token 생성
- `hashlib` (stdlib): SHA-256 해싱
- Alembic: DB 마이그레이션

## Known Issues

- `app-frontend/src/features/growth-club/components/PostCard.tsx:152` — `<img>` warning (기존, 무관)
- `app-frontend/src/features/growth-club/components/CreatePostForm.tsx:227` — `<img>` warning (기존, 무관)
- `pnpm` not in PATH — `npx` 사용 필요
