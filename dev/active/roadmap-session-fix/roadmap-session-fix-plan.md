# 로드맵 세션 만료 버그 수정 계획

Last Updated: 2026-02-23

## Executive Summary

로그인 후 30분이 지나면 JWT 토큰이 만료되어 로드맵 페이지에서 기존 로드맵 대신 "생성 화면"이 표시되는 버그를 수정한다. 로드맵 데이터는 DB에 안전하게 보존되어 있으며, 이것은 순수한 인증 세션 관리 문제이다.

**해결 방식**: Refresh Token 기반의 세션 자동 갱신 구현

## Current State Analysis

### 근본 원인

`GET /dashboard` 엔드포인트가 `get_optional_current_user`를 사용하는데, 이 함수는 만료된 JWT를 401로 반환하지 않고 `None`(게스트)으로 처리한다.

```python
# app-backend/app/api/deps.py:113-114
except JWTError:
    return None  # 만료된 토큰도 게스트로 처리됨!
```

### 버그 재현 흐름

1. 토큰 만료 → `GET /dashboard` 200 OK (게스트 데이터, `status: "GUEST"`)
2. 프론트엔드: `status === "GUEST"` → `hasExistingRoadmap = false`
3. `RoadmapGenerationPanel` 표시 (기존 로드맵이 있는데 생성 화면이 보임)
4. 프론트엔드의 401 인터셉터는 **절대 발동되지 않음** (200 응답이므로)

### 현재 인증 구조

- JWT access token만 사용 (refresh token 없음)
- `ACCESS_TOKEN_EXPIRE_MINUTES: int = 30` (30분 만료)
- 토큰 저장: localStorage (`token`, `user`, `current_team_id`)
- 401 인터셉터: localStorage 전체 삭제 + `AUTH_STORAGE_EVENT` 발송

### 판단: 로그아웃 vs 데이터 보존

- 로드맵 데이터는 **이미 안전** (DB에 team_id와 연결되어 저장됨)
- 문제는 만료된 세션을 "게스트"로 잘못 처리하는 것
- **올바른 처리**: 토큰이 있지만 만료됐으면 → 세션 자동 갱신 (refresh token)
- **갱신 실패 시**: 로그인 페이지로 리디렉트 (데이터는 재로그인 후 복원)

---

## Implementation Phases

### Phase 1: 백엔드 — Refresh Token 구현

#### 1-1. RefreshToken 모델 추가 [S]
- **파일**: `app-backend/app/models/refresh_token.py` (NEW)
- SQLModel 테이블: `id(UUID)`, `user_id(FK)`, `token_hash`, `expires_at`, `revoked`, `created_at`, `replaced_by`
- 7일 만료, SHA-256 해싱 저장
- `replaced_by` 필드로 토큰 로테이션 체인 추적

#### 1-2. config.py 설정 추가 [S]
- **파일**: `app-backend/app/core/config.py` (MODIFY)
- `REFRESH_TOKEN_EXPIRE_DAYS: int = 7`

#### 1-3. security.py에 refresh token 헬퍼 추가 [S]
- **파일**: `app-backend/app/core/security.py` (MODIFY)
- `create_refresh_token()`: `secrets.token_urlsafe(48)` 생성
- `hash_refresh_token()`: SHA-256 해싱

#### 1-4. RefreshToken Repository [M]
- **파일**: `app-backend/app/repositories/refresh_token_repository.py` (NEW)
- `create()`, `get_by_hash()`, `revoke()`, `revoke_all_for_user()`, `mark_replaced()`

#### 1-5. AuthService 수정 — 로그인 시 refresh token 발급 [M]
- **파일**: `app-backend/app/features/auth/application/auth_service.py` (MODIFY)
- `AuthResult`에 `refresh_token: str` 추가
- `_build_auth_result()`에서 refresh token 생성 & DB 저장
- `__init__`에 `refresh_token_repo` 추가

#### 1-6. API 스키마 수정 [S]
- **파일**: `app-backend/app/api/v1/schemas.py` (MODIFY)
- `TokenWithTeams`에 `refresh_token: str` 필드 추가

#### 1-7. POST /auth/refresh, POST /auth/logout 엔드포인트 [L]
- **파일**: `app-backend/app/api/v1/auth/router.py` (MODIFY)
- `/auth/refresh`: refresh_token → 새 access + refresh 토큰 (로테이션)
  - 만료/폐기된 토큰 → 401
  - 재사용 감지 → 해당 사용자 전체 토큰 폐기
- `/auth/logout`: refresh_token 폐기 + 204 반환
- `_auth_service()` 팩토리에 `refresh_token_repo` 추가

#### 1-8. get_optional_current_user → get_current_user_or_guest [M]
- **파일**: `app-backend/app/api/deps.py` (MODIFY)
- 새 의존성 `get_current_user_or_guest`:
  - 토큰 없음 → `None` (진짜 게스트)
  - 토큰 유효 → `AuthenticatedUser`
  - 토큰 만료 → **401** (프론트엔드에서 refresh 트리거)

```python
from jose.exceptions import ExpiredSignatureError

async def get_current_user_or_guest(...) -> AuthenticatedUser | None:
    if not token:
        return None  # 진짜 게스트
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        ...
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        return None
```

- **파일**: `app-backend/app/api/v1/dashboard/stats.py` (MODIFY)
- `get_optional_current_user` → `get_current_user_or_guest`로 교체

#### 1-9. DB 마이그레이션 [S]
- Alembic migration으로 `refresh_tokens` 테이블 생성
- `app-backend/app/core/db.py`에 모델 import 추가

---

### Phase 2: 프론트엔드 — Silent Refresh 구현

#### 2-1. API 타입 업데이트 [S]
- **파일**: `app-frontend/src/lib/api-types.ts` (MODIFY)
- `TokenWithTeams`에 `refresh_token: string` 추가

#### 2-2. API 인터셉터에 자동 갱신 로직 [L]
- **파일**: `app-frontend/src/lib/api-client.ts` (MODIFY)
- 401 수신 시 → `localStorage.getItem("refresh_token")`으로 `/auth/refresh` 호출
- 성공 → 새 토큰 저장 + 원래 요청 재시도
- 실패 → 기존대로 로그아웃 처리 (clearAuthState)
- **핵심**: 동시 401 처리를 위한 요청 큐잉 패턴
  - `isRefreshing` 플래그로 중복 refresh 방지
  - `failedQueue` 배열에 대기 요청 저장
  - refresh 완료 후 큐 일괄 처리
- `_retry` 플래그로 무한 루프 방지
- refresh 요청은 raw `axios.post` 사용 (인터셉터 재귀 방지)

#### 2-3. AuthProvider 수정 [M]
- **파일**: `app-frontend/src/providers/AuthProvider.tsx` (MODIFY)
- `login()`: `refreshToken` 파라미터 추가, localStorage에 저장
- `logout()`: `refresh_token` 제거 + 서버 `/auth/logout` best-effort 호출
- `loginWithCredentials()`: 응답에서 `refresh_token` 추출
- `AuthContextType` 인터페이스 업데이트

#### 2-4. 로그인 컴포넌트 업데이트 [S]
- **파일**: `app-frontend/src/features/auth/components/SocialAuthModal.tsx` (MODIFY)
- `completeLogin()`에서 `payload.refresh_token`을 `login()`에 전달

---

### Phase 3: 검증 및 엣지 케이스

#### 3-1. Mock 소셜 로그인 업데이트 [S]
- **파일**: `app-backend/app/api/v1/auth/router.py`
- `_login_social_mock_user()` fallback 경로에도 refresh_token 포함

#### 3-2. E2E 검증 시나리오
- 로그인 → 로드맵 생성 → 30분+ 대기 → 자동 갱신 → 로드맵 정상 표시
- refresh_token 만료(7일+) → 로그인 화면 안내
- 게스트 모드(토큰 없음) → 기존대로 게스트 대시보드
- 동시 401 (dashboard + roadmap detail 동시 호출) → 1회만 refresh
- 명시적 로그아웃 → refresh token 서버 폐기
- 기존 백엔드 테스트 33개 통과

---

## Risk Assessment

| 리스크 | 완화 방안 |
|--------|----------|
| 기존 로그인 플로우 파손 | refresh token은 순수 추가 기능. 기존 access token 흐름 변경 없음 |
| 무한 refresh 루프 | `_retry` 플래그 + raw axios 사용으로 인터셉터 재귀 차단 |
| 동시 401 race condition | 요청 큐잉 패턴으로 1회만 refresh, 나머지는 대기 후 재시도 |
| refresh token 탈취 | 단일 사용 로테이션: 매번 새 토큰 발급. 재사용 감지 시 전체 폐기 |
| DB 마이그레이션 롤백 | 새 테이블만 추가, 기존 스키마 변경 없음. 롤백 = DROP TABLE |
| 백엔드만 먼저 배포 | 프론트엔드가 `/auth/refresh` 미호출 → 기존 동작 유지 |
| 프론트엔드만 먼저 배포 | `/auth/refresh` 404 → catch에서 기존 로그아웃 동작으로 fallback |

## Success Metrics

- 토큰 만료 후 로드맵 페이지 접속 시 자동 갱신되어 정상 표시
- 사용자가 세션 만료를 인지하지 못하는 투명한 UX
- 7일 이내 재방문 시 재로그인 불필요
- 기존 테스트 전체 통과
- 보안: refresh token 단일 사용 + 재사용 감지

## Timeline Estimate

| Phase | 예상 소요 | 비고 |
|-------|----------|------|
| Phase 1 (백엔드) | 2-3시간 | 독립 배포 가능 |
| Phase 2 (프론트엔드) | 1.5-2시간 | Phase 1 완료 후 |
| Phase 3 (검증) | 0.5-1시간 | |
| **합계** | **4-6시간** | |
