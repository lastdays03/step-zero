# Tasks: Playwright MCP 통합 디버깅 인프라

> Last Updated: 2026-03-12

---

## Phase 0: 실행 모델 및 prerequisite 확정 [High Priority]

- [x] 0.1 `scripts/playwright/README.md` 규약 정의 (`browser_run_code` 주입 절차, 파일 역할, 사용 예시)
- [x] 0.2 인증 bootstrap 전략 확정 (local dev account / social mock / public-only fallback)
- [x] 0.3 시나리오별 prerequisite 매트릭스 정리 (frontend/backend/db/redis/worker)

## Phase 1: data-testid 속성 추가 [High Priority]

- [x] 1.1 `LoginForm` `data-testid` 추가 (`login-email`, `login-password`, `login-submit`)
- [x] 1.2 `DashboardLayout` / `Header` 컨테이너 `data-testid` 추가 (`header`, `main-content`)
- [x] 1.3 `Sidebar` + `MobileNav` 네비게이션 링크 `data-testid` 추가 (`sidebar` 포함)
- [x] 1.4 `RoadmapChatIntake` 실제 입력/검증/생성 UI `data-testid` 추가
- [x] 1.5 `RoadmapGenerationPanel` 상태/오류 영역 `data-testid` 추가
- [x] 1.6 `ChatWidget` / `ChatFAB` / `ChatPanel` / `ChatInput` 상태 전환용 `data-testid` 추가

## Phase 2: 디버깅 스크립트 정리 [Medium Priority]

- [x] 2.1 `scripts/playwright/smoke-test.js` 작성 (public + authenticated navigation smoke)
- [x] 2.2 `scripts/playwright/api-health.js` 작성 (token/teamId bootstrap 또는 skip 전략 포함)
- [x] 2.3 `scripts/playwright/web-vitals.js` 작성 (Core Web Vitals 수집 snippet)

## Phase 3: 성능 베이스라인 [Low Priority]

- [x] 3.1 주요 5개 페이지 Core Web Vitals 초기 측정 (public/auth 구분)
- [x] 3.2 성능 회귀 감지 기준 문서화 (목표 vs 실측)

---

## Completion Criteria

- [x] login/layout/nav/roadmap/chat 프로덕션 컴포넌트에 `data-testid` 반영
- [x] `scripts/playwright/README.md` + 3개 snippet source 파일 정리
- [x] 최소 1개 public 시나리오와 1개 authenticated 시나리오를 MCP로 재현 성공
- [x] `pnpm lint` 통과 확인
