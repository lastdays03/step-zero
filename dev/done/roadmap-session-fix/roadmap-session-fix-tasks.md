# 로드맵 세션 만료 버그 수정 — Tasks

Last Updated: 2026-02-23 21:30

## Phase 1: 백엔드 — Refresh Token 구현

- [x] 1-1. `app-backend/app/models/refresh_token.py` 생성 (RefreshToken SQLModel) [S]
- [x] 1-2. `app-backend/app/core/config.py`에 `REFRESH_TOKEN_EXPIRE_DAYS: int = 7` 추가 [S]
- [x] 1-3. `app-backend/app/core/security.py`에 `create_refresh_token()`, `hash_refresh_token()` 추가 [S]
- [x] 1-4. `app-backend/app/repositories/refresh_token_repository.py` 생성 [M]
- [x] 1-5. `auth_service.py` 수정 — `AuthResult`에 refresh_token 추가, 로그인 시 발급 [M]
- [x] 1-6. `schemas.py` 수정 — `TokenWithTeams`에 `refresh_token` 필드 추가 [S]
- [x] 1-7. `auth/router.py` 수정 — `POST /auth/refresh`, `POST /auth/logout` 엔드포인트 추가 [L]
- [x] 1-8. `deps.py` 수정 — `get_current_user_or_guest` 추가 (만료 토큰 → 401) [M]
  - [x] `dashboard/stats.py`에서 `get_optional_current_user` → `get_current_user_or_guest` 교체
- [x] 1-9. Alembic 마이그레이션 생성 + `db.py` 모델 import 추가 [S]
- [x] 1-10. 백엔드 테스트 통과 확인 (40개: 기존 33 + 신규 7) [M]

## Phase 2: 프론트엔드 — Silent Refresh 구현

- [x] 2-1. `api-types.ts` 수정 — `TokenWithTeams`에 `refresh_token` 추가 [S]
- [x] 2-2. `api-client.ts` 수정 — 401 인터셉터에 자동 갱신 + 요청 큐잉 [L]
  - [x] `isRefreshing` 플래그 + `failedQueue` 배열
  - [x] `_retry` 플래그로 무한 루프 방지
  - [x] raw `axios.post` 사용 (인터셉터 재귀 방지)
  - [x] `clearAuthState()` 헬퍼 함수 추출
- [x] 2-3. `AuthProvider.tsx` 수정 — login/logout에 refresh token 처리 [M]
  - [x] `login()` 시그니처에 `refreshToken` 파라미터 추가
  - [x] `logout()`에서 서버 `/auth/logout` best-effort 호출
  - [x] `loginWithCredentials()`에서 refresh_token 추출
- [x] 2-4. `SocialAuthModal.tsx` 수정 — `completeLogin()`에서 refresh_token 전달 [S]
- [x] 2-5. 프론트엔드 lint 통과 확인 [S]

## Phase 3: 검증 및 엣지 케이스

- [x] 3-1. `_login_social_mock_user()` fallback에 refresh_token 포함 [S]
- [x] 3-2. 백엔드 API 테스트 (7개): 토큰 로테이션, 재사용 감지, 무효 토큰, 게스트 모드, 만료 401, 로그아웃 폐기 ✅ 40/40 통과
- [x] 3-3. 브라우저 E2E 검증: 토큰 만료 후 로드맵 자동 갱신 확인 ✅ 수동 검증 통과
- [x] 3-4. 브라우저 E2E 검증: 동시 401 → 1회만 refresh 확인 ✅ 수동 검증 통과
- [x] 3-5. 브라우저 E2E 검증: 게스트 모드 (토큰 없음) 정상 동작 ✅ 수동 검증 통과
- [x] 3-6. 브라우저 E2E 검증: 명시적 로그아웃 → refresh token 폐기 ✅ 수동 검증 통과
- [x] 3-7. develop → main PR 생성 ✅ https://github.com/lastdays03/step-zero/pull/9
- [x] 3-8. PR 병합 완료 ✅ 2026-02-23T12:40:32Z

---

## 현재 상태 (2026-02-23 21:30)

- **개발 완료**: Phase 1, 2, 3-1, 3-2 완료. 모든 변경사항 커밋 완료.
- **현재 브랜치**: `develop`
- **남은 작업**: 브라우저 E2E 검증(3-3 ~ 3-6) 및 main 병합(3-7)
- **추가 픽스**: asyncpg 호환을 위해 `datetime.now(timezone.utc)` → `datetime.utcnow()` 전체 교체 완료

---

**Effort Legend**: S = Small (< 30min), M = Medium (30min-1h), L = Large (1-2h)
