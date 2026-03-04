# StepZero 인증 시스템 보안 감사 및 UX 검토 보고서

> **작성일:** 2026-03-02
> **대상:** `feature/2-template-system` 브랜치 기준
> **범위:** JWT + Refresh Token 인증 체계 전반, 수정된 Silent Refresh 포함

---

## 1. 시스템 아키텍처 요약

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                           │
│                                                                     │
│  localStorage: token, refresh_token, user, current_team_id          │
│  ┌──────────────┐  ┌─────────────────────┐  ┌───────────────────┐  │
│  │ AuthProvider  │  │ apiClient (Axios)   │  │ useSyncExternal   │  │
│  │ login/logout  │  │ request interceptor │  │ Store (탭 동기화) │  │
│  └──────────────┘  │ response interceptor│  └───────────────────┘  │
│                     │ (silent refresh)    │                          │
│                     └─────────────────────┘                          │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS
┌───────────────────────────▼─────────────────────────────────────────┐
│                       Backend (FastAPI)                              │
│                                                                     │
│  POST /auth/login          → Access Token (JWT HS256, 30분)         │
│  POST /auth/refresh        → 새 Access + Refresh (토큰 로테이션)    │
│  POST /auth/logout         → Refresh Token 폐기                     │
│                                                                     │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐    │
│  │ AuthService  │  │ RefreshTokenRepo │  │ refresh_tokens DB  │    │
│  │ 토큰 발급    │  │ 해시 저장/검증   │  │ hash, revoked,     │    │
│  │ 재사용 감지  │  │ 만료 확인        │  │ replaced_by, TTL   │    │
│  └──────────────┘  └──────────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

| 항목 | 값 | 설정 위치 |
|------|-----|----------|
| Access Token 알고리즘 | HS256 (HMAC SHA-256) | `config.py:34` |
| Access Token TTL | **30분** | `config.py:35` |
| Refresh Token 형식 | `secrets.token_urlsafe(48)` (384비트 랜덤) | `security.py:24` |
| Refresh Token TTL | **7일** | `config.py:36` |
| Refresh Token 저장 | SHA-256 해시 → DB | `security.py:27-28` |
| 비밀번호 해시 | bcrypt | `security.py:11` |

---

## 2. 보안 분석

### 2.1 잘 구현된 부분 (Good Practices)

| # | 항목 | 구현 | 참조 |
|---|------|------|------|
| G1 | **토큰 로테이션** | 리프레시 시 새 refresh token 발급, 기존 토큰은 `replaced_by`로 마킹 후 폐기 | `auth_service.py:95-112` |
| G2 | **재사용 감지** | 이미 교체된(revoked) refresh token 사용 시 해당 유저의 **모든 세션 강제 폐기** (탈취 방어) | `auth_service.py:116-134` |
| G3 | **Refresh Token 해시 저장** | 원문 대신 SHA-256 해시만 DB에 저장, DB 유출 시 토큰 원문 복원 불가 | `security.py:27-28` |
| G4 | **알고리즘 명시적 제한** | JWT decode 시 `algorithms=[settings.ALGORITHM]`로 허용 알고리즘 지정, `none` 알고리즘 공격 차단 | `deps.py:34-35` |
| G5 | **비밀번호 bcrypt** | 적절한 해시 알고리즘 사용 | `security.py:11` |
| G6 | **요청 큐잉** | 동시 다발 401 시 리프레시 1회만 실행, 나머지 요청은 큐 대기 후 일괄 재시도 | `api-client.ts:94-112` |
| G7 | **크로스탭 동기화** | `AUTH_STORAGE_EVENT` + `useSyncExternalStore`로 모든 탭의 인증 상태 동기화 | `AuthProvider.tsx:79-92` |
| G8 | **Best-effort 서버 로그아웃** | 프론트엔드 logout 시 서버에도 refresh token 폐기 요청 | `AuthProvider.tsx:162-166` |
| G9 | **CORS 명시적 Origin** | 와일드카드(`*`) 대신 허용 도메인 목록 지정 | `.env`, `main.py:58-64` |
| G10 | **사용자 상태 검증** | 리프레시 시 `user.is_active` 확인, 비활성 유저는 모든 토큰 폐기 | `auth_service.py:96-99` |

### 2.2 수정된 suppressAuthEvent 평가

**수정 전 (버그):**
```javascript
// catch block
suppressAuthEvent = true;
clearAuthState();        // AUTH_STORAGE_EVENT 발송 차단됨
suppressAuthEvent = false;
```

**수정 후:**
```javascript
// catch block
processQueue(refreshError, null);
clearAuthState();        // AUTH_STORAGE_EVENT 정상 발송
```

**업계 표준 부합 여부: 적합**

이 수정은 올바릅니다. 무한루프 우려는 다음 가드에 의해 이미 차단됩니다:

1. `clearAuthState()` → `token` 제거
2. 이후 401 발생 시 인터셉터의 `!localStorage.getItem("token")` → `true` → 바로 reject
3. 컴포넌트들이 `user === null` 상태에서 API 호출을 스킵

**결론:** `suppressAuthEvent`는 불필요한 방어 코드였으며, 오히려 UI 미갱신 버그를 야기했습니다. 제거가 올바릅니다.

### 2.3 보안 위험 사항

#### CRITICAL (즉시 조치 필요)

| # | 위험 | 현재 상태 | 위협 | 권장 조치 |
|---|------|----------|------|----------|
| C1 | **개발용 SECRET_KEY가 .env에 노출** | `.env`에 `SECRET_KEY=dev-secret-key-change-me` 하드코딩 | 이 값이 프로덕션에서 사용되면 누구나 JWT 위조 가능 | `.env`에서 제거, 프로덕션은 `.env.local` 또는 환경변수로만 주입. `config.py`의 validator가 프로덕션에서 "CHANGE_ME_IN_PROD"만 차단하므로 "dev-secret-key-change-me"는 통과함 |
| C2 | **localStorage에 토큰 저장 (XSS 취약)** | `localStorage.token`, `localStorage.refresh_token` | XSS 공격 시 토큰 탈취 가능. localStorage는 JavaScript로 자유롭게 접근 가능 | **장기 과제**: HttpOnly + Secure + SameSite 쿠키로 전환. 단기: CSP 헤더 강화, XSS 방어 |

#### HIGH (단기 개선 필요)

| # | 위험 | 현재 상태 | 위협 | 권장 조치 |
|---|------|----------|------|----------|
| H1 | **Rate limiting 미적용** | `/auth/login`, `/auth/refresh` 엔드포인트에 rate limit 없음 | 브루트포스 로그인, refresh token 무차별 대입 공격 | `slowapi` 또는 nginx level rate limiting 적용 (예: login 5회/분, refresh 10회/분) |
| H2 | **하드코딩된 관리자 이메일** | `auth_service.py:206` — 특정 이메일(`dojyu1928@gmail.com`)은 로그인 시 무조건 `is_superuser=True` | 코드 리뷰 시 노출, 이메일 탈취 시 무조건 관리자 접근 | DB 기반 관리자 지정으로 전환, 코드에서 제거 |
| H3 | **Refresh Token 누적** | `_build_auth_result()` 에서 매 로그인마다 새 refresh token 생성, 기존 것을 폐기하지 않음 | 다수 디바이스 로그인 시 유효한 refresh token 무제한 누적 | 로그인 시 기존 토큰 개수 제한 (예: 최대 5개, FIFO 폐기) |
| H4 | **`_retry` 플래그 타입 안전성** | `originalRequest._retry`를 임의 속성으로 추가 | 인터셉터 체인에서 예기치 않은 동작 가능 | TypeScript에서 명시적 타입 선언 (이미 `& { _retry?: boolean }`로 되어있어 양호) |

#### MEDIUM (중기 개선)

| # | 위험 | 현재 상태 | 위협 | 권장 조치 |
|---|------|----------|------|----------|
| M1 | **JWT `iss` 클레임 미검증** | 토큰 생성 시 `iss`를 설정하지만 decode 시 검증하지 않음 | 다른 서비스의 JWT를 이 서비스에서 수용할 수 있음 | `jwt.decode()`에 `issuer=settings.PROJECT_NAME` 옵션 추가 |
| M2 | **`jti` 클레임 부재** | JWT에 고유 ID(jti) 미포함 | Access token 블랙리스트 기능 구현 불가 | 장기 과제로 `jti` 추가 검토 |
| M3 | **Refresh Token 정리 미실행** | 만료된 refresh token이 DB에 영구 잔존 | DB 테이블 무한 증가 | 주기적 cleanup 작업 (cron/ARQ task) 추가 |
| M4 | **CORS `allow_headers=["*"]`** | 모든 헤더 허용 | 불필요하게 넓은 허용 | 필요한 헤더만 명시: `Authorization`, `Content-Type`, `X-Team-Id` |
| M5 | **Google OAuth 토큰 검증 블로킹** | `run_in_threadpool`으로 감싸지만 Google 서버 응답 지연 시 워커 스레드 점유 | 서버 응답 지연 시 인증 처리 병목 | 타임아웃 설정 추가 |
| M6 | **datetime.utcnow() 사용** | 여러 곳에서 deprecated `datetime.utcnow()` 사용 | Python 3.12+ 에서 경고, timezone-naive datetime 혼용 위험 | `datetime.now(timezone.utc)` 통일 |

### 2.4 업계 표준 대비 평가

| 기준 | RFC/표준 | StepZero 현재 상태 | 평가 |
|------|---------|-------------------|------|
| **Refresh Token 로테이션** | OAuth 2.0 Security BCP (RFC 9700 §2.2.2) | 구현됨 — 매 리프레시 시 새 토큰 발급 | **적합** |
| **토큰 재사용 감지** | OAuth 2.0 Security BCP §4.14.2 | 구현됨 — 재사용 시 전체 세션 폐기 | **적합** |
| **Refresh Token 서버 저장** | RFC 6749 §10.4 | 해시 저장 + revoked 플래그 | **적합** |
| **HTTPS 전용** | OWASP ASVS V3.4 | CORS origin이 `https://` | **적합** |
| **짧은 Access Token TTL** | RFC 6749 §5.1 | 30분 | **적합** (15-60분 권장범위 내) |
| **합리적 Refresh Token TTL** | 서비스 특성에 따라 | 7일 | **적합** (1-30일 권장범위 내) |
| **토큰 저장 방식** | OWASP ASVS V3.3 | localStorage (XSS 취약) | **부분 적합** — 쿠키 권장 |
| **알고리즘 제한** | JWT BCP (RFC 8725 §3.1) | `algorithms=[...]` 명시 | **적합** |
| **Rate Limiting** | OWASP ASVS V11.1 | 미구현 | **미달** |

---

## 3. 인증 만료 시 사용자 경험 (UX) 심층 검토

### 3.1 시나리오별 사용자 경험

#### 시나리오 A: 정상 사용 중 Access Token 만료 (30분)

```
사용자 동작 → API 호출 → 401 → Silent Refresh → 성공 → 원래 요청 재시도
```

| 항목 | 현재 상태 | 평가 |
|------|----------|------|
| 시각적 피드백 | **없음** — 완전 투명 | 양호 (의도된 동작) |
| 데이터 손실 | 없음 — 요청이 큐잉되어 자동 재시도 | 양호 |
| 사용자 인지 | 약간의 응답 지연 (리프레시 왕복 ~200ms) | 양호 |

**평가: 양호** — Silent refresh가 정상 동작하면 사용자는 아무 것도 인지하지 못합니다.

#### 시나리오 B: 30분~7일 비활성 후 복귀

```
사용자 복귀 → API 호출 → 401 → Silent Refresh → 성공 → 정상 이용
```

**평가: 양호** — Refresh token이 유효하므로 시나리오 A와 동일.

#### 시나리오 C: 7일 이상 비활성 후 복귀 (Refresh Token 만료)

```
사용자 복귀 → API 호출 → 401 → Silent Refresh 시도 → 실패
→ clearAuthState() → AUTH_STORAGE_EVENT → UI 갱신
```

| 항목 | 수정 전 | 수정 후 | 평가 |
|------|--------|--------|------|
| 인증 상태 정리 | localStorage 삭제됨 | localStorage 삭제됨 | 동일 |
| UI 갱신 | **이벤트 차단 → UI 미갱신** (버그) | 이벤트 정상 발송 → UI 갱신 | **개선됨** |
| 사용자 위치 | 현재 페이지에 머무름 | 현재 페이지에 머무름 | 아래 참조 |
| 안내 메시지 | 없음 (대시보드만 "로그인이 만료되었습니다") | 동일 | **개선 필요** |
| 로그인 페이지 이동 | 수동 클릭 필요 | 수동 클릭 필요 | **개선 필요** |

#### 시나리오 D: 긴 양식 작성 중 토큰 만료

```
사용자가 프로필/게시글 작성 (30분 이상 소요) → 저장 클릭
→ 401 → Silent Refresh → 성공하면 저장 완료 / 실패하면 에러 표시
```

| 항목 | 현재 상태 | 평가 |
|------|----------|------|
| 폼 데이터 보존 | React state에 유지됨 (브라우저 새로고침 전까지) | 양호 |
| 에러 메시지 | 컴포넌트별 에러 표시 (통일성 부족) | 개선 필요 |
| 재로그인 후 복구 | 페이지가 바뀌면 폼 데이터 유실 | **위험** |

#### 시나리오 E: 다중 탭 사용

```
탭 A에서 세션 만료 → clearAuthState() → AUTH_STORAGE_EVENT
→ 탭 B, C도 동시에 로그아웃 상태로 전환
```

**평가: 양호** — `useSyncExternalStore` + 커스텀 이벤트로 완벽한 크로스탭 동기화.

#### 시나리오 F: 네트워크 불안정 중 리프레시 실패

```
API 호출 → 401 → Silent Refresh 시도 → Network Error
→ clearAuthState() → 완전 로그아웃
```

| 항목 | 현재 상태 | 평가 |
|------|----------|------|
| 재시도 | **없음** — 1회 실패로 즉시 전체 로그아웃 | **개선 필요** |
| 오프라인 처리 | 없음 | 개선 필요 |

### 3.2 UX 문제점 상세

#### UX-1: 세션 만료 후 자동 리디렉션 없음 (HIGH)

**현재:** 사용자가 대시보드, 로드맵, 프로필 등 어디에 있든 세션 만료 후 **같은 페이지에 머무릅니다.** 사이드바의 "로그인하기" 버튼을 직접 찾아 클릭해야 합니다.

**문제:**
- 사용자가 왜 데이터가 안 나오는지 혼란
- "로그인이 만료되었습니다" 메시지는 대시보드 페이지에서만 표시 (`useDashboard.ts`)
- 다른 페이지에서는 아무 안내 없이 빈 화면 또는 에러

**권장:** 레이아웃 수준에서 `isLoggedIn === false` 감지 시 `/login`으로 리디렉션 또는 글로벌 만료 모달 표시.

#### UX-2: 세션 만료 사전 경고 없음 (MEDIUM)

**현재:** 30분 TTL이 다 되어가도 아무 경고 없음. 긴 양식을 작성하다 저장 시점에서야 만료를 알게 됨.

**권장:**
- Access token 만료 5분 전에 proactive refresh (만료 전 갱신)
- 또는 "세션이 곧 만료됩니다" 토스트 메시지

#### UX-3: 네트워크 오류 시 과도한 로그아웃 (MEDIUM)

**현재:** 리프레시 요청이 **1회 실패**하면 즉시 전체 로그아웃. 일시적 네트워크 문제와 실제 토큰 만료를 구분하지 않음.

**Axios의 `Network Error`는 다음을 모두 포함:**
- 서버 일시 장애
- Wi-Fi 전환 중 연결 끊김
- DNS 일시 오류

**권장:**
- Network Error (서버 미응답) 시 2-3회 재시도 후 로그아웃
- 401/403 응답 (토큰 무효)은 즉시 로그아웃
- 구분 기준: `error.response` 존재 여부 (있으면 서버 응답, 없으면 네트워크 문제)

#### UX-4: 통일되지 않은 에러 메시지 (LOW)

**현재:** 인증 만료 에러 메시지가 페이지마다 다름:
- 대시보드: "로그인이 만료되었습니다. 다시 로그인해 주세요."
- 다른 페이지: 각자 `alert()` 또는 컴포넌트 에러 또는 무반응

**권장:** 글로벌 토스트/스낵바 컴포넌트로 통일된 만료 알림.

#### UX-5: 만료 후 폼 데이터 유실 위험 (LOW)

**현재:** 세션 만료 → 사용자가 로그인 버튼 클릭 → `/login` 이동 → 로그인 완료 → `/dashboard`로 이동. 작성 중이던 폼 데이터는 React state에서 사라짐.

**권장:**
- 로그인 후 이전 페이지로 복귀 (`returnUrl` 파라미터)
- 또는 중요 폼은 `sessionStorage`에 임시 저장

### 3.3 사용자 경험 품질 종합 평가

| 시나리오 | 발생 빈도 | 현재 UX 품질 | 수정 후 개선 |
|---------|----------|------------|------------|
| 정상 사용 (30분 내) | 매우 높음 | 우수 | - |
| 짧은 이탈 후 복귀 (30분~7일) | 높음 | 우수 | - |
| 장기 이탈 후 복귀 (7일+) | 보통 | 불량 → 보통 | UI 갱신됨 |
| 양식 작성 중 만료 | 낮음 | 보통 | - |
| 네트워크 불안정 | 낮음 | 불량 | - |
| 다중 탭 | 보통 | 우수 | - |

---

## 4. 이번 수정(`suppressAuthEvent` 제거)의 안전성 결론

### 4.1 수정이 안전한 이유

**무한루프가 발생하지 않는 3중 가드:**

```
Guard 1: clearAuthState() → localStorage.removeItem("token")
         ↓
Guard 2: 이후 401 → interceptor → !localStorage.getItem("token") === true
         → Promise.reject (clearAuthState 재호출 없음)
         ↓
Guard 3: AUTH_STORAGE_EVENT → user=null → 컴포넌트에서 API 호출 스킵
         (NotificationBell: if (!user) return null;)
         (DashboardView: 401 catch에서 에러 메시지만 표시)
```

### 4.2 업계 표준 부합 여부

| 기준 | 판정 | 근거 |
|------|------|------|
| **RFC 6749 (OAuth 2.0)** | 부합 | Refresh token rotation + 재사용 감지 구현 |
| **RFC 8725 (JWT BCP)** | 부합 | 알고리즘 제한, 짧은 TTL |
| **OWASP Session Management** | 부분 부합 | 서버 측 토큰 폐기는 적합, localStorage 저장은 부적합 |
| **Silent Refresh 패턴** | 부합 | SPA에서의 표준적인 구현 방식 |

### 4.3 최종 판정

> **이번 수정(`suppressAuthEvent` 제거)은 보안적으로 안전하며, 오히려 기존 버그를 올바르게 수정한 것입니다.**
>
> - 보안 수준: 변화 없음 (인증 로직 자체는 변경 없음)
> - UX 개선: 세션 만료 시 UI가 즉시 갱신되어 사용자 혼란 방지
> - 안정성: 3중 가드로 무한루프 방지 보장

---

## 5. 권장 개선 로드맵

### Phase 1: 즉시 (이번 작업에 포함 가능)
- [x] `suppressAuthEvent` 제거 → UI 미갱신 버그 수정 (완료)

### Phase 2: 단기 (1-2주)
- [ ] 레이아웃 수준 인증 만료 감지 → 로그인 페이지 리디렉션 또는 글로벌 만료 모달
- [ ] 네트워크 오류 시 리프레시 재시도 (2-3회) 로직 추가
- [ ] Auth 엔드포인트 rate limiting 적용 (`slowapi`)
- [ ] 하드코딩된 관리자 이메일 제거 (`auth_service.py:206`)

### Phase 3: 중기 (1개월)
- [ ] Proactive token refresh (만료 5분 전 사전 갱신)
- [ ] 글로벌 토스트/스낵바 컴포넌트로 인증 에러 통일
- [ ] Refresh Token DB cleanup 스케줄러 (만료 토큰 정리)
- [ ] JWT `iss` 클레임 검증 추가
- [ ] 로그인 시 기존 refresh token 개수 제한 (최대 5개)

### Phase 4: 장기 (분기)
- [ ] HttpOnly + Secure + SameSite 쿠키로 토큰 저장 전환 (XSS 방어)
- [ ] CSP (Content-Security-Policy) 헤더 적용
- [ ] 로그인 후 이전 페이지 복귀 (`returnUrl`) 구현
- [ ] SECRET_KEY 로테이션 메커니즘
