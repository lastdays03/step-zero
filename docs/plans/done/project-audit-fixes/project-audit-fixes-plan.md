# PLAN: 프로젝트 감사 기반 개선 작업

> **Last Updated:** 2026-03-06
> **근거:** `docs/plans/reports/REPORT-project-audit-2026-03-06.md`
> **목표:** 프론트엔드 빌드 복구, 인증 안정화, CI 강화, UX/코드 품질 개선

---

## Executive Summary

2026-03-06 프로젝트 전수 감사에서 **프론트엔드 빌드 불가**, **refresh token 중복 저장 버그**, **CI 품질 게이트 미흡** 등 10개 항목이 발견되었다. 이 계획은 감사 보고서의 A~J 항목을 4개 Phase로 나누어 우선순위 순으로 해결한다.

---

## Phase 1: 즉시 복구 (Critical)

프론트엔드 빌드/테스트 통과를 최우선으로 복구한다.

### 1-1. chat/SSE import-export 수정 (항목 A)

**문제:** `useChat.ts:7`, `api.ts:6`, `chat/index.ts:22`, `sse.test.ts:1`이 `sse.ts`에서 `getApiBaseUrl`을 import/re-export하지만, `sse.ts`는 해당 함수를 export하지 않음 (내부에서 `@/lib/env`로부터 import하여 사용만 함).

**조치:**
- `useChat.ts`의 `getApiBaseUrl` import 경로를 `@/lib/env`로 변경
- `api.ts`의 `getApiBaseUrl` import 경로를 `@/lib/env`로 변경 (`getAuthHeaders`, `tryRefreshToken`은 `sse.ts` 유지)
- `chat/index.ts`의 `getApiBaseUrl` re-export 소스를 `@/lib/env` 기준으로 정렬
- `sse.test.ts`의 `getApiBaseUrl` import를 실제 정의 위치 기준으로 정리
- (useNotificationSSE.ts는 d4a622b에서 이미 수정 완료)

**검증:** `cd app-frontend && pnpm lint`, `cd app-frontend && pnpm test --runInBand`, `cd app-frontend && pnpm build` 성공

### 1-2. Notifications API 단일화 (항목 E)

**문제:** `notifications/api/index.ts`와 `notifications/api/notifications.ts`가 동일 API를 서로 다른 메서드명/HTTP method로 중복 구현.
- `index.ts`: `POST /read-all`, `POST /{id}/read`, `DELETE /{id}` (백엔드와 일치)
- `notifications.ts`: `PUT /read-all`, `PUT /{id}/read` (불일치) + 별도 `Notification` 타입 정의

**조치:**
1. `notifications.ts` 삭제 (또는 `index.ts`로 통합)
2. `notifications.ts`를 import하는 코드를 `index.ts` 기준으로 전환
3. `Notification` 타입은 `../types`에 통합

**검증:** `cd app-frontend && pnpm test --runInBand`, `cd app-frontend && pnpm build` 통과

### 1-3. 프론트엔드 테스트 실패 수정

**문제:** 4 failed suites, 14 failed tests

**조치:**
- 1-1, 1-2 수정 후 테스트 재실행
- 잔여 실패가 있으면 개별 분석/수정
- `cd app-frontend && pnpm lint`, `cd app-frontend && pnpm test --runInBand`, `cd app-frontend && pnpm build` 모두 통과 확인

**Effort:** M | **Priority:** P0

---

## Phase 2: 인증 안정화 (Critical)

### 2-1. refresh token 중복 저장 버그 수정 (항목 B)

**문제:** `refresh_access_token()` 흐름:
1. `_build_auth_result(user)` 호출 → 내부에서 `refresh_token_repo.create()` (1차 저장)
2. 반환 후 `result.refresh_token`의 해시로 다시 `refresh_token_repo.create()` (2차 저장)
→ 동일 토큰이 2행으로 저장됨. `token_hash`에 UNIQUE 제약 없음.

**조치:**
1. `refresh_access_token()`에서 `_build_auth_result()` 호출 시 토큰 저장 책임 분리
   - Option A: `_build_auth_result()`에서 저장하되, `refresh_access_token()`의 중복 create 삭제
   - Option B: `_build_auth_result()`는 토큰만 생성, 저장은 호출자 책임 (더 큰 리팩토링)
   - **추천: Option A** (최소 변경)
2. `token_hash`에 UNIQUE 제약 추가 검토 (Alembic 마이그레이션)
3. `mark_replaced()` 호출이 올바른 stored.id를 참조하도록 수정

**검증:**
- refresh 2회 연속 시나리오 테스트 추가
- DB에 동일 hash 중복 행 생성 안 되는지 확인
- `cd app-backend && uv run pytest -q` 통과

### 2-2. Google OAuth graceful fallback (항목 C)

**문제:** `NEXT_PUBLIC_GOOGLE_CLIENT_ID`가 비어 있으면 `GoogleOAuthProvider` 제거되지만, `SocialAuthModal`은 항상 `GoogleLogin` 렌더링 → provider 없이 사용 시 런타임 크래시.

**조치:**
1. `SocialAuthModal`에 `NEXT_PUBLIC_GOOGLE_CLIENT_ID` 존재 여부 체크 추가
2. 값 없으면 `GoogleLogin` 대신 대체 UI (이메일 로그인 안내 등) 표시
3. 환경변수 미설정 개발환경에서 로그인 모달 테스트
4. `cd app-frontend && pnpm lint` 통과 확인

**Effort:** M | **Priority:** P0

---

## Phase 3: 운영 UX 정리 (Medium)

### 3-1. Ops confirm/alert → Dialog 전환 (항목 F)

**문제:** 프로젝트 결정(2026-03-02)은 Dialog 사용을 명시했으나, 실제 Ops UI 전반에 브라우저 native `confirm/alert`가 잔존한다.

**확인된 사용처:**
- `ops/files/view.tsx:189-219`
- `ops/actionkit/view.tsx:98-106`
- `ops/actionkit/components/category-edit-modal.tsx:79`
- `ops/announcements/view.tsx:170-177`
- `ops/roadmap-templates/view.tsx:114`
- `ops/roadmap-templates/components/template-action-editor.tsx:48`
- `ops/roadmap-templates/components/template-step-editor.tsx:142`
- `ops/growth-club/view.tsx:286-395`
- `ops/users/view.tsx:314`

**조치:**
1. `rg -n "confirm\\(|alert\\(" app-frontend/src/features/ops` 기준으로 잔존 사용처를 전수 기준점으로 고정
2. `shadcn/ui AlertDialog` 기반 공통 `ConfirmDialog` 컴포넌트 작성
3. 삭제/상태변경 confirm 사용처를 전수 전환
4. `users/view.tsx`의 placeholder `alert`는 toast 또는 적절한 비차단 UI로 교체
5. 삭제 액션에 사유 입력 필드 포함 여부 검토
6. 주요 Ops 경로 수동 QA

### 3-2. 멀티팀 기본 팀 선택 안전화 (항목 G)

**문제:** `deps.py:111`에서 `scalar_one_or_none()` 사용 → 팀 2개 이상이면 `MultipleResultsFound` 예외 가능.

**조치:**
1. `scalar_one_or_none()` → `scalars().first()` 변경
2. 멀티팀 사용자 fixture 추가 + API 테스트
3. `cd app-backend && uv run pytest -q` 통과 확인

### 3-3. 테스트 warning 정리 (항목 J)

**조치:**
1. `datetime.utcnow()` → `utc_now()` 잔존 교체 (hardcode-cleanup에서 일부 완료)
2. `AsyncMock` 미대기 warning 수정
3. pytest warning budget 설정 (`filterwarnings` in `pyproject.toml`)
4. `cd app-backend && uv run pytest -q` warning 추이 확인

**Effort:** L | **Priority:** P1

---

## Phase 4: 문서/품질 게이트 (Low)

### 4-1. CI에 frontend test/build 추가 (항목 D)

**문제:** CI가 `pnpm lint`만 실행 → 빌드 실패를 놓침.

**조치:**
1. `.github/workflows/ci.yml`의 `frontend-lint` job에 `pnpm test --runInBand` 단계 추가
2. `pnpm build` 단계 추가 (또는 별도 job)
3. job 이름을 `frontend-quality`로 변경 검토

### 4-2. 문서 정합성 (항목 I)

**조치:**
1. `decisions.md:8`의 `app/api/v2/` → `app/api/v1/`로 정정
2. `docs/dev-guide/` 내 v2 잔존 참조 정리

### 4-3. Template resolution 예외 축소 (항목 H)

**조치:**
1. `roadmap_generation_service.py:207-217`의 `except Exception` → 구체적 DB 예외로 축소
2. fallback 시 structured warning 로그 추가

**Effort:** S | **Priority:** P2

---

## Risk Assessment

| 리스크 | 영향 | 완화 |
|--------|------|------|
| Phase 1 수정이 다른 테스트를 깨뜨림 | 높음 | `cd app-frontend && pnpm lint && pnpm test --runInBand && pnpm build` 후 커밋 |
| refresh token 로직 변경으로 기존 토큰 무효화 | 중간 | 기존 저장된 토큰은 영향 없음 (신규 발급만 변경) |
| CI build 단계 추가로 CI 시간 증가 | 낮음 | build cache 활용 |
| Ops Dialog 전환 시 기존 동작 누락 | 중간 | `ops` 경로 잔존 사용처 전수 검색 + 각 뷰별 수동 QA |

## Success Metrics

- `cd app-frontend && pnpm lint` 성공
- `cd app-frontend && pnpm test --runInBand` 성공
- `cd app-frontend && pnpm build` 성공
- `cd app-backend && uv run pytest -q` 성공
- refresh token 2회 연속 rotation 테스트 통과
- CI에서 frontend build 검증 활성화
