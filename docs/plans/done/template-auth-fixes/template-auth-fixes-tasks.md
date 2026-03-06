# 템플릿 버그 수정 + 인증 시스템 개선 — 태스크 체크리스트

> Last Updated: 2026-03-02

---

## Phase A: 이번 세션 완료 작업 (커밋 + PR)

### Section A-1: 버그 수정 (이번 세션 완료)

- [x] A-1-1: `step_order` None 버그 수정 (`service.py:309`)
  - `data.get("step_order", next_order)` → `data.get("step_order") or next_order`
- [x] A-1-2: 템플릿 단계 DnD 순서 변경 UI 추가 (`template-detail-view.tsx`, `template-step-editor.tsx`)
  - `@hello-pangea/dnd` DragDropContext + Draggable + Droppable
  - GripVertical 드래그 핸들, optimistic update
- [x] A-1-3: FastAPI reorder 라우트 순서 충돌 해결 (`roadmap_templates.py`)
  - `/steps/reorder` 엔드포인트를 `/steps/{step_id}` 위로 이동
  - 응답에 `_serialize_step` 적용
- [x] A-1-4: Silent Refresh `suppressAuthEvent` 제거 (`api-client.ts`)
  - `suppressAuthEvent` 변수 및 조건부 로직 완전 제거
  - `clearAuthState()`가 항상 AUTH_STORAGE_EVENT 발송
- [x] A-1-5: 보안 감사 보고서 작성 (`docs/planning/completed/REPORT-auth-security-audit.md`)

### Section A-2: 품질 게이트

- [x] A-2-1: Backend pytest 전체 통과 (179 passed)
- [x] A-2-2: Frontend ESLint 0 errors
- [ ] A-2-3: 변경사항 git commit (conventional format)
- [ ] A-2-4: PR 생성 (`feature/2-template-system` → `develop`)

---

## Phase B: 인증 만료 UX 개선 [단기 1-2주]

- [x] B-1: 세션 만료 배너 + AuthGuard 컴포넌트
  - AuthGuard: 레이아웃 수준 인증 감지 → /login?expired=1 리디렉션
  - SessionExpiredBanner: 로그인 페이지에서 만료 안내 표시
  - **AC:** 어떤 페이지에서든 세션 만료 시 로그인으로 리디렉션 + 안내
- [x] B-2: 레이아웃 수준 인증 감지 → 리디렉션
  - `(dashboard)/layout.tsx`에서 AuthGuard 래핑
  - `isLoggedIn === false` 감지 시 즉시 /login 리디렉션
  - **AC:** 세션 만료 시 즉시 로그인 페이지로 이동
- [x] B-3: 네트워크 오류 시 리프레시 재시도 로직
  - `error.response` 없음 (Network Error) → 최대 3회 재시도 (1초, 2초, 3초 간격)
  - `error.response` 있음 (서버 거부) → 즉시 로그아웃
  - **AC:** Wi-Fi 전환 시 불필요한 로그아웃 방지
- [x] B-4: `returnUrl` 저장 → 재로그인 후 이전 페이지 복귀
  - AuthGuard에서 `sessionStorage.setItem("returnUrl", pathname)`
  - AuthProvider의 `login()`에서 returnUrl 읽고 navigate
  - **AC:** 로드맵 상세에서 만료 → 재로그인 → 로드맵 상세로 복귀

---

## Phase C: 백엔드 보안 강화 [단기 1-2주]

- [x] C-1: Auth 엔드포인트 Rate Limiting
  - `slowapi` 패키지 설치 + `core/rate_limit.py` 모듈 추가
  - `/auth/login`, `/auth/login/google`, `/auth/login/social/{provider}`: 5req/min per IP
  - `/auth/refresh`, `/auth/logout`: 10req/min per IP
  - 테스트에서 `limiter.enabled = False`로 비활성화
  - **AC:** 초과 시 429 Too Many Requests 응답 ✓
- [x] C-2: 하드코딩 관리자 이메일 제거
  - `auth_service.py:206` — `dojyu1928@gmail.com` 강제 superuser 부여 코드 삭제
  - DB `user.is_superuser` 플래그 기반으로 전환
  - **AC:** 코드에 이메일 하드코딩 없음
- [x] C-3: Refresh Token 개수 제한
  - `RefreshTokenRepository.evict_oldest_for_user()` 메서드 추가
  - `_build_auth_result()`에서 로그인 시 자동 호출 (max 5)
  - **AC:** 한 유저의 active token이 최대 5개
- [x] C-4: SECRET_KEY validator 강화
  - `config.py`에 `_INSECURE_SECRET_PATTERNS` 집합 추가
  - 프로덕션에서 dev 키 패턴 (`dev-*`, `secret`, `password`, `test`) 차단
  - **AC:** 프로덕션에서 dev 키 사용 시 앱 시작 실패

---

## Phase D: 인증 시스템 고도화 [중기 1개월]

- [x] D-1: Proactive Token Refresh
  - `api-client.ts`에 `scheduleProactiveRefresh()` 추가
  - JWT `exp` 클레임 base64 파싱 → 만료 5분 전 타이머 설정
  - AUTH_STORAGE_EVENT 리스너로 로그인/갱신 시 자동 재스케줄
  - 실패 시 silent (401 interceptor가 후속 처리)
  - **AC:** 사용자가 30분 연속 사용 시 401 에러 제로 ✓
- [x] D-2: 글로벌 Toast 컴포넌트 통합
  - `sonner` 라이브러리 설치 + `components/ui/sonner.tsx` Toaster 래퍼 생성
  - `layout.tsx`에 `<Toaster />` 추가 (position: top-right, richColors)
  - 18개 파일에서 `alert()` → `toast.error/success/warning/info()` 교체
  - 에러 메시지 → `toast.error()`, 성공 → `toast.success()`, 경고 → `toast.warning()`
  - **AC:** alert() 호출 전면 제거 ✓
- [x] D-3: Refresh Token DB Cleanup Task
  - ARQ worker에 `cleanup_expired_refresh_tokens` cron job 추가 (매일 03:00 UTC)
  - `RefreshTokenRepository.delete_expired_and_revoked()` 메서드 추가
  - 만료 + revoked 토큰 중 30일 경과분 삭제
  - **AC:** refresh_tokens 테이블 무제한 성장 방지 ✓
- [x] D-4: JWT `iss` 클레임 검증
  - `deps.py`의 3개 `jwt.decode()` 호출에 `issuer=settings.PROJECT_NAME` 추가
  - `get_current_user`, `get_optional_current_user`, `get_current_user_or_guest` 모두 적용
  - **AC:** 다른 서비스의 JWT 거부 ✓
- [x] D-5: `datetime.utcnow()` 통일
  - `app/` 전체에서 `datetime.now(timezone.utc)` 사용으로 교체 완료
  - RefreshToken 모델의 `default_factory`도 수정
  - timezone-aware/naive 비교 문제 해결
  - **AC:** `grep -r "utcnow()" app/` 결과 0건 ✓
- [x] D-6: CORS `allow_headers` 명시화
  - `["*"]` → `["Authorization", "Content-Type", "X-Team-Id"]`
  - **AC:** 필요한 헤더만 허용 ✓

---

## Phase E: 장기 보안 과제 [분기]

- [ ] E-1: HttpOnly + Secure + SameSite 쿠키 전환
  - 백엔드: Set-Cookie 헤더로 토큰 발급
  - 프론트엔드: localStorage 대신 쿠키 자동 전송
  - **AC:** JavaScript에서 토큰 접근 불가 (XSS 방어)
- [ ] E-2: CSP 헤더 적용
  - `Content-Security-Policy` 미들웨어 추가
  - **AC:** 인라인 스크립트 차단, CDN whitelist만 허용
- [ ] E-3: SECRET_KEY 로테이션 메커니즘
  - 복수 키 지원 (primary + fallback)
  - **AC:** 키 교체 시 기존 세션 유효 유지

---

## Progress Summary

| Phase | 완료 | 전체 | 진행률 |
|-------|------|------|--------|
| A: 이번 세션 | 7 | 9 | 78% |
| B: UX 개선 | 4 | 4 | 100% |
| C: 보안 강화 | 4 | 4 | 100% |
| D: 고도화 | 6 | 6 | 100% |
| E: 장기 | 0 | 3 | 0% |
| **합계** | **21** | **26** | **81%** |
