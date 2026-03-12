# Playwright MCP Snippets

이 디렉터리는 StepZero 브라우저 디버깅을 위한 `browser_run_code` 재사용 스니펫 소스를 관리한다.

## 파일 구성

- `smoke-test.js`: public + authenticated 페이지 스모크 점검
- `api-health.js`: 백엔드 public/protected 엔드포인트 응답 점검
- `web-vitals.js`: 현재 페이지의 Web Vitals/Navigation Timing 수집

## 사용 순서

1. 필요한 스니펫 파일을 연다.
2. 상단 설정값(`frontendBaseUrl`, `backendBaseUrl`, `auth.mode`, `credentials`)을 현재 환경에 맞게 수정한다.
3. 파일 전체 내용을 `browser_run_code({ code: "..." })`의 `code` 값으로 그대로 넣어 실행한다.

터미널에서 파일 내용을 그대로 확인할 때는 다음처럼 읽을 수 있다.

```bash
node -p "require('fs').readFileSync('scripts/playwright/smoke-test.js', 'utf8')"
```

## 인증 bootstrap 전략

- 기본값은 `public-only`다. 이 모드에서는 public 페이지/API만 검사하고 인증 시나리오는 skip 된다.
- 로컬 dev 계정이 있으면 `auth.mode = "credentials"`로 두고 `credentials`를 채운 뒤 `/login`에서 `data-testid` 기반 로그인 플로우를 사용한다.
- `ENABLE_SOCIAL_MOCK=true`인 개발 환경이면 `auth.mode = "social-mock"`으로 두고 `provider`를 지정하면 `/api/v1/auth/login/social/{provider}`를 통해 인증 상태를 주입한다.
- pytest fixture 계정(`test@example.com` 등)은 개발 DB에서 자동 보장되지 않으므로 기본값으로 넣지 않는다.

## 시나리오별 prerequisite

| 시나리오 | Frontend | Backend | DB | Redis | Worker | Auth |
|---|---|---|---|---|---|---|
| `/login` 렌더링 | 필요 | 선택 | 선택 | 선택 | 불필요 | 불필요 |
| `/dashboard`, `/actionkit`, `/growth-club`, `/profile`, `/settings` | 필요 | 필요 | 권장 | 선택 | 불필요 | 필요 |
| `/roadmap` 진입 | 필요 | 필요 | 권장 | 권장 | 불필요 | 필요 |
| 로드맵 생성 폴링/상태 확인 | 필요 | 필요 | 필요 | 필요 | 필요 | 필요 |
| `api-health.js` public endpoints | 선택 | 필요 | 선택 | 선택 | 불필요 | 불필요 |
| `api-health.js` protected endpoints | 선택 | 필요 | 권장 | 선택 | 불필요 | 필요 |
| `web-vitals.js` | 필요 | 페이지에 따라 다름 | 페이지에 따라 다름 | 페이지에 따라 다름 | 불필요 | 페이지에 따라 다름 |

## 권장 실행 루틴

1. `browser_navigate` 또는 스니펫 내부 `page.goto()`로 대상 페이지를 연다.
2. 필요한 경우 `browser_snapshot`으로 `data-testid`가 붙은 요소를 확인한다.
3. `browser_run_code`로 스니펫을 실행한다.
4. 실패한 케이스만 `browser_console_messages`, `browser_network_requests`, `browser_take_screenshot`로 추가 확인한다.
