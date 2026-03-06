# Tasks: 프로젝트 감사 기반 개선 작업

> **Last Updated:** 2026-03-07

## Phase 1: 즉시 복구 (Critical) — Effort: M

### 1-1. chat/SSE import-export 수정 [항목 A]
- [x] `useChat.ts:7` — `getApiBaseUrl` import를 `@/lib/env`로 변경
- [x] `api.ts:6` — `getApiBaseUrl` import를 `@/lib/env`로 변경 (`getAuthHeaders`, `tryRefreshToken`은 `sse.ts` 유지)
- [x] `chat/index.ts` — `getApiBaseUrl` re-export 소스를 `@/lib/env` 기준으로 정렬
- [x] `chat/__tests__/sse.test.ts` — `getApiBaseUrl` import 경로를 실제 정의 위치 기준으로 정리
- [x] `cd app-frontend && pnpm lint` 성공 확인
- [x] `cd app-frontend && pnpm test --runInBand` 성공 확인
- [x] `cd app-frontend && pnpm build` 성공 확인

### 1-2. Notifications API 단일화 [항목 E]
- [x] `notifications.ts`를 import하는 코드 전수 조사
- [x] 참조를 `index.ts`의 `notificationsApi`로 전환
- [x] `notifications.ts` 삭제
- [x] `Notification` 타입이 `../types`에 통합되었는지 확인
- [x] 테스트 코드도 단일 API 기준으로 정렬

### 1-3. 프론트엔드 테스트 복구
- [x] `cd app-frontend && pnpm test --runInBand` 실행 — 잔여 실패 분석
- [x] 실패 테스트 수정
- [x] `cd app-frontend && pnpm lint && pnpm test --runInBand && pnpm build` 모두 통과 확인

---

## Phase 2: 인증 안정화 (Critical) — Effort: M

### 2-1. refresh token 중복 저장 수정 [항목 B]
- [x] `refresh_access_token()`의 중복 `create()` 호출 제거
- [x] `mark_replaced()` 호출이 `_build_auth_result` 내부 저장 ID를 참조하도록 조정
- [x] `token_hash` UNIQUE 제약 추가 여부 결정
- [x] refresh 2회 연속 rotation 테스트 추가
- [x] `cd app-backend && uv run pytest -q` 통과 확인

### 2-2. Google OAuth graceful fallback [항목 C]
- [x] `SocialAuthModal`에 Google Client ID 존재 여부 분기 추가
- [x] Client ID 없을 때 대체 UI 표시
- [x] 환경변수 미설정 상태에서 로그인 모달 동작 확인
- [x] `cd app-frontend && pnpm lint` 통과 확인

---

## Phase 3: 운영 UX 정리 (Medium) — Effort: L

### 3-1. Ops confirm/alert → Dialog 전환 [항목 F]
- [x] `rg -n "confirm\\(|alert\\(" app-frontend/src/features/ops` 기준으로 잔존 사용처 전수 확인
- [x] 공통 `ConfirmDialog` 컴포넌트 작성 (AlertDialog 기반)
- [x] `ops/files`, `ops/actionkit`, `ops/announcements` — confirm/alert 전환
- [x] `ops/roadmap-templates`, `ops/growth-club` — 잔존 confirm 전환
- [x] `ops/users/view.tsx` — placeholder `alert` 제거
- [x] 주요 Ops 경로 동작 확인

### 3-2. 멀티팀 기본 팀 선택 안전화 [항목 G]
- [x] `deps.py:111` — `scalar_one_or_none()` → `scalars().first()` 변경
- [x] 멀티팀 사용자 fixture 추가
- [x] 팀 2개 이상 사용자의 API 테스트 추가
- [x] `cd app-backend && uv run pytest -q` 통과 확인

### 3-3. 테스트 warning 정리 [항목 J]
- [x] `datetime.utcnow()` 잔존 사용처 조사 및 `utc_now()` 교체
- [x] `AsyncMock` 미대기 warning 수정
- [x] `pyproject.toml`에 warning filter 설정
- [x] warning 수 대폭 감소 확인
- [x] `cd app-backend && uv run pytest -q` warning 추이 확인

---

## Phase 4: 문서/품질 게이트 (Low) — Effort: S

### 4-1. CI에 frontend test/build 추가 [항목 D]
- [x] `ci.yml` frontend job에 `pnpm test --runInBand` 단계 추가
- [x] `ci.yml` frontend job에 `pnpm build` 단계 추가
- [x] PR 생성하여 CI 통과 확인

### 4-2. 문서 정합성 [항목 I]
- [x] `decisions.md:8` — `v2` → `v1` 정정
- [x] `docs/dev-guide/` 내 v2 잔존 참조 검색 및 정리

### 4-3. Template resolution 예외 축소 [항목 H]
- [x] `roadmap_generation_service.py:207-217` — `except Exception` → 구체적 예외
- [x] fallback 시 structured warning 로그 추가
- [x] `cd app-backend && uv run pytest -q` 통과 확인
