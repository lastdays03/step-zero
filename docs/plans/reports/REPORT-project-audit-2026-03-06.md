# 프로젝트 전수 분석 보고서

> **작성일:** 2026-03-06
> **브랜치:** `feature/0-hardcode-cleanup`
> **범위:** Backend, Frontend, 인증, 저장소 설정, CI, 운영 문서
> **현황:** 분석 완료 / 수정 미착수

---

## 1. Executive Summary

전체 프로젝트를 전수 점검한 결과, **백엔드는 테스트 기준으로는 안정적이지만 프론트엔드는 현재 빌드 불가 상태**로 판단된다.

가장 큰 문제는 다음 4가지다.

1. 프론트엔드 `chat/SSE/notifications` 경로에 import-export 불일치가 있어 `pnpm build`가 실패한다.
2. refresh token 회전 로직에 중복 저장 버그가 있어 재발급 체인이 길어질수록 인증 장애 가능성이 있다.
3. `NEXT_PUBLIC_GOOGLE_CLIENT_ID`가 비어 있을 때 Google 로그인 모달이 안전하게 비활성화되지 않는다.
4. CI가 프론트엔드 `lint`만 검사해 실제 `test/build` 장애를 차단하지 못한다.

즉시 수정 우선순위는 다음과 같다.

1. 프론트엔드 build/test 복구
2. refresh token rotation 로직 수정
3. Google OAuth graceful fallback 정리
4. CI에 frontend `test` + `build` 추가

---

## 2. 검증 결과

| 항목 | 실행 결과 | 판단 |
|------|-----------|------|
| Backend 테스트 | `421 passed, 10 skipped, 185 warnings` | 기능 회귀는 크지 않음. 다만 warning 정리 필요 |
| Frontend lint | `0 errors, 1 warning` | lint만으로는 품질 보장 불가 |
| Frontend test | `4 failed suites, 14 failed tests, 17 passed suites` | 현재 실패 상태 |
| Frontend build | 실패 | 현재 배포 불가 |

### 실행한 검증 명령

```bash
cd app-backend && uv run pytest -q
cd app-frontend && pnpm lint
cd app-frontend && pnpm test --runInBand
cd app-frontend && pnpm build
```

### build 실패 원인 요약

- 실제 코드 오류:
  - `app-frontend/src/features/chat/utils/sse.ts`에서 `getApiBaseUrl`를 export하지 않음
  - `useChat.ts`, `chat/utils/api.ts`, `notifications/hooks/useNotificationSSE.ts`가 해당 export를 import함
- 환경성 보조 오류:
  - 현재 실행 환경에서는 Google Fonts fetch도 실패
  - 다만 이는 부차적이며, import-export 오류만으로도 build는 실패한다

---

## 3. 긍정적 관찰 사항

### 3.1 백엔드 기본 구조는 비교적 안정적

- `app-backend/app/features/<feature>/{application,domain}` 구조가 전반적으로 유지되고 있다.
- API 경로도 `app/api/v1` 기준으로 일관성 있게 묶여 있다.
- 전체 백엔드 테스트 수와 범위가 충분한 편이다.

### 3.2 환경파일 추적 정책은 대체로 안전함

- `git ls-files` 기준으로 `.env.example`만 추적되고, `.env`, `.env.local`은 추적되지 않는다.
- 루트 `.gitignore`도 `.env*`를 기본 차단하도록 설정되어 있다.

### 3.3 브랜치/PR 정책과 commitlint는 잘 구성돼 있음

- `.github/workflows/ci.yml`에 브랜치 흐름 검증, branch naming, commitlint가 포함돼 있다.
- 협업 절차 문서도 비교적 잘 유지되고 있다.

---

## 4. 우선순위별 개선 필요 항목

## 4.1 치명적

### A. 프론트엔드가 현재 빌드되지 않음

**증상**

- `pnpm build` 실패
- `pnpm test --runInBand` 실패
- 채팅/SSE/알림 경로가 동일 원인으로 연쇄 실패

**근거 파일**

- `app-frontend/src/features/chat/hooks/useChat.ts:6`
- `app-frontend/src/features/chat/utils/api.ts:6`
- `app-frontend/src/features/notifications/hooks/useNotificationSSE.ts:4`
- `app-frontend/src/features/chat/utils/sse.ts:1-73`

**원인**

- `sse.ts`는 `getAuthHeaders`, `tryRefreshToken`, `parseSSELine`만 export한다.
- 그러나 다른 모듈은 `getApiBaseUrl`도 여기서 export된다고 가정하고 import한다.

**영향**

- 프론트엔드 production build 실패
- 알림 SSE, 채팅 SSE, 세션 로딩 관련 기능 전반 불안정
- lint는 통과하므로 CI에서 놓치기 쉬움

**권장 조치**

1. `getApiBaseUrl` import 경로를 `@/lib/env`로 통일하거나 `sse.ts`에서 재-export
2. chat/notifications 공용 네트워크 유틸 구조 정리
3. `pnpm test`, `pnpm build`를 회귀 게이트에 추가

---

### B. refresh token rotation 로직에 중복 저장 버그 가능성

**근거 파일**

- `app-backend/app/features/auth/application/auth_service.py:86-114`
- `app-backend/app/repositories/refresh_token_repository.py:16-36`
- `app-backend/app/models/refresh_token.py:12-21`

**문제 요약**

- `refresh_access_token()`은 `_build_auth_result()`를 호출하면서 새 refresh token을 이미 저장한다.
- 그 직후 같은 토큰 해시를 다시 `create()`로 저장한다.
- 조회는 `get_by_hash()`에서 `scalar_one_or_none()`를 사용한다.
- `token_hash`에는 유니크 제약도 없다.

**예상 리스크**

- refresh token 재발급이 반복될수록 동일 해시의 active row가 복수 생성될 수 있음
- 이후 token lookup 시 `MultipleResultsFound` 또는 예기치 않은 인증 실패 가능
- 현재 테스트는 한 번의 rotation만 검증해 이 결함을 놓치고 있음

**권장 조치**

1. `_build_auth_result()`와 `refresh_access_token()` 중 한 곳만 refresh token 저장 책임을 갖도록 분리
2. `token_hash` unique 제약 추가 여부 검토
3. "두 번째 refresh까지" 검증하는 회귀 테스트 추가

---

## 4.2 높음

### C. Google Client ID가 비어 있을 때 graceful fallback이 완전하지 않음

**근거 파일**

- `app-frontend/src/app/layout.tsx:22-49`
- `app-frontend/src/features/auth/components/SocialAuthModal.tsx:13-147`
- `app-frontend/node_modules/@react-oauth/google/dist/index.esm.js:52-69`

**문제 요약**

- RootLayout은 `NEXT_PUBLIC_GOOGLE_CLIENT_ID`가 비어 있으면 `GoogleOAuthProvider`를 제거한다.
- 하지만 `SocialAuthModal`은 항상 `GoogleLogin` 컴포넌트를 렌더링한다.
- 해당 라이브러리는 provider 없이 사용되면 즉시 예외를 던진다.

**영향**

- 환경변수가 비어 있는 개발/검증 환경에서 로그인 모달을 여는 순간 런타임 크래시 가능
- 프로젝트 규칙의 "graceful fallback"을 충족하지 못함

**권장 조치**

1. `hasGoogleClientId`를 중앙 유틸로 분리
2. 값이 없으면 `GoogleLogin` 자체를 렌더링하지 않도록 수정
3. 대체 UI를 명시적으로 제공

---

### D. CI가 frontend 실제 장애를 막지 못함

**근거 파일**

- `.github/workflows/ci.yml:157-176`

**문제 요약**

- 현재 CI의 frontend job은 `pnpm lint`만 실행한다.
- 실제로 현재 상태는 `lint`는 통과하지만 `test`와 `build`는 실패한다.

**영향**

- PR green 상태로 머지되더라도 프론트엔드가 깨진 채 배포될 수 있음
- 품질 게이트가 실제 사용자 영향 문제를 놓치고 있음

**권장 조치**

1. frontend CI에 `pnpm test --runInBand`
2. frontend CI에 `pnpm build`
3. 경고만 남는 lint와 실제 배포 가능성 검사를 분리

---

## 4.3 중간

### E. Notifications API 모듈이 이중화돼 contract drift 발생

**근거 파일**

- `app-frontend/src/features/notifications/api/index.ts:1-21`
- `app-frontend/src/features/notifications/api/notifications.ts:1-29`
- `app-backend/app/api/v1/notifications.py:49-125`

**문제 요약**

- `index.ts`와 `notifications.ts`가 서로 다른 메서드명과 HTTP method를 사용한다.
- 컴포넌트와 hook이 서로 다른 API 모듈을 참조한다.
- 백엔드 구현은 `POST /read-all`, `POST /{id}/read`, `DELETE /{id}` 기준이다.

**영향**

- 테스트 코드가 둘로 갈라짐
- 프론트 API contract 유지비용 증가
- 향후 endpoint 변경 시 한쪽만 수정될 가능성 큼

**권장 조치**

1. notifications API 엔트리를 하나로 통합
2. 메서드명과 HTTP method를 백엔드와 일치시켜 정리
3. tests도 단일 entry 기준으로 정렬

---

### F. Ops UI가 여전히 `confirm/alert`에 의존

**근거 파일**

- `app-frontend/src/features/ops/files/view.tsx:189-219`
- `app-frontend/src/features/ops/actionkit/view.tsx:98-106`
- `app-frontend/src/features/ops/announcements/view.tsx:170-177`
- `docs/context/decisions.md:26`

**문제 요약**

- 프로젝트 결정 문서는 상태 변경/삭제 확인을 `Dialog`로 통일한다고 명시한다.
- 실제 구현은 여전히 브라우저 native `confirm`, `alert`를 다수 사용한다.

**영향**

- UX 일관성 저하
- 사유 입력, 상세 확인, 접근성 보완이 어려움
- 테스트 자동화와 추후 확장성도 낮음

**권장 조치**

1. `shadcn/ui Dialog` 기반 공통 Confirm 컴포넌트 작성
2. Ops 경로부터 순차 전환
3. 삭제/상태변경에 사유 입력이 필요한 액션은 별도 폼 포함

---

### G. 멀티팀 사용자 기본 팀 선택 로직이 예외에 취약

**근거 파일**

- `app-backend/app/api/deps.py:104-117`
- `app-backend/app/repositories/team_repository.py:26-44`

**문제 요약**

- 기본 팀을 고르는 의도인데 `order_by()` 후 `scalar_one_or_none()`를 사용한다.
- 사용자에게 팀이 2개 이상 있으면 첫 팀 반환이 아니라 예외가 날 수 있다.

**영향**

- 멀티팀 기능이 확장될수록 인증 후 기본 팀 로딩 실패 가능
- 현재는 프론트가 `current_team_id`를 보내는 동안 가려질 수 있으나 fallback은 취약함

**권장 조치**

1. 기본 팀 선택은 `scalars().first()` 또는 `limit(1)`로 명시
2. 멀티팀 사용자 fixture 기반 API 테스트 추가

---

## 4.4 낮음

### H. Template resolution 예외를 너무 넓게 삼켜 실제 장애를 숨길 수 있음

**근거 파일**

- `app-backend/app/features/roadmaps/application/roadmap_generation_service.py:207-217`

**문제 요약**

- `TemplateResolver.resolve()`를 `except Exception`으로 감싸고 템플릿 미사용 경로로 fallback한다.
- 의도는 "테이블 미존재 대응"으로 보이지만, 실제 쿼리 오류나 매핑 버그도 함께 숨겨진다.

**권장 조치**

1. 잡아야 하는 예외를 DB schema 관련 예외로 축소
2. fallback 시 warning 로그를 구조화해서 남기기

---

### I. 문서와 실제 API 버전 구조가 불일치

**근거 파일**

- `docs/context/decisions.md:8`
- `app-backend/app/api/v1/api.py:1-36`

**문제 요약**

- 결정 문서에는 `app/api/v2/...`가 적혀 있으나 실제 구현은 `app/api/v1/...` 기준이다.
- 신규 작업자가 문서를 진실 원천으로 믿고 잘못된 경로에 구현할 가능성이 있다.

**권장 조치**

1. `decisions.md` 정정
2. `docs/dev-guide/*`의 `v2` 잔존 문서 함께 정리

---

### J. 테스트 warning과 테스트 취약성이 누적되어 있음

**관찰 사항**

- backend pytest warning 185건
- `datetime.utcnow()` 관련 deprecation warning 존재
- `AsyncMock` 미대기 warning 존재
- frontend `file-utils` 테스트는 env helper가 import 시점 값을 캡처하는 구조 때문에 취약함

**영향**

- 실제 회귀 신호가 warning 소음에 묻힐 수 있음
- 테스트 신뢰도가 떨어짐

**권장 조치**

1. warning budget을 정하고 점진적으로 축소
2. `env.ts`는 함수 호출 시점 평가로 바꾸거나 테스트가 모듈 재로드를 사용하도록 정리
3. `AsyncMock` 기반 integration test 보강

---

## 5. 보안 및 운영 메모

- 로컬 `.env.local` 파일에는 실제 비밀값 형식의 설정이 존재하는 것으로 확인되었다.
- 현재는 `.gitignore`와 `git ls-files` 기준으로 추적되지 않아 즉시 노출 상태는 아니다.
- 다만 PR/배포 전 secret scan 또는 pre-commit 검증을 도입하는 편이 안전하다.

---

## 6. 권장 실행 순서

### Phase 1. 즉시 복구

1. chat/SSE/notifications import-export 정리
2. notifications API 단일화
3. frontend `pnpm test`, `pnpm build` 통과 복구

### Phase 2. 인증 안정화

1. refresh token 저장 책임 분리
2. token_hash uniqueness 전략 확정
3. 재발급 2회 이상 시나리오 테스트 추가

### Phase 3. 운영 UX 정리

1. Ops confirm/alert → Dialog 전환
2. 멀티팀 fallback 로직 안전화
3. warning 정리

### Phase 4. 문서/품질 게이트 정합화

1. CI에 frontend test/build 추가
2. `decisions.md`와 개발 가이드 문서 정리
3. 문서상 규칙과 구현 상태의 차이 제거

---

## 7. 결론

현재 프로젝트는 **백엔드 안정성은 양호하지만 프론트엔드 배포 가능 상태는 아님**이 핵심 결론이다.

특히 다음 두 가지는 선행 조치가 필요하다.

1. 프론트엔드 build/test 복구
2. refresh token rotation 로직 수정

이 두 축만 정리해도 사용자 영향이 큰 위험 대부분이 해소된다. 이후 CI 보강과 운영 UI 정리를 진행하면 프로젝트 전반의 품질 신뢰도를 크게 올릴 수 있다.
