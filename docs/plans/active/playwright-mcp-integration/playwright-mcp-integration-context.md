# Context: Playwright MCP 통합 디버깅 인프라

> Last Updated: 2026-03-12

---

## Key Files

### 참고 문서
| File | Purpose |
|------|---------|
| `docs/plans/reports/REPORT-playwright-mcp-debugging-guide.md` | 원본 보고서 (시나리오별 가이드, 자동화 스크립트) |
| `CLAUDE.md` | Browser Testing 섹션 - Playwright MCP 표준 명시 |
| `docs/context/decisions.md` | 브라우저 디버깅 표준 결정 기록 |

### Phase 1: data-testid 추가 대상
| File | 추가할 testid |
|------|---------------|
| `app-frontend/src/features/auth/components/LoginForm.tsx` | `login-email`, `login-password`, `login-submit` |
| `app-frontend/src/app/(dashboard)/layout.tsx` + `app-frontend/src/features/dashboard/components/Header.tsx` | `header`, `main-content` |
| `app-frontend/src/features/dashboard/components/Sidebar.tsx` | `sidebar`, `nav-dashboard`, `nav-roadmap`, `nav-actionkit`, `nav-growth-club`, `nav-ops` |
| `app-frontend/src/features/dashboard/components/MobileNav.tsx` | 모바일 대응 nav testid (`mobile-nav-*`) |
| `app-frontend/src/features/roadmap/components/RoadmapChatIntake.tsx` | 실제 입력 필드/검증/생성 버튼 testid |
| `app-frontend/src/features/roadmap/components/RoadmapGenerationPanel.tsx` | 폴링 상태/오류 영역 등 컨테이너 testid |
| `app-frontend/src/features/chat/components/ChatFAB.tsx` | `chat-fab` |
| `app-frontend/src/features/chat/components/ChatPanel.tsx` | `chat-panel` |
| `app-frontend/src/features/chat/components/ChatInput.tsx` | `chat-input`, submit button |
| `app-frontend/src/features/chat/components/ChatWidget.tsx` | FAB ↔ Panel 전환 검증용 wrapper testid |

### Phase 2: 스크립트 생성 위치
| File | Source |
|------|--------|
| `scripts/playwright/README.md` | snippet 로드/실행 규약, 인증 전제, prerequisite 설명 |
| `scripts/playwright/smoke-test.js` | 보고서 §7.1 기반 `browser_run_code` snippet source |
| `scripts/playwright/api-health.js` | 보고서 §7.2 기반 `browser_run_code` snippet source |
| `scripts/playwright/web-vitals.js` | 보고서 §6.1 기반 `browser_run_code` snippet source |

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| `data-testid` 속성은 production 빌드에서 유지 | 현 규모에서 성능 영향 무시 가능, 디버깅 편의성 우선 |
| 스크립트는 **직접 실행형 Node 스크립트가 아니라** `browser_run_code`에 주입할 JS snippet source로 관리 | 현재 표준은 Playwright MCP이며, repo 산출물은 MCP 재사용성을 우선한다 |
| `scripts/playwright/README.md`에 snippet 사용법을 반드시 문서화 | 파일만 두고 실행 경로가 없는 상태를 방지 |
| `data-testid` 네이밍: `{feature}-{element}` 패턴 | 예: `login-email`, `roadmap-create-btn`, `chat-fab` |
| 인증 필요 시나리오는 pytest fixture 계정을 전제로 하지 않음 | `tests/conftest.py` 시드는 테스트 DB 전용이므로 dev DB에서 보장되지 않음 |
| 네비게이션 셀렉터는 `Sidebar`와 `MobileNav`를 모두 포함 | 데스크톱/모바일 회귀를 함께 잡아야 함 |
| 채팅은 FAB와 Panel의 **상태 전환**을 검증 | `ChatWidget`은 둘을 동시에 렌더링하지 않음 |

---

## Dependencies

- **Playwright MCP 플러그인**: Claude Code 설정에서 활성화 필수
- **로컬 서버**: `localhost:3000` (frontend) + `localhost:8000` (backend)
- **Docker 서비스**: `app-db` (PostgreSQL) + `app-redis` (Redis)
- **ARQ Worker**: 로드맵 생성 플로우 검증 시 `make worker` 필요
- **인증 시나리오용 계정 또는 mock 로그인 전략**: 로컬 dev DB의 실제 계정, 또는 환경별 허용된 mock/social login
- **주의**: `test@example.com` / `password123`는 pytest fixture 기준이며, 일반 개발 DB에서 자동 보장되지 않음

---

## Notes

- 보고서의 SSE 스트리밍 디버깅(§3.6)은 `network_requests`로 개별 이벤트를 볼 수 없음 → `console_messages` + `snapshot`으로 대체
- Docker 내부에서 실행 시 `host.docker.internal` 사용 필요
- z-index 계층: Header(z-30) < MobileNav(z-40) < ChatFAB/ChatPanel(z-50)
- `scripts/playwright/` 디렉터리와 README/snippet 3종 생성 완료
- login/layout/nav/roadmap/chat 핵심 프로덕션 컴포넌트에 `data-testid` 반영 완료
- 로드맵 입력 폼의 실제 인터랙션 지점은 `RoadmapGenerationPanel`이 아니라 `RoadmapChatIntake` 쪽에 위치함

---

## Performance Baseline (2026-03-12, dev mode)

> 측정 환경: Playwright MCP (Chromium), localhost dev server, social-mock 인증
> 목표값: LCP <2000ms, FCP <1000ms, CLS <0.1, TTI <2500ms, TBT <300ms

| Page | Type | FCP (ms) | LCP (ms) | CLS | TBT (ms) | TTI (ms) | TTFB (ms) | Load (ms) | Pass |
|------|------|----------|----------|-----|----------|----------|-----------|-----------|------|
| `/login` | public | 56 | 56 | 0 | 147 | 44 | 25 | 464 | ALL |
| `/dashboard` | auth | 152 | 732 | 0.0003 | 182 | 124 | 105 | 595 | ALL |
| `/roadmap` | auth | 96 | 688 | 0.0003 | 182 | 79 | 59 | 542 | ALL |
| `/actionkit` | auth | 68 | 648 | 0.0244 | 160 | 49 | 32 | 480 | ALL |
| `/growth-club` | auth | 888 | 888 | 0.0701 | 150 | 858 | 838 | 1274 | ALL |

### 회귀 감지 기준

회귀 판정 임계값은 **목표값의 80%** 도달 시 경고, **초과 시 실패**로 판단한다.

| Metric | Target | Warning (≥80%) | Fail (≥100%) |
|--------|--------|----------------|--------------|
| FCP | <1000ms | ≥800ms | ≥1000ms |
| LCP | <2000ms | ≥1600ms | ≥2000ms |
| CLS | <0.1 | ≥0.08 | ≥0.1 |
| TBT | <300ms | ≥240ms | ≥300ms |
| TTI | <2500ms | ≥2000ms | ≥2500ms |

### 관찰 사항

- `/growth-club`: TTFB 838ms, FCP 888ms로 다른 페이지 대비 현저히 느림. 이미지 리소스 404 에러 다수 (프로필 이미지/게시물 썸네일). SSR 또는 데이터 로딩 최적화 후보.
- `/actionkit`: CLS 0.0244로 다른 페이지보다 높음. 탭 전환 시 레이아웃 시프트 가능성.
- `/login`: 가장 가벼운 페이지. 모든 지표 최상.
- 전체적으로 dev mode 기준 모든 페이지가 목표치 통과.
