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
- [x] A-1-5: 보안 감사 보고서 작성 (`docs/research/auth-security-audit-report.md`)

### Section A-2: 품질 게이트

- [x] A-2-1: Backend pytest 전체 통과 (179 passed)
- [x] A-2-2: Frontend ESLint 0 errors
- [ ] A-2-3: 변경사항 git commit (conventional format)
- [ ] A-2-4: PR 생성 (`feature/2-template-system` → `develop`)

---

## Phase B: 인증 만료 UX 개선 [단기 1-2주]

- [ ] B-1: 글로벌 인증 만료 토스트/모달 컴포넌트 생성
  - 세션 만료 시 "세션이 만료되었습니다. 다시 로그인해주세요." 메시지
  - shadcn/ui Dialog 또는 Toast 패턴
  - **AC:** 어떤 페이지에서든 동일한 만료 안내 표시
- [ ] B-2: 레이아웃 수준 인증 감지 → 리디렉션/모달
  - `(dashboard)/layout.tsx`에서 `isLoggedIn === false` 감지
  - **AC:** 세션 만료 시 3초 내 로그인 페이지로 이동 또는 모달 표시
- [ ] B-3: 네트워크 오류 시 리프레시 재시도 로직
  - `error.response` 없음 (Network Error) → 2-3회 재시도 후 로그아웃
  - `error.response.status === 401` (서버 거부) → 즉시 로그아웃
  - **AC:** Wi-Fi 전환 시 불필요한 로그아웃 방지
- [ ] B-4: `returnUrl` 저장 → 재로그인 후 이전 페이지 복귀
  - `sessionStorage.setItem("returnUrl", currentPath)`
  - 로그인 성공 시 returnUrl로 navigate
  - **AC:** 로드맵 상세에서 만료 → 재로그인 → 로드맵 상세로 복귀

---

## Phase C: 백엔드 보안 강화 [단기 1-2주]

- [ ] C-1: Auth 엔드포인트 Rate Limiting
  - `slowapi` 패키지 설치
  - `/auth/login`: 5req/min per IP
  - `/auth/refresh`: 10req/min per IP
  - **AC:** 초과 시 429 Too Many Requests 응답
- [ ] C-2: 하드코딩 관리자 이메일 제거
  - `auth_service.py:206` 삭제
  - DB `user.is_superuser` 플래그 기반으로 전환
  - **AC:** 코드에 이메일 하드코딩 없음
- [ ] C-3: Refresh Token 개수 제한
  - 로그인 시 해당 유저의 active refresh token 수 확인
  - 5개 초과 시 가장 오래된 것부터 폐기
  - **AC:** 한 유저의 active token이 최대 5개
- [ ] C-4: SECRET_KEY validator 강화
  - `config.py` validator에 "dev-secret-key" 패턴도 차단
  - **AC:** 프로덕션에서 dev 키 사용 시 앱 시작 실패

---

## Phase D: 인증 시스템 고도화 [중기 1개월]

- [ ] D-1: Proactive Token Refresh
  - Access Token 만료 5분 전에 백그라운드 갱신
  - JWT `exp` 클레임 파싱하여 타이머 설정
  - **AC:** 사용자가 30분 연속 사용 시 401 에러 제로
- [ ] D-2: 글로벌 Toast 컴포넌트 통합
  - shadcn/ui Toast 또는 react-hot-toast
  - 인증 에러, 저장 성공, 네트워크 오류 등 통일된 알림
  - **AC:** alert() 호출 전면 제거
- [ ] D-3: Refresh Token DB Cleanup Task
  - ARQ worker에 주기적 cleanup 작업 추가
  - 만료 + revoked 토큰 중 30일 경과분 삭제
  - **AC:** refresh_tokens 테이블 무제한 성장 방지
- [ ] D-4: JWT `iss` 클레임 검증
  - `jwt.decode()`에 `issuer=settings.PROJECT_NAME` 추가
  - **AC:** 다른 서비스의 JWT 거부
- [ ] D-5: `datetime.utcnow()` 통일
  - 전체 프로젝트에서 `datetime.now(timezone.utc)` 사용
  - **AC:** `grep -r "utcnow()" app/` 결과 0건
- [ ] D-6: CORS `allow_headers` 명시화
  - `["*"]` → `["Authorization", "Content-Type", "X-Team-Id"]`
  - **AC:** 필요한 헤더만 허용

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
| B: UX 개선 | 0 | 4 | 0% |
| C: 보안 강화 | 0 | 4 | 0% |
| D: 고도화 | 0 | 6 | 0% |
| E: 장기 | 0 | 3 | 0% |
| **합계** | **7** | **26** | **27%** |
