# REPORT: Playwright MCP 기반 프로젝트 디버깅 가이드

> 작성일: 2026-03-11
> 대상: StepZero 프로젝트 (Next.js 16 + FastAPI 모노레포)
> 도구: Playwright MCP (Claude Code 내장 플러그인)

---

## 1. 개요

### Playwright MCP란?

Claude Code에 내장된 Playwright 기반 브라우저 자동화 도구로, **실제 브라우저를 제어**하여 프론트엔드/백엔드 통합 디버깅을 수행한다. 별도 패키지 설치 없이 Claude Code 세션에서 즉시 사용 가능하다.

### 기존 테스트 도구와의 차이

| 도구 | 범위 | 특징 |
|------|------|------|
| Jest + @testing-library | 컴포넌트 단위 | jsdom 환경, API 모킹 필요 |
| Pytest | 백엔드 API 단위 | SQLite in-memory, 외부 서비스 모킹 |
| **Playwright MCP** | **풀스택 통합** | **실제 브라우저 + 실제 서버**, 사용자 시나리오 재현 |

### 사전 조건

```bash
# 최소: 프론트엔드 + 백엔드 실행
cd app-backend && make run          # localhost:8000
cd app-frontend && npx next dev     # localhost:3000

# 전체 스택 (DB + Redis 포함)
docker compose -f docker-compose.dev.yml up -d app-db app-redis
cd app-backend && make run
cd app-frontend && npx next dev
```

---

## 2. 사용 가능한 Playwright MCP 도구 전체 목록

### 2.1 네비게이션 & 페이지 제어

| 도구 | 용도 | 핵심 파라미터 |
|------|------|--------------|
| `browser_navigate` | URL로 이동 | `url` |
| `browser_navigate_back` | 뒤로 가기 | - |
| `browser_tabs` | 탭 관리 (목록/생성/닫기/선택) | `action`, `index` |
| `browser_resize` | 뷰포트 크기 변경 | `width`, `height` |
| `browser_wait_for` | 텍스트 출현/소멸/시간 대기 | `text`, `textGone`, `time` |
| `browser_close` | 브라우저 종료 | - |
| `browser_install` | 브라우저 바이너리 설치 | - |

### 2.2 페이지 분석 & 캡처

| 도구 | 용도 | 핵심 파라미터 |
|------|------|--------------|
| `browser_snapshot` | **접근성 트리 스냅샷** (액션 수행용) | `filename` |
| `browser_take_screenshot` | 스크린샷 캡처 | `fullPage`, `type`, `element`+`ref` |
| `browser_console_messages` | 콘솔 로그 수집 | `level` (error/warning/info/debug) |
| `browser_network_requests` | 네트워크 요청 기록 | `includeStatic` |
| `browser_evaluate` | JavaScript 실행 | `function`, `ref` |

### 2.3 사용자 인터랙션

| 도구 | 용도 | 핵심 파라미터 |
|------|------|--------------|
| `browser_click` | 클릭 | `ref`, `element`, `button` |
| `browser_type` | 텍스트 입력 | `ref`, `text`, `submit`, `slowly` |
| `browser_fill_form` | 폼 일괄 입력 | `fields[]` (textbox/checkbox/radio/combobox) |
| `browser_hover` | 호버 | `ref`, `element` |
| `browser_press_key` | 키보드 입력 | `key` (예: `ArrowLeft`, `Enter`) |
| `browser_select_option` | 드롭다운 선택 | `ref`, `values[]` |
| `browser_drag` | 드래그 앤 드롭 | `startRef`, `endRef` |
| `browser_file_upload` | 파일 업로드 | `paths[]` |
| `browser_handle_dialog` | alert/confirm/prompt 처리 | `accept`, `promptText` |

### 2.4 고급

| 도구 | 용도 | 핵심 파라미터 |
|------|------|--------------|
| `browser_run_code` | Playwright 코드 직접 실행 | `code` (JS 함수) |

---

## 3. 디버깅 시나리오별 실전 가이드

### 3.1 페이지 로딩 & 렌더링 디버깅

**목적:** 페이지가 정상적으로 렌더링되는지, 에러가 있는지 확인

```
Step 1: 페이지 이동
→ browser_navigate({ url: "http://localhost:3000/dashboard" })

Step 2: 접근성 스냅샷으로 DOM 구조 확인
→ browser_snapshot()
   - 렌더링된 요소 목록 확인
   - ref 값 획득 (이후 인터랙션에 사용)

Step 3: 콘솔 에러 확인
→ browser_console_messages({ level: "error" })
   - React 에러 바운더리 메시지
   - Hydration mismatch
   - undefined 참조 에러

Step 4: 시각적 확인 (필요 시)
→ browser_take_screenshot({ type: "png", fullPage: true })
```

**StepZero 주요 페이지 경로:**

| 페이지 | URL | 인증 필요 |
|--------|-----|----------|
| 로그인 | `/login` | No |
| 대시보드 | `/dashboard` | Yes |
| 로드맵 | `/roadmap` | Yes |
| 액션킷 | `/actionkit` | Yes |
| 커뮤니티 | `/growth-club` | Yes |
| 프로필 | `/profile` | Yes |
| 관리자 콘솔 | `/ops` | Yes (superuser) |
| 설정 | `/settings` | Yes |

### 3.2 인증 플로우 디버깅

**목적:** 로그인 → 토큰 발급 → 인증된 페이지 접근 검증

```
Step 1: 로그인 페이지 이동
→ browser_navigate({ url: "http://localhost:3000/login" })

Step 2: 스냅샷으로 폼 요소 ref 확인
→ browser_snapshot()

Step 3: 로그인 폼 입력
→ browser_fill_form({ fields: [
    { name: "이메일", type: "textbox", ref: "<email-ref>", value: "test@test.com" },
    { name: "비밀번호", type: "textbox", ref: "<password-ref>", value: "password123" }
  ]})

Step 4: 로그인 버튼 클릭
→ browser_click({ ref: "<submit-ref>", element: "로그인 버튼" })

Step 5: 리다이렉트 대기
→ browser_wait_for({ text: "대시보드" })

Step 6: 네트워크 요청으로 토큰 발급 확인
→ browser_network_requests({ includeStatic: false })
   - POST /api/v1/auth/login → 200 확인
   - access_token, refresh_token 응답 확인

Step 7: localStorage 토큰 확인
→ browser_evaluate({ function: "() => ({ token: localStorage.getItem('token'), refresh: localStorage.getItem('refresh_token'), team: localStorage.getItem('current_team_id') })" })
```

**디버깅 포인트:**

| 증상 | 확인 사항 | 도구 |
|------|----------|------|
| 로그인 후 리다이렉트 안됨 | 네트워크 응답 코드 확인 | `network_requests` |
| 401 에러 반복 | localStorage 토큰 존재 여부 | `evaluate` |
| 토큰 만료 후 갱신 실패 | refresh 요청 네트워크 로그 | `network_requests` |
| Google OAuth 실패 | 콘솔 에러 (CORS, client_id) | `console_messages` |

### 3.3 API 통신 디버깅

**목적:** 프론트엔드 ↔ 백엔드 API 호출 검증

```
Step 1: 페이지 이동 (인증 후)
→ browser_navigate({ url: "http://localhost:3000/roadmap" })

Step 2: 네트워크 요청 확인
→ browser_network_requests({ includeStatic: false })
   확인 항목:
   - 요청 URL이 올바른지 (base URL, prefix)
   - HTTP 메서드가 맞는지
   - 응답 상태 코드
   - CORS 에러 여부

Step 3: 실패한 요청의 상세 확인
→ browser_console_messages({ level: "error" })
   - AxiosError 메시지
   - CORS 차단 메시지
   - Network Error

Step 4: 요청 헤더 검증 (JavaScript로)
→ browser_evaluate({ function: "() => ({ token: localStorage.getItem('token') ? 'exists' : 'missing', teamId: localStorage.getItem('current_team_id') })" })
```

**StepZero API 에러 응답 형식 (RFC 9457):**

```json
{
  "type": "https://stepzero.dev/problems/roadmap-not-found",
  "title": "Roadmap Not Found",
  "status": 404,
  "detail": "로드맵을 찾을 수 없습니다",
  "error_code": "ROADMAP_NOT_FOUND",
  "timestamp": "2026-03-11T10:00:00Z"
}
```

**주요 API 엔드포인트 디버깅 체크리스트:**

| API | 메서드 | 흔한 에러 | 원인 |
|-----|--------|----------|------|
| `/api/v1/auth/login` | POST | 401 | 잘못된 자격증명 |
| `/api/v1/roadmaps` | GET | 403 | X-Team-Id 헤더 누락 |
| `/api/v1/roadmaps/jobs` | POST | 503 | Worker 미실행 |
| `/api/v1/chat/stream` | POST | CORS | SSE 스트리밍 CORS 설정 |
| `/api/v1/rag/query` | POST | 503 | RAG 벡터 미적재 |
| `/api/v1/actionkits/files/*` | GET | 404 | 파일 경로 인코딩 |

### 3.4 반응형 UI 디버깅

**목적:** 모바일/태블릿 뷰포트에서의 레이아웃 검증

```
Step 1: 모바일 뷰포트 설정
→ browser_resize({ width: 375, height: 812 })  # iPhone X

Step 2: 페이지 이동
→ browser_navigate({ url: "http://localhost:3000/dashboard" })

Step 3: 스냅샷으로 모바일 레이아웃 확인
→ browser_snapshot()
   - Sidebar 숨김 여부
   - MobileNav(z-40) 표시 여부
   - Header(z-30) 레이아웃

Step 4: 스크린샷 비교
→ browser_take_screenshot({ type: "png", fullPage: true })

Step 5: 태블릿 뷰포트로 전환
→ browser_resize({ width: 768, height: 1024 })  # iPad

Step 6: 데스크탑 복원
→ browser_resize({ width: 1920, height: 1080 })
```

**StepZero z-index 계층:**
- Header: `z-30`
- MobileNav: `z-40`
- ChatFAB/ChatPanel: `z-50`

### 3.5 로드맵 생성 플로우 (비동기 파이프라인) 디버깅

**목적:** 가장 복잡한 비동기 워크플로우 검증

```
Step 1: 로드맵 페이지 이동 (인증 상태)
→ browser_navigate({ url: "http://localhost:3000/roadmap" })

Step 2: 로드맵 생성 버튼 클릭
→ browser_snapshot()  # ref 확인
→ browser_click({ ref: "<create-btn-ref>", element: "로드맵 생성 버튼" })

Step 3: 입력 폼 작성 (스냅샷으로 필드 확인 후)
→ browser_snapshot()
→ browser_fill_form({ fields: [...] })

Step 4: 생성 요청 전송
→ browser_click({ ref: "<submit-ref>", element: "생성 버튼" })

Step 5: 비동기 Job 상태 폴링 확인
→ browser_network_requests({ includeStatic: false })
   확인: POST /api/v1/roadmaps/jobs → 201 (Job 생성)
   확인: GET /api/v1/roadmaps/jobs/{id} → 200 (폴링)

Step 6: 콘솔에서 폴링 상태 모니터링
→ browser_console_messages({ level: "info" })

Step 7: 완료 대기
→ browser_wait_for({ text: "로드맵이 생성되었습니다" })
   또는 타임아웃 확인:
→ browser_wait_for({ time: 30 })
→ browser_network_requests({ includeStatic: false })
```

**비동기 파이프라인 디버깅 포인트:**

| 단계 | 정상 | 실패 시 확인 |
|------|------|-------------|
| Job 생성 | 201 Created | Worker 연결 (Redis) |
| Job 폴링 | status: QUEUED → RUNNING → COMPLETED | Worker 로그 (`make worker`) |
| 결과 표시 | 로드맵 렌더링 | 프론트엔드 폴링 로직 |

### 3.6 AI 채팅 (SSE 스트리밍) 디버깅

**목적:** SSE 기반 실시간 스트리밍 채팅 검증

```
Step 1: 대시보드에서 채팅 위젯 열기
→ browser_navigate({ url: "http://localhost:3000/dashboard" })
→ browser_snapshot()
→ browser_click({ ref: "<chat-fab-ref>", element: "채팅 버튼" })

Step 2: 채팅 패널 렌더링 확인
→ browser_snapshot()
   - ChatPanel(z-50) 표시 확인
   - 입력 필드 ref 확인

Step 3: 메시지 입력 & 전송
→ browser_type({ ref: "<input-ref>", text: "사업자등록 방법 알려줘", submit: true })

Step 4: SSE 스트리밍 확인
→ browser_wait_for({ text: "사업자" })  # 응답 텍스트 일부
→ browser_network_requests({ includeStatic: false })
   확인: POST /api/v1/chat/stream → 200 (text/event-stream)

Step 5: 에러 시 콘솔 확인
→ browser_console_messages({ level: "error" })
   - SSE 연결 실패
   - CORS 에러 (스트리밍 특유)
   - RAG 서비스 503
```

### 3.7 관리자(Ops) 콘솔 디버깅

**목적:** superuser 전용 기능 검증

```
Step 1: superuser 계정으로 로그인 (3.2 플로우 참조)

Step 2: 관리자 페이지 이동
→ browser_navigate({ url: "http://localhost:3000/ops" })

Step 3: 권한 확인
→ browser_snapshot()
   - 정상: 관리자 대시보드 렌더링
   - 실패: 권한 에러 또는 리다이렉트

Step 4: 하위 페이지 순회
→ browser_navigate({ url: "http://localhost:3000/ops/users" })
→ browser_navigate({ url: "http://localhost:3000/ops/actionkit" })
→ browser_navigate({ url: "http://localhost:3000/ops/roadmap-templates" })

Step 5: 각 페이지 API 호출 확인
→ browser_network_requests({ includeStatic: false })
   모든 /api/v1/ops/* 요청에 require_platform_admin 의존성 적용 확인
```

### 3.8 파일 업로드/다운로드 디버깅

```
Step 1: 파일 업로드 페이지 이동
→ browser_navigate({ url: "http://localhost:3000/ops/files" })

Step 2: 파일 선택
→ browser_file_upload({ paths: ["/absolute/path/to/test-file.pdf"] })

Step 3: 업로드 진행 확인
→ browser_network_requests({ includeStatic: false })
   확인: POST /api/v1/storage/* → 200/201

Step 4: 업로드된 파일 접근
→ browser_evaluate({ function: "() => document.querySelectorAll('a[href*=\"/api/uploads\"]').length" })
```

---

## 4. 고급 디버깅 테크닉

### 4.1 JavaScript 평가를 통한 상태 검사

```javascript
// React 상태 확인 (React DevTools 없이)
browser_evaluate({
  function: "() => JSON.parse(localStorage.getItem('user') || '{}')"
})

// 인증 토큰 디코딩
browser_evaluate({
  function: "() => { const t = localStorage.getItem('token'); if (!t) return null; const p = JSON.parse(atob(t.split('.')[1])); return { sub: p.sub, exp: new Date(p.exp * 1000).toISOString(), iss: p.iss }; }"
})

// API base URL 확인
browser_evaluate({
  function: "() => ({ env: window.__NEXT_DATA__?.runtimeConfig, apiUrl: document.querySelector('meta[name=api-url]')?.content })"
})

// 현재 라우트 정보
browser_evaluate({
  function: "() => ({ pathname: location.pathname, search: location.search, hash: location.hash })"
})

// 성능 메트릭 수집
browser_evaluate({
  function: "() => { const e = performance.getEntriesByType('navigation')[0]; return { domContentLoaded: Math.round(e.domContentLoadedEventEnd), loadComplete: Math.round(e.loadEventEnd), ttfb: Math.round(e.responseStart - e.requestStart) }; }"
})
```

### 4.2 Playwright 코드 직접 실행

`browser_run_code`로 복잡한 시나리오를 한 번에 실행할 수 있다.

```javascript
// 로그인 + 특정 페이지 이동 + 데이터 수집 (올인원)
browser_run_code({
  code: `async (page) => {
    // 로그인
    await page.goto('http://localhost:3000/login');
    await page.fill('input[type="email"]', 'test@test.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard');

    // 대시보드 데이터 확인
    await page.goto('http://localhost:3000/roadmap');
    await page.waitForLoadState('networkidle');

    // 결과 수집
    const cards = await page.locator('[data-testid="roadmap-card"]').count();
    const errors = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });

    return { roadmapCards: cards, consoleErrors: errors, url: page.url() };
  }`
})
```

```javascript
// 전체 페이지 헬스체크 자동화
browser_run_code({
  code: `async (page) => {
    const pages = ['/login', '/dashboard', '/roadmap', '/actionkit', '/growth-club', '/profile'];
    const results = [];

    for (const path of pages) {
      const url = 'http://localhost:3000' + path;
      const response = await page.goto(url);
      const status = response?.status() || 'no response';
      const title = await page.title();
      results.push({ path, status, title });
    }

    return results;
  }`
})
```

### 4.3 네트워크 요청 필터링 패턴

```
# API 실패만 확인 (4xx, 5xx)
→ browser_network_requests({ includeStatic: false })
  → 결과에서 status >= 400인 항목 필터

# 정적 리소스 포함 (이미지 깨짐, 폰트 로딩 실패 등)
→ browser_network_requests({ includeStatic: true })

# 파일로 저장하여 분석
→ browser_network_requests({ includeStatic: false, filename: "network-log.txt" })
```

### 4.4 멀티 탭 시나리오

```
# 탭 1: 일반 사용자
→ browser_navigate({ url: "http://localhost:3000/dashboard" })

# 탭 2: 관리자 (새 탭)
→ browser_tabs({ action: "new" })
→ browser_navigate({ url: "http://localhost:3000/ops" })

# 탭 간 전환
→ browser_tabs({ action: "list" })   # 탭 목록 확인
→ browser_tabs({ action: "select", index: 0 })  # 첫 번째 탭 선택

# 크로스 탭 인증 동기화 테스트 (useSyncExternalStore)
→ browser_tabs({ action: "select", index: 1 })
→ browser_evaluate({ function: "() => { localStorage.removeItem('token'); window.dispatchEvent(new StorageEvent('storage', { key: 'token' })); }" })
→ browser_tabs({ action: "select", index: 0 })
→ browser_snapshot()  # 로그아웃 동기화 확인
```

---

## 5. 문제 유형별 디버깅 워크플로우

### 5.1 "화면이 하얗게 나와요" (White Screen)

```
1. browser_navigate → 해당 URL
2. browser_console_messages({ level: "error" })
   → React 에러 확인 (Hydration, import 에러, undefined 접근)
3. browser_network_requests({ includeStatic: false })
   → JS 번들 로딩 실패 여부
4. browser_evaluate({ function: "() => document.getElementById('__next')?.innerHTML?.length" })
   → React 마운트 여부 (0이면 완전 실패)
```

### 5.2 "데이터가 안 불러와져요"

```
1. browser_navigate → 해당 페이지
2. browser_network_requests({ includeStatic: false })
   → API 호출 상태 코드 확인
   → 401: 토큰 만료 → evaluate로 토큰 확인
   → 403: X-Team-Id 누락 → evaluate로 team_id 확인
   → 404: 엔드포인트 경로 오류
   → 503: 백엔드 서비스 다운
3. browser_console_messages({ level: "warning" })
   → Axios 인터셉터 에러 메시지
```

### 5.3 "로그인이 안 돼요"

```
1. browser_navigate({ url: "http://localhost:3000/login" })
2. browser_snapshot() → 폼 필드 확인
3. 로그인 시도 (fill_form + click)
4. browser_network_requests({ includeStatic: false })
   → POST /api/v1/auth/login 응답 확인
   → CORS 에러: 백엔드 BACKEND_CORS_ORIGINS 설정 확인
   → 422: 요청 본문 형식 오류 (URLEncoded vs JSON)
   → 401: 자격증명 불일치
5. browser_evaluate → localStorage 토큰 저장 확인
```

### 5.4 "채팅 응답이 안 와요"

```
1. 채팅 패널 열기 → 메시지 전송
2. browser_network_requests({ includeStatic: false })
   → POST /api/v1/chat/stream 상태 확인
   → 503: RAG 서비스 또는 OpenAI API 연결 실패
   → CORS: SSE 스트리밍 CORS 설정 문제
3. browser_console_messages({ level: "error" })
   → EventSource 또는 fetch 스트리밍 에러
4. 백엔드 로그 확인 (별도 터미널)
   → SemanticRouter 분류 결과
   → LLM API 호출 에러
```

### 5.5 "로드맵 생성이 멈춰있어요"

```
1. browser_network_requests({ includeStatic: false })
   → POST /api/v1/roadmaps/jobs → 201 확인
   → GET /api/v1/roadmaps/jobs/{id} 폴링 응답 확인
   → status 필드: QUEUED → RUNNING → COMPLETED (또는 FAILED)
2. browser_evaluate({
     function: "() => localStorage.getItem('roadmap_polling_job_id')"
   })
   → Job ID 존재 확인
3. Worker 실행 확인 (별도 터미널: make worker)
4. Redis 연결 확인 (docker compose logs app-redis)
```

---

## 6. 성능 디버깅

### 6.1 Core Web Vitals 측정

```javascript
// browser_evaluate로 Web Vitals 수집
browser_evaluate({
  function: `() => {
    return new Promise(resolve => {
      const metrics = {};

      // Navigation Timing
      const nav = performance.getEntriesByType('navigation')[0];
      metrics.ttfb = Math.round(nav.responseStart - nav.requestStart);
      metrics.domContentLoaded = Math.round(nav.domContentLoadedEventEnd);
      metrics.loadComplete = Math.round(nav.loadEventEnd);

      // Paint Timing
      const paints = performance.getEntriesByType('paint');
      paints.forEach(p => {
        if (p.name === 'first-contentful-paint') metrics.fcp = Math.round(p.startTime);
      });

      // Long Tasks (TBT 근사치)
      metrics.longTasks = performance.getEntriesByType('longtask').length;

      resolve(metrics);
    });
  }`
})
```

**StepZero 성능 목표 (CLAUDE.md 기준):**

| 메트릭 | 목표 | 측정 방법 |
|--------|------|----------|
| LCP | < 2000ms | `browser_evaluate` + PerformanceObserver |
| FCP | < 1000ms | Paint Timing API |
| CLS | < 0.1 | Layout Shift API |
| TTI | < 2500ms | Navigation Timing |
| TBT | < 300ms | Long Tasks API |

### 6.2 번들 로딩 분석

```
# 모든 정적 리소스 포함하여 네트워크 요청 확인
→ browser_network_requests({ includeStatic: true })
  → JS 청크 크기 확인
  → 불필요한 리소스 로딩 감지
  → 캐시 히트율 확인
```

---

## 7. 자동화 스크립트 예제

### 7.1 전체 페이지 스모크 테스트

```javascript
browser_run_code({
  code: `async (page) => {
    const BASE = 'http://localhost:3000';
    const publicPages = ['/login'];
    const authPages = ['/dashboard', '/roadmap', '/actionkit', '/growth-club', '/profile', '/settings'];

    const results = { public: [], auth: [] };

    // Public pages
    for (const path of publicPages) {
      const res = await page.goto(BASE + path);
      results.public.push({
        path,
        status: res?.status(),
        hasContent: (await page.locator('body').textContent()).length > 0
      });
    }

    // Login
    await page.goto(BASE + '/login');
    await page.fill('input[type="email"]', 'test@test.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/dashboard', { timeout: 10000 }).catch(() => {});

    // Auth pages
    for (const path of authPages) {
      const res = await page.goto(BASE + path);
      const errors = [];
      page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
      await page.waitForLoadState('networkidle').catch(() => {});
      results.auth.push({
        path,
        status: res?.status(),
        errors: errors.slice(0, 3)
      });
    }

    return results;
  }`
})
```

### 7.2 API 엔드포인트 연결 테스트

```javascript
browser_run_code({
  code: `async (page) => {
    const BASE = 'http://localhost:8000';
    const endpoints = [
      { method: 'GET', path: '/api/v1/auth/me' },
      { method: 'GET', path: '/api/v1/roadmaps' },
      { method: 'GET', path: '/api/v1/actionkits' },
      { method: 'GET', path: '/docs' },  // OpenAPI docs
    ];

    const results = [];
    for (const ep of endpoints) {
      const res = await page.request[ep.method.toLowerCase()](BASE + ep.path);
      results.push({
        ...ep,
        status: res.status(),
        contentType: res.headers()['content-type']
      });
    }
    return results;
  }`
})
```

---

## 8. 트러블슈팅 FAQ

### Q: 브라우저가 설치되지 않았다는 에러가 나옵니다

```
→ browser_install()
```
Chromium 바이너리를 자동 다운로드한다.

### Q: snapshot에서 ref를 찾을 수 없습니다

원인: 요소가 아직 렌더링되지 않음 또는 동적 로딩 중

```
→ browser_wait_for({ text: "예상되는 텍스트" })
→ browser_snapshot()  # 다시 시도
```

### Q: 인증이 필요한 페이지에서 로그인 상태를 유지하려면?

Playwright MCP는 세션 내에서 브라우저 상태(쿠키, localStorage)를 유지한다. 한 번 로그인하면 `browser_close()`를 호출하기 전까지 인증 상태가 유지된다.

### Q: SSE 스트리밍 응답을 어떻게 디버깅하나요?

`network_requests`로는 SSE 스트림의 개별 이벤트를 볼 수 없다. 대신:

```
1. browser_console_messages({ level: "debug" })
   → 프론트엔드 채팅 훅의 로그 확인

2. browser_evaluate({
     function: "() => document.querySelector('[data-testid=\"chat-messages\"]')?.textContent"
   })
   → 렌더링된 채팅 메시지 직접 확인
```

### Q: Docker 환경에서 localhost 접근이 안됩니다

Docker 내부에서 실행 시 `host.docker.internal` 사용:
```
→ browser_navigate({ url: "http://host.docker.internal:3000" })
```

로컬 개발 시에는 `localhost:3000` / `localhost:8000` 사용.

---

## 9. 요약: 디버깅 도구 선택 가이드

```
문제 발생
  │
  ├─ 컴포넌트 렌더링 문제 → browser_snapshot + browser_console_messages
  │
  ├─ API 통신 문제 → browser_network_requests + browser_console_messages
  │
  ├─ 인증/권한 문제 → browser_evaluate (localStorage) + browser_network_requests
  │
  ├─ 레이아웃/UI 문제 → browser_resize + browser_take_screenshot
  │
  ├─ 사용자 플로우 문제 → browser_snapshot → browser_click/type/fill_form
  │
  ├─ 성능 문제 → browser_evaluate (Performance API)
  │
  └─ 복합 시나리오 → browser_run_code (Playwright 코드 직접 실행)
```

---

## 부록: 참고 파일 경로

| 파일 | 역할 |
|------|------|
| `app-frontend/src/lib/api-client.ts` | Axios 인스턴스 + 토큰 인터셉터 |
| `app-frontend/src/providers/AuthProvider.tsx` | 인증 상태 관리 |
| `app-frontend/src/app/(dashboard)/layout.tsx` | 대시보드 레이아웃 (z-index 계층) |
| `app-backend/app/main.py` | FastAPI 앱 + 미들웨어 체인 |
| `app-backend/app/core/exceptions.py` | DDD 예외 계층 |
| `app-backend/app/api/problem.py` | RFC 9457 에러 응답 |
| `app-backend/app/api/deps.py` | 인증/팀 의존성 주입 |
| `app-backend/app/middleware/logging.py` | 요청 로깅 + request_id |
| `docker-compose.dev.yml` | 개발 환경 서비스 구성 |
